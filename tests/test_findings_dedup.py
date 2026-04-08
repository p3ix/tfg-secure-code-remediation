"""Tests para agrupación de hallazgos equivalentes."""

from app.models.finding import NormalizedFinding
from app.services.findings_dedup import (
    equivalence_key,
    group_findings_by_equivalence,
    max_severity,
)
from app.services.presentable_scan import (
    build_presentable_scan,
    presentable_from_internal_analysis,
)


def _f(
    *,
    tool: str,
    rule: str,
    path: str = "fixtures/mvp/x.py",
    line: int = 10,
    category: str = "command_injection",
    severity: str = "high",
) -> NormalizedFinding:
    return NormalizedFinding(
        source_tool=tool,
        source_rule_id=rule,
        file_path=path,
        line_start=line,
        raw_message="m",
        severity=severity,
        mvp_category=category,
        candidate_for_remediation=True,
        remediation_mode="autofix_candidate",
        title="t",
    )


def test_equivalence_key_same_for_two_tools() -> None:
    a = _f(tool="bandit", rule="B602")
    b = _f(tool="semgrep", rule="python.lang.security")
    assert equivalence_key(a) == equivalence_key(b)


def test_group_merges_two_tools() -> None:
    findings = [
        _f(tool="bandit", rule="B602"),
        _f(tool="semgrep", rule="R1"),
    ]
    groups = group_findings_by_equivalence(findings)
    assert len(groups) == 1
    assert len(groups[0]) == 2


def test_max_severity() -> None:
    findings = [
        _f(tool="a", rule="1", severity="low"),
        _f(tool="b", rule="2", severity="high"),
    ]
    assert max_severity(findings) == "high"


def test_build_presentable_grouped() -> None:
    findings = [
        _f(tool="bandit", rule="B602"),
        _f(tool="semgrep", rule="R1"),
    ]
    out = build_presentable_scan(
        findings,
        analysis_target="fixtures/mvp",
        execution_mode="static_reports",
        group_equivalent=True,
    )
    assert out["meta"].get("group_equivalent") is True
    assert out["summary"]["total_findings"] == 1
    row = out["findings"][0]
    assert row["group_size"] == 2
    assert len(row["sources"]) == 2
    assert {s["tool"] for s in row["sources"]} == {"bandit", "semgrep"}


def test_build_presentable_flat_unchanged_count() -> None:
    findings = [
        _f(tool="bandit", rule="B602"),
        _f(tool="semgrep", rule="R1"),
    ]
    out = build_presentable_scan(
        findings,
        analysis_target="fixtures/mvp",
        execution_mode="static_reports",
        group_equivalent=False,
    )
    assert out["summary"]["total_findings"] == 2
    assert "sources" not in out["findings"][0]


def test_presentable_from_internal_group_equivalent() -> None:
    internal = {
        "analysis_target": "fixtures/mvp",
        "bandit_report": "reports/bandit/x.json",
        "semgrep_report": "reports/semgrep/y.json",
        "findings": [
            {
                "source_tool": "bandit",
                "source_rule_id": "B602",
                "file_path": "fixtures/mvp/cmd.py",
                "line_start": 5,
                "raw_message": "x",
                "severity": "high",
                "mvp_category": "command_injection",
                "candidate_for_remediation": True,
                "remediation_mode": "autofix_candidate",
                "title": "cmd",
                "line_end": None,
                "source_rule_name": None,
                "code_snippet": None,
                "description": None,
                "confidence": None,
                "reference_url": None,
                "cwe_id": None,
                "cwe_url": None,
                "owasp_top10": None,
                "owasp_asvs": None,
                "verification_status": None,
                "detected_at": None,
                "analysis_target": None,
                "raw_tool_data": None,
            },
            {
                "source_tool": "semgrep",
                "source_rule_id": "S1",
                "file_path": "fixtures/mvp/cmd.py",
                "line_start": 5,
                "raw_message": "x",
                "severity": "high",
                "mvp_category": "command_injection",
                "candidate_for_remediation": True,
                "remediation_mode": "autofix_candidate",
                "title": "cmd",
                "line_end": None,
                "source_rule_name": None,
                "code_snippet": None,
                "description": None,
                "confidence": None,
                "reference_url": None,
                "cwe_id": None,
                "cwe_url": None,
                "owasp_top10": None,
                "owasp_asvs": None,
                "verification_status": None,
                "detected_at": None,
                "analysis_target": None,
                "raw_tool_data": None,
            },
        ],
    }
    out = presentable_from_internal_analysis(internal, group_equivalent=True)
    assert out["summary"]["total_findings"] == 1
    assert out["findings"][0]["group_size"] == 2
