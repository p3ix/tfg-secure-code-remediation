from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.models.finding import NormalizedFinding

SCHEMA_VERSION = "1.0"

REMEDIATION_MODE_LABELS: dict[str, str] = {
    "autofix_candidate": "Remediación asistida posible (MVP)",
    "proposal_only": "Solo detección y propuesta (sin parche automático)",
    "detection_only": "Solo detección",
}

SEVERITY_LABELS: dict[str, str] = {
    "high": "Alta",
    "medium": "Media",
    "low": "Baja",
    "unknown": "Desconocida",
}


def _finding_to_presentable_row(index: int, f: NormalizedFinding) -> dict[str, Any]:
    title = f.title or f.mvp_category.replace("_", " ").title()
    mode = f.remediation_mode
    return {
        "id": index,
        "title": title,
        "severity": f.severity,
        "severity_label": SEVERITY_LABELS.get(f.severity, f.severity),
        "category": f.mvp_category,
        "file": f.file_path,
        "line_start": f.line_start,
        "line_end": f.line_end,
        "tool": f.source_tool,
        "rule_id": f.source_rule_id,
        "rule_name": f.source_rule_name,
        "message": (f.description or f.raw_message or "")[:2000],
        "standards": {
            "cwe_id": f.cwe_id,
            "cwe_url": f.cwe_url,
            "owasp_top10": f.owasp_top10,
            "owasp_asvs": f.owasp_asvs,
        },
        "remediation": {
            "mode": f.remediation_mode,
            "mode_label": REMEDIATION_MODE_LABELS.get(mode, mode),
            "candidate": f.candidate_for_remediation,
        },
        "reference_url": f.reference_url,
    }


def build_presentable_scan(
    findings: list[NormalizedFinding],
    *,
    analysis_target: str,
    execution_mode: str,
    reports: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    JSON estable para vista previa / memoria: sin raw_tool_data, mensajes acotados.
    """
    from collections import Counter

    by_sev = Counter(f.severity for f in findings)
    by_cat = Counter(f.mvp_category for f in findings)
    by_mode = Counter(f.remediation_mode for f in findings)

    rows = [
        _finding_to_presentable_row(i + 1, f)
        for i, f in enumerate(findings)
    ]

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "analysis_target": analysis_target,
            "execution_mode": execution_mode,
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "note": (
                "Vista presentable del escaneo para el TFG. "
                "Los hallazgos no incluyen el volcado crudo de la herramienta."
            ),
        },
        "summary": {
            "total_findings": len(findings),
            "by_severity": dict(sorted(by_sev.items())),
            "by_mvp_category": dict(sorted(by_cat.items())),
            "by_remediation_mode": dict(sorted(by_mode.items())),
        },
        "findings": rows,
    }

    if reports:
        payload["meta"]["reports"] = reports

    return payload


def presentable_from_internal_analysis(internal: dict[str, Any]) -> dict[str, Any]:
    """
    Convierte la respuesta interna de analyze_fixtures_reports / analyze_fixtures_runtime
    (con claves findings como listas de dict) en presentable.
    """
    findings_dicts = internal.get("findings") or []
    findings = [_dict_to_normalized(d) for d in findings_dicts]
    reports = None
    if "bandit_report" in internal:
        reports = {
            "bandit": internal.get("bandit_report"),
            "semgrep": internal.get("semgrep_report"),
        }
    elif internal.get("generated_reports"):
        reports = internal["generated_reports"]

    execution_mode = internal.get("execution_mode", "static")
    if "bandit_report" in internal and execution_mode != "runtime":
        execution_mode = "static_reports"

    return build_presentable_scan(
        findings,
        analysis_target=str(internal.get("analysis_target", "")),
        execution_mode=execution_mode,
        reports=reports,
    )


def _dict_to_normalized(d: dict[str, Any]) -> NormalizedFinding:
    """Reconstruye NormalizedFinding desde asdict (respuesta interna)."""
    return NormalizedFinding(**{k: v for k, v in d.items() if k in NormalizedFinding.__dataclass_fields__})
