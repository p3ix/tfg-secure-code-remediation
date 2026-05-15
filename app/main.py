from pathlib import Path
import logging
import inspect
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
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from starlette.templating import Jinja2Templates

from app.config import get_settings
from app.services.analysis_service import analyze_fixtures_reports
from app.services.project_scan_service import (
    PayloadTooLargeError,
    analyze_local_path_relative,
    analyze_zip_bytes,
    clone_and_analyze_repo,
)
from app.services.pipeline_orchestrator import run_mvp_autofix_verification_roundtrip
from app.services.presentable_scan import (
    filter_presentable_scan,
    presentable_from_internal_analysis,
)
from app.services.runtime_analysis_service import analyze_fixtures_runtime

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

app = FastAPI(
    title="TFG Secure Code Remediation",
    description="API base del TFG para análisis y remediación asistida de vulnerabilidades",
    version="0.1.0"
)
logger = logging.getLogger(__name__)


_ALLOWED_ZIP_CONTENT_TYPES = {
    "application/zip",
    "application/x-zip-compressed",
    "application/octet-stream",
}


def _looks_like_zip(content: bytes) -> bool:
    # ZIP signatures: local file header / empty archive / spanned archive
    return content.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"))


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
        if "URL HTTPS" in text and analysis_mode == "git_clone":
            return 400, "GIT_URL_REQUIRED", text
        if "Host no permitido" in text:
            return 400, "GIT_HOST_NOT_ALLOWED", text
        if "https://" in text:
            return 400, "GIT_URL_INVALID", text
        if analysis_mode == "local_path":
            return 400, "LOCAL_PATH_INVALID", text
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


def _call_with_optional_analysis_id(func: object, *args: object, analysis_id: str, **kwargs: object):
    callable_obj = func
    if not callable(callable_obj):
        raise TypeError(f"Objeto no invocable: {callable_obj!r}")
    try:
        signature = inspect.signature(callable_obj)
    except (TypeError, ValueError):
        signature = None
    if signature is not None and "analysis_id" in signature.parameters:
        return callable_obj(*args, analysis_id=analysis_id, **kwargs)
    return callable_obj(*args, **kwargs)


def _build_dashboard_scan(
    internal_scan: dict,
    *,
    hide_info: bool,
    group_equivalent: bool,
) -> dict:
    scan = presentable_from_internal_analysis(
        internal_scan,
        group_equivalent=group_equivalent,
    )
    return filter_presentable_scan(scan, hide_info=hide_info)


def _render_dashboard(
    request: Request,
    *,
    scan: dict | None,
    hide_info: bool,
    group_equivalent: bool,
    analysis_mode: str,
    analysis_error: str | None = None,
    analysis_notice: str | None = None,
) -> HTMLResponse:
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "scan": scan,
            "hide_info": hide_info,
            "group_equivalent": group_equivalent,
            "analysis_mode": analysis_mode,
            "analysis_error": analysis_error,
            "analysis_notice": analysis_notice,
            "local_path_enabled": settings.local_analysis_root is not None,
            "local_analysis_root": str(settings.local_analysis_root)
            if settings.local_analysis_root is not None
            else None,
            "git_clone_enabled": settings.enable_git_clone,
            "git_allowed_hosts": ", ".join(sorted(settings.git_allowed_hosts)),
            "zip_max_bytes": settings.zip_max_bytes,
        },
    )


@app.get("/", response_class=RedirectResponse)
def root(request: Request) -> RedirectResponse:
    query = request.url.query
    target = "/dashboard" + (f"?{query}" if query else "")
    return RedirectResponse(url=target, status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
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


@app.post("/dashboard/analyze", response_class=HTMLResponse)
async def dashboard_analyze(
    request: Request,
    analysis_mode: str = Form(...),
    hide_info: bool = Form(False),
    group_equivalent: bool = Form(False),
    local_path: str = Form(""),
    git_url: str = Form(""),
    file: UploadFile | None = File(default=None),
) -> HTMLResponse:
    """
    Ejecuta análisis desde la interfaz web y renderiza el resultado en la misma vista.
    """
    analysis_id = _new_analysis_id()
    _log_event("dashboard_analysis_start", analysis_id=analysis_id, analysis_mode=analysis_mode)
    try:
        if analysis_mode == "fixture_reports":
            internal = analyze_fixtures_reports()
        elif analysis_mode == "fixture_runtime":
            internal = _call_with_optional_analysis_id(
                analyze_fixtures_runtime, analysis_id=analysis_id
            )
        elif analysis_mode == "upload_zip":
            if file is None or not file.filename:
                raise ValueError("Selecciona un fichero ZIP antes de lanzar el análisis.")
            if not file.filename.lower().endswith(".zip"):
                raise ValueError("El fichero seleccionado debe terminar en .zip")
            if file.content_type and file.content_type not in _ALLOWED_ZIP_CONTENT_TYPES:
                raise ValueError(
                    "Tipo de contenido no permitido para ZIP. "
                    f"Recibido: {file.content_type}"
                )
            content = await file.read()
            if not content:
                raise ValueError("El fichero ZIP está vacío")
            if not _looks_like_zip(content):
                raise ValueError("El contenido subido no tiene firma ZIP válida")
            internal = _call_with_optional_analysis_id(
                analyze_zip_bytes, content, analysis_id=analysis_id
            )
        elif analysis_mode == "local_path":
            settings = get_settings()
            if settings.local_analysis_root is None:
                raise PermissionError(
                    "El análisis por ruta local está desactivado en este entorno."
                )
            if not local_path.strip():
                raise ValueError("Indica una ruta relativa para el modo local_path")
            internal = _call_with_optional_analysis_id(
                analyze_local_path_relative,
                local_path,
                allowed_root=settings.local_analysis_root,
                analysis_id=analysis_id,
            )
        elif analysis_mode == "git_clone":
            settings = get_settings()
            if not settings.enable_git_clone:
                raise PermissionError(
                    "El análisis por git clone está desactivado en este entorno."
                )
            if not git_url.strip():
                raise ValueError("Indica una URL HTTPS para el modo git_clone")
            internal = _call_with_optional_analysis_id(
                clone_and_analyze_repo,
                git_url.strip(),
                analysis_id=analysis_id,
            )
        else:
            raise ValueError(f"Modo de análisis no soportado: {analysis_mode}")

        internal = _attach_analysis_id(internal, analysis_id)
        _log_event("dashboard_analysis_done", analysis_id=analysis_id, analysis_mode=analysis_mode)

        scan = _build_dashboard_scan(
            internal,
            hide_info=hide_info,
            group_equivalent=group_equivalent,
        )
        return _render_dashboard(
            request,
            scan=scan,
            hide_info=hide_info,
            group_equivalent=group_equivalent,
            analysis_mode=analysis_mode,
        )
    except (FileNotFoundError, PermissionError, RuntimeError, ValueError, PayloadTooLargeError) as exc:
        _, code, msg = _map_analysis_error(exc, analysis_mode=analysis_mode)
        _log_event(
            "dashboard_analysis_error",
            analysis_id=analysis_id,
            analysis_mode=analysis_mode,
            error_code=code,
            message=msg,
        )
        return _render_dashboard(
            request,
            scan=None,
            hide_info=hide_info,
            group_equivalent=group_equivalent,
            analysis_mode=analysis_mode,
            analysis_error=f"[{code}] {msg} (analysis_id={analysis_id})",
        )

@app.get("/health")
def health():
    return {"status": "ok"}


class GitCloneRequest(BaseModel):
    url: str = Field(
        ...,
        min_length=12,
        description="URL https:// del repositorio Git (p. ej. GitHub/GitLab público).",
    )


class LocalPathRequest(BaseModel):
    relative_path: str = Field(
        ...,
        min_length=1,
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
        out = _call_with_optional_analysis_id(
            analyze_zip_bytes, content, analysis_id=analysis_id
        )
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
        out = _call_with_optional_analysis_id(
            clone_and_analyze_repo, body.url, analysis_id=analysis_id
        )
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
        out = _call_with_optional_analysis_id(
            analyze_local_path_relative,
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
        "git_clone_enabled": s.enable_git_clone,
        "local_analysis_root_configured": s.local_analysis_root is not None,
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
) -> dict:
    """Vista JSON orientada a presentación (sin datos crudos de herramienta)."""
    analysis_id = _new_analysis_id()
    try:
        scan = presentable_from_internal_analysis(
            _attach_analysis_id(analyze_fixtures_reports(), analysis_id),
            group_equivalent=group_equivalent,
        )
        return filter_presentable_scan(scan, hide_info=hide_info)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/analysis/run-fixtures")
def run_fixtures_analysis() -> dict:
    analysis_id = _new_analysis_id()
    try:
        out = _call_with_optional_analysis_id(
            analyze_fixtures_runtime, analysis_id=analysis_id
        )
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
) -> dict:
    """Mismo escaneo que /analysis/run-fixtures, respuesta presentable."""
    analysis_id = _new_analysis_id()
    try:
        scan = presentable_from_internal_analysis(
            _attach_analysis_id(
                _call_with_optional_analysis_id(
                    analyze_fixtures_runtime, analysis_id=analysis_id
                ),
                analysis_id,
            ),
            group_equivalent=group_equivalent,
        )
        return filter_presentable_scan(scan, hide_info=hide_info)
    except (FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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
