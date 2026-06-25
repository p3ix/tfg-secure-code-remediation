from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.models.finding import NormalizedFinding
from app.services.ai.cache import ExplanationCache, explain_cached
from app.services.ai.provider import AIProvider
from app.services.findings_dedup import (
    group_findings_by_equivalence,
    max_severity,
    primary_finding,
)

SCHEMA_VERSION = "1.2"


def _ai_explanation_for(
    finding: NormalizedFinding,
    provider: AIProvider | None,
    cache: ExplanationCache,
) -> dict[str, object] | None:
    """Explicación IA del hallazgo (degradable: None si no hay proveedor o falla)."""
    if provider is None:
        return None
    try:
        explanation = explain_cached(provider, finding, cache)
    except Exception:  # noqa: BLE001 - la IA nunca debe tumbar el escaneo
        return None
    return explanation.to_dict() if explanation is not None else None

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

_TOOL_ORDER = ("bandit", "semgrep")


def _tool_run_status(returncode: int | None) -> tuple[str, str]:
    if returncode is None:
        return "unknown", "Desconocido"
    if returncode == 0:
        return "ok", "Completado (sin issues reportados)"
    if returncode == 1:
        return "completed_with_findings", "Completado (con hallazgos)"
    return "error", f"Finalizó con código {returncode}"


def build_tool_diagnostics(
    tool_runs: dict[str, Any],
    findings: list[NormalizedFinding],
) -> list[dict[str, Any]]:
    """
    Resume ejecución de Bandit/Semgrep para la vista presentable (dashboard/API).
    """
    from collections import Counter

    by_tool = Counter(f.source_tool for f in findings)
    diagnostics: list[dict[str, Any]] = []
    for tool in _TOOL_ORDER:
        run = tool_runs.get(tool)
        if not isinstance(run, dict):
            continue
        returncode = run.get("returncode")
        rc_int = returncode if isinstance(returncode, int) else None
        status_key, status_label = _tool_run_status(rc_int)
        findings_count = by_tool.get(tool, 0)
        entry: dict[str, Any] = {
            "tool": tool,
            "returncode": returncode,
            "status": status_key,
            "status_label": status_label,
            "findings_count": findings_count,
        }
        if findings_count == 0 and status_key in {"ok", "completed_with_findings"}:
            entry["note"] = "La herramienta terminó pero no aportó hallazgos en esta ejecución."
        stderr_preview = run.get("stderr_preview")
        if isinstance(stderr_preview, str) and stderr_preview.strip():
            entry["stderr_preview"] = stderr_preview.strip()
        diagnostics.append(entry)
    return diagnostics


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
    analysis_id: str | None = None,
    reports: dict[str, str] | None = None,
    group_equivalent: bool = False,
    ai_provider: AIProvider | None = None,
    ai_cache: ExplanationCache | None = None,
) -> dict[str, Any]:
    """
    JSON estable para vista previa / memoria: sin raw_tool_data, mensajes acotados.

    Si group_equivalent=True, agrupa hallazgos con mismo fichero, línea y mvp_category
    y añade `sources` + `group_size` en cada fila.

    Si ai_provider no es None, cada fila incluye `ai_explanation` (ADR-003); en otro
    caso el campo es None. La generación es degradable y nunca tumba el escaneo.
    """
    from collections import Counter

    def _safe_label(value: Any, default: str) -> str:
        text = str(value).strip() if value is not None else ""
        return text or default

    if ai_cache is None:
        ai_cache = ExplanationCache()

    if group_equivalent:
        groups = group_findings_by_equivalence(findings)
        by_sev = Counter(_safe_label(max_severity(g), "unknown") for g in groups)
        by_cat = Counter(_safe_label(primary_finding(g).mvp_category, "unknown") for g in groups)
        by_mode = Counter(
            _safe_label(primary_finding(g).remediation_mode, "detection_only") for g in groups
        )
        rows = []
        for i, g in enumerate(groups):
            row = _group_to_presentable_row(i + 1, g)
            row["ai_explanation"] = _ai_explanation_for(
                primary_finding(g), ai_provider, ai_cache
            )
            rows.append(row)
    else:
        by_sev = Counter(_safe_label(f.severity, "unknown") for f in findings)
        by_cat = Counter(_safe_label(f.mvp_category, "unknown") for f in findings)
        by_mode = Counter(_safe_label(f.remediation_mode, "detection_only") for f in findings)
        rows = []
        for i, f in enumerate(findings):
            row = _finding_to_presentable_row(i + 1, f)
            row["ai_explanation"] = _ai_explanation_for(f, ai_provider, ai_cache)
            rows.append(row)

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "analysis_target": analysis_target,
            "execution_mode": execution_mode,
            "analysis_id": analysis_id,
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
    ai_provider: AIProvider | None = None,
    ai_cache: ExplanationCache | None = None,
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
        analysis_id=internal.get("analysis_id"),
        reports=reports,
        group_equivalent=group_equivalent,
        ai_provider=ai_provider,
        ai_cache=ai_cache,
    )
    if invalid_findings:
        out_meta = dict(out.get("meta") or {})
        out_meta["invalid_findings_skipped"] = invalid_findings
        out["meta"] = out_meta
    tool_runs = internal.get("tool_runs")
    if isinstance(tool_runs, dict) and tool_runs:
        out_meta = dict(out.get("meta") or {})
        out_meta["tool_diagnostics"] = build_tool_diagnostics(tool_runs, findings)
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
