from pathlib import Path

from app.models.finding import NormalizedFinding
from app.services.presentable_scan import (
    build_presentable_scan,
    build_tool_diagnostics,
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

    assert out["schema_version"] == "1.1"
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


def test_build_tool_diagnostics_from_tool_runs() -> None:
    findings = [
        NormalizedFinding(
            source_tool="bandit",
            source_rule_id="B602",
            file_path="a.py",
            line_start=1,
            raw_message="x",
            severity="low",
            mvp_category="command_injection",
            candidate_for_remediation=True,
            remediation_mode="autofix_candidate",
        ),
        NormalizedFinding(
            source_tool="bandit",
            source_rule_id="B404",
            file_path="a.py",
            line_start=1,
            raw_message="y",
            severity="low",
            mvp_category="subprocess_import_info",
            candidate_for_remediation=False,
            remediation_mode="detection_only",
        ),
    ]
    tool_runs = {
        "bandit": {"returncode": 1, "stderr_preview": "bandit warn"},
        "semgrep": {"returncode": 0, "stderr_preview": ""},
    }
    diag = build_tool_diagnostics(tool_runs, findings)
    assert len(diag) == 2
    assert diag[0]["tool"] == "bandit"
    assert diag[0]["findings_count"] == 2
    assert diag[0]["status"] == "completed_with_findings"
    assert diag[1]["tool"] == "semgrep"
    assert diag[1]["findings_count"] == 0
    assert diag[1]["status"] == "ok"
    assert "note" in diag[1]


def test_presentable_from_internal_includes_tool_diagnostics() -> None:
    internal = {
        "analysis_target": "upload.zip",
        "execution_mode": "runtime",
        "tool_runs": {
            "bandit": {"returncode": 1},
            "semgrep": {"returncode": 0},
        },
        "findings": [
            {
                "source_tool": "bandit",
                "source_rule_id": "B602",
                "file_path": "src/a.py",
                "line_start": 1,
                "raw_message": "shell",
                "severity": "low",
                "mvp_category": "command_injection",
                "candidate_for_remediation": True,
                "remediation_mode": "autofix_candidate",
            }
        ],
    }
    out = presentable_from_internal_analysis(internal)
    assert "tool_diagnostics" in out["meta"]
    assert len(out["meta"]["tool_diagnostics"]) == 2
    assert out["meta"]["tool_diagnostics"][0]["findings_count"] == 1


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
    assert "tool_diagnostics" not in out["meta"]


def test_presentable_from_internal_skips_invalid_findings() -> None:
    internal = {
        "analysis_target": "fixtures/mvp",
        "execution_mode": "runtime",
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
            },
            "invalid-row",
        ],
    }
    out = presentable_from_internal_analysis(internal)
    assert out["summary"]["total_findings"] == 1
    assert out["meta"]["invalid_findings_skipped"] == 1


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
    assert body["schema_version"] == "1.1"
    assert body["summary"]["total_findings"] > 0
    assert isinstance(body["findings"], list)
