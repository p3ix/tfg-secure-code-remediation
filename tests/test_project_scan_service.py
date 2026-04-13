"""Tests de límites y validación del escaneo de proyectos reales (ZIP / Git)."""

import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services.project_scan_service import (
    _validate_https_git_url,
    resolve_allowed_analysis_path,
)


def test_validate_https_git_url_allows_github() -> None:
    _validate_https_git_url(
        "https://github.com/octocat/Hello-World.git",
        frozenset({"github.com"}),
    )


def test_validate_https_git_url_rejects_http() -> None:
    with pytest.raises(ValueError, match="https"):
        _validate_https_git_url(
            "http://github.com/a/b.git",
            frozenset({"github.com"}),
        )


def test_validate_https_git_url_rejects_wrong_host() -> None:
    with pytest.raises(ValueError, match="Host no permitido"):
        _validate_https_git_url(
            "https://evil.example.com/repo.git",
            frozenset({"github.com"}),
        )


def test_zip_path_traversal_rejected() -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("../../../evil.txt", b"x")
    buf.seek(0)
    from app.services.project_scan_service import analyze_zip_bytes

    with pytest.raises(ValueError, match="sospechosa|path"):
        analyze_zip_bytes(buf.getvalue())


def test_ai_status_endpoint() -> None:
    client = TestClient(app)
    r = client.get("/ai/status")
    assert r.status_code == 200
    data = r.json()
    assert "ai_explanations_enabled" in data
    assert "local_analysis_root_configured" in data
    assert "documentation" in data


def test_resolve_allowed_analysis_path_ok(tmp_path) -> None:
    sub = tmp_path / "proj"
    sub.mkdir()
    resolved = resolve_allowed_analysis_path("proj", tmp_path)
    assert resolved == sub.resolve()


def test_resolve_allowed_analysis_path_rejects_dotdot(tmp_path) -> None:
    with pytest.raises(ValueError, match=r"\.\."):
        resolve_allowed_analysis_path("../outside", tmp_path)


def test_resolve_allowed_analysis_path_rejects_absolute(tmp_path) -> None:
    with pytest.raises(ValueError, match="absolutas"):
        resolve_allowed_analysis_path("/etc", tmp_path)


def test_local_path_forbidden_without_env(monkeypatch) -> None:
    monkeypatch.delenv("TFG_LOCAL_ANALYSIS_ROOT", raising=False)
    get_settings.cache_clear()
    try:
        client = TestClient(app)
        r = client.post("/analysis/local-path", json={"relative_path": "x"})
        assert r.status_code == 403
    finally:
        get_settings.cache_clear()
