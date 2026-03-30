from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_mvp_autofix_verification_endpoint_ok(monkeypatch) -> None:
    def fake_roundtrip() -> dict:
        return {
            "pipeline_step": "mvp_autofix_verify",
            "categories": {
                "unsafe_yaml_load": [
                    {"fixture": "fixtures/mvp/unsafe_yaml_load/vuln_yaml_load.py", "verification": {}}
                ],
            },
        }

    monkeypatch.setattr(
        "app.main.run_mvp_autofix_verification_roundtrip",
        fake_roundtrip,
    )

    response = client.get("/analysis/pipeline/mvp-autofix-verification")

    assert response.status_code == 200
    body = response.json()
    assert body["pipeline_step"] == "mvp_autofix_verify"
    assert "unsafe_yaml_load" in body["categories"]
