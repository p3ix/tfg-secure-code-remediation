from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_run_fixtures_endpoint_returns_runtime_payload(monkeypatch) -> None:
    def fake_runtime_analysis() -> dict:
        return {
            "analysis_target": "fixtures/mvp",
            "execution_mode": "runtime",
            "generated_reports": {
                "bandit": "reports/runtime/fixtures-mvp-bandit-runtime.json",
                "semgrep": "reports/runtime/fixtures-mvp-semgrep-runtime.json",
            },
            "tool_runs": {
                "bandit": {"returncode": 0, "command": ["bandit"]},
                "semgrep": {"returncode": 0, "command": ["semgrep", "scan"]},
            },
            "total_findings": 2,
            "findings": [
                {
                    "source_tool": "bandit",
                    "source_rule_id": "B501",
                    "file_path": "fixtures/mvp/example.py",
                    "severity": "high",
                    "mvp_category": "verify_false",
                    "remediation_mode": "autofix_candidate",
                    "cwe_id": 295,
                },
                {
                    "source_tool": "semgrep",
                    "source_rule_id": "python.lang.security...",
                    "file_path": "fixtures/mvp/example.py",
                    "severity": "medium",
                    "mvp_category": "sql_injection",
                    "remediation_mode": "proposal_only",
                    "cwe_id": 89,
                },
            ],
        }

    monkeypatch.setattr("app.main.analyze_fixtures_runtime", fake_runtime_analysis)

    response = client.post("/analysis/run-fixtures")

    assert response.status_code == 200

    payload = response.json()
    assert payload["analysis_target"] == "fixtures/mvp"
    assert payload["execution_mode"] == "runtime"
    assert payload["total_findings"] == 2
    assert len(payload["findings"]) == 2
