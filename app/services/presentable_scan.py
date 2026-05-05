from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.models.finding import NormalizedFinding
from app.services.findings_dedup import (
    group_findings_by_equivalence,
    max_severity,
    primary_finding,
)

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


def _group_to_presentable_row(index: int, group: list[NormalizedFinding]) -> dict[str, Any]:
    """Una fila por grupo; severidad = máxima del grupo; `sources` lista todas las herramientas."""
    primary = primary_finding(group)
    sev = max_severity(group)
    mode = primary.remediation_mode
    title = primary.title or primary.mvp_category.replace("_", " ").title()
    sources = [
        {
            "tool": f.source_tool,
            "rule_id": f.source_rule_id,
            "rule_name": f.source_rule_name,
        }
        for f in group
    ]
    row: dict[str, Any] = {
        "id": index,
        "title": title,
        "severity": sev,
        "severity_label": SEVERITY_LABELS.get(sev, sev),
        "category": primary.mvp_category,
        "file": primary.file_path,
        "line_start": primary.line_start,
        "line_end": primary.line_end,
        "tool": primary.source_tool,
        "rule_id": primary.source_rule_id,
        "rule_name": primary.source_rule_name,
        "message": (primary.description or primary.raw_message or "")[:2000],
        "standards": {
            "cwe_id": primary.cwe_id,
            "cwe_url": primary.cwe_url,
            "owasp_top10": primary.owasp_top10,
            "owasp_asvs": primary.owasp_asvs,
        },
        "remediation": {
            "mode": mode,
            "mode_label": REMEDIATION_MODE_LABELS.get(mode, mode),
            "candidate": primary.candidate_for_remediation,
        },
        "reference_url": primary.reference_url,
        "sources": sources,
        "group_size": len(group),
    }
    return row


def build_presentable_scan(
    findings: list[NormalizedFinding],
    *,
    analysis_target: str,
    execution_mode: str,
    reports: dict[str, str] | None = None,
    group_equivalent: bool = False,
) -> dict[str, Any]:
    """
    JSON estable para vista previa / memoria: sin raw_tool_data, mensajes acotados.

    Si group_equivalent=True, agrupa hallazgos con mismo fichero, línea y mvp_category
    y añade `sources` + `group_size` en cada fila.
    """
    from collections import Counter

    def _safe_label(value: Any, default: str) -> str:
        text = str(value).strip() if value is not None else ""
        return text or default

    if group_equivalent:
        groups = group_findings_by_equivalence(findings)
        by_sev = Counter(_safe_label(max_severity(g), "unknown") for g in groups)
        by_cat = Counter(_safe_label(primary_finding(g).mvp_category, "unknown") for g in groups)
        by_mode = Counter(
            _safe_label(primary_finding(g).remediation_mode, "detection_only") for g in groups
        )
        rows = [_group_to_presentable_row(i + 1, g) for i, g in enumerate(groups)]
    else:
        by_sev = Counter(_safe_label(f.severity, "unknown") for f in findings)
        by_cat = Counter(_safe_label(f.mvp_category, "unknown") for f in findings)
        by_mode = Counter(_safe_label(f.remediation_mode, "detection_only") for f in findings)
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
            "total_findings": len(rows),
            "by_severity": dict(sorted(by_sev.items())),
            "by_mvp_category": dict(sorted(by_cat.items())),
            "by_remediation_mode": dict(sorted(by_mode.items())),
        },
        "findings": rows,
    }

    if group_equivalent:
        payload["meta"]["group_equivalent"] = True
        payload["meta"]["group_equivalent_note"] = (
            "Hallazgos agrupados por fichero, línea y categoría MVP; "
            "cada fila puede listar varias fuentes (Bandit/Semgrep) en `sources`."
        )

    if reports:
        payload["meta"]["reports"] = reports

    return payload


def presentable_from_internal_analysis(
    internal: dict[str, Any],
    *,
    group_equivalent: bool = False,
) -> dict[str, Any]:
    """
    Convierte la respuesta interna de analyze_fixtures_reports / analyze_fixtures_runtime
    (con claves findings como listas de dict) en presentable.
    """
    findings_dicts = internal.get("findings") or []
    findings: list[NormalizedFinding] = []
    invalid_findings = 0
    for d in findings_dicts:
        normalized = _dict_to_normalized(d)
        if normalized is None:
            invalid_findings += 1
            continue
        findings.append(normalized)
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

    out = build_presentable_scan(
        findings,
        analysis_target=str(internal.get("analysis_target", "")),
        execution_mode=execution_mode,
        reports=reports,
        group_equivalent=group_equivalent,
    )
    if invalid_findings:
        out_meta = dict(out.get("meta") or {})
        out_meta["invalid_findings_skipped"] = invalid_findings
        out["meta"] = out_meta
    return out


def filter_presentable_scan(scan: dict[str, Any], *, hide_info: bool) -> dict[str, Any]:
    """
    Vista demo: excluye hallazgos puramente informativos o de baja severidad.

    Criterio cuando hide_info=True: se omiten filas con remediation.mode ==
    detection_only o severity == low. Recalcula summary y renumera id.
    """
    if not hide_info:
        return scan

    from collections import Counter

    findings = list(scan.get("findings") or [])
    filtered = [
        f
        for f in findings
        if not (
            f.get("remediation", {}).get("mode") == "detection_only"
            or f.get("severity") == "low"
        )
    ]
    by_sev = Counter((f.get("severity") or "unknown") for f in filtered)
    by_cat = Counter((f.get("category") or "unknown") for f in filtered)
    by_mode = Counter((f.get("remediation", {}).get("mode") or "detection_only") for f in filtered)
    renumbered = [{**row, "id": i + 1} for i, row in enumerate(filtered)]

    meta = dict(scan.get("meta") or {})
    meta["presentable_filter"] = "hide_info"
    meta["presentable_filter_note"] = (
        "Excluye hallazgos con remediación solo detección o severidad baja. "
        "Quitar el parámetro hide_info para ver el listado completo."
    )

    return {
        **scan,
        "meta": meta,
        "summary": {
            "total_findings": len(renumbered),
            "by_severity": dict(sorted(by_sev.items())),
            "by_mvp_category": dict(sorted(by_cat.items())),
            "by_remediation_mode": dict(sorted(by_mode.items())),
        },
        "findings": renumbered,
    }


def _dict_to_normalized(d: dict[str, Any]) -> NormalizedFinding | None:
    """Reconstruye NormalizedFinding desde asdict (respuesta interna)."""
    if not isinstance(d, dict):
        return None
    fields = NormalizedFinding.__dataclass_fields__
    payload = {k: v for k, v in d.items() if k in fields}
    required_defaults: dict[str, Any] = {
        "source_tool": "unknown",
        "source_rule_id": "unknown",
        "file_path": "unknown",
        "line_start": 0,
        "raw_message": "",
        "severity": "unknown",
        "mvp_category": "unknown",
        "candidate_for_remediation": False,
        "remediation_mode": "detection_only",
    }
    for key, default in required_defaults.items():
        payload[key] = payload.get(key, default)
    try:
        payload["line_start"] = int(payload["line_start"])
    except (TypeError, ValueError):
        payload["line_start"] = 0
    try:
        return NormalizedFinding(**payload)
    except TypeError:
        return None
