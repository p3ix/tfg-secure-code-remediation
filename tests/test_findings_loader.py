from app.services.findings_loader import (
    load_all_findings,
    load_bandit_findings,
    load_semgrep_findings,
)


BANDIT_REPORT = "reports/bandit/fixtures-mvp-bandit.json"
SEMGREP_REPORT = "reports/semgrep/fixtures-mvp-semgrep.json"


def test_load_bandit_findings_returns_normalized_findings() -> None:
    findings = load_bandit_findings(BANDIT_REPORT)

    assert len(findings) > 0
    assert all(f.source_tool == "bandit" for f in findings)
    assert any(f.mvp_category == "verify_false" for f in findings)
    assert any(f.mvp_category == "unsafe_yaml_load" for f in findings)


def test_load_semgrep_findings_returns_normalized_findings() -> None:
    findings = load_semgrep_findings(SEMGREP_REPORT)

    assert len(findings) > 0
    assert all(f.source_tool == "semgrep" for f in findings)
    assert any(f.mvp_category == "verify_false" for f in findings)
    assert any(f.mvp_category == "sql_injection" for f in findings)


def test_load_all_findings_combines_both_sources() -> None:
    findings = load_all_findings(
        bandit_report_path=BANDIT_REPORT,
        semgrep_report_path=SEMGREP_REPORT,
    )

    assert len(findings) > 0
    assert any(f.source_tool == "bandit" for f in findings)
    assert any(f.source_tool == "semgrep" for f in findings)


def test_load_all_findings_can_load_only_one_source() -> None:
    findings = load_all_findings(bandit_report_path=BANDIT_REPORT)

    assert len(findings) > 0
    assert all(f.source_tool == "bandit" for f in findings)


def test_load_all_findings_are_sorted() -> None:
    findings = load_all_findings(
        bandit_report_path=BANDIT_REPORT,
        semgrep_report_path=SEMGREP_REPORT,
    )

    sorted_findings = sorted(
        findings,
        key=lambda f: (
            f.file_path,
            f.line_start,
            f.source_tool,
            f.source_rule_id,
        ),
    )

    assert findings == sorted_findings
