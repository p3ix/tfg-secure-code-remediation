from app.models.finding import NormalizedFinding
from pathlib import Path

from app.services.pipeline_orchestrator import (
    build_pipeline_view,
    run_mvp_autofix_verification_roundtrip,
)


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


def test_run_mvp_autofix_verification_roundtrip_partial_errors(
    monkeypatch, tmp_path
) -> None:
    ok_fixture = tmp_path / "ok.py"
    ok_fixture.write_text("print('x')", encoding="utf-8")
    missing_fixture = tmp_path / "missing.py"

    monkeypatch.setattr(
        "app.services.pipeline_orchestrator.MVP_AUTOFIX_FIXTURES",
        {"unsafe_yaml_load": [ok_fixture, missing_fixture]},
    )
    monkeypatch.setattr(
        "app.services.pipeline_orchestrator._load_verifier_map",
        lambda: {"unsafe_yaml_load": lambda source: {"ok": bool(source)}},
    )

    out = run_mvp_autofix_verification_roundtrip()
    summary = out["summary"]
    assert summary["categories_total"] == 1
    assert summary["categories_with_errors"] == 1
    assert summary["fixtures_total"] == 2
    assert summary["fixtures_verified"] == 1
    assert summary["fixtures_with_errors"] == 1
    assert out["categories"]["unsafe_yaml_load"][1]["error"] == "fixture no encontrado"


def test_run_mvp_autofix_verification_roundtrip_missing_verifier(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.pipeline_orchestrator.MVP_AUTOFIX_FIXTURES",
        {"verify_false": [Path("fixtures/mvp/https_verify_false/vuln_requests_verify_false.py")]},
    )
    monkeypatch.setattr(
        "app.services.pipeline_orchestrator._load_verifier_map",
        lambda: {},
    )

    out = run_mvp_autofix_verification_roundtrip()
    err = out["categories"]["verify_false"][0]["error"]
    assert "verificador no registrado" in err
