"""Tests deterministas del cálculo de métricas de evaluación (sin Bandit/Semgrep)."""

from app.services.evaluation.ground_truth import CleanCase, GroundTruth, VulnCase
from app.services.evaluation.metrics import (
    build_report,
    classification_coverage,
    detection_metrics,
    false_positive_metrics,
    remediation_metrics,
    tool_coverage,
)


def _vuln_cases() -> tuple[VulnCase, ...]:
    return (
        VulnCase("x/a.py", "command_injection", 78, autofix_expected=True),
        VulnCase("y/b.py", "sql_injection", 89, autofix_expected=False),
        VulnCase("z/c.py", "missing_timeout", 400, autofix_expected=True),  # no detectado
    )


def _clean_cases() -> tuple[CleanCase, ...]:
    return (
        CleanCase("clean/safe_a.py", "command_injection"),
        CleanCase("clean/safe_b.py", "sql_injection"),
    )


def _vuln_findings() -> list[dict]:
    return [
        {"file_path": "x/a.py", "mvp_category": "command_injection", "source_tool": "bandit",
         "remediation_mode": "autofix_candidate", "cwe_id": 78, "owasp_top10": "A05"},
        {"file_path": "x/a.py", "mvp_category": "command_injection", "source_tool": "semgrep",
         "remediation_mode": "autofix_candidate", "cwe_id": 78, "owasp_top10": "A05"},
        {"file_path": "y/b.py", "mvp_category": "sql_injection", "source_tool": "bandit",
         "remediation_mode": "proposal_only", "cwe_id": 89, "owasp_top10": "A05"},
        {"file_path": "x/a.py", "mvp_category": "subprocess_import_info", "source_tool": "bandit",
         "remediation_mode": "detection_only", "cwe_id": None, "owasp_top10": None},
    ]


def _clean_findings() -> list[dict]:
    return [
        {"file_path": "clean/safe_a.py", "mvp_category": "command_injection", "source_tool": "bandit"},
        {"file_path": "clean/safe_b.py", "mvp_category": "subprocess_import_info", "source_tool": "bandit"},
    ]


def test_detection_recall_overall_and_by_category() -> None:
    out = detection_metrics(_vuln_cases(), _vuln_findings())
    assert out["total_cases"] == 3
    assert out["detected"] == 2
    assert out["recall"] == 0.6667
    assert out["by_category"]["command_injection"]["recall"] == 1.0
    assert out["by_category"]["missing_timeout"]["recall"] == 0.0


def test_tool_coverage_counts() -> None:
    out = tool_coverage(_vuln_cases(), _vuln_findings())
    assert out == {"both": 1, "bandit_only": 1, "semgrep_only": 0, "none": 1}


def test_classification_coverage() -> None:
    out = classification_coverage(_vuln_findings())
    assert out["total_findings"] == 4
    assert out["with_cwe"] == 3
    assert out["cwe_coverage"] == 0.75
    assert out["owasp_coverage"] == 0.75


def test_false_positive_specificity() -> None:
    out = false_positive_metrics(_clean_cases(), _clean_findings())
    assert out["total_cases"] == 2
    assert out["false_positives"] == 1
    assert out["specificity"] == 0.5
    fp_paths = {c["path"] for c in out["per_case"] if c["false_positive"]}
    assert fp_paths == {"clean/safe_a.py"}


def test_remediation_coverage_only_counts_autofix_expected() -> None:
    out = remediation_metrics(_vuln_cases(), _vuln_findings())
    # Esperan autofix: a.py y c.py (b.py es proposal_only por diseño, no cuenta).
    assert out["autofix_expected_cases"] == 2
    assert out["autofix_candidate"] == 1
    assert out["coverage"] == 0.5


def test_build_report_summary() -> None:
    gt = GroundTruth(vulnerable=_vuln_cases(), clean=_clean_cases())
    report = build_report(gt, _vuln_findings(), _clean_findings())
    s = report["summary"]
    assert s["vulnerable_cases"] == 3
    assert s["clean_cases"] == 2
    assert s["recall"] == 0.6667
    assert s["specificity"] == 0.5
    assert s["false_positives"] == 1
    assert s["cwe_coverage"] == 0.75
    assert s["remediation_coverage"] == 0.5
    assert set(report) == {
        "summary", "detection", "tool_coverage",
        "classification", "false_positives", "remediation",
    }
