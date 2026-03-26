from pathlib import Path

from app.services.remediations.verify_false_remediator import (
    propose_verify_false_remediation,
)


def test_verify_false_remediation_replaces_simple_pattern() -> None:
    source_code = """
import requests

def fetch_data() -> str:
    response = requests.get("https://example.com", verify=False)
    return response.text
""".strip()

    proposal = propose_verify_false_remediation(source_code)

    assert proposal.applicable is True
    assert proposal.confidence == "high"
    assert proposal.original_snippet == "verify=False"
    assert proposal.proposed_snippet == "verify=True"
    assert proposal.changed_content is not None
    assert "verify=True" in proposal.changed_content
    assert "verify=False" not in proposal.changed_content


def test_verify_false_remediation_returns_not_applicable_when_pattern_absent() -> None:
    source_code = """
import requests

def fetch_data() -> str:
    response = requests.get("https://example.com", verify=True)
    return response.text
""".strip()

    proposal = propose_verify_false_remediation(source_code)

    assert proposal.applicable is False
    assert proposal.changed_content is None


def test_verify_false_remediation_works_with_real_fixture() -> None:
    fixture_path = Path("fixtures/mvp/https_verify_false/vuln_requests_verify_false.py")
    assert fixture_path.exists()

    source_code = fixture_path.read_text(encoding="utf-8")
    proposal = propose_verify_false_remediation(source_code)

    assert proposal.applicable is True
    assert proposal.changed_content is not None
    assert "verify=True" in proposal.changed_content
    assert "verify=False" not in proposal.changed_content
