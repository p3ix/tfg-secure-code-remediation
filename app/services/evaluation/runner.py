"""Ejecuta el pipeline real (Bandit + Semgrep) sobre el corpus y construye el informe.

Requiere Bandit y Semgrep en el PATH. La lógica de métricas vive en `metrics.py`
(pura y testeable sin herramientas).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.evaluation.ground_truth import (
    GroundTruth,
    load_ground_truth,
)
from app.services.evaluation.metrics import build_report
from app.services.project_scan_service import analyze_directory

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_VULN_ROOT = _REPO_ROOT / "fixtures" / "mvp"
DEFAULT_CLEAN_ROOT = _REPO_ROOT / "fixtures" / "eval" / "clean"


def _scan_findings(root: Path, label: str) -> list[dict[str, Any]]:
    internal = analyze_directory(root, analysis_target_label=label)
    return list(internal.get("findings") or [])


def run_evaluation(
    *,
    ground_truth: GroundTruth | None = None,
    vuln_root: Path | None = None,
    clean_root: Path | None = None,
) -> dict[str, Any]:
    """Escanea ambos corpus y devuelve el informe de métricas (dict JSON-serializable)."""
    gt = ground_truth if ground_truth is not None else load_ground_truth()
    vuln_findings = _scan_findings(vuln_root or DEFAULT_VULN_ROOT, "eval:vulnerable")
    clean_findings = _scan_findings(clean_root or DEFAULT_CLEAN_ROOT, "eval:clean")
    return build_report(gt, vuln_findings, clean_findings)
