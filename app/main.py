import logging
from pathlib import Path
from uuid import uuid4

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.templating import Jinja2Templates

from app.config import get_settings
from app.services.ai.factory import get_ai_provider
from app.services.ai.provider import AIProvider
from app.services.analysis_service import analyze_fixtures_reports
from app.services.pipeline_orchestrator import run_mvp_autofix_verification_roundtrip
from app.services.presentable_scan import (
    filter_presentable_scan,
    presentable_from_internal_analysis,
)
from app.services.project_scan_service import (
    PayloadTooLargeError,
    analyze_local_path_relative,
    analyze_zip_bytes,
    clone_and_analyze_repo,
)
from app.services.runtime_analysis_service import analyze_fixtures_runtime
from app.services.scan_result_store import get_scan_result_store
from app.services.web_analysis_flow import execute_web_analysis, looks_like_zip

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_STATIC_DIR = Path(__file__).resolve().parent / "static"
templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

app = FastAPI(
    title="TFG Secure Code Remediation",
    description="API base del TFG para análisis y remediación asistida de vulnerabilidades",
    version="0.1.0"
)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
logger = logging.getLogger(__name__)


_ALLOWED_ZIP_CONTENT_TYPES = {
    "application/zip",
    "application/x-zip-compressed",
    "application/octet-stream",
}


def _looks_like_zip(content: bytes) -> bool:
    return looks_like_zip(content)


def _map_analysis_error(exc: Exception, *, analysis_mode: str) -> tuple[int, str, str]:
    text = str(exc)

    if isinstance(exc, PayloadTooLargeError):
        return 413, "ZIP_TOO_LARGE", text

    if isinstance(exc, PermissionError):
        if analysis_mode == "git_clone":
            return 403, "GIT_CLONE_DISABLED", text
        if analysis_mode == "local_path":
            return 403, "LOCAL_PATH_DISABLED", text
        return 403, "ANALYSIS_FORBIDDEN", text

    if isinstance(exc, FileNotFoundError):
        if analysis_mode == "local_path":
            return 404, "LOCAL_PATH_NOT_FOUND", text
        if analysis_mode == "fixture_reports":
            return 500, "FIXTURE_REPORTS_MISSING", text
        return 404, "RESOURCE_NOT_FOUND", text

    if isinstance(exc, ValueError):
        if "extensión .zip" in text:
            return 400, "ZIP_EXTENSION_REQUIRED", text
        if "firma ZIP válida" in text:
            return 400, "ZIP_INVALID_SIGNATURE", text
        if "Tipo de contenido no permitido" in text:
            return 400, "ZIP_CONTENT_TYPE_INVALID", text
        if "No se recibió contenido ZIP" in text or "ZIP está vacío" in text:
            return 400, "ZIP_EMPTY_CONTENT", text
        if "demasiadas entradas" in text:
            return 400, "ZIP_TOO_MANY_ENTRIES", text
        if "Contenido descomprimido supera" in text:
            return 400, "ZIP_DECOMPRESSED_TOO_LARGE", text
        if "URL HTTPS" in text and analysis_mode == "git_clone":
            return 400, "GIT_URL_REQUIRED", text
        if "URL demasiado larga" in text:
            return 400, "GIT_URL_INVALID", text
        if "Host no permitido" in text:
            return 400, "GIT_HOST_NOT_ALLOWED", text
        if analysis_mode == "local_path":
            return 400, "LOCAL_PATH_INVALID", text
        if "https://" in text:
            return 400, "GIT_URL_INVALID", text
        if "Modo de análisis no soportado" in text:
            return 400, "ANALYSIS_MODE_UNSUPPORTED", text
        return 400, "ANALYSIS_BAD_REQUEST", text

    if isinstance(exc, RuntimeError):
        if "comando 'git' no disponible" in text:
            return 502, "GIT_BINARY_MISSING", text
        if "git clone superó el tiempo límite" in text:
            return 502, "GIT_CLONE_TIMEOUT", text
        if "git clone falló" in text or "git clone fallo" in text:
            return 502, "GIT_CLONE_FAILED", text
        if "superó el tiempo límite" in text:
            return 502, "ANALYZER_TIMEOUT", text
        if "no generó informe" in text:
            return 502, "ANALYZER_REPORT_MISSING", text
        return 502, "ANALYSIS_RUNTIME_ERROR", text

    return 500, "ANALYSIS_INTERNAL_ERROR", text


def _error_detail(error_code: str, message: str, *, analysis_id: str) -> dict[str, str]:
    return {"error_code": error_code, "message": message, "analysis_id": analysis_id}


def _new_analysis_id() -> str:
    return uuid4().hex


def _attach_analysis_id(payload: dict, analysis_id: str) -> dict:
    out = dict(payload)
    out["analysis_id"] = analysis_id
    return out


def _log_event(event: str, *, analysis_id: str, **fields: object) -> None:
    logger.info("event=%s analysis_id=%s payload=%s", event, analysis_id, fields)


def _results_page_url(
    analysis_id: str,
    *,
    hide_info: bool = False,
    group_equivalent: bool = False,
) -> str:
    params: list[str] = []
    if hide_info:
        params.append("hide_info=true")
    if group_equivalent:
        params.append("group_equivalent=true")
    query = f"?{'&'.join(params)}" if params else ""
    return f"/results/{analysis_id}{query}"


def _results_resource_url(
    analysis_id: str,
    resource: str,
    *,
    hide_info: bool = False,
    group_equivalent: bool = False,
) -> str:
    params: list[str] = []
    if hide_info:
        params.append("hide_info=true")
    if group_equivalent:
        params.append("group_equivalent=true")
    query = f"?{'&'.join(params)}" if params else ""
    return f"/results/{analysis_id}/{resource}{query}"


def _presentable_for_analysis_id(
    analysis_id: str,
    *,
    hide_info: bool | None = None,
    group_equivalent: bool | None = None,
):
    """Carga presentable desde almacén; None si expiró."""
    stored = get_scan_result_store().get(analysis_id)
    if stored is None:
        return None, None, False, False
    hi = hide_info if hide_info is not None else stored.hide_info
    ge = group_equivalent if group_equivalent is not None else stored.group_equivalent
    scan = _scan_from_stored(stored, hide_info=hi, group_equivalent=ge)
    return stored, scan, hi, ge


def _resolve_ai_provider(*, user_requested: bool) -> AIProvider | None:
    """
    Devuelve el proveedor IA solo si el usuario lo pidió y la capa está habilitada
    en el servidor. Evita llamadas a Ollama al abrir el dashboard por defecto.
    """
    if not user_requested:
        return None
    settings = get_settings()
    if not settings.ai_explanations_enabled:
        return None
    return get_ai_provider(settings)


def _build_dashboard_scan(
    internal_scan: dict,
    *,
    hide_info: bool,
    group_equivalent: bool,
    enable_ai_explanations: bool = False,
) -> dict:
    scan = presentable_from_internal_analysis(
        internal_scan,
        group_equivalent=group_equivalent,
        ai_provider=_resolve_ai_provider(user_requested=enable_ai_explanations),
    )
    return filter_presentable_scan(scan, hide_info=hide_info)


def _web_settings_context() -> dict:
    settings = get_settings()
    provider = settings.ai_provider
    return {
        "ai_explanations_available": settings.ai_explanations_enabled,
        "ai_provider_label": provider,
        "ai_provider_hint": _ai_provider_hint(provider),
        "local_path_enabled": settings.enable_local_path
        and settings.local_analysis_root is not None,
        "enable_local_path": settings.enable_local_path,
        "local_analysis_root": str(settings.local_analysis_root)
        if settings.local_analysis_root is not None
        else None,
        "git_clone_enabled": settings.enable_git_clone,
        "git_allowed_hosts": ", ".join(sorted(settings.git_allowed_hosts)),
        "zip_max_bytes": settings.zip_max_bytes,
    }


def _scan_can_enrich_with_ai(scan: dict | None, *, ai_available: bool) -> bool:
    """True si el resultado mostrado puede enriquecerse con IA sin re-escanear (WEB-5)."""
    if not ai_available or scan is None:
        return False
    meta = scan.get("meta") or {}
    if not meta.get("analysis_id"):
        return False
    findings = scan.get("findings") or []
    if not findings:
        return False
    return any(row.get("ai_explanation") is None for row in findings)


def _enrich_presentable_scan(
    internal: dict,
    *,
    hide_info: bool,
    group_equivalent: bool,
) -> dict:
    scan = presentable_from_internal_analysis(
        internal,
        group_equivalent=group_equivalent,
        ai_provider=_resolve_ai_provider(user_requested=True),
    )
    return filter_presentable_scan(scan, hide_info=hide_info)


def _ai_provider_hint(provider: str) -> str:
    if provider == "ollama":
        return (
            "Ollama genera una explicación por hallazgo; puede tardar varios segundos "
            "en proyectos grandes."
        )
    if provider == "stub":
        return (
            "Modo stub: respuestas deterministas útiles para demostración y pruebas "
            "sin modelo externo."
        )
    return f"Proveedor configurado: {provider}."


def _ai_results_status_context(
    *,
    scan: dict | None,
    scan_used_ai: bool,
    can_enrich_with_ai: bool,
    ai_available: bool,
    provider: str,
) -> dict[str, str]:
    if scan is None:
        return {
            "ai_status_kind": "neutral",
            "ai_status_label": "IA",
            "ai_status_message": "",
        }
    if not ai_available:
        return {
            "ai_status_kind": "off",
            "ai_status_label": "IA desactivada",
            "ai_status_message": (
                "Las explicaciones IA no están habilitadas en el servidor "
                "(TFG_AI_EXPLANATIONS_ENABLED=0). El análisis SAST no depende de ellas."
            ),
        }
    if scan_used_ai:
        return {
            "ai_status_kind": "on",
            "ai_status_label": "Con explicaciones IA",
            "ai_status_message": (
                f"Este escaneo incluyó explicaciones generadas con {provider}. "
                "Puedes ajustar los filtros de vista sin repetir el análisis."
            ),
        }
    if can_enrich_with_ai:
        hint = _ai_provider_hint(provider)
        return {
            "ai_status_kind": "pending",
            "ai_status_label": "Sin IA en este escaneo",
            "ai_status_message": (
                "Puedes añadir explicaciones abajo sin volver a ejecutar Bandit ni Semgrep. "
                + hint
            ),
        }
    findings = scan.get("findings") or []
    if not findings:
        return {
            "ai_status_kind": "neutral",
            "ai_status_label": "Sin hallazgos",
            "ai_status_message": "No hay filas que enriquecer con IA en este resultado.",
        }
    return {
        "ai_status_kind": "on",
        "ai_status_label": "Explicaciones IA completas",
        "ai_status_message": "Todos los hallazgos visibles ya incluyen explicación IA.",
    }


def _persist_web_scan(
    analysis_id: str,
    internal: dict,
    *,
    analysis_mode: str,
    hide_info: bool,
    group_equivalent: bool,
    enable_ai_explanations: bool,
) -> None:
    get_scan_result_store().put(
        analysis_id,
        internal,
        analysis_mode=analysis_mode,
        hide_info=hide_info,
        group_equivalent=group_equivalent,
        enable_ai_explanations=enable_ai_explanations,
    )


def _scan_from_stored(
    stored,
    *,
    hide_info: bool | None = None,
    group_equivalent: bool | None = None,
    enable_ai_explanations: bool | None = None,
) -> dict:
    return _build_dashboard_scan(
        stored.internal,
        hide_info=hide_info if hide_info is not None else stored.hide_info,
        group_equivalent=group_equivalent
        if group_equivalent is not None
        else stored.group_equivalent,
        enable_ai_explanations=enable_ai_explanations
        if enable_ai_explanations is not None
        else stored.enable_ai_explanations,
    )


def _render_analyze(
    request: Request,
    *,
    analysis_mode: str = "upload_zip",
    enable_ai_explanations: bool = False,
    analysis_error: str | None = None,
    local_path_value: str = "",
    git_url_value: str = "",
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "analyze.html",
        {
            "request": request,
            "nav_active": "analyze",
            "analysis_mode": analysis_mode,
            "enable_ai_explanations": enable_ai_explanations,
            "analysis_error": analysis_error,
            "local_path_value": local_path_value,
            "git_url_value": git_url_value,
            **_web_settings_context(),
        },
    )


def _render_results(
    request: Request,
    *,
    scan: dict | None,
    hide_info: bool = False,
    group_equivalent: bool = False,
    analysis_error: str | None = None,
    analysis_id: str | None = None,
    scan_used_ai: bool = False,
) -> HTMLResponse:
    settings = get_settings()
    ai_available = settings.ai_explanations_enabled
    can_enrich = _scan_can_enrich_with_ai(scan, ai_available=ai_available)
    analysis_target = None
    if scan is not None:
        analysis_target = (scan.get("meta") or {}).get("analysis_target")
    results_filter_url = (
        _results_page_url(analysis_id) if analysis_id else "/analyze"
    )
    report_url = (
        _results_resource_url(
            analysis_id,
            "report",
            hide_info=hide_info,
            group_equivalent=group_equivalent,
        )
        if analysis_id
        else None
    )
    export_url = (
        _results_resource_url(
            analysis_id,
            "export.json",
            hide_info=hide_info,
            group_equivalent=group_equivalent,
        )
        if analysis_id
        else None
    )
    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "request": request,
            "nav_active": "results",
            "scan": scan,
            "hide_info": hide_info,
            "group_equivalent": group_equivalent,
            "can_enrich_with_ai": can_enrich,
            "analysis_error": analysis_error,
            "analysis_id": analysis_id,
            "analysis_target": analysis_target,
            "results_filter_url": results_filter_url,
            "report_url": report_url,
            "export_url": export_url,
            "scan_used_ai": scan_used_ai,
            **_web_settings_context(),
            **_ai_results_status_context(
                scan=scan,
                scan_used_ai=scan_used_ai,
                can_enrich_with_ai=can_enrich,
                ai_available=ai_available,
                provider=settings.ai_provider,
            ),
        },
    )


def _render_dashboard(
    request: Request,
    *,
    scan: dict | None,
    hide_info: bool,
    group_equivalent: bool,
    analysis_mode: str,
    enable_ai_explanations: bool = False,
    analysis_error: str | None = None,
    analysis_notice: str | None = None,
    local_path_value: str = "",
    git_url_value: str = "",
) -> HTMLResponse:
    settings = get_settings()
    ai_available = settings.ai_explanations_enabled
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "scan": scan,
            "hide_info": hide_info,
            "group_equivalent": group_equivalent,
            "enable_ai_explanations": enable_ai_explanations,
            "ai_explanations_available": ai_available,
            "can_enrich_with_ai": _scan_can_enrich_with_ai(scan, ai_available=ai_available),
            "ai_provider_label": settings.ai_provider,
            "analysis_mode": analysis_mode,
            "analysis_error": analysis_error,
            "analysis_notice": analysis_notice,
            "local_path_enabled": settings.enable_local_path
            and settings.local_analysis_root is not None,
            "enable_local_path": settings.enable_local_path,
            "local_analysis_root": str(settings.local_analysis_root)
            if settings.local_analysis_root is not None
            else None,
            "git_clone_enabled": settings.enable_git_clone,
            "git_allowed_hosts": ", ".join(sorted(settings.git_allowed_hosts)),
            "zip_max_bytes": settings.zip_max_bytes,
            "local_path_value": local_path_value,
            "git_url_value": git_url_value,
        },
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    """Landing v2: presentación del producto y enlace a nuevo análisis."""
    return templates.TemplateResponse(
        request,
        "home.html",
        {"request": request, "nav_active": "home", **_web_settings_context()},
    )


@app.get("/analyze", response_class=HTMLResponse)
def analyze_form(request: Request) -> HTMLResponse:
    """Formulario de análisis (solo modos reales)."""
    return _render_analyze(request)


@app.post("/analyze", response_model=None)
async def analyze_submit(
    request: Request,
    analysis_mode: str = Form(...),
    hide_info: bool = Form(False),
    group_equivalent: bool = Form(False),
    enable_ai_explanations: bool = Form(False),
    local_path: str = Form(""),
    git_url: str = Form(""),
    file: UploadFile | None = File(default=None),
) -> RedirectResponse | HTMLResponse:
    """Ejecuta SAST y redirige a la página de resultados (WEB v2 PRG)."""
    analysis_id = _new_analysis_id()
    _log_event("web_v2_analysis_start", analysis_id=analysis_id, analysis_mode=analysis_mode)
    try:
        internal = await execute_web_analysis(
            analysis_mode=analysis_mode,
            analysis_id=analysis_id,
            local_path=local_path,
            git_url=git_url,
            file=file,
            allow_demo_modes=False,
        )
        internal = _attach_analysis_id(internal, analysis_id)
        _log_event("web_v2_analysis_done", analysis_id=analysis_id, analysis_mode=analysis_mode)
        _persist_web_scan(
            analysis_id,
            internal,
            analysis_mode=analysis_mode,
            hide_info=hide_info,
            group_equivalent=group_equivalent,
            enable_ai_explanations=enable_ai_explanations,
        )
        return RedirectResponse(url=f"/results/{analysis_id}", status_code=303)
    except (FileNotFoundError, PermissionError, RuntimeError, ValueError, PayloadTooLargeError) as exc:
        _, code, msg = _map_analysis_error(exc, analysis_mode=analysis_mode)
        _log_event(
            "web_v2_analysis_error",
            analysis_id=analysis_id,
            analysis_mode=analysis_mode,
            error_code=code,
            message=msg,
        )
        return _render_analyze(
            request,
            analysis_mode=analysis_mode,
            enable_ai_explanations=enable_ai_explanations,
            analysis_error=f"[{code}] {msg} (analysis_id={analysis_id})",
            local_path_value=local_path,
            git_url_value=git_url,
        )


@app.get("/results/{analysis_id}", response_class=HTMLResponse)
def results_page(
    request: Request,
    analysis_id: str,
    hide_info: bool | None = Query(default=None),
    group_equivalent: bool | None = Query(default=None),
) -> HTMLResponse:
    """Muestra el resultado de un análisis guardado en el almacén efímero."""
    stored = get_scan_result_store().get(analysis_id)
    if stored is None:
        return _render_results(
            request,
            scan=None,
            analysis_error=(
                f"[SCAN_RESULT_EXPIRED] El resultado ya no está disponible "
                f"(analysis_id={analysis_id}). Vuelve a lanzar el análisis."
            ),
        )
    hi = hide_info if hide_info is not None else stored.hide_info
    ge = group_equivalent if group_equivalent is not None else stored.group_equivalent
    if hide_info is not None or group_equivalent is not None:
        get_scan_result_store().update_view_prefs(
            analysis_id,
            hide_info=hi,
            group_equivalent=ge,
        )
    scan = _scan_from_stored(stored, hide_info=hi, group_equivalent=ge)
    return _render_results(
        request,
        scan=scan,
        hide_info=hi,
        group_equivalent=ge,
        analysis_id=analysis_id,
        scan_used_ai=stored.enable_ai_explanations,
    )


@app.get("/results/{analysis_id}/export.json")
def results_export_json(
    analysis_id: str,
    hide_info: bool | None = Query(default=None),
    group_equivalent: bool | None = Query(default=None),
) -> JSONResponse:
    """Exporta el presentable JSON del análisis (mismos filtros que la vista web)."""
    stored, scan, hi, ge = _presentable_for_analysis_id(
        analysis_id,
        hide_info=hide_info,
        group_equivalent=group_equivalent,
    )
    if stored is None or scan is None:
        raise HTTPException(
            status_code=404,
            detail=_error_detail(
                "SCAN_RESULT_EXPIRED",
                "El resultado del análisis ya no está disponible en el servidor.",
                analysis_id=analysis_id,
            ),
        )
    return JSONResponse(content=scan)


@app.get("/results/{analysis_id}/report", response_class=HTMLResponse)
def results_report_page(
    request: Request,
    analysis_id: str,
    hide_info: bool | None = Query(default=None),
    group_equivalent: bool | None = Query(default=None),
) -> HTMLResponse:
    """Informe HTML imprimible para memoria / defensa del TFG."""
    stored, scan, hi, ge = _presentable_for_analysis_id(
        analysis_id,
        hide_info=hide_info,
        group_equivalent=group_equivalent,
    )
    if stored is None or scan is None:
        return templates.TemplateResponse(
            request,
            "report.html",
            {
                "request": request,
                "scan": None,
                "analysis_error": (
                    f"[SCAN_RESULT_EXPIRED] El resultado ya no está disponible "
                    f"(analysis_id={analysis_id})."
                ),
                "analysis_id": analysis_id,
                "hide_info": False,
                "group_equivalent": False,
                "results_url": f"/results/{analysis_id}",
            },
        )
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "report.html",
        {
            "request": request,
            "scan": scan,
            "analysis_error": None,
            "analysis_id": analysis_id,
            "hide_info": hi,
            "group_equivalent": ge,
            "results_url": _results_page_url(analysis_id, hide_info=hi, group_equivalent=ge),
            "export_url": _results_resource_url(
                analysis_id,
                "export.json",
                hide_info=hi,
                group_equivalent=ge,
            ),
            "scan_used_ai": stored.enable_ai_explanations,
            "ai_explanations_available": settings.ai_explanations_enabled,
        },
    )


@app.post("/results/{analysis_id}/view-prefs", response_model=None)
def results_view_prefs(
    analysis_id: str,
    hide_info: bool = Form(False),
    group_equivalent: bool = Form(False),
) -> RedirectResponse:
    """Actualiza filtros de vista sin re-ejecutar SAST."""
    stored = get_scan_result_store().get(analysis_id)
    if stored is None:
        return RedirectResponse(url=f"/results/{analysis_id}", status_code=303)
    get_scan_result_store().update_view_prefs(
        analysis_id,
        hide_info=hide_info,
        group_equivalent=group_equivalent,
    )
    return RedirectResponse(
        url=_results_page_url(
            analysis_id,
            hide_info=hide_info,
            group_equivalent=group_equivalent,
        ),
        status_code=303,
    )


@app.post("/results/{analysis_id}/enrich-ai", response_model=None)
def results_enrich_ai(
    request: Request,
    analysis_id: str,
    hide_info: bool = Form(False),
    group_equivalent: bool = Form(False),
) -> RedirectResponse | HTMLResponse:
    """Añade explicaciones IA sin re-escanear y redirige a resultados."""
    settings = get_settings()
    if not settings.ai_explanations_enabled:
        return _render_results(
            request,
            scan=None,
            analysis_error=(
                "[AI_DISABLED] Las explicaciones IA están desactivadas "
                "(TFG_AI_EXPLANATIONS_ENABLED=0)."
            ),
        )
    stored = get_scan_result_store().get(analysis_id)
    if stored is None:
        return _render_results(
            request,
            scan=None,
            analysis_error=(
                f"[SCAN_RESULT_EXPIRED] El resultado ya no está disponible "
                f"(analysis_id={analysis_id})."
            ),
        )
    _log_event("web_v2_enrich_ai_start", analysis_id=analysis_id)
    get_scan_result_store().mark_ai_enriched(analysis_id)
    get_scan_result_store().update_view_prefs(
        analysis_id,
        hide_info=hide_info,
        group_equivalent=group_equivalent,
    )
    _log_event("web_v2_enrich_ai_done", analysis_id=analysis_id)
    return RedirectResponse(
        url=_results_page_url(
            analysis_id,
            hide_info=hide_info,
            group_equivalent=group_equivalent,
        ),
        status_code=303,
    )


@app.get("/dashboard", response_class=RedirectResponse)
def dashboard_legacy_redirect() -> RedirectResponse:
    """Compatibilidad: la consola antigua redirige al formulario v2."""
    return RedirectResponse(url="/analyze", status_code=302)


@app.get("/dashboard-legacy", response_class=HTMLResponse)
def dashboard(
    request: Request,
    hide_info: bool = Query(
        default=False,
        description="Oculta hallazgos solo detección o severidad baja (vista demo).",
    ),
    group_equivalent: bool = Query(
        default=False,
        description="Agrupa hallazgos del mismo fichero/línea/categoría MVP (Bandit+Semgrep).",
    ),
) -> HTMLResponse:
    """Dashboard principal: carga por defecto los informes estáticos del corpus MVP."""
    scan: dict | None = None
    notice: str | None = None
    try:
        scan = _build_dashboard_scan(
            analyze_fixtures_reports(),
            hide_info=hide_info,
            group_equivalent=group_equivalent,
        )
    except FileNotFoundError as exc:
        notice = (
            "No se encontraron informes estáticos del corpus MVP. "
            "Puedes relanzar análisis con 'Ejecutar fixtures' o usar 'Subir ZIP'. "
            f"Detalle técnico: {exc}"
        )
    return _render_dashboard(
        request,
        scan=scan,
        hide_info=hide_info,
        group_equivalent=group_equivalent,
        analysis_mode="fixture_reports",
        analysis_notice=notice,
    )


@app.post("/dashboard/analyze", response_model=None)
async def dashboard_analyze(
    request: Request,
    analysis_mode: str = Form(...),
    hide_info: bool = Form(False),
    group_equivalent: bool = Form(False),
    enable_ai_explanations: bool = Form(False),
    local_path: str = Form(""),
    git_url: str = Form(""),
    file: UploadFile | None = File(default=None),
) -> RedirectResponse | HTMLResponse:
    """
    Ruta legacy: mismo flujo que /analyze pero permite modos demo para tests/CI.
    """
    analysis_id = _new_analysis_id()
    _log_event("dashboard_analysis_start", analysis_id=analysis_id, analysis_mode=analysis_mode)
    try:
        internal = await execute_web_analysis(
            analysis_mode=analysis_mode,
            analysis_id=analysis_id,
            local_path=local_path,
            git_url=git_url,
            file=file,
            allow_demo_modes=True,
        )
        internal = _attach_analysis_id(internal, analysis_id)
        _log_event("dashboard_analysis_done", analysis_id=analysis_id, analysis_mode=analysis_mode)
        _persist_web_scan(
            analysis_id,
            internal,
            analysis_mode=analysis_mode,
            hide_info=hide_info,
            group_equivalent=group_equivalent,
            enable_ai_explanations=enable_ai_explanations,
        )
        return RedirectResponse(url=f"/results/{analysis_id}", status_code=303)
    except (FileNotFoundError, PermissionError, RuntimeError, ValueError, PayloadTooLargeError) as exc:
        _, code, msg = _map_analysis_error(exc, analysis_mode=analysis_mode)
        _log_event(
            "dashboard_analysis_error",
            analysis_id=analysis_id,
            analysis_mode=analysis_mode,
            error_code=code,
            message=msg,
        )
        if analysis_mode in {"fixture_reports", "fixture_runtime"}:
            return _render_dashboard(
                request,
                scan=None,
                hide_info=hide_info,
                group_equivalent=group_equivalent,
                analysis_mode=analysis_mode,
                enable_ai_explanations=enable_ai_explanations,
                analysis_error=f"[{code}] {msg} (analysis_id={analysis_id})",
                local_path_value=local_path,
                git_url_value=git_url,
            )
        return _render_analyze(
            request,
            analysis_mode=analysis_mode,
            enable_ai_explanations=enable_ai_explanations,
            analysis_error=f"[{code}] {msg} (analysis_id={analysis_id})",
            local_path_value=local_path,
            git_url_value=git_url,
        )


@app.post("/dashboard/enrich-ai", response_model=None)
def dashboard_enrich_ai(
    request: Request,
    analysis_id: str = Form(...),
    analysis_mode: str = Form("fixture_reports"),
    hide_info: bool = Form(False),
    group_equivalent: bool = Form(False),
) -> RedirectResponse | HTMLResponse:
    """Ruta legacy de enrich: redirige a /results/{id} (WEB-5 / WEB v2)."""
    settings = get_settings()
    if not settings.ai_explanations_enabled:
        return _render_results(
            request,
            scan=None,
            analysis_error=(
                "[AI_DISABLED] Las explicaciones IA están desactivadas "
                "(TFG_AI_EXPLANATIONS_ENABLED=0)."
            ),
        )

    stored = get_scan_result_store().get(analysis_id.strip())
    if stored is None:
        return _render_results(
            request,
            scan=None,
            analysis_error=(
                f"[SCAN_RESULT_EXPIRED] El resultado ya no está disponible "
                f"(analysis_id={analysis_id})."
            ),
        )

    _log_event("dashboard_enrich_ai_start", analysis_id=analysis_id)
    get_scan_result_store().mark_ai_enriched(analysis_id.strip())
    _log_event("dashboard_enrich_ai_done", analysis_id=analysis_id)
    aid = analysis_id.strip()
    return RedirectResponse(
        url=_results_page_url(aid, hide_info=hide_info, group_equivalent=group_equivalent),
        status_code=303,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


class GitCloneRequest(BaseModel):
    url: str = Field(
        ...,
        min_length=12,
        max_length=8192,
        description="URL https:// del repositorio Git (p. ej. GitHub/GitLab público).",
    )


class LocalPathRequest(BaseModel):
    relative_path: str = Field(
        ...,
        min_length=1,
        max_length=8192,
        description="Ruta relativa dentro de TFG_LOCAL_ANALYSIS_ROOT (sin ..).",
    )


@app.post("/analysis/upload-zip")
async def analysis_upload_zip(
    file: UploadFile = File(..., description="ZIP con código fuente a analizar"),
) -> dict:
    """
    Extrae el ZIP de forma acotada y ejecuta Bandit + Semgrep sobre el contenido.
    Límite de tamaño: variable de entorno `TFG_ZIP_MAX_BYTES` (por defecto ~20 MB).
    """
    analysis_id = _new_analysis_id()
    _log_event("api_upload_zip_start", analysis_id=analysis_id)
    content = await file.read()
    if not content:
        status, code, msg = _map_analysis_error(
            ValueError("No se recibió contenido ZIP en el fichero subido."),
            analysis_mode="upload_zip",
        )
        raise HTTPException(
            status_code=status,
            detail=_error_detail(code, msg, analysis_id=analysis_id),
        )
    if file.filename and not file.filename.lower().endswith(".zip"):
        status, code, msg = _map_analysis_error(
            ValueError("El fichero debe tener extensión .zip"),
            analysis_mode="upload_zip",
        )
        raise HTTPException(
            status_code=status,
            detail=_error_detail(code, msg, analysis_id=analysis_id),
        )
    if file.content_type and file.content_type not in _ALLOWED_ZIP_CONTENT_TYPES:
        status, code, msg = _map_analysis_error(
            ValueError(
                "Tipo de contenido no permitido para ZIP. "
                f"Recibido: {file.content_type}"
            ),
            analysis_mode="upload_zip",
        )
        raise HTTPException(
            status_code=status,
            detail=_error_detail(code, msg, analysis_id=analysis_id),
        )
    if not _looks_like_zip(content):
        status, code, msg = _map_analysis_error(
            ValueError("El contenido subido no tiene firma ZIP válida"),
            analysis_mode="upload_zip",
        )
        raise HTTPException(
            status_code=status,
            detail=_error_detail(code, msg, analysis_id=analysis_id),
        )
    try:
        out = analyze_zip_bytes(content, analysis_id=analysis_id)
        _log_event("api_upload_zip_done", analysis_id=analysis_id)
        return _attach_analysis_id(out, analysis_id)
    except (PayloadTooLargeError, ValueError, RuntimeError) as exc:
        status, code, msg = _map_analysis_error(exc, analysis_mode="upload_zip")
        raise HTTPException(
            status_code=status,
            detail=_error_detail(code, msg, analysis_id=analysis_id),
        ) from exc


@app.post("/analysis/git-clone")
def analysis_git_clone(body: GitCloneRequest) -> dict:
    """
    Clona un repositorio HTTPS con `git clone --depth 1` y analiza el resultado.
    Hosts permitidos: `TFG_GIT_ALLOWED_HOSTS` (por defecto github.com, gitlab.com).
    Desactivar: `TFG_ENABLE_GIT_CLONE=0`.
    """
    analysis_id = _new_analysis_id()
    _log_event("api_git_clone_start", analysis_id=analysis_id, url=body.url)
    try:
        out = clone_and_analyze_repo(body.url, analysis_id=analysis_id)
        _log_event("api_git_clone_done", analysis_id=analysis_id, url=body.url)
        return _attach_analysis_id(out, analysis_id)
    except (PermissionError, ValueError, RuntimeError) as exc:
        status, code, msg = _map_analysis_error(exc, analysis_mode="git_clone")
        raise HTTPException(
            status_code=status,
            detail=_error_detail(code, msg, analysis_id=analysis_id),
        ) from exc


@app.post("/analysis/local-path")
def analysis_local_path(body: LocalPathRequest) -> dict:
    """
    Analiza un directorio bajo una ruta base fijada en el servidor (`TFG_LOCAL_ANALYSIS_ROOT`).
    Solo disponible si esa variable está definida; evita rutas arbitrarias en el sistema de ficheros.
    """
    analysis_id = _new_analysis_id()
    _log_event("api_local_path_start", analysis_id=analysis_id, relative_path=body.relative_path)
    s = get_settings()
    if not s.enable_local_path:
        status, code, msg = _map_analysis_error(
            PermissionError(
                "Análisis por ruta local desactivado (TFG_ENABLE_LOCAL_PATH=0). "
                "Activar solo en entornos controlados."
            ),
            analysis_mode="local_path",
        )
        raise HTTPException(
            status_code=status,
            detail=_error_detail(code, msg, analysis_id=analysis_id),
        )
    if s.local_analysis_root is None:
        status, code, msg = _map_analysis_error(
            PermissionError(
                "Análisis por ruta local desactivado: definir la variable de entorno "
                "TFG_LOCAL_ANALYSIS_ROOT con un directorio permitido."
            ),
            analysis_mode="local_path",
        )
        raise HTTPException(
            status_code=status,
            detail=_error_detail(code, msg, analysis_id=analysis_id),
        )
    try:
        out = analyze_local_path_relative(
            body.relative_path,
            allowed_root=s.local_analysis_root,
            analysis_id=analysis_id,
        )
        _log_event("api_local_path_done", analysis_id=analysis_id)
        return _attach_analysis_id(out, analysis_id)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        status, code, msg = _map_analysis_error(exc, analysis_mode="local_path")
        raise HTTPException(
            status_code=status,
            detail=_error_detail(code, msg, analysis_id=analysis_id),
        ) from exc


@app.get("/ai/status")
def ai_status() -> dict:
    """Estado de la capa IA opcional (explicaciones / asistencia); ver ADR-002."""
    s = get_settings()
    return {
        "ai_explanations_enabled": s.ai_explanations_enabled,
        "ai_provider": s.ai_provider,
        "ai_model": s.ai_model,
        "ai_include_snippet": s.ai_include_snippet,
        "ai_timeout_sec": s.ai_timeout_sec,
        "git_clone_enabled": s.enable_git_clone,
        "local_analysis_root_configured": s.local_analysis_root is not None,
        "local_path_enabled": s.enable_local_path and s.local_analysis_root is not None,
        "enable_local_path": s.enable_local_path,
        "zip_max_bytes": s.zip_max_bytes,
        "zip_max_entries": s.zip_max_entries,
        "zip_max_uncompressed_bytes": s.zip_max_uncompressed_bytes,
        "git_url_max_length": s.git_url_max_length,
        "local_path_max_length": s.local_path_max_length,
        "analysis_subprocess_timeout_sec": s.analysis_subprocess_timeout_sec,
        "analysis_exclude_patterns_count": len(s.analysis_exclude_patterns),
        "message": (
            "Capa IA de explicación en roadmap (ADR-002); el núcleo MVP no depende "
            "de un modelo generativo."
        ),
        "documentation": "docs/02_decisions/ADR-002-ai-assisted-roadmap.md",
    }

@app.get("/analysis/fixtures")
def analyze_fixtures() -> dict:
    analysis_id = _new_analysis_id()
    try:
        out = analyze_fixtures_reports()
        return _attach_analysis_id(out, analysis_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/analysis/fixtures/presentable")
def analyze_fixtures_presentable(
    hide_info: bool = Query(
        default=False,
        description="Oculta hallazgos solo detección o severidad baja (vista demo).",
    ),
    group_equivalent: bool = Query(
        default=False,
        description="Agrupa hallazgos equivalentes (mismo fichero, línea y categoría MVP).",
    ),
    enable_ai: bool = Query(
        default=False,
        description="Genera explicaciones IA por hallazgo (requiere capa habilitada).",
    ),
) -> dict:
    """Vista JSON orientada a presentación (sin datos crudos de herramienta)."""
    analysis_id = _new_analysis_id()
    try:
        scan = presentable_from_internal_analysis(
            _attach_analysis_id(analyze_fixtures_reports(), analysis_id),
            group_equivalent=group_equivalent,
            ai_provider=_resolve_ai_provider(user_requested=enable_ai),
        )
        return filter_presentable_scan(scan, hide_info=hide_info)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/analysis/run-fixtures")
def run_fixtures_analysis() -> dict:
    analysis_id = _new_analysis_id()
    try:
        out = analyze_fixtures_runtime(analysis_id=analysis_id)
        return _attach_analysis_id(out, analysis_id)
    except (FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/analysis/run-fixtures/presentable")
def run_fixtures_analysis_presentable(
    hide_info: bool = Query(
        default=False,
        description="Oculta hallazgos solo detección o severidad baja (vista demo).",
    ),
    group_equivalent: bool = Query(
        default=False,
        description="Agrupa hallazgos equivalentes (mismo fichero, línea y categoría MVP).",
    ),
    enable_ai: bool = Query(
        default=False,
        description="Genera explicaciones IA por hallazgo (requiere capa habilitada).",
    ),
) -> dict:
    """Mismo escaneo que /analysis/run-fixtures, respuesta presentable."""
    analysis_id = _new_analysis_id()
    try:
        scan = presentable_from_internal_analysis(
            _attach_analysis_id(
                analyze_fixtures_runtime(analysis_id=analysis_id),
                analysis_id,
            ),
            group_equivalent=group_equivalent,
            ai_provider=_resolve_ai_provider(user_requested=enable_ai),
        )
        return filter_presentable_scan(scan, hide_info=hide_info)
    except (FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/analysis/{analysis_id}/presentable/enrich")
def enrich_presentable_analysis(
    analysis_id: str,
    hide_info: bool = Query(
        default=False,
        description="Oculta hallazgos solo detección o severidad baja (vista demo).",
    ),
    group_equivalent: bool = Query(
        default=False,
        description="Agrupa hallazgos equivalentes (mismo fichero, línea y categoría MVP).",
    ),
) -> dict:
    """
    Reconstruye el presentable con explicaciones IA desde el almacén efímero (WEB-5).
    Requiere que el analysis_id provenga de un análisis web guardado recientemente.
    """
    settings = get_settings()
    if not settings.ai_explanations_enabled:
        raise HTTPException(
            status_code=403,
            detail=_error_detail(
                "AI_DISABLED",
                "Las explicaciones IA están desactivadas (TFG_AI_EXPLANATIONS_ENABLED=0).",
                analysis_id=analysis_id,
            ),
        )

    stored = get_scan_result_store().get(analysis_id.strip())
    if stored is None:
        raise HTTPException(
            status_code=404,
            detail=_error_detail(
                "SCAN_RESULT_EXPIRED",
                "El resultado del análisis ya no está disponible en el servidor.",
                analysis_id=analysis_id,
            ),
        )

    return _enrich_presentable_scan(
        stored.internal,
        hide_info=hide_info,
        group_equivalent=group_equivalent,
    )


@app.get("/analysis/pipeline/mvp-autofix-verification")
def mvp_autofix_verification() -> dict:
    """
    Ejecuta repair→verify sobre los fixtures canónicos del MVP (autofix).
    Puede tardar (Bandit + Semgrep por verificación). sql_injection no incluido.
    """
    try:
        return run_mvp_autofix_verification_roundtrip()
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
