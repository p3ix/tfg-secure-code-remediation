from __future__ import annotations

import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.services.findings_loader import load_all_findings
from app.services.findings_mapper import enrich_findings_with_classification

FIXTURES_TARGET = Path("fixtures/mvp")
RUNTIME_REPORTS_DIR = Path("reports/runtime")
BANDIT_RUNTIME_REPORT = RUNTIME_REPORTS_DIR / "fixtures-mvp-bandit-runtime.json"
SEMGREP_RUNTIME_REPORT = RUNTIME_REPORTS_DIR / "fixtures-mvp-semgrep-runtime.json"


def build_bandit_command(target_path: str | Path, output_path: str | Path) -> list[str]:
    return [
        "bandit",
        "-c",
        "pyproject.toml",
        "-r",
        str(target_path),
        "-f",
        "json",
        "-o",
        str(output_path),
    ]


def build_semgrep_command(target_path: str | Path, output_path: str | Path) -> list[str]:
    return [
        "semgrep",
        "scan",
        "--config",
        "p/default",
        "--metrics",
        "off",
        "--json-output",
        str(output_path),
        str(target_path),
    ]


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def analyze_fixtures_runtime() -> dict[str, Any]:
    if not FIXTURES_TARGET.exists():
        raise FileNotFoundError(f"Analysis target not found: {FIXTURES_TARGET}")

    RUNTIME_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    bandit_cmd = build_bandit_command(FIXTURES_TARGET, BANDIT_RUNTIME_REPORT)
    semgrep_cmd = build_semgrep_command(FIXTURES_TARGET, SEMGREP_RUNTIME_REPORT)

    bandit_result = run_command(bandit_cmd)
    semgrep_result = run_command(semgrep_cmd)

    if not BANDIT_RUNTIME_REPORT.exists():
        raise RuntimeError(
            "Bandit execution did not produce the expected runtime report."
        )

    if not SEMGREP_RUNTIME_REPORT.exists():
        raise RuntimeError(
            "Semgrep execution did not produce the expected runtime report."
        )

    findings = load_all_findings(
        bandit_report_path=BANDIT_RUNTIME_REPORT,
        semgrep_report_path=SEMGREP_RUNTIME_REPORT,
    )
    enriched_findings = enrich_findings_with_classification(findings)

    return {
        "analysis_target": str(FIXTURES_TARGET),
        "execution_mode": "runtime",
        "generated_reports": {
            "bandit": str(BANDIT_RUNTIME_REPORT),
            "semgrep": str(SEMGREP_RUNTIME_REPORT),
        },
        "tool_runs": {
            "bandit": {
                "returncode": bandit_result.returncode,
                "command": bandit_cmd,
            },
            "semgrep": {
                "returncode": semgrep_result.returncode,
                "command": semgrep_cmd,
            },
        },
        "total_findings": len(enriched_findings),
        "findings": [asdict(finding) for finding in enriched_findings],
    }
