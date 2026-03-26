from pathlib import Path

from app.services.verification.verify_false_verifier import (
    verify_verify_false_remediation,
)


def test_verify_verify_false_remediation_succeeds_on_real_fixture() -> None:
    fixture_path = Path("fixtures/mvp/https_verify_false/vuln_requests_verify_false.py")
    source_code = fixture_path.read_text(encoding="utf-8")

    result = verify_verify_false_remediation(source_code)

    assert result["applicable"] is True
    assert result["verified"] is True
    assert result["remaining_findings"] == []
    assert result["proposed_snippet"] == "verify=True"
    assert "missing_timeout" in result["other_remaining_categories"]


def test_verify_verify_false_remediation_not_applicable_on_safe_code() -> None:
    source_code = """
import requests

def fetch_data() -> str:
    response = requests.get("https://example.com", verify=True)
    return response.text
""".strip()

    result = verify_verify_false_remediation(source_code)

    assert result["applicable"] is False
    assert result["verified"] is False
