from __future__ import annotations

from pathlib import Path

from app.models.finding import NormalizedFinding
from app.services.parsers.bandit_parser import parse_bandit_report_file
from app.services.parsers.semgrep_parser import parse_semgrep_report_file


def sort_findings(findings: list[NormalizedFinding]) -> list[NormalizedFinding]:
    return sorted(
        findings,
        key=lambda f: (
            f.file_path,
            f.line_start,
            f.source_tool,
            f.source_rule_id,
        ),
    )


def load_bandit_findings(report_path: str | Path) -> list[NormalizedFinding]:
    findings = parse_bandit_report_file(report_path)
    return sort_findings(findings)


def load_semgrep_findings(report_path: str | Path) -> list[NormalizedFinding]:
    findings = parse_semgrep_report_file(report_path)
    return sort_findings(findings)


def load_all_findings(
    *,
    bandit_report_path: str | Path | None = None,
    semgrep_report_path: str | Path | None = None,
) -> list[NormalizedFinding]:
    findings: list[NormalizedFinding] = []

    if bandit_report_path is not None:
        findings.extend(load_bandit_findings(bandit_report_path))

    if semgrep_report_path is not None:
        findings.extend(load_semgrep_findings(semgrep_report_path))

    return sort_findings(findings)
