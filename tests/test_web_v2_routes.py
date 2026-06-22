from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.scan_result_store import get_scan_result_store

client = TestClient(app)
REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_ZIP = REPO_ROOT / "vulnerable_demo.zip"


def test_home_page_renders_landing() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Secure Code Remediation" in response.text
    assert "Nuevo análisis" in response.text
    assert "vulnerable_demo.zip" in response.text
    assert "Informes guardados" not in response.text


def test_root_no_longer_redirects_to_dashboard() -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 200


def test_dashboard_redirects_to_analyze() -> None:
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/analyze"


def test_analyze_form_lists_only_real_modes() -> None:
    response = client.get("/analyze")
    assert response.status_code == 200
    assert "Subir ZIP" in response.text
    assert "Clonar repositorio Git" in response.text
    assert "Ruta local permitida" in response.text
    assert "fixture_reports" not in response.text
    assert "fixture_runtime" not in response.text


def test_analyze_zip_redirects_to_results(monkeypatch) -> None:
    def fake_zip(content: bytes, *, analysis_id: str | None = None) -> dict:
        return {
            "analysis_target": "upload.zip",
            "execution_mode": "runtime",
            "generated_reports": {"bandit": "x", "semgrep": "y"},
            "findings": [
                {
                    "source_tool": "bandit",
                    "source_rule_id": "B602",
                    "file_path": "app.py",
                    "line_start": 1,
                    "raw_message": "test",
                    "severity": "high",
                    "mvp_category": "command_injection",
                    "candidate_for_remediation": True,
                    "remediation_mode": "autofix_candidate",
                }
            ],
        }

    monkeypatch.setattr("app.services.web_analysis_flow.analyze_zip_bytes", fake_zip)
    get_scan_result_store().clear()
    try:
        response = client.post(
            "/analyze",
            data={"analysis_mode": "upload_zip"},
            files={"file": ("demo.zip", b"PK\x03\x04x", "application/zip")},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"].startswith("/results/")
        results = client.get(response.headers["location"])
        assert results.status_code == 200
        assert "upload.zip" in results.text
        assert "command_injection" in results.text
    finally:
        get_scan_result_store().clear()


def test_analyze_rejects_demo_mode() -> None:
    response = client.post(
        "/analyze",
        data={"analysis_mode": "fixture_runtime"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "no disponible en la interfaz v2" in response.text


def test_results_unknown_analysis_id() -> None:
    get_scan_result_store().clear()
    response = client.get("/results/deadbeef")
    assert response.status_code == 200
    assert "[SCAN_RESULT_EXPIRED]" in response.text


def test_vulnerable_demo_zip_integration() -> None:
    if not DEMO_ZIP.is_file():
        return

    get_scan_result_store().clear()
    try:
        with DEMO_ZIP.open("rb") as handle:
            response = client.post(
                "/analyze",
                data={"analysis_mode": "upload_zip"},
                files={"file": ("vulnerable_demo.zip", handle, "application/zip")},
                follow_redirects=False,
            )
        if response.status_code != 303:
            return
        results = client.get(response.headers["location"], timeout=120)
        assert results.status_code == 200
        assert "Resultado del escaneo" in results.text
    finally:
        get_scan_result_store().clear()
