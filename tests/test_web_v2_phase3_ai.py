"""WEB v2 fase 3: experiencia con/sin IA y filtros en resultados."""

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services.scan_result_store import get_scan_result_store
from tests.web_html_assertions import extract_analysis_id

client = TestClient(app)


def _runtime_payload(*, analysis_id: str | None = None) -> dict:
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
                "cwe_id": 78,
            },
            {
                "source_tool": "bandit",
                "source_rule_id": "B101",
                "file_path": "app.py",
                "line_start": 1,
                "raw_message": "info level",
                "severity": "low",
                "mvp_category": "test_cat",
                "candidate_for_remediation": False,
                "remediation_mode": "detection_only",
            },
        ],
    }


def test_analyze_shows_ai_disabled_notice_when_layer_off(monkeypatch) -> None:
    monkeypatch.delenv("TFG_AI_EXPLANATIONS_ENABLED", raising=False)
    get_settings.cache_clear()
    try:
        html = client.get("/analyze").text
        assert "IA no disponible en este servidor" in html
        assert 'id="enable-ai-explanations"' not in html
        assert "Explicaciones IA" in html
    finally:
        get_settings.cache_clear()


def test_analyze_shows_ai_toggle_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("TFG_AI_EXPLANATIONS_ENABLED", "1")
    monkeypatch.setenv("TFG_AI_PROVIDER", "stub")
    get_settings.cache_clear()
    try:
        html = client.get("/analyze").text
        assert "Incluir explicaciones IA en este escaneo" in html
        assert "Modo stub" in html
        assert "Filtros de vista" not in html
    finally:
        get_settings.cache_clear()


def test_analyze_without_ai_shows_enrich_on_results(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_zip_bytes",
        lambda content, *, analysis_id=None: _runtime_payload(analysis_id=analysis_id),
    )
    monkeypatch.setenv("TFG_AI_EXPLANATIONS_ENABLED", "1")
    monkeypatch.setenv("TFG_AI_PROVIDER", "stub")
    get_settings.cache_clear()
    get_scan_result_store().clear()
    try:
        response = client.post(
            "/analyze",
            data={"analysis_mode": "upload_zip"},
            files={"file": ("demo.zip", b"PK\x03\x04x", "application/zip")},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "Sin IA en este escaneo" in response.text
        assert "Añadir explicaciones IA" in response.text
        assert "Explicación IA" not in response.text
        assert "Filtros de vista" in response.text
    finally:
        get_scan_result_store().clear()
        get_settings.cache_clear()


def test_analyze_with_ai_includes_explanations(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_zip_bytes",
        lambda content, *, analysis_id=None: _runtime_payload(analysis_id=analysis_id),
    )
    monkeypatch.setenv("TFG_AI_EXPLANATIONS_ENABLED", "1")
    monkeypatch.setenv("TFG_AI_PROVIDER", "stub")
    get_settings.cache_clear()
    get_scan_result_store().clear()
    try:
        response = client.post(
            "/analyze",
            data={
                "analysis_mode": "upload_zip",
                "enable_ai_explanations": "true",
            },
            files={"file": ("demo.zip", b"PK\x03\x04x", "application/zip")},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "Con explicaciones IA" in response.text
        assert "Explicación IA" in response.text
        assert "Añadir explicaciones IA" not in response.text
    finally:
        get_scan_result_store().clear()
        get_settings.cache_clear()


def test_results_view_prefs_hide_info_without_rescan(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_zip_bytes",
        lambda content, *, analysis_id=None: _runtime_payload(analysis_id=analysis_id),
    )
    get_scan_result_store().clear()
    try:
        redirect = client.post(
            "/analyze",
            data={"analysis_mode": "upload_zip"},
            files={"file": ("demo.zip", b"PK\x03\x04x", "application/zip")},
            follow_redirects=False,
        )
        analysis_id = redirect.headers["location"].split("/")[-1]

        before = client.get(f"/results/{analysis_id}")
        assert "info level" in before.text or "B101" in before.text

        filtered = client.post(
            f"/results/{analysis_id}/view-prefs",
            data={"hide_info": "true"},
            follow_redirects=True,
        )
        assert filtered.status_code == 200
        stored = get_scan_result_store().get(analysis_id)
        assert stored is not None
        assert stored.hide_info is True
    finally:
        get_scan_result_store().clear()


def test_results_enrich_after_view_prefs(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_zip_bytes",
        lambda content, *, analysis_id=None: _runtime_payload(analysis_id=analysis_id),
    )
    monkeypatch.setenv("TFG_AI_EXPLANATIONS_ENABLED", "1")
    monkeypatch.setenv("TFG_AI_PROVIDER", "stub")
    get_settings.cache_clear()
    get_scan_result_store().clear()
    try:
        analyze_response = client.post(
            "/analyze",
            data={"analysis_mode": "upload_zip"},
            files={"file": ("demo.zip", b"PK\x03\x04x", "application/zip")},
            follow_redirects=True,
        )
        analysis_id = extract_analysis_id(analyze_response.text)

        client.post(
            f"/results/{analysis_id}/view-prefs",
            data={"hide_info": "true", "group_equivalent": "true"},
            follow_redirects=True,
        )

        enrich_response = client.post(
            f"/results/{analysis_id}/enrich-ai",
            data={"hide_info": "true", "group_equivalent": "true"},
            follow_redirects=True,
        )
        assert enrich_response.status_code == 200
        assert "Explicación IA" in enrich_response.text
        stored = get_scan_result_store().get(analysis_id)
        assert stored is not None
        assert stored.enable_ai_explanations is True
        assert stored.hide_info is True
    finally:
        get_scan_result_store().clear()
        get_settings.cache_clear()
