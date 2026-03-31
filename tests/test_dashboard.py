from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_redirects_to_dashboard() -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


def test_dashboard_renders_html_when_reports_exist() -> None:
    bandit = Path("reports/bandit/fixtures-mvp-bandit.json")
    semgrep = Path("reports/semgrep/fixtures-mvp-semgrep.json")
    if not bandit.exists() or not semgrep.exists():
        return

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Resultado del escaneo" in response.text
    assert "schema_version" in response.text or "Hallazgos" in response.text


def test_dashboard_returns_500_when_reports_missing(monkeypatch) -> None:
    def fake_analyze() -> dict:
        raise FileNotFoundError("no report")

    monkeypatch.setattr("app.main.analyze_fixtures_reports", fake_analyze)

    response = client.get("/dashboard")

    assert response.status_code == 500
