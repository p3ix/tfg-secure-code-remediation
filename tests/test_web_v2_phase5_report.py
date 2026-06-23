"""WEB v2 fase 5: informe imprimible y export JSON."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.scan_result_store import get_scan_result_store

client = TestClient(app)


def _payload() -> dict:
    return {
        "analysis_target": "upload.zip",
        "execution_mode": "runtime",
        "generated_reports": {"bandit": "x", "semgrep": "y"},
        "findings": [
            {
                "source_tool": "bandit",
                "source_rule_id": "B602",
                "file_path": "app.py",
                "line_start": 4,
                "raw_message": "subprocess shell=True",
                "severity": "high",
                "mvp_category": "command_injection",
                "candidate_for_remediation": True,
                "remediation_mode": "autofix_candidate",
            }
        ],
    }


def test_results_report_page_renders(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_zip_bytes",
        lambda content, *, analysis_id=None: _payload(),
    )
    get_scan_result_store().clear()
    try:
        redirect = client.post(
            "/analyze",
            data={"analysis_mode": "upload_zip"},
            files={"file": ("demo.zip", b"PK\x03\x04x", "application/zip")},
            follow_redirects=False,
        )
        analysis_id = redirect.headers["location"].rsplit("/", 1)[-1]
        response = client.get(f"/results/{analysis_id}/report")
        assert response.status_code == 200
        html = response.text
        assert "Informe de seguridad Python" in html
        assert "Resumen ejecutivo" in html
        assert "Metodología" in html
        assert "upload.zip" in html
        assert "report.css" in html
        assert "Imprimir / guardar PDF" in html
    finally:
        get_scan_result_store().clear()


def test_results_export_json_returns_presentable(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_zip_bytes",
        lambda content, *, analysis_id=None: _payload(),
    )
    get_scan_result_store().clear()
    try:
        redirect = client.post(
            "/analyze",
            data={"analysis_mode": "upload_zip"},
            files={"file": ("demo.zip", b"PK\x03\x04x", "application/zip")},
            follow_redirects=False,
        )
        analysis_id = redirect.headers["location"].rsplit("/", 1)[-1]
        response = client.get(f"/results/{analysis_id}/export.json")
        assert response.status_code == 200
        body = response.json()
        assert body["schema_version"]
        assert body["summary"]["total_findings"] == 1
        assert body["findings"][0]["category"] == "command_injection"
    finally:
        get_scan_result_store().clear()


def test_results_page_links_to_report_and_export(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_zip_bytes",
        lambda content, *, analysis_id=None: _payload(),
    )
    get_scan_result_store().clear()
    try:
        response = client.post(
            "/analyze",
            data={"analysis_mode": "upload_zip"},
            files={"file": ("demo.zip", b"PK\x03\x04x", "application/zip")},
            follow_redirects=True,
        )
        assert "Informe imprimible" in response.text
        assert "/export.json" in response.text
        assert "/report" in response.text
    finally:
        get_scan_result_store().clear()


def test_results_export_json_expired() -> None:
    get_scan_result_store().clear()
    response = client.get("/results/deadbeef/export.json")
    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "SCAN_RESULT_EXPIRED"
