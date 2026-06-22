from app.models.finding import NormalizedFinding
from app.services.ai.enrichment import (
    build_code_focus,
    build_location_hint,
)
from app.services.ai.stub_provider import StubProvider


def _finding(**overrides: object) -> NormalizedFinding:
    base = {
        "source_tool": "bandit",
        "source_rule_id": "B602",
        "file_path": "app/cli.py",
        "line_start": 12,
        "raw_message": "subprocess con shell=True",
        "severity": "high",
        "mvp_category": "command_injection",
        "candidate_for_remediation": True,
        "remediation_mode": "autofix_candidate",
        "code_snippet": "subprocess.call(cmd, shell=True)",
    }
    base.update(overrides)
    return NormalizedFinding(**base)  # type: ignore[arg-type]


def test_build_location_hint_single_line() -> None:
    assert build_location_hint(_finding()) == "app/cli.py:12"


def test_build_location_hint_with_range() -> None:
    assert build_location_hint(_finding(line_start=10, line_end=14)) == "app/cli.py:10-14"


def test_build_code_focus_prefers_snippet() -> None:
    assert build_code_focus(_finding()) == "subprocess.call(cmd, shell=True)"


def test_build_code_focus_falls_back_to_message() -> None:
    assert (
        build_code_focus(_finding(code_snippet=None, raw_message="yaml.load(data)"))
        == "yaml.load(data)"
    )


def test_apply_finding_enrichment_on_stub() -> None:
    explanation = StubProvider().explain(_finding())
    assert explanation.location_hint == "app/cli.py:12"
    assert explanation.code_focus == "subprocess.call(cmd, shell=True)"
    assert len(explanation.action_steps or []) >= 2
