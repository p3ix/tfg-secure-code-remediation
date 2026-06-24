"""Valida el ground truth real y el render del informe (sin Bandit/Semgrep)."""

from pathlib import Path

from app.services.evaluation.ground_truth import load_ground_truth
from app.services.evaluation.metrics import build_report
from app.services.evaluation.report import render_markdown

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_ground_truth_loads_and_paths_exist() -> None:
    gt = load_ground_truth()
    assert len(gt.vulnerable) >= 8
    assert len(gt.clean) >= 6
    # Todas las rutas etiquetadas existen en el repo.
    for case in gt.vulnerable:
        assert (_REPO_ROOT / case.path).is_file(), case.path
    for case in gt.clean:
        assert (_REPO_ROOT / case.path).is_file(), case.path
    # Cada caso limpio referencia una categoría también presente en los vulnerables.
    vuln_categories = {c.category for c in gt.vulnerable}
    for case in gt.clean:
        assert case.forbidden_category in vuln_categories


def test_render_markdown_with_empty_findings() -> None:
    gt = load_ground_truth()
    # Sin hallazgos: recall 0, especificidad 1 (ningún FP). El render no debe romper.
    report = build_report(gt, [], [])
    assert report["summary"]["recall"] == 0.0
    assert report["summary"]["specificity"] == 1.0
    md = render_markdown(report)
    assert "# Evaluación cuantitativa del MVP" in md
    assert "Recall" in md
    assert "Especificidad" in md
