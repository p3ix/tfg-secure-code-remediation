from app.models.finding import NormalizedFinding
from app.services.pipeline_orchestrator import build_pipeline_view


def test_build_pipeline_view_counts_and_groups() -> None:
    findings = [
        NormalizedFinding(
            source_tool="bandit",
            source_rule_id="B608",
            file_path="a.py",
            line_start=1,
            raw_message="x",
            severity="medium",
            mvp_category="sql_injection",
            candidate_for_remediation=True,
            remediation_mode="proposal_only",
        ),
        NormalizedFinding(
            source_tool="bandit",
            source_rule_id="B602",
            file_path="b.py",
            line_start=2,
            raw_message="y",
            severity="high",
            mvp_category="command_injection",
            candidate_for_remediation=True,
            remediation_mode="autofix_candidate",
        ),
        NormalizedFinding(
            source_tool="semgrep",
            source_rule_id="r1",
            file_path="b.py",
            line_start=3,
            raw_message="z",
            severity="medium",
            mvp_category="command_injection",
            candidate_for_remediation=True,
            remediation_mode="autofix_candidate",
        ),
    ]

    view = build_pipeline_view(findings)

    assert view["pipeline_step"] == "classified"
    assert view["total_findings"] == 3
    assert view["counts_by_mvp_category"]["sql_injection"] == 1
    assert view["counts_by_mvp_category"]["command_injection"] == 2
    assert view["counts_by_remediation_mode"]["proposal_only"] == 1
    assert view["counts_by_remediation_mode"]["autofix_candidate"] == 2
    assert len(view["findings_by_mvp_category"]["sql_injection"]) == 1
    assert len(view["findings_by_mvp_category"]["command_injection"]) == 2
