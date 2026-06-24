from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GROUND_TRUTH_PATH = _REPO_ROOT / "fixtures" / "eval" / "ground_truth.json"


@dataclass(frozen=True)
class VulnCase:
    """Caso vulnerable etiquetado: una vulnerabilidad principal por fichero."""

    path: str
    category: str
    cwe_id: int | None
    autofix_expected: bool

    @property
    def filename(self) -> str:
        return Path(self.path).name


@dataclass(frozen=True)
class CleanCase:
    """Variante segura: no debe disparar `forbidden_category` (control de FP)."""

    path: str
    forbidden_category: str

    @property
    def filename(self) -> str:
        return Path(self.path).name


@dataclass(frozen=True)
class GroundTruth:
    vulnerable: tuple[VulnCase, ...]
    clean: tuple[CleanCase, ...]


def load_ground_truth(path: Path | str | None = None) -> GroundTruth:
    """Carga el ground truth desde JSON (por defecto `fixtures/eval/ground_truth.json`)."""
    source = Path(path) if path is not None else DEFAULT_GROUND_TRUTH_PATH
    data = json.loads(source.read_text(encoding="utf-8"))
    vulnerable = tuple(
        VulnCase(
            path=str(item["path"]),
            category=str(item["category"]),
            cwe_id=item.get("cwe_id"),
            autofix_expected=bool(item.get("autofix_expected", False)),
        )
        for item in data.get("vulnerable", [])
    )
    clean = tuple(
        CleanCase(
            path=str(item["path"]),
            forbidden_category=str(item["forbidden_category"]),
        )
        for item in data.get("clean", [])
    )
    return GroundTruth(vulnerable=vulnerable, clean=clean)
