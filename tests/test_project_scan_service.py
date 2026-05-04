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
    assert "analysis_subprocess_timeout_sec" in data
    assert "analysis_exclude_patterns_count" in data
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


def test_analysis_upload_zip_success(monkeypatch) -> None:
    def fake_analyze_zip(content: bytes) -> dict:
        assert content == b"zip-ok"
        return {"analysis_target": "upload.zip", "total_findings": 0, "findings": []}

    monkeypatch.setattr("app.main.analyze_zip_bytes", fake_analyze_zip)

    client = TestClient(app)
    r = client.post(
        "/analysis/upload-zip",
        files={"file": ("project.zip", b"zip-ok", "application/zip")},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["analysis_target"] == "upload.zip"


def test_analysis_upload_zip_bad_request(monkeypatch) -> None:
    def fake_analyze_zip(_: bytes) -> dict:
        raise ValueError("zip invalido")

    monkeypatch.setattr("app.main.analyze_zip_bytes", fake_analyze_zip)

    client = TestClient(app)
    r = client.post(
        "/analysis/upload-zip",
        files={"file": ("bad.zip", b"bad", "application/zip")},
    )

    assert r.status_code == 400
    assert "zip invalido" in r.json()["detail"]


def test_analysis_upload_zip_runtime_error(monkeypatch) -> None:
    def fake_analyze_zip(_: bytes) -> dict:
        raise RuntimeError("bandit no disponible")

    monkeypatch.setattr("app.main.analyze_zip_bytes", fake_analyze_zip)

    client = TestClient(app)
    r = client.post(
        "/analysis/upload-zip",
        files={"file": ("bad.zip", b"bad", "application/zip")},
    )

    assert r.status_code == 502
    assert "bandit no disponible" in r.json()["detail"]


def test_analysis_git_clone_success(monkeypatch) -> None:
    def fake_clone(url: str) -> dict:
        assert url == "https://github.com/octocat/Hello-World.git"
        return {"analysis_target": f"git:{url}", "total_findings": 1, "findings": [{}]}

    monkeypatch.setattr("app.main.clone_and_analyze_repo", fake_clone)

    client = TestClient(app)
    r = client.post(
        "/analysis/git-clone",
        json={"url": "https://github.com/octocat/Hello-World.git"},
    )

    assert r.status_code == 200
    assert r.json()["analysis_target"].startswith("git:https://")


def test_analysis_git_clone_bad_request(monkeypatch) -> None:
    def fake_clone(_: str) -> dict:
        raise ValueError("URL invalida")

    monkeypatch.setattr("app.main.clone_and_analyze_repo", fake_clone)

    client = TestClient(app)
    r = client.post("/analysis/git-clone", json={"url": "https://example.com/r.git"})

    assert r.status_code == 400
    assert "URL invalida" in r.json()["detail"]


def test_analysis_git_clone_forbidden(monkeypatch) -> None:
    def fake_clone(_: str) -> dict:
        raise PermissionError("clonado desactivado")

    monkeypatch.setattr("app.main.clone_and_analyze_repo", fake_clone)

    client = TestClient(app)
    r = client.post("/analysis/git-clone", json={"url": "https://example.com/r.git"})

    assert r.status_code == 403
    assert "clonado desactivado" in r.json()["detail"]


def test_analysis_git_clone_runtime_error(monkeypatch) -> None:
    def fake_clone(_: str) -> dict:
        raise RuntimeError("git clone fallo")

    monkeypatch.setattr("app.main.clone_and_analyze_repo", fake_clone)

    client = TestClient(app)
    r = client.post("/analysis/git-clone", json={"url": "https://example.com/r.git"})

    assert r.status_code == 502
    assert "git clone fallo" in r.json()["detail"]


def test_local_path_with_root_success(monkeypatch, tmp_path) -> None:
    root = tmp_path / "allowed-root"
    root.mkdir()
    project = root / "proj"
    project.mkdir()
    monkeypatch.setenv("TFG_LOCAL_ANALYSIS_ROOT", str(root))
    get_settings.cache_clear()

    def fake_local(relative_path: str, *, allowed_root) -> dict:
        assert relative_path == "proj"
        assert str(allowed_root) == str(root)
        return {"analysis_target": f"local:{relative_path}", "findings": [], "total_findings": 0}

    monkeypatch.setattr("app.main.analyze_local_path_relative", fake_local)
    try:
        client = TestClient(app)
        r = client.post("/analysis/local-path", json={"relative_path": "proj"})
        assert r.status_code == 200
        assert r.json()["analysis_target"] == "local:proj"
    finally:
        get_settings.cache_clear()


def test_local_path_with_root_bad_request(monkeypatch, tmp_path) -> None:
    root = tmp_path / "allowed-root"
    root.mkdir()
    monkeypatch.setenv("TFG_LOCAL_ANALYSIS_ROOT", str(root))
    get_settings.cache_clear()

    def fake_local(_: str, *, allowed_root) -> dict:
        assert str(allowed_root) == str(root)
        raise ValueError("ruta invalida")

    monkeypatch.setattr("app.main.analyze_local_path_relative", fake_local)
    try:
        client = TestClient(app)
        r = client.post("/analysis/local-path", json={"relative_path": "../evil"})
        assert r.status_code == 400
        assert "ruta invalida" in r.json()["detail"]
    finally:
        get_settings.cache_clear()


def test_local_path_with_root_not_found(monkeypatch, tmp_path) -> None:
    root = tmp_path / "allowed-root"
    root.mkdir()
    monkeypatch.setenv("TFG_LOCAL_ANALYSIS_ROOT", str(root))
    get_settings.cache_clear()

    def fake_local(_: str, *, allowed_root) -> dict:
        assert str(allowed_root) == str(root)
        raise FileNotFoundError("proyecto no encontrado")

    monkeypatch.setattr("app.main.analyze_local_path_relative", fake_local)
    try:
        client = TestClient(app)
        r = client.post("/analysis/local-path", json={"relative_path": "missing"})
        assert r.status_code == 404
        assert "proyecto no encontrado" in r.json()["detail"]
    finally:
        get_settings.cache_clear()


def test_local_path_with_root_runtime_error(monkeypatch, tmp_path) -> None:
    root = tmp_path / "allowed-root"
    root.mkdir()
    monkeypatch.setenv("TFG_LOCAL_ANALYSIS_ROOT", str(root))
    get_settings.cache_clear()

    def fake_local(_: str, *, allowed_root) -> dict:
        assert str(allowed_root) == str(root)
        raise RuntimeError("bandit timeout")

    monkeypatch.setattr("app.main.analyze_local_path_relative", fake_local)
    try:
        client = TestClient(app)
        r = client.post("/analysis/local-path", json={"relative_path": "proj"})
        assert r.status_code == 502
        assert "bandit timeout" in r.json()["detail"]
    finally:
        get_settings.cache_clear()
