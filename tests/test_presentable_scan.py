from pathlib import Path

from app.models.finding import NormalizedFinding
from app.services.presentable_scan import (
    build_presentable_scan,
    filter_presentable_scan,
    presentable_from_internal_analysis,
)


def test_build_presentable_scan_shape() -> None:
    findings = [
        NormalizedFinding(
            source_tool="bandit",
            source_rule_id="B608",
            file_path="fixtures/mvp/sql_injection/x.py",
            line_start=1,
            raw_message="sql",
            severity="medium",
            mvp_category="sql_injection",
            candidate_for_remediation=True,
            remediation_mode="proposal_only",
            title="Posible SQL injection",
            cwe_id=89,
            cwe_url="https://cwe.mitre.org/data/definitions/89.html",
            owasp_top10="A05:2025 - Injection",
            owasp_asvs="ASVS v5.0.0 V1.2 Injection Prevention",
        ),
    ]

    out = build_presentable_scan(
        findings,
        analysis_target="fixtures/mvp",
        execution_mode="static_reports",
        reports={"bandit": "r1.json", "semgrep": "r2.json"},
    )

    assert out["schema_version"] == "1.0"
    assert out["meta"]["execution_mode"] == "static_reports"
    assert "generated_at" in out["meta"]
    assert out["meta"]["reports"]["bandit"] == "r1.json"
    assert out["summary"]["total_findings"] == 1
    assert out["summary"]["by_mvp_category"]["sql_injection"] == 1
    assert len(out["findings"]) == 1
    row = out["findings"][0]
    assert row["id"] == 1
    assert row["remediation"]["mode"] == "proposal_only"
    assert "Solo detección" in row["remediation"]["mode_label"]
    assert row["standards"]["cwe_id"] == 89


def test_filter_presentable_scan_hide_info() -> None:
    scan = {
        "schema_version": "1.0",
        "meta": {"analysis_target": "x", "execution_mode": "static_reports"},
        "summary": {},
        "findings": [
            {
                "id": 1,
                "severity": "low",
                "category": "command_injection",
                "remediation": {"mode": "autofix_candidate"},
            },
            {
                "id": 2,
                "severity": "high",
                "category": "command_injection",
                "remediation": {"mode": "detection_only"},
            },
            {
                "id": 3,
                "severity": "high",
                "category": "verify_false",
                "remediation": {"mode": "autofix_candidate"},
            },
        ],
    }

    out = filter_presentable_scan(scan, hide_info=True)

    assert out["meta"]["presentable_filter"] == "hide_info"
    assert len(out["findings"]) == 1
    assert out["findings"][0]["category"] == "verify_false"
    assert out["findings"][0]["id"] == 1
    assert out["summary"]["total_findings"] == 1

    unchanged = filter_presentable_scan(scan, hide_info=False)
    assert unchanged == scan


def test_presentable_from_internal_analysis_roundtrip() -> None:
    internal = {
        "analysis_target": "fixtures/mvp",
        "bandit_report": "reports/bandit/x.json",
        "semgrep_report": "reports/semgrep/y.json",
        "total_findings": 1,
        "findings": [
            {
                "source_tool": "bandit",
                "source_rule_id": "B602",
                "file_path": "a.py",
                "line_start": 2,
                "raw_message": "shell",
                "severity": "high",
                "mvp_category": "command_injection",
                "candidate_for_remediation": True,
                "remediation_mode": "autofix_candidate",
                "title": "Posible command injection",
                "line_end": None,
                "source_rule_name": None,
                "code_snippet": None,
                "description": None,
                "confidence": None,
                "reference_url": None,
                "cwe_id": 78,
                "cwe_url": None,
                "owasp_top10": None,
                "owasp_asvs": None,
                "verification_status": None,
                "detected_at": None,
                "analysis_target": None,
                "raw_tool_data": None,
            }
        ],
    }

    out = presentable_from_internal_analysis(internal)

    assert out["meta"]["execution_mode"] == "static_reports"
    assert out["findings"][0]["category"] == "command_injection"


def test_presentable_fixtures_endpoint_if_reports_exist() -> None:
    bandit = Path("reports/bandit/fixtures-mvp-bandit.json")
    semgrep = Path("reports/semgrep/fixtures-mvp-semgrep.json")
    if not bandit.exists() or not semgrep.exists():
        return

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/analysis/fixtures/presentable")

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["summary"]["total_findings"] > 0
    assert isinstance(body["findings"], list)
