from __future__ import annotations

from pathlib import Path
from typing import Any

from app.models.finding import NormalizedFinding


def normalize_bandit_severity(value: str | None) -> str:
    if not value:
        return "unknown"

    value = value.lower()
    if value in {"low", "medium", "high"}:
        return value
    return "unknown"


def normalize_bandit_confidence(value: str | None) -> str:
    if not value:
        return "unknown"

    value = value.lower()
    if value in {"low", "medium", "high"}:
        return value
    return "unknown"


def infer_mvp_category_from_bandit_result(result: dict[str, Any]) -> str:
    test_id = result.get("test_id", "")
    file_path = result.get("filename", "")
    message = result.get("issue_text", "").lower()

    if test_id in {"B602", "B605"} or "shell" in message:
        return "command_injection"

    # B404: import subprocess — informativo; categoría propia para no mezclar con B602/B605 en verificación
    if test_id == "B404" and "command_injection" in file_path.replace("\\", "/"):
        return "subprocess_import_info"

    if test_id == "B506" or "yaml" in message:
        return "unsafe_yaml_load"

    if test_id == "B501" or "verify=false" in message or "certificate" in message:
        return "verify_false"

    if test_id == "B113" or "without timeout" in message:
        return "missing_timeout"

    if test_id == "B201" or "debug=true" in message or "flask" in file_path.lower():
        return "flask_debug_true"

    if test_id == "B608" or "sql injection" in message or "sql" in message:
        return "sql_injection"

    return "unknown"


def infer_remediation_mode(mvp_category: str) -> str:
    if mvp_category == "sql_injection":
        return "proposal_only"

    if mvp_category == "subprocess_import_info":
        return "detection_only"

    if mvp_category in {
        "command_injection",
        "unsafe_yaml_load",
        "verify_false",
        "missing_timeout",
        "flask_debug_true",
    }:
        return "autofix_candidate"

    return "detection_only"


def build_title(mvp_category: str) -> str:
    titles = {
        "command_injection": "Posible command injection",
        "subprocess_import_info": "Importación de subprocess (aviso informativo)",
        "unsafe_yaml_load": "Uso inseguro de yaml.load",
        "verify_false": "Desactivación de verificación TLS",
        "missing_timeout": "Petición HTTP sin timeout",
        "flask_debug_true": "Flask ejecutado con debug=True",
        "sql_injection": "Posible SQL injection",
        "unknown": "Hallazgo de seguridad",
    }
    return titles.get(mvp_category, "Hallazgo de seguridad")


def parse_bandit_result(
    result: dict[str, Any],
    *,
    analysis_target: str | None = None,
) -> NormalizedFinding:
    test_id = result.get("test_id", "")
    mvp_category = infer_mvp_category_from_bandit_result(result)
    remediation_mode = infer_remediation_mode(mvp_category)

    issue_cwe = result.get("issue_cwe") or {}
    line_range = result.get("line_range") or []
    line_start = result.get("line_number", 0)
    line_end = line_range[-1] if line_range else line_start

    title = build_title(mvp_category)

    return NormalizedFinding(
        source_tool="bandit",
        source_rule_id=result.get("test_id", "unknown"),
        source_rule_name=result.get("test_name"),
        file_path=result.get("filename", ""),
        line_start=line_start,
        line_end=line_end,
        code_snippet=result.get("code"),
        title=title,
        description=result.get("issue_text"),
        severity=normalize_bandit_severity(result.get("issue_severity")),
        confidence=normalize_bandit_confidence(result.get("issue_confidence")),
        raw_message=result.get("issue_text", ""),
        reference_url=result.get("more_info"),
        cwe_id=issue_cwe.get("id"),
        cwe_url=issue_cwe.get("link"),
        owasp_top10=None,
        owasp_asvs=None,
        mvp_category=mvp_category,
        candidate_for_remediation=remediation_mode != "detection_only",
        remediation_mode=remediation_mode,
        verification_status="pending",
        detected_at=None,
        analysis_target=analysis_target,
        raw_tool_data=result,
    )


def parse_bandit_report(
    report: dict[str, Any],
    *,
    analysis_target: str | None = None,
) -> list[NormalizedFinding]:
    results = report.get("results", [])
    return [
        parse_bandit_result(result, analysis_target=analysis_target)
        for result in results
    ]


def parse_bandit_report_file(file_path: str | Path) -> list[NormalizedFinding]:
    import json

    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        report = json.load(f)

    return parse_bandit_report(report, analysis_target=str(path))
