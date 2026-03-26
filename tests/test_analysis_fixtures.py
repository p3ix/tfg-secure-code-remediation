from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analysis_fixtures_endpoint_returns_findings() -> None:
    response = client.get("/analysis/fixtures")

    assert response.status_code == 200

    payload = response.json()

    assert payload["analysis_target"] == "fixtures/mvp"
    assert payload["total_findings"] > 0
    assert "findings" in payload
    assert isinstance(payload["findings"], list)
    assert len(payload["findings"]) > 0

    first_finding = payload["findings"][0]

    assert "source_tool" in first_finding
    assert "source_rule_id" in first_finding
    assert "file_path" in first_finding
    assert "severity" in first_finding
    assert "mvp_category" in first_finding
    assert "remediation_mode" in first_finding


def test_analysis_fixtures_endpoint_contains_classified_findings() -> None:
    response = client.get("/analysis/fixtures")

    assert response.status_code == 200

    findings = response.json()["findings"]

    assert any(f["cwe_id"] == 78 for f in findings)
    assert any(f["cwe_id"] == 89 for f in findings)
    assert any(f["cwe_id"] == 295 for f in findings)
