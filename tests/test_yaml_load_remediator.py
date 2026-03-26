from pathlib import Path

from app.services.remediations.yaml_load_remediator import (
    propose_yaml_load_remediation,
)


def test_yaml_load_remediation_replaces_simple_unsafe_pattern() -> None:
    source_code = """
import yaml

def load_config(data: str):
    return yaml.load(data, Loader=yaml.Loader)
""".strip()

    proposal = propose_yaml_load_remediation(source_code)

    assert proposal.applicable is True
    assert proposal.confidence == "high"
    assert proposal.original_snippet == "yaml.load(data, Loader=yaml.Loader)"
    assert proposal.proposed_snippet == "yaml.safe_load(data)"
    assert proposal.changed_content is not None
    assert "yaml.safe_load(data)" in proposal.changed_content
    assert "yaml.load(data, Loader=yaml.Loader)" not in proposal.changed_content


def test_yaml_load_remediation_returns_not_applicable_for_non_matching_code() -> None:
    source_code = """
import yaml

def load_config(data: str):
    return yaml.safe_load(data)
""".strip()

    proposal = propose_yaml_load_remediation(source_code)

    assert proposal.applicable is False
    assert proposal.changed_content is None
    assert proposal.original_snippet is None
    assert proposal.proposed_snippet is None


def test_yaml_load_remediation_works_with_real_fixture() -> None:
    fixture_path = Path("fixtures/mvp/unsafe_yaml_load/vuln_yaml_load.py")
    assert fixture_path.exists()

    source_code = fixture_path.read_text(encoding="utf-8")
    proposal = propose_yaml_load_remediation(source_code)

    assert proposal.applicable is True
    assert proposal.changed_content is not None
    assert "yaml.safe_load(data)" in proposal.changed_content
