"""Agrupación de hallazgos normalizados equivalentes (misma ubicación lógica y categoría)."""

from __future__ import annotations

from pathlib import Path

from app.models.finding import NormalizedFinding

_SEVERITY_RANK: dict[str, int] = {
    "high": 3,
    "medium": 2,
    "low": 1,
    "unknown": 0,
}


def equivalence_key(finding: NormalizedFinding) -> tuple[str, int, str]:
    """Misma clave => mismo problema lógico para la vista agrupada."""
    path = Path(finding.file_path).as_posix()
    return (path, finding.line_start, finding.mvp_category)


def group_findings_by_equivalence(
    findings: list[NormalizedFinding],
) -> list[list[NormalizedFinding]]:
    """
    Agrupa hallazgos por (fichero, línea, mvp_category).
    Orden estable: grupos por ruta/línea/categoría; dentro del grupo por herramienta y regla.
    """
    buckets: dict[tuple[str, int, str], list[NormalizedFinding]] = {}
    for f in findings:
        key = equivalence_key(f)
        buckets.setdefault(key, []).append(f)

    groups: list[list[NormalizedFinding]] = []
    for key in sorted(buckets.keys(), key=lambda k: (k[0], k[1], k[2])):
        grp = sorted(
            buckets[key],
            key=lambda x: (x.source_tool, x.source_rule_id or "", x.source_rule_name or ""),
        )
        groups.append(grp)
    return groups


def max_severity(findings: list[NormalizedFinding]) -> str:
    return max(
        findings,
        key=lambda f: _SEVERITY_RANK.get(f.severity, 0),
    ).severity


def primary_finding(findings: list[NormalizedFinding]) -> NormalizedFinding:
    """Representante del grupo: mayor severidad; empate por herramienta y regla."""
    return sorted(
        findings,
        key=lambda f: (
            -_SEVERITY_RANK.get(f.severity, 0),
            f.source_tool,
            f.source_rule_id or "",
        ),
    )[0]
