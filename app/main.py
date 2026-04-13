from pathlib import Path

from fastapi import (
    FastAPI,
    File,
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
    """Vista HTML del escaneo sobre reports estáticos (misma lógica que /analysis/fixtures/presentable)."""
    try:
        scan = presentable_from_internal_analysis(
            analyze_fixtures_reports(),
            group_equivalent=group_equivalent,
        )
        scan = filter_presentable_scan(scan, hide_info=hide_info)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "scan": scan,
            "hide_info": hide_info,
            "group_equivalent": group_equivalent,
        },
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
    try:
        return analyze_zip_bytes(content)
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
