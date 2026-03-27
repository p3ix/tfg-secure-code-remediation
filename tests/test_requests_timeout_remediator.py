from pathlib import Path

from app.services.remediations.requests_timeout_remediator import (
    propose_requests_timeout_remediation,
)


def test_requests_timeout_remediation_adds_timeout() -> None:
    source_code = """
import requests

def fetch_api_data() -> str:
    response = requests.get("https://api.example.com/data")
    return response.text
""".strip()

    proposal = propose_requests_timeout_remediation(source_code)

    assert proposal.applicable is True
    assert proposal.confidence == "high"
    assert proposal.changed_content is not None
    assert 'timeout=10' in proposal.changed_content
    assert 'requests.get("https://api.example.com/data", timeout=10)' in proposal.changed_content


def test_requests_timeout_remediation_returns_not_applicable_when_timeout_exists() -> None:
    source_code = """
import requests

def fetch_api_data() -> str:
    response = requests.get("https://api.example.com/data", timeout=10)
    return response.text
""".strip()

    proposal = propose_requests_timeout_remediation(source_code)

    assert proposal.applicable is False
    assert proposal.changed_content is None


def test_requests_timeout_remediation_works_with_real_fixture() -> None:
    fixture_path = Path("fixtures/mvp/missing_timeout/vuln_requests_no_timeout.py")
    assert fixture_path.exists()

    source_code = fixture_path.read_text(encoding="utf-8")
    proposal = propose_requests_timeout_remediation(source_code)

    assert proposal.applicable is True
    assert proposal.changed_content is not None
    assert "timeout=10" in proposal.changed_content
