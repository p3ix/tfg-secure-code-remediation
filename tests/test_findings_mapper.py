from app.models.finding import NormalizedFinding
from app.services.findings_loader import load_all_findings
from app.services.findings_mapper import (
    enrich_finding_with_classification,
    enrich_findings_with_classification,
)


def build_base_finding(mvp_category: str) -> NormalizedFinding:
    return NormalizedFinding(
        source_tool="bandit",
        source_rule_id="TEST",
        file_path="fixtures/example.py",
        line_start=1,
        raw_message="example",
        severity="medium",
        mvp_category=mvp_category,
        candidate_for_remediation=True,
        remediation_mode="autofix_candidate",
    )


def test_command_injection_mapping() -> None:
    finding = build_base_finding("command_injection")

    enriched = enrich_finding_with_classification(finding)

    assert enriched.cwe_id == 78
    assert enriched.owasp_top10 == "A05:2025 - Injection"
    assert enriched.owasp_asvs == "ASVS v5.0.0 V1.2 Injection Prevention"


def test_yaml_mapping_uses_project_primary_classification() -> None:
    finding = build_base_finding("unsafe_yaml_load")

    enriched = enrich_finding_with_classification(finding)

    assert enriched.cwe_id == 502
    assert enriched.owasp_top10 == "A08:2025 - Software or Data Integrity Failures"
    assert enriched.owasp_asvs == "ASVS v5.0.0 V1.5 Safe Deserialization"


def test_missing_timeout_mapping_is_partial() -> None:
    finding = build_base_finding("missing_timeout")

    enriched = enrich_finding_with_classification(finding)

    assert enriched.cwe_id == 400
    assert enriched.owasp_top10 is None
    assert enriched.owasp_asvs is None


def test_sql_injection_mapping() -> None:
    finding = build_base_finding("sql_injection")

    enriched = enrich_finding_with_classification(finding)

    assert enriched.cwe_id == 89
    assert enriched.owasp_top10 == "A05:2025 - Injection"
    assert enriched.owasp_asvs == "ASVS v5.0.0 V1.2 Injection Prevention"


def test_enrich_findings_with_classification_on_real_data() -> None:
    findings = load_all_findings(
        bandit_report_path="reports/bandit/fixtures-mvp-bandit.json",
        semgrep_report_path="reports/semgrep/fixtures-mvp-semgrep.json",
    )

    enriched = enrich_findings_with_classification(findings)

    assert len(enriched) == len(findings)
    assert any(f.cwe_id == 78 for f in enriched)
    assert any(f.cwe_id == 89 for f in enriched)
    assert any(f.cwe_id == 295 for f in enriched)
    assert any(f.cwe_id == 489 for f in enriched)
