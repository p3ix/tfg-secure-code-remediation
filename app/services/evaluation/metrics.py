"""Cálculo de métricas de evaluación (puro y determinista, sin herramientas externas).

Entrada: el ground truth y listas de hallazgos (dicts `asdict(NormalizedFinding)`),
ya sea del corpus vulnerable o del corpus limpio.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.evaluation.ground_truth import (
    CleanCase,
    GroundTruth,
    VulnCase,
)

Finding = dict[str, Any]


def _basename(path: str) -> str:
    return Path(path).name


def _findings_for_file(findings: list[Finding], filename: str) -> list[Finding]:
    return [f for f in findings if _basename(str(f.get("file_path", ""))) == filename]


def _round(value: float) -> float:
    return round(value, 4)


def detection_metrics(
    vuln_cases: tuple[VulnCase, ...], findings: list[Finding]
) -> dict[str, Any]:
    """Recall global y por categoría: ¿se detectó la categoría esperada en cada fichero?"""
    per_case: list[dict[str, Any]] = []
    by_category: dict[str, dict[str, int]] = {}

    for case in vuln_cases:
        matches = [
            f
            for f in _findings_for_file(findings, case.filename)
            if f.get("mvp_category") == case.category
        ]
        tools = sorted({str(f.get("source_tool")) for f in matches if f.get("source_tool")})
        detected = len(matches) > 0
        per_case.append(
            {
                "path": case.path,
                "category": case.category,
                "cwe_id": case.cwe_id,
                "detected": detected,
                "tools": tools,
            }
        )
        bucket = by_category.setdefault(case.category, {"total": 0, "detected": 0})
        bucket["total"] += 1
        if detected:
            bucket["detected"] += 1

    total = len(vuln_cases)
    detected = sum(1 for c in per_case if c["detected"])
    for bucket in by_category.values():
        bucket["recall"] = _round(bucket["detected"] / bucket["total"]) if bucket["total"] else 0.0

    return {
        "total_cases": total,
        "detected": detected,
        "recall": _round(detected / total) if total else 0.0,
        "by_category": dict(sorted(by_category.items())),
        "per_case": per_case,
    }


def tool_coverage(
    vuln_cases: tuple[VulnCase, ...], findings: list[Finding]
) -> dict[str, Any]:
    """Reparto de detecciones por herramienta sobre los casos vulnerables."""
    counts = {"bandit_only": 0, "semgrep_only": 0, "both": 0, "none": 0}
    for case in vuln_cases:
        tools = {
            str(f.get("source_tool"))
            for f in _findings_for_file(findings, case.filename)
            if f.get("mvp_category") == case.category and f.get("source_tool")
        }
        has_b = "bandit" in tools
        has_s = "semgrep" in tools
        if has_b and has_s:
            counts["both"] += 1
        elif has_b:
            counts["bandit_only"] += 1
        elif has_s:
            counts["semgrep_only"] += 1
        else:
            counts["none"] += 1
    return counts


def classification_coverage(findings: list[Finding]) -> dict[str, Any]:
    """Fracción de hallazgos con CWE y con OWASP asignados (clasificación)."""
    total = len(findings)
    with_cwe = sum(1 for f in findings if f.get("cwe_id") is not None)
    with_owasp = sum(1 for f in findings if f.get("owasp_top10"))
    return {
        "total_findings": total,
        "with_cwe": with_cwe,
        "with_owasp": with_owasp,
        "cwe_coverage": _round(with_cwe / total) if total else 0.0,
        "owasp_coverage": _round(with_owasp / total) if total else 0.0,
    }


def false_positive_metrics(
    clean_cases: tuple[CleanCase, ...], findings: list[Finding]
) -> dict[str, Any]:
    """Falsos positivos sobre el corpus limpio: la categoría prohibida no debe aparecer."""
    per_case: list[dict[str, Any]] = []
    false_positives = 0
    for case in clean_cases:
        hits = [
            f
            for f in _findings_for_file(findings, case.filename)
            if f.get("mvp_category") == case.forbidden_category
        ]
        is_fp = len(hits) > 0
        if is_fp:
            false_positives += 1
        per_case.append(
            {
                "path": case.path,
                "forbidden_category": case.forbidden_category,
                "false_positive": is_fp,
            }
        )
    total = len(clean_cases)
    clean_ok = total - false_positives
    return {
        "total_cases": total,
        "false_positives": false_positives,
        "specificity": _round(clean_ok / total) if total else 0.0,
        "per_case": per_case,
    }


def remediation_metrics(
    vuln_cases: tuple[VulnCase, ...], findings: list[Finding]
) -> dict[str, Any]:
    """Cobertura de remediación: de los casos con autofix esperado, ¿cuántos quedan
    clasificados como `autofix_candidate`?"""
    expected = [c for c in vuln_cases if c.autofix_expected]
    covered = 0
    per_case: list[dict[str, Any]] = []
    for case in expected:
        modes = {
            str(f.get("remediation_mode"))
            for f in _findings_for_file(findings, case.filename)
            if f.get("mvp_category") == case.category and f.get("remediation_mode")
        }
        is_autofix = "autofix_candidate" in modes
        if is_autofix:
            covered += 1
        per_case.append(
            {
                "path": case.path,
                "category": case.category,
                "autofix_candidate": is_autofix,
                "modes": sorted(modes),
            }
        )
    total = len(expected)
    return {
        "autofix_expected_cases": total,
        "autofix_candidate": covered,
        "coverage": _round(covered / total) if total else 0.0,
        "per_case": per_case,
    }


def build_report(
    ground_truth: GroundTruth,
    vuln_findings: list[Finding],
    clean_findings: list[Finding],
) -> dict[str, Any]:
    """Agrega todas las métricas en un informe serializable a JSON."""
    detection = detection_metrics(ground_truth.vulnerable, vuln_findings)
    tools = tool_coverage(ground_truth.vulnerable, vuln_findings)
    classification = classification_coverage(vuln_findings)
    false_positives = false_positive_metrics(ground_truth.clean, clean_findings)
    remediation = remediation_metrics(ground_truth.vulnerable, vuln_findings)

    return {
        "summary": {
            "vulnerable_cases": detection["total_cases"],
            "clean_cases": false_positives["total_cases"],
            "recall": detection["recall"],
            "specificity": false_positives["specificity"],
            "false_positives": false_positives["false_positives"],
            "cwe_coverage": classification["cwe_coverage"],
            "remediation_coverage": remediation["coverage"],
        },
        "detection": detection,
        "tool_coverage": tools,
        "classification": classification,
        "false_positives": false_positives,
        "remediation": remediation,
    }
