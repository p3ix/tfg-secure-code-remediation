from pathlib import Path

from app.services.verification.command_injection_verifier import (
    verify_command_injection_remediation,
)


def test_verify_shell_true_remediation_succeeds_on_real_fixture() -> None:
    fixture_path = Path("fixtures/mvp/command_injection/vuln_shell_true.py")
    source_code = fixture_path.read_text(encoding="utf-8")

    result = verify_command_injection_remediation(source_code)

    assert result["applicable"] is True
    assert result["verified"] is True
    assert result["remaining_findings"] == []
    assert "shlex.split" in result["proposed_snippet"]


def test_verify_os_system_remediation_succeeds_on_real_fixture() -> None:
    fixture_path = Path("fixtures/mvp/command_injection/vuln_os_system.py")
    source_code = fixture_path.read_text(encoding="utf-8")

    result = verify_command_injection_remediation(source_code)

    assert result["applicable"] is True
    assert result["verified"] is True
    assert result["remaining_findings"] == []
    assert "subprocess.run" in result["proposed_snippet"]


def test_verify_command_injection_not_applicable_on_safe_code() -> None:
    source_code = """
import subprocess

def run_safe_command() -> None:
    subprocess.run(["ls", "-l"], check=False)
""".strip()

    result = verify_command_injection_remediation(source_code)

    assert result["applicable"] is False
    assert result["verified"] is False
