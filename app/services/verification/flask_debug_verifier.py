from __future__ import annotations

import tempfile
from pathlib import Path

from app.services.findings_loader import load_all_findings
from app.services.findings_mapper import enrich_findings_with_classification
from app.services.remediations.flask_debug_remediator import (
    propose_flask_debug_remediation,
)
from app.services.runtime_analysis_service import (
    build_bandit_command,
    build_semgrep_command,
    run_command,
)


def verify_flask_debug_remediation(source_code: str) -> dict:
    proposal = propose_flask_debug_remediation(source_code)

    if not proposal.applicable or not proposal.changed_content:
        return {
            "verification_kind": "flask_debug_true",
            "applicable": False,
            "verified": False,
            "reason": "No se pudo generar una propuesta de remediación aplicable.",
            "remaining_findings": [],
        }

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        target_dir = tmp_path / "case"
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / "remediated_flask_debug_case.py"
        target_file.write_text(proposal.changed_content, encoding="utf-8")

        bandit_report = tmp_path / "bandit-report.json"
        semgrep_report = tmp_path / "semgrep-report.json"

        bandit_cmd = build_bandit_command(target_dir, bandit_report)
        semgrep_cmd = build_semgrep_command(target_dir, semgrep_report)

        bandit_result = run_command(bandit_cmd)
        semgrep_result = run_command(semgrep_cmd)

        if not bandit_report.exists():
            raise RuntimeError("Bandit no generó report de verificación para flask_debug_true.")

        if not semgrep_report.exists():
            raise RuntimeError("Semgrep no generó report de verificación para flask_debug_true.")

        findings = load_all_findings(
            bandit_report_path=bandit_report,
            semgrep_report_path=semgrep_report,
        )
        findings = enrich_findings_with_classification(findings)

        remaining_debug_findings = [
            f for f in findings if f.mvp_category == "flask_debug_true"
        ]

        return {
            "verification_kind": "flask_debug_true",
            "applicable": True,
            "verified": len(remaining_debug_findings) == 0,
            "reason": (
                "No quedan hallazgos de flask_debug_true tras la remediación."
                if len(remaining_debug_findings) == 0
                else "Siguen existiendo hallazgos de flask_debug_true tras la remediación."
            ),
            "bandit_returncode": bandit_result.returncode,
            "semgrep_returncode": semgrep_result.returncode,
            "remaining_findings": [
                {
                    "source_tool": f.source_tool,
                    "source_rule_id": f.source_rule_id,
                    "file_path": f.file_path,
                    "line_start": f.line_start,
                    "severity": f.severity,
                    "mvp_category": f.mvp_category,
                    "raw_message": f.raw_message,
                }
                for f in remaining_debug_findings
            ],
            "proposed_snippet": proposal.proposed_snippet,
        }
