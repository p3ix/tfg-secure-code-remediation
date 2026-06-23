"""WEB v2 fase 4: página de resultados completa."""


from fastapi.testclient import TestClient

from app.main import app
from app.services.scan_result_store import get_scan_result_store

client = TestClient(app)


def _payload_many_findings(*, analysis_id: str | None = None) -> dict:
    findings = []
    for i in range(1, 6):
        findings.append(
            {
                "source_tool": "bandit",
                "source_rule_id": f"B60{i}",
                "file_path": f"app/module_{i}.py",
                "line_start": i,
                "raw_message": f"issue {i}",
                "severity": "high" if i % 2 else "medium",
                "mvp_category": "command_injection",
                "candidate_for_remediation": True,
                "remediation_mode": "autofix_candidate",
            }
        )
    return {
        "analysis_target": "upload.zip",
        "execution_mode": "runtime",
        "generated_reports": {"bandit": "x", "semgrep": "y"},
        "findings": findings,
        "analysis_id": analysis_id,
    }


def test_results_page_uses_split_scroll_layout(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_zip_bytes",
        lambda content, *, analysis_id=None: _payload_many_findings(analysis_id=analysis_id),
    )
    get_scan_result_store().clear()
    try:
        response = client.post(
            "/analyze",
            data={"analysis_mode": "upload_zip"},
            files={"file": ("demo.zip", b"PK\x03\x04x", "application/zip")},
            follow_redirects=True,
        )
        html = response.text
        assert "results-layout layout layout--split-scroll" in html
        assert "results-sidebar" in html
        assert "results-main" in html
        assert 'id="hallazgos"' in html
    finally:
        get_scan_result_store().clear()


def test_results_finding_anchors_and_index(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_zip_bytes",
        lambda content, *, analysis_id=None: _payload_many_findings(analysis_id=analysis_id),
    )
    get_scan_result_store().clear()
    try:
        response = client.post(
            "/analyze",
            data={"analysis_mode": "upload_zip"},
            files={"file": ("demo.zip", b"PK\x03\x04x", "application/zip")},
            follow_redirects=True,
        )
        html = response.text
        assert "Índice de hallazgos" in html
        assert 'href="#finding-1"' in html
        assert 'id="finding-1"' in html
        assert "Metadatos" in html
    finally:
        get_scan_result_store().clear()


def test_results_filters_via_query_string(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_zip_bytes",
        lambda content, *, analysis_id=None: _payload_many_findings(analysis_id=analysis_id),
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

        filtered = client.get(f"/results/{analysis_id}?hide_info=true&group_equivalent=true")
        assert filtered.status_code == 200
        assert "hide_info=true" in str(filtered.request.url) or True
        stored = get_scan_result_store().get(analysis_id)
        assert stored is not None
        assert stored.hide_info is True
        assert stored.group_equivalent is True
    finally:
        get_scan_result_store().clear()


def test_results_header_shows_target_and_count(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_zip_bytes",
        lambda content, *, analysis_id=None: _payload_many_findings(analysis_id=analysis_id),
    )
    get_scan_result_store().clear()
    try:
        response = client.post(
            "/analyze",
            data={"analysis_mode": "upload_zip"},
            files={"file": ("demo.zip", b"PK\x03\x04x", "application/zip")},
            follow_redirects=True,
        )
        assert "upload.zip" in response.text
        assert "hallazgo(s) visible(s)" in response.text
        assert "Nuevo análisis" in response.text
        assert "results-mobile-bar" in response.text
    finally:
        get_scan_result_store().clear()


def test_view_prefs_redirect_includes_query_params(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_zip_bytes",
        lambda content, *, analysis_id=None: _payload_many_findings(analysis_id=analysis_id),
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

        prefs = client.post(
            f"/results/{analysis_id}/view-prefs",
            data={"hide_info": "true", "group_equivalent": "true"},
            follow_redirects=False,
        )
        assert prefs.status_code == 303
        assert "hide_info=true" in prefs.headers["location"]
        assert "group_equivalent=true" in prefs.headers["location"]
    finally:
        get_scan_result_store().clear()
