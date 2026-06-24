"""Render del informe de evaluación a Markdown (para la memoria)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_markdown(report: dict[str, Any]) -> str:
    s = report["summary"]
    det = report["detection"]
    tools = report["tool_coverage"]
    cls = report["classification"]
    fp = report["false_positives"]
    rem = report["remediation"]

    lines: list[str] = []
    lines.append("# Evaluación cuantitativa del MVP")
    lines.append("")
    lines.append(
        "Generado automáticamente por `python -m app.services.evaluation` sobre el corpus "
        "etiquetado en `fixtures/eval/ground_truth.json`. Las métricas se calculan con "
        "funciones deterministas cubiertas por `tests/test_evaluation_metrics.py`."
    )
    lines.append("")
    lines.append(f"_Fecha: {datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')}_")
    lines.append("")

    lines.append("## Resumen")
    lines.append("")
    lines.append("| Métrica | Valor |")
    lines.append("|---------|-------|")
    lines.append(f"| Casos vulnerables | {s['vulnerable_cases']} |")
    lines.append(f"| Casos limpios (control) | {s['clean_cases']} |")
    lines.append(f"| **Recall** (detección) | {_pct(s['recall'])} |")
    lines.append(f"| **Especificidad** (1 − FP) | {_pct(s['specificity'])} |")
    lines.append(f"| Falsos positivos | {s['false_positives']} |")
    lines.append(f"| Cobertura CWE | {_pct(s['cwe_coverage'])} |")
    lines.append(f"| Cobertura de remediación (autofix) | {_pct(s['remediation_coverage'])} |")
    lines.append("")

    lines.append("## Detección por categoría (recall)")
    lines.append("")
    lines.append("| Categoría | Detectados / Total | Recall |")
    lines.append("|-----------|--------------------|--------|")
    for cat, b in det["by_category"].items():
        lines.append(f"| {cat} | {b['detected']} / {b['total']} | {_pct(b['recall'])} |")
    lines.append("")
    lines.append(f"Global: **{det['detected']} / {det['total_cases']}** ({_pct(det['recall'])}).")
    lines.append("")

    lines.append("### Detalle por caso")
    lines.append("")
    lines.append("| Fichero | Categoría | Detectado | Herramientas |")
    lines.append("|---------|-----------|-----------|--------------|")
    for c in det["per_case"]:
        mark = "✅" if c["detected"] else "❌"
        tools_str = ", ".join(c["tools"]) if c["tools"] else "—"
        lines.append(f"| `{c['path']}` | {c['category']} | {mark} | {tools_str} |")
    lines.append("")

    lines.append("## Cobertura por herramienta")
    lines.append("")
    lines.append(
        f"- Ambas (Bandit + Semgrep): **{tools['both']}**\n"
        f"- Solo Bandit: **{tools['bandit_only']}**\n"
        f"- Solo Semgrep: **{tools['semgrep_only']}**\n"
        f"- Ninguna: **{tools['none']}**"
    )
    lines.append("")

    lines.append("## Clasificación (estándares)")
    lines.append("")
    lines.append(
        f"- Hallazgos con CWE: **{cls['with_cwe']} / {cls['total_findings']}** "
        f"({_pct(cls['cwe_coverage'])}).\n"
        f"- Hallazgos con OWASP: **{cls['with_owasp']} / {cls['total_findings']}** "
        f"({_pct(cls['owasp_coverage'])})."
    )
    lines.append("")

    lines.append("## Falsos positivos (corpus limpio)")
    lines.append("")
    lines.append(
        f"Especificidad: **{_pct(fp['specificity'])}** "
        f"({fp['false_positives']} falsos positivos sobre {fp['total_cases']} casos limpios)."
    )
    lines.append("")
    lines.append("| Fichero | Categoría prohibida | Falso positivo |")
    lines.append("|---------|---------------------|----------------|")
    for c in fp["per_case"]:
        mark = "⚠️ sí" if c["false_positive"] else "no"
        lines.append(f"| `{c['path']}` | {c['forbidden_category']} | {mark} |")
    lines.append("")

    lines.append("## Remediación (autofix esperado)")
    lines.append("")
    lines.append(
        f"Cobertura: **{rem['autofix_candidate']} / {rem['autofix_expected_cases']}** "
        f"({_pct(rem['coverage'])}) clasificados como `autofix_candidate`."
    )
    lines.append("")
    lines.append("| Fichero | Categoría | Autofix candidate | Modos |")
    lines.append("|---------|-----------|-------------------|-------|")
    for c in rem["per_case"]:
        mark = "✅" if c["autofix_candidate"] else "❌"
        modes = ", ".join(c["modes"]) if c["modes"] else "—"
        lines.append(f"| `{c['path']}` | {c['category']} | {mark} | {modes} |")
    lines.append("")

    return "\n".join(lines)
