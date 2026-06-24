"""Harness de evaluación cuantitativa del MVP (recall, falsos positivos, etc.).

El cálculo de métricas (`metrics.py`) es puro y determinista; el `runner` ejecuta
el pipeline real sobre el corpus y requiere Bandit/Semgrep.
"""

from app.services.evaluation.ground_truth import (
    GroundTruth,
    load_ground_truth,
)
from app.services.evaluation.metrics import build_report

__all__ = ["GroundTruth", "load_ground_truth", "build_report"]
