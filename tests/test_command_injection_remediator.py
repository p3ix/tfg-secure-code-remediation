from pathlib import Path

from app.services.remediations.command_injection_remediator import (
    propose_command_injection_remediation,
)


def test_shell_true_remediation_replaces_pattern() -> None:
    source_code = """
import subprocess

def run_user_command(user_input: str) -> None:
    subprocess.run(f"ls {user_input}", shell=True, check=False)
""".strip()

    proposal = propose_command_injection_remediation(source_code)

    assert proposal.applicable is True
    assert proposal.confidence == "high"
    assert proposal.remediation_kind == "command_injection"
    assert "shell=True" in proposal.original_snippet
    assert "shell=False" in proposal.proposed_snippet
    assert "shlex.split" in proposal.proposed_snippet
    assert proposal.changed_content is not None
    assert "shell=True" not in proposal.changed_content
    assert "import shlex" in proposal.changed_content


def test_os_system_remediation_replaces_pattern() -> None:
    source_code = """
import os

def list_directory(user_input: str) -> None:
    os.system("ls " + user_input)
""".strip()

    proposal = propose_command_injection_remediation(source_code)

    assert proposal.applicable is True
    assert proposal.confidence == "high"
    assert proposal.remediation_kind == "command_injection"
    assert "os.system" in proposal.original_snippet
    assert "subprocess.run" in proposal.proposed_snippet
    assert "shlex.split" in proposal.proposed_snippet
    assert proposal.changed_content is not None
    assert "os.system" not in proposal.changed_content
    assert "import shlex" in proposal.changed_content
    assert "import subprocess" in proposal.changed_content


def test_remediation_returns_not_applicable_for_safe_code() -> None:
    source_code = """
import subprocess

def run_safe_command() -> None:
    subprocess.run(["ls", "-l"], check=False)
""".strip()

    proposal = propose_command_injection_remediation(source_code)

    assert proposal.applicable is False
    assert proposal.changed_content is None
    assert proposal.original_snippet is None


def test_shell_true_remediation_works_with_real_fixture() -> None:
    fixture_path = Path("fixtures/mvp/command_injection/vuln_shell_true.py")
    assert fixture_path.exists()

    source_code = fixture_path.read_text(encoding="utf-8")
    proposal = propose_command_injection_remediation(source_code)

    assert proposal.applicable is True
    assert proposal.changed_content is not None
    assert "shell=False" in proposal.changed_content
    assert "shlex.split" in proposal.changed_content


def test_os_system_remediation_works_with_real_fixture() -> None:
    fixture_path = Path("fixtures/mvp/command_injection/vuln_os_system.py")
    assert fixture_path.exists()

    source_code = fixture_path.read_text(encoding="utf-8")
    proposal = propose_command_injection_remediation(source_code)

    assert proposal.applicable is True
    assert proposal.changed_content is not None
    assert "subprocess.run" in proposal.changed_content
    assert "shlex.split" in proposal.changed_content
