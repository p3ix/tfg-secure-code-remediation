from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.models.finding import NormalizedFinding


def normalize_semgrep_severity(value: str | None) -> str:
    if not value:
        return "unknown"

    value = value.lower()

    if value in {"error", "high"}:
        return "high"
    if value in {"warning", "medium"}:
        return "medium"
    if value in {"info", "low"}:
        return "low"

    return "unknown"


def infer_mvp_category_from_semgrep_result(result: dict[str, Any]) -> str:
    check_id = (result.get("check_id") or "").lower()
    path = (result.get("path") or "").lower()
    message = (
        result.get("extra", {}).get("message", "") or ""
    ).lower()

    if "subprocess-shell-true" in check_id or "shell=true" in message:
        return "command_injection"

    if "yaml" in check_id or "pyyaml" in check_id or "yaml" in message:
        return "unsafe_yaml_load"

    if "disabled-cert-validation" in check_id or "verify=false" in message:
        return "verify_false"

    if "timeout" in check_id or "without timeout" in message:
        return "missing_timeout"

    if "debug-enabled" in check_id or ("flask" in path and "debug" in message):
        return "flask_debug_true"

    if "sql" in check_id or "sql injection" in message or "query" in message:
        return "sql_injection"

    return "unknown"


def infer_remediation_mode(mvp_category: str) -> str:
    if mvp_category == "sql_injection":
        return "proposal_only"

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
        "unsafe_yaml_load": "Uso inseguro de yaml.load",
        "verify_false": "Desactivación de verificación TLS",
        "missing_timeout": "Petición HTTP sin timeout",
        "flask_debug_true": "Flask ejecutado con debug=True",
        "sql_injection": "Posible SQL injection",
        "unknown": "Hallazgo de seguridad",
    }
    return titles.get(mvp_category, "Hallazgo de seguridad")


def extract_first_cwe_id(metadata: Any) -> int | None:
    if metadata is None:
        return None

    if isinstance(metadata, dict):
        for value in metadata.values():
            found = extract_first_cwe_id(value)
            if found is not None:
                return found
        return None

    if isinstance(metadata, list):
        for item in metadata:
            found = extract_first_cwe_id(item)
            if found is not None:
                return found
        return None

    if isinstance(metadata, str):
        match = re.search(r"CWE[-\s:]*(\d+)", metadata, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


def build_cwe_url(cwe_id: int | None) -> str | None:
    if cwe_id is None:
        return None
    return f"https://cwe.mitre.org/data/definitions/{cwe_id}.html"


def extract_reference_url(extra: dict[str, Any]) -> str | None:
    metadata = extra.get("metadata", {}) or {}

    for key in ("source", "shortlink"):
        value = metadata.get(key)
        if isinstance(value, str) and value:
            return value

    references = metadata.get("references")
    if isinstance(references, list):
        for item in references:
            if isinstance(item, str) and item:
                return item

    return None


def parse_semgrep_result(
    result: dict[str, Any],
    *,
    analysis_target: str | None = None,
) -> NormalizedFinding:
    extra = result.get("extra", {}) or {}
    metadata = extra.get("metadata", {}) or {}

    mvp_category = infer_mvp_category_from_semgrep_result(result)
    remediation_mode = infer_remediation_mode(mvp_category)

    line_start = result.get("start", {}).get("line", 0)
    line_end = result.get("end", {}).get("line", line_start)

    cwe_id = extract_first_cwe_id(metadata)

    return NormalizedFinding(
        source_tool="semgrep",
        source_rule_id=result.get("check_id", "unknown"),
        source_rule_name=None,
        file_path=result.get("path", ""),
        line_start=line_start,
        line_end=line_end,
        code_snippet=extra.get("lines"),
        title=build_title(mvp_category),
        description=extra.get("message"),
        severity=normalize_semgrep_severity(extra.get("severity")),
        confidence="unknown",
        raw_message=extra.get("message", ""),
        reference_url=extract_reference_url(extra),
        cwe_id=cwe_id,
        cwe_url=build_cwe_url(cwe_id),
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


def parse_semgrep_report(
    report: dict[str, Any],
    *,
    analysis_target: str | None = None,
) -> list[NormalizedFinding]:
    results = report.get("results", [])
    return [
        parse_semgrep_result(result, analysis_target=analysis_target)
        for result in results
    ]


def parse_semgrep_report_file(file_path: str | Path) -> list[NormalizedFinding]:
    import json

    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        report = json.load(f)

    return parse_semgrep_report(report, analysis_target=str(path))
