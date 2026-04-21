import sys

import pytest

from app.config import get_settings
from app.services.runtime_analysis_service import (
    build_bandit_command,
    build_semgrep_command,
    run_analysis_command,
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
    assert "-x" in command
    x_idx = command.index("-x")
    assert "node_modules" in command[x_idx + 1]


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
    assert any("node_modules" in arg for arg in command)


def test_build_bandit_command_respects_empty_exclude(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TFG_ANALYSIS_EXCLUDE_DIRS", "")
    get_settings.cache_clear()
    try:
        command = build_bandit_command("fixtures/mvp", "/tmp/out.json")
        assert "-x" not in command
    finally:
        get_settings.cache_clear()


def test_run_analysis_command_raises_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TFG_ANALYSIS_TIMEOUT_SEC", "1")
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="superó el tiempo límite"):
            run_analysis_command(
                [sys.executable, "-c", "import time; time.sleep(3600)"]
            )
    finally:
        get_settings.cache_clear()
