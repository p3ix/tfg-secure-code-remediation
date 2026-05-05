from pathlib import Path

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
    file: UploadFile | None = File(default=None),
) -> HTMLResponse:
    """
    Ejecuta análisis desde la interfaz web y renderiza el resultado en la misma vista.
    """
    try:
        if analysis_mode == "fixture_reports":
            internal = analyze_fixtures_reports()
        elif analysis_mode == "fixture_runtime":
            internal = analyze_fixtures_runtime()
        elif analysis_mode == "upload_zip":
            if file is None or not file.filename:
                raise ValueError("Selecciona un fichero ZIP antes de lanzar el análisis.")
            if not file.filename.lower().endswith(".zip"):
                raise ValueError("El fichero seleccionado debe terminar en .zip")
            content = await file.read()
            if not content:
                raise ValueError("El fichero ZIP está vacío")
            internal = analyze_zip_bytes(content)
        elif analysis_mode == "local_path":
            settings = get_settings()
            if settings.local_analysis_root is None:
                raise PermissionError(
                    "El análisis por ruta local está desactivado en este entorno."
                )
            if not local_path.strip():
                raise ValueError("Indica una ruta relativa para el modo local_path")
            internal = analyze_local_path_relative(
                local_path,
                allowed_root=settings.local_analysis_root,
            )
        else:
            raise ValueError(f"Modo de análisis no soportado: {analysis_mode}")

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
        return _render_dashboard(
            request,
            scan=None,
            hide_info=hide_info,
            group_equivalent=group_equivalent,
            analysis_mode=analysis_mode,
            analysis_error=str(exc),
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
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=400,
            detail="No se recibió contenido ZIP en el fichero subido.",
        )
    if file.filename and not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="El fichero debe tener extensión .zip",
        )
    try:
        return analyze_zip_bytes(content)
    except PayloadTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/analysis/git-clone")
def analysis_git_clone(body: GitCloneRequest) -> dict:
    """
    Clona un repositorio HTTPS con `git clone --depth 1` y analiza el resultado.
    Hosts permitidos: `TFG_GIT_ALLOWED_HOSTS` (por defecto github.com, gitlab.com).
    Desactivar: `TFG_ENABLE_GIT_CLONE=0`.
    """
    try:
        return clone_and_analyze_repo(body.url)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/analysis/local-path")
def analysis_local_path(body: LocalPathRequest) -> dict:
    """
    Analiza un directorio bajo una ruta base fijada en el servidor (`TFG_LOCAL_ANALYSIS_ROOT`).
    Solo disponible si esa variable está definida; evita rutas arbitrarias en el sistema de ficheros.
    """
    s = get_settings()
    if s.local_analysis_root is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "Análisis por ruta local desactivado: definir la variable de entorno "
                "TFG_LOCAL_ANALYSIS_ROOT con un directorio permitido."
            ),
        )
    try:
        return analyze_local_path_relative(
            body.relative_path, allowed_root=s.local_analysis_root
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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
    try:
        return analyze_fixtures_reports()
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
    try:
        scan = presentable_from_internal_analysis(
            analyze_fixtures_reports(),
            group_equivalent=group_equivalent,
        )
        return filter_presentable_scan(scan, hide_info=hide_info)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/analysis/run-fixtures")
def run_fixtures_analysis() -> dict:
    try:
        return analyze_fixtures_runtime()
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
    try:
        scan = presentable_from_internal_analysis(
            analyze_fixtures_runtime(),
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
