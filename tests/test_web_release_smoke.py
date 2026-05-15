"""
Humo de release: web operativa sin IA (hito fase 2).

Valida que el dashboard expone todos los modos y que la API mínima
de análisis real responde sin depender de la capa IA.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

client = TestClient(app)

_REAL_MODES = (
    "upload_zip",
    "git_clone",
    "local_path",
)
_DEMO_MODES = (
    "fixture_reports",
    "fixture_runtime",
)


def test_release_dashboard_lists_all_analysis_modes() -> None:
    response = client.get("/dashboard")
    assert response.status_code == 200
    html = response.text
    assert "Subir ZIP (real)" in html
    assert "Clonar repositorio Git (real)" in html
    assert "Ruta local permitida (real)" in html
    assert "Informes guardados (MVP/demo)" in html
    assert "Ejecutar fixtures (MVP/demo)" in html
    for mode in _REAL_MODES + _DEMO_MODES:
        assert f'value="{mode}"' in html


def test_release_ai_status_defaults_without_generative_layer(monkeypatch) -> None:
    monkeypatch.delenv("TFG_AI_EXPLANATIONS_ENABLED", raising=False)
    get_settings.cache_clear()
    try:
        data = client.get("/ai/status").json()
        assert data["ai_explanations_enabled"] is False
        assert "zip_max_bytes" in data
        assert "local_path_enabled" in data
    finally:
        get_settings.cache_clear()


def test_release_health_and_dashboard_entrypoints() -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/", follow_redirects=False).headers["location"] == "/dashboard"


def test_release_dashboard_fixture_reports_via_form(monkeypatch) -> None:
    def fake_reports() -> dict:
        return {
            "analysis_target": "fixtures/mvp",
            "execution_mode": "static_reports",
            "bandit_report": "reports/bandit/x.json",
            "semgrep_report": "reports/semgrep/y.json",
            "findings": [
                {
                    "source_tool": "bandit",
                    "source_rule_id": "B101",
                    "file_path": "fixtures/mvp/a.py",
                    "line_start": 1,
                    "raw_message": "test",
                    "severity": "medium",
                    "mvp_category": "test_cat",
                    "candidate_for_remediation": False,
                    "remediation_mode": "detection_only",
                }
            ],
        }

    monkeypatch.setattr("app.main.analyze_fixtures_reports", fake_reports)
    response = client.post(
        "/dashboard/analyze",
        data={"analysis_mode": "fixture_reports"},
    )
    assert response.status_code == 200
    assert "fixtures/mvp" in response.text
    assert "test_cat" in response.text


def test_release_dashboard_local_path_success_when_configured(
    monkeypatch, tmp_path: Path
) -> None:
    project = tmp_path / "demo"
    project.mkdir()
    monkeypatch.setenv("TFG_LOCAL_ANALYSIS_ROOT", str(tmp_path))
    monkeypatch.setenv("TFG_ENABLE_LOCAL_PATH", "1")
    get_settings.cache_clear()

    def fake_local(relative_path: str, *, allowed_root: Path, analysis_id: str | None = None):
        assert relative_path == "demo"
        return {
            "analysis_target": "local:demo",
            "execution_mode": "runtime",
            "generated_reports": {"bandit": "(temporal)", "semgrep": "(temporal)"},
            "findings": [],
            "analysis_id": analysis_id,
        }

    monkeypatch.setattr("app.main.analyze_local_path_relative", fake_local)
    try:
        response = client.post(
            "/dashboard/analyze",
            data={"analysis_mode": "local_path", "local_path": "demo"},
        )
        assert response.status_code == 200
        assert "local:demo" in response.text
        assert "Analysis ID:" in response.text
    finally:
        get_settings.cache_clear()


def test_release_api_upload_zip_contract(monkeypatch) -> None:
    def fake_zip(content: bytes, *, analysis_id: str | None = None) -> dict:
        return {
            "analysis_target": "upload.zip",
            "execution_mode": "runtime",
            "findings": [],
            "total_findings": 0,
        }

    monkeypatch.setattr("app.main.analyze_zip_bytes", fake_zip)
    r = client.post(
        "/analysis/upload-zip",
        files={"file": ("p.zip", b"PK\x03\x04x", "application/zip")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["analysis_target"] == "upload.zip"
    assert isinstance(body["analysis_id"], str)


def test_release_api_git_clone_contract(monkeypatch) -> None:
    def fake_clone(url: str, *, analysis_id: str | None = None) -> dict:
        return {
            "analysis_target": f"git:{url}",
            "execution_mode": "runtime",
            "findings": [],
            "total_findings": 0,
        }

    monkeypatch.setattr("app.main.clone_and_analyze_repo", fake_clone)
    r = client.post(
        "/analysis/git-clone",
        json={"url": "https://github.com/octocat/Hello-World.git"},
    )
    assert r.status_code == 200
    assert "analysis_id" in r.json()
