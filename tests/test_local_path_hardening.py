from pathlib import Path

import pytest

from app.services.project_scan_service import (
    analyze_local_path_relative,
    resolve_allowed_analysis_path,
)


def test_resolve_allowed_analysis_path_rejects_invalid_root(tmp_path) -> None:
    missing_root = tmp_path / "missing-root"
    with pytest.raises(ValueError, match="raíz permitido no existe"):
        resolve_allowed_analysis_path("proj", missing_root)


def test_resolve_allowed_analysis_path_rejects_backslash(tmp_path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(ValueError, match="separadores"):
        resolve_allowed_analysis_path(r"proj\\sub", root)


def test_analyze_local_path_relative_normalizes_analysis_target(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "root"
    project = root / "proj" / "nested"
    project.mkdir(parents=True)

    def fake_analyze_directory(target: Path, *, analysis_target_label: str) -> dict:
        assert target == project.resolve()
        return {"analysis_target": analysis_target_label, "findings": [], "total_findings": 0}

    monkeypatch.setattr(
        "app.services.project_scan_service.analyze_directory",
        fake_analyze_directory,
    )
    out = analyze_local_path_relative("proj/nested", allowed_root=root)
    assert out["analysis_target"] == "local:proj/nested"
