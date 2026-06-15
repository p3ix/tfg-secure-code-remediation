"""
Lógica común de verificación detect→repair→verify para las categorías MVP.

Todas las verificaciones siguen el mismo flujo: proponer remediación, escribir
el código remediado a un directorio temporal, reejecutar Bandit + Semgrep y
comprobar si quedan hallazgos de la categoría. Cada categoría solo aporta su
`kind` y su función de propuesta; ver wrappers en este mismo paquete.
"""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.models.remediation import RemediationProposal
from app.services.findings_loader import load_all_findings
from app.services.findings_mapper import enrich_findings_with_classification
from app.services.runtime_analysis_service import (
    build_bandit_command,
    build_semgrep_command,
    run_analysis_command,
)


def _finding_summary(finding: Any) -> dict[str, Any]:
    return {
        "source_tool": finding.source_tool,
        "source_rule_id": finding.source_rule_id,
        "file_path": finding.file_path,
        "line_start": finding.line_start,
        "severity": finding.severity,
        "mvp_category": finding.mvp_category,
        "raw_message": finding.raw_message,
    }


def verify_remediation(
    source_code: str,
    *,
    kind: str,
    propose_fn: Callable[[str], RemediationProposal],
    include_other_categories: bool = False,
) -> dict[str, Any]:
    """
    Verifica la remediación de una categoría MVP reejecutando el SAST.

    `kind` es la categoría MVP (p. ej. ``unsafe_yaml_load``); `propose_fn` es el
    remediador asociado. Si `include_other_categories`, el resultado incluye un
    resumen de hallazgos de otras categorías que quedan tras el parche.
    """
    proposal = propose_fn(source_code)

    if not proposal.applicable or not proposal.changed_content:
        result: dict[str, Any] = {
            "verification_kind": kind,
            "applicable": False,
            "verified": False,
            "reason": "No se pudo generar una propuesta de remediación aplicable.",
            "remaining_findings": [],
        }
        if include_other_categories:
            result["other_remaining_categories"] = []
        return result

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        target_dir = tmp_path / "case"
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / f"remediated_{kind}_case.py"
        target_file.write_text(proposal.changed_content, encoding="utf-8")

        bandit_report = tmp_path / "bandit-report.json"
        semgrep_report = tmp_path / "semgrep-report.json"

        bandit_cmd = build_bandit_command(target_dir, bandit_report)
        semgrep_cmd = build_semgrep_command(target_dir, semgrep_report)

        bandit_result = run_analysis_command(bandit_cmd)
        semgrep_result = run_analysis_command(semgrep_cmd)

        if not bandit_report.exists():
            raise RuntimeError(f"Bandit no generó report de verificación para {kind}.")

        semgrep_report_missing = False
        if not semgrep_report.exists():
            # En algunos entornos Semgrep puede fallar antes de persistir JSON
            # (por red/reglas remotas). Mantengo el flujo verificable con fallback vacío.
            semgrep_report.write_text('{"results": []}', encoding="utf-8")
            semgrep_report_missing = True

        findings = load_all_findings(
            bandit_report_path=bandit_report,
            semgrep_report_path=semgrep_report,
        )
        findings = enrich_findings_with_classification(findings)

        remaining = [f for f in findings if f.mvp_category == kind]

        result = {
            "verification_kind": kind,
            "applicable": True,
            "verified": len(remaining) == 0,
            "reason": (
                f"No quedan hallazgos de {kind} tras la remediación."
                if len(remaining) == 0
                else f"Siguen existiendo hallazgos de {kind} tras la remediación."
            ),
            "bandit_returncode": bandit_result.returncode,
            "semgrep_returncode": semgrep_result.returncode,
            "semgrep_report_missing": semgrep_report_missing,
            "remaining_findings": [_finding_summary(f) for f in remaining],
            "proposed_snippet": proposal.proposed_snippet,
        }

        if include_other_categories:
            other = [f for f in findings if f.mvp_category != kind]
            result["other_remaining_findings_count"] = len(other)
            result["other_remaining_categories"] = sorted(
                {f.mvp_category for f in other}
            )

        return result
