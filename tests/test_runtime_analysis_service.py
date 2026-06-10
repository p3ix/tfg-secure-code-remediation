import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.config import get_settings
from app.services import runtime_analysis_service as runtime
from app.services.runtime_analysis_service import (
    analyze_fixtures_runtime,
    build_bandit_command,
    build_semgrep_command,
    run_analysis_command,
)


def test_build_bandit_command() -> None:
    command = build_bandit_command(
        "fixtures/mvp",
        "reports/runtime/fixtures-mvp-bandit-runtime.json",
    )

    assert "bandit" in " ".join(command[:3])
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

    assert "semgrep" in " ".join(command[:3])
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


def test_run_analysis_command_raises_when_tool_missing() -> None:
    with pytest.raises(RuntimeError, match="comando no encontrado"):
        run_analysis_command(["definitely-missing-tool-xyz"])


def _redirect_runtime_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path]:
    target = tmp_path / "fixtures-mvp"
    target.mkdir()
    (target / "sample.py").write_text("x = 1\n", encoding="utf-8")
    reports_dir = tmp_path / "runtime"
    bandit_report = reports_dir / "bandit.json"
    semgrep_report = reports_dir / "semgrep.json"
    monkeypatch.setattr(runtime, "FIXTURES_TARGET", target)
    monkeypatch.setattr(runtime, "RUNTIME_REPORTS_DIR", reports_dir)
    monkeypatch.setattr(runtime, "BANDIT_RUNTIME_REPORT", bandit_report)
    monkeypatch.setattr(runtime, "SEMGREP_RUNTIME_REPORT", semgrep_report)
    return bandit_report, semgrep_report


def _fake_completed(returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["tool"], returncode=returncode, stdout="", stderr=stderr)


def test_analyze_fixtures_runtime_happy_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bandit_report, semgrep_report = _redirect_runtime_paths(monkeypatch, tmp_path)

    def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        if "bandit" in " ".join(command):
            bandit_report.write_text(json.dumps({"results": []}), encoding="utf-8")
        else:
            semgrep_report.write_text(json.dumps({"results": []}), encoding="utf-8")
        return _fake_completed()

    monkeypatch.setattr(runtime, "run_analysis_command", fake_run)

    out = analyze_fixtures_runtime(analysis_id="abc123")

    assert out["analysis_id"] == "abc123"
    assert out["execution_mode"] == "runtime"
    assert out["total_findings"] == 0
    assert set(out["tool_runs"]) == {"bandit", "semgrep"}
    assert out["tool_runs"]["bandit"]["returncode"] == 0


def test_analyze_fixtures_runtime_missing_target(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(runtime, "FIXTURES_TARGET", tmp_path / "nope")
    with pytest.raises(FileNotFoundError, match="Analysis target not found"):
        analyze_fixtures_runtime()


def test_analyze_fixtures_runtime_missing_bandit_report(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _bandit_report, semgrep_report = _redirect_runtime_paths(monkeypatch, tmp_path)

    def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        if "semgrep" in " ".join(command):
            semgrep_report.write_text(json.dumps({"results": []}), encoding="utf-8")
        return _fake_completed()

    monkeypatch.setattr(runtime, "run_analysis_command", fake_run)

    with pytest.raises(RuntimeError, match="Bandit execution did not produce"):
        analyze_fixtures_runtime()


def test_analyze_fixtures_runtime_missing_semgrep_report(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bandit_report, _semgrep_report = _redirect_runtime_paths(monkeypatch, tmp_path)

    def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        if "bandit" in " ".join(command):
            bandit_report.write_text(json.dumps({"results": []}), encoding="utf-8")
        return _fake_completed()

    monkeypatch.setattr(runtime, "run_analysis_command", fake_run)

    with pytest.raises(RuntimeError, match="Semgrep execution did not produce"):
        analyze_fixtures_runtime()
