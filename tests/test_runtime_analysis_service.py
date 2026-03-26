from app.services.runtime_analysis_service import (
    build_bandit_command,
    build_semgrep_command,
)


def test_build_bandit_command() -> None:
    command = build_bandit_command(
        "fixtures/mvp",
        "reports/runtime/fixtures-mvp-bandit-runtime.json",
    )

    assert command[0] == "bandit"
    assert "-r" in command
    assert "fixtures/mvp" in command
    assert "-o" in command


def test_build_semgrep_command() -> None:
    command = build_semgrep_command(
        "fixtures/mvp",
        "reports/runtime/fixtures-mvp-semgrep-runtime.json",
    )

    assert command[0] == "semgrep"
    assert "scan" in command
    assert "--config" in command
    assert "p/default" in command
    assert "--json-output" in command
