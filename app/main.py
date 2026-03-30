from fastapi import FastAPI, HTTPException
from app.services.analysis_service import analyze_fixtures_reports
from app.services.pipeline_orchestrator import run_mvp_autofix_verification_roundtrip
from app.services.presentable_scan import presentable_from_internal_analysis
from app.services.runtime_analysis_service import analyze_fixtures_runtime

app = FastAPI(
    title="TFG Secure Code Remediation",
    description="API base del TFG para análisis y remediación asistida de vulnerabilidades",
    version="0.1.0"
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
def analyze_fixtures_presentable() -> dict:
    """Vista JSON orientada a presentación (sin datos crudos de herramienta)."""
    try:
        return presentable_from_internal_analysis(analyze_fixtures_reports())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/analysis/run-fixtures")
def run_fixtures_analysis() -> dict:
    try:
        return analyze_fixtures_runtime()
    except (FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/analysis/run-fixtures/presentable")
def run_fixtures_analysis_presentable() -> dict:
    """Mismo escaneo que /analysis/run-fixtures, respuesta presentable."""
    try:
        return presentable_from_internal_analysis(analyze_fixtures_runtime())
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
