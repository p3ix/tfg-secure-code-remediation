from fastapi.testclient import TestClient

from app.main import app
from app.services.scan_result_store import get_scan_result_store
from tests.web_html_assertions import extract_analysis_id

client = TestClient(app)


def _runtime_payload(*, analysis_id: str | None = None) -> dict:
    return {
        "analysis_target": "fixtures/mvp",
        "execution_mode": "runtime",
        "generated_reports": {"bandit": "x", "semgrep": "y"},
        "findings": [
            {
                "source_tool": "bandit",
                "source_rule_id": "B602",
                "file_path": "fixtures/mvp/cmd.py",
                "line_start": 4,
                "raw_message": "subprocess shell=True",
                "severity": "high",
                "mvp_category": "command_injection",
                "candidate_for_remediation": True,
                "remediation_mode": "autofix_candidate",
                "cwe_id": 78,
            }
        ],
    }


def test_dashboard_shows_enrich_button_after_analyze_without_ai(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_fixtures_runtime",
        lambda *, analysis_id=None: _runtime_payload(analysis_id=analysis_id),
    )
    monkeypatch.setenv("TFG_AI_EXPLANATIONS_ENABLED", "1")
    monkeypatch.setenv("TFG_AI_PROVIDER", "stub")
    get_settings.cache_clear()
    get_scan_result_store().clear()
    try:
        response = client.post(
            "/dashboard/analyze",
            data={"analysis_mode": "fixture_runtime"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "Añadir explicaciones IA" in response.text
        assert "dashboard-enrich-form" in response.text
        assert "Explicación IA" not in response.text
    finally:
        get_scan_result_store().clear()
        get_settings.cache_clear()


def test_dashboard_enrich_ai_adds_explanations_without_rescan(monkeypatch) -> None:
    from app.config import get_settings

    calls = {"runtime": 0}

    def fake_runtime(*, analysis_id: str | None = None) -> dict:
        calls["runtime"] += 1
        return _runtime_payload(analysis_id=analysis_id)

    monkeypatch.setattr("app.services.web_analysis_flow.analyze_fixtures_runtime", fake_runtime)
    monkeypatch.setenv("TFG_AI_EXPLANATIONS_ENABLED", "1")
    monkeypatch.setenv("TFG_AI_PROVIDER", "stub")
    get_settings.cache_clear()
    get_scan_result_store().clear()
    try:
        analyze_response = client.post(
            "/dashboard/analyze",
            data={"analysis_mode": "fixture_runtime"},
            follow_redirects=True,
        )
        analysis_id = extract_analysis_id(analyze_response.text)

        enrich_response = client.post(
            f"/results/{analysis_id}/enrich-ai",
            data={},
            follow_redirects=True,
        )

        assert enrich_response.status_code == 200
        assert calls["runtime"] == 1
        assert "Explicación IA" in enrich_response.text
        assert "Ubicación" in enrich_response.text
        assert "Pasos sugeridos" in enrich_response.text
        assert "Añadir explicaciones IA" not in enrich_response.text
    finally:
        get_scan_result_store().clear()
        get_settings.cache_clear()


def test_dashboard_enrich_ai_unknown_analysis_id(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("TFG_AI_EXPLANATIONS_ENABLED", "1")
    get_settings.cache_clear()
    get_scan_result_store().clear()
    try:
        response = client.post(
            "/results/deadbeef/enrich-ai",
            data={},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "[SCAN_RESULT_EXPIRED]" in response.text
    finally:
        get_settings.cache_clear()


def test_dashboard_enrich_ai_disabled_on_server(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("TFG_AI_EXPLANATIONS_ENABLED", "0")
    get_settings.cache_clear()
    try:
        response = client.post(
            "/results/abc/enrich-ai",
            data={},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "[AI_DISABLED]" in response.text
    finally:
        get_settings.cache_clear()


def test_api_presentable_enrich_returns_explanations(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setattr(
        "app.services.web_analysis_flow.analyze_fixtures_runtime",
        lambda *, analysis_id=None: _runtime_payload(analysis_id=analysis_id),
    )
    monkeypatch.setenv("TFG_AI_EXPLANATIONS_ENABLED", "1")
    monkeypatch.setenv("TFG_AI_PROVIDER", "stub")
    get_settings.cache_clear()
    get_scan_result_store().clear()
    try:
        analyze_response = client.post(
            "/dashboard/analyze",
            data={"analysis_mode": "fixture_runtime"},
            follow_redirects=True,
        )
        analysis_id = extract_analysis_id(analyze_response.text)

        api_response = client.post(f"/analysis/{analysis_id}/presentable/enrich")

        assert api_response.status_code == 200
        payload = api_response.json()
        assert payload["findings"][0]["ai_explanation"] is not None
        assert payload["findings"][0]["ai_explanation"]["location_hint"]
    finally:
        get_scan_result_store().clear()
        get_settings.cache_clear()


def test_api_presentable_enrich_not_found(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("TFG_AI_EXPLANATIONS_ENABLED", "1")
    get_settings.cache_clear()
    get_scan_result_store().clear()
    try:
        response = client.post("/analysis/unknown-id/presentable/enrich")
        assert response.status_code == 404
        assert response.json()["detail"]["error_code"] == "SCAN_RESULT_EXPIRED"
    finally:
        get_settings.cache_clear()
