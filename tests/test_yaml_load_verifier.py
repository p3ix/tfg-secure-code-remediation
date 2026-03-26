from pathlib import Path

from app.services.verification.yaml_load_verifier import verify_yaml_load_remediation


def test_verify_yaml_load_remediation_succeeds_on_real_fixture() -> None:
    fixture_path = Path("fixtures/mvp/unsafe_yaml_load/vuln_yaml_load.py")
    source_code = fixture_path.read_text(encoding="utf-8")

    result = verify_yaml_load_remediation(source_code)

    assert result["applicable"] is True
    assert result["verified"] is True
    assert result["remaining_findings"] == []
    assert result["proposed_snippet"] == "yaml.safe_load(data)"


def test_verify_yaml_load_remediation_not_applicable_on_safe_code() -> None:
    source_code = """
import yaml

def load_config(data: str):
    return yaml.safe_load(data)
""".strip()

    result = verify_yaml_load_remediation(source_code)

    assert result["applicable"] is False
    assert result["verified"] is False
