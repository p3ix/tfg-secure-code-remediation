from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from app.services.analysis_service import analyze_fixtures_reports
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
