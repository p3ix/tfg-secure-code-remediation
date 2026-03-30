from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.services.findings_loader import load_all_findings
from app.services.findings_mapper import enrich_findings_with_classification
from app.services.pipeline_orchestrator import build_pipeline_view


BANDIT_REPORT = Path("reports/bandit/fixtures-mvp-bandit.json")
SEMGREP_REPORT = Path("reports/semgrep/fixtures-mvp-semgrep.json")


def analyze_fixtures_reports() -> dict[str, Any]:
    if not BANDIT_REPORT.exists():
        raise FileNotFoundError(f"Bandit report not found: {BANDIT_REPORT}")

    if not SEMGREP_REPORT.exists():
        raise FileNotFoundError(f"Semgrep report not found: {SEMGREP_REPORT}")

    findings = load_all_findings(
        bandit_report_path=BANDIT_REPORT,
        semgrep_report_path=SEMGREP_REPORT,
    )
    enriched_findings = enrich_findings_with_classification(findings)

    return {
        "analysis_target": "fixtures/mvp",
        "bandit_report": str(BANDIT_REPORT),
        "semgrep_report": str(SEMGREP_REPORT),
        "total_findings": len(enriched_findings),
        "findings": [asdict(finding) for finding in enriched_findings],
        "pipeline": build_pipeline_view(enriched_findings),
    }
