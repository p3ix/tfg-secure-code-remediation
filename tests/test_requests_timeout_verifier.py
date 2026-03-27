from pathlib import Path

from app.services.verification.requests_timeout_verifier import (
    verify_requests_timeout_remediation,
)


def test_verify_requests_timeout_remediation_succeeds_on_real_fixture() -> None:
    fixture_path = Path("fixtures/mvp/missing_timeout/vuln_requests_no_timeout.py")
    source_code = fixture_path.read_text(encoding="utf-8")

    result = verify_requests_timeout_remediation(source_code)

    assert result["applicable"] is True
    assert result["verified"] is True
    assert result["remaining_findings"] == []
    assert "timeout=10" in result["proposed_snippet"]


def test_verify_requests_timeout_remediation_not_applicable_when_timeout_exists() -> None:
    source_code = """
import requests

def fetch_api_data() -> str:
    response = requests.get("https://api.example.com/data", timeout=10)
    return response.text
""".strip()

    result = verify_requests_timeout_remediation(source_code)

    assert result["applicable"] is False
    assert result["verified"] is False
