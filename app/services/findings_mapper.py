from __future__ import annotations

from dataclasses import replace

from app.models.finding import NormalizedFinding


CLASSIFICATION_MAP: dict[str, dict[str, str | int | None]] = {
    "command_injection": {
        "cwe_id": 78,
        "owasp_top10": "A05:2025 - Injection",
        "owasp_asvs": "ASVS v5.0.0 V1.2 Injection Prevention",
    },
    "unsafe_yaml_load": {
        "cwe_id": 502,
        "owasp_top10": "A08:2025 - Software or Data Integrity Failures",
        "owasp_asvs": "ASVS v5.0.0 V1.5 Safe Deserialization",
    },
    "verify_false": {
        "cwe_id": 295,
        "owasp_top10": "A04:2025 - Cryptographic Failures",
        "owasp_asvs": "ASVS v5.0.0 V12.2 HTTPS Communication with External Facing Services",
    },
    "missing_timeout": {
        "cwe_id": 400,
        "owasp_top10": None,
        "owasp_asvs": None,
    },
    "flask_debug_true": {
        "cwe_id": 489,
        "owasp_top10": "A02:2025 - Security Misconfiguration",
        "owasp_asvs": "ASVS v5.0.0 V13 Configuration",
    },
    "sql_injection": {
        "cwe_id": 89,
        "owasp_top10": "A05:2025 - Injection",
        "owasp_asvs": "ASVS v5.0.0 V1.2 Injection Prevention",
    },
}


def build_cwe_url(cwe_id: int | None) -> str | None:
    if cwe_id is None:
        return None
    return f"https://cwe.mitre.org/data/definitions/{cwe_id}.html"


def enrich_finding_with_classification(
    finding: NormalizedFinding,
) -> NormalizedFinding:
    mapping = CLASSIFICATION_MAP.get(finding.mvp_category)

    if mapping is None:
        return finding

    cwe_id = mapping["cwe_id"]
    assert cwe_id is None or isinstance(cwe_id, int)

    return replace(
        finding,
        cwe_id=cwe_id,
        cwe_url=build_cwe_url(cwe_id),
        owasp_top10=mapping["owasp_top10"],
        owasp_asvs=mapping["owasp_asvs"],
    )


def enrich_findings_with_classification(
    findings: list[NormalizedFinding],
) -> list[NormalizedFinding]:
    return [enrich_finding_with_classification(f) for f in findings]
