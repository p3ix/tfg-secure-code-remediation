"""Tests de límites y validación del escaneo de proyectos reales (ZIP / Git)."""

import io
import subprocess
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services.project_scan_service import (
    PayloadTooLargeError,
    _validate_https_git_url,
    analyze_directory,
    analyze_local_path_relative,
    clone_and_analyze_repo,
    extract_zip_safely,
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
            "https://evil.example.com/acme/repo.git",
            frozenset({"github.com"}),
        )


def test_validate_https_git_url_rejects_credentials() -> None:
    with pytest.raises(ValueError, match="credenciales"):
        _validate_https_git_url(
            "https://user:pass@github.com/octocat/repo.git",
            frozenset({"github.com"}),
        )


def test_validate_https_git_url_rejects_query() -> None:
    with pytest.raises(ValueError, match="query params"):
        _validate_https_git_url(
            "https://github.com/octocat/repo.git?ref=main",
            frozenset({"github.com"}),
        )


def test_validate_https_git_url_rejects_short_path() -> None:
    with pytest.raises(ValueError, match="owner/repo"):
        _validate_https_git_url(
            "https://github.com/repo-only",
            frozenset({"github.com"}),
        )


def test_validate_https_git_url_rejects_excessive_length(monkeypatch) -> None:
    monkeypatch.setenv("TFG_GIT_URL_MAX_LENGTH", "40")
    get_settings.cache_clear()
    try:
        long_url = "https://github.com/" + ("x" * 50) + "/a/b.git"
        assert len(long_url) > 40
        with pytest.raises(ValueError, match="demasiado larga"):
            _validate_https_git_url(long_url, frozenset({"github.com"}))
    finally:
        get_settings.cache_clear()


def test_zip_path_traversal_rejected() -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("../../../evil.txt", b"x")
    buf.seek(0)
    from app.services.project_scan_service import analyze_zip_bytes

    with pytest.raises(ValueError, match="sospechosa|path"):
        analyze_zip_bytes(buf.getvalue())


def test_extract_zip_safely_rejects_invalid_zip(tmp_path) -> None:
    with pytest.raises(ValueError, match="ZIP válido"):
        extract_zip_safely(b"not-a-zip", tmp_path, max_uncompressed_bytes=1024)


def test_extract_zip_safely_rejects_too_many_entries(tmp_path) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("a.txt", b"x")
        zf.writestr("b.txt", b"y")
    with pytest.raises(ValueError, match="demasiadas entradas"):
        extract_zip_safely(
            buf.getvalue(),
            tmp_path,
            max_uncompressed_bytes=1024,
            max_entries=1,
        )


def test_analyze_zip_bytes_respects_tfg_zip_max_entries(monkeypatch) -> None:
    monkeypatch.setenv("TFG_ZIP_MAX_ENTRIES", "1")
    get_settings.cache_clear()
    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("a.txt", b"x")
            zf.writestr("b.txt", b"y")
        from app.services.project_scan_service import analyze_zip_bytes

        with pytest.raises(ValueError, match="demasiadas entradas"):
            analyze_zip_bytes(buf.getvalue())
    finally:
        get_settings.cache_clear()


def test_analyze_directory_rejects_non_directory(tmp_path) -> None:
    file_path = tmp_path / "not_dir.txt"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="No es un directorio"):
        analyze_directory(file_path, analysis_target_label="local:test")


def test_analyze_directory_rejects_too_many_files(monkeypatch, tmp_path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    for i in range(3):
        (target / f"f{i}.py").write_text("print('x')", encoding="utf-8")

    monkeypatch.setenv("TFG_ANALYSIS_MAX_FILES", "2")
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="límite de ficheros"):
            analyze_directory(target, analysis_target_label="local:test")
    finally:
        get_settings.cache_clear()


def test_analyze_directory_rejects_too_many_bytes(monkeypatch, tmp_path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    (target / "big.py").write_text("x" * 50, encoding="utf-8")

    monkeypatch.setenv("TFG_ANALYSIS_MAX_FILES", "10")
    monkeypatch.setenv("TFG_ANALYSIS_MAX_BYTES", "40")
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="límite de bytes"):
            analyze_directory(target, analysis_target_label="local:test")
    finally:
        get_settings.cache_clear()


def test_analyze_directory_fails_when_bandit_report_missing(monkeypatch, tmp_path) -> None:
    target = tmp_path / "target"
    target.mkdir()

    class _FixedTmpDir:
        def __init__(self, path: Path):
            self.path = path

        def __enter__(self):
            self.path.mkdir(parents=True, exist_ok=True)
            return str(self.path)

        def __exit__(self, exc_type, exc, tb):
            return False

    temp_root = tmp_path / "temp-work"

    monkeypatch.setattr(
        "app.services.project_scan_service.tempfile.TemporaryDirectory",
        lambda prefix="": _FixedTmpDir(temp_root),
    )

    def fake_bandit_command(_root, output):
        return ["bandit", "-o", str(output)]

    def fake_semgrep_command(_root, output):
        return ["semgrep", "--json-output", str(output), str(_root)]

    def fake_run(_cmd):
        return subprocess.CompletedProcess(args=_cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(
        "app.services.project_scan_service.build_bandit_command",
        fake_bandit_command,
    )
    monkeypatch.setattr(
        "app.services.project_scan_service.build_semgrep_command",
        fake_semgrep_command,
    )
    monkeypatch.setattr("app.services.project_scan_service.run_analysis_command", fake_run)

    with pytest.raises(RuntimeError, match="Bandit no generó informe"):
        analyze_directory(target, analysis_target_label="local:test")


def test_analyze_directory_fails_when_semgrep_report_missing(monkeypatch, tmp_path) -> None:
    target = tmp_path / "target"
    target.mkdir()

    class _FixedTmpDir:
        def __init__(self, path: Path):
            self.path = path

        def __enter__(self):
            self.path.mkdir(parents=True, exist_ok=True)
            return str(self.path)

        def __exit__(self, exc_type, exc, tb):
            return False

    temp_root = tmp_path / "temp-work"

    monkeypatch.setattr(
        "app.services.project_scan_service.tempfile.TemporaryDirectory",
        lambda prefix="": _FixedTmpDir(temp_root),
    )

    def fake_bandit_command(_root, output):
        return ["bandit", "-o", str(output)]

    def fake_semgrep_command(_root, output):
        return ["semgrep", "--json-output", str(output), str(_root)]

    def fake_run(cmd):
        if "bandit" in cmd[0]:
            out_idx = cmd.index("-o")
            Path(cmd[out_idx + 1]).write_text("{}", encoding="utf-8")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(
        "app.services.project_scan_service.build_bandit_command",
        fake_bandit_command,
    )
    monkeypatch.setattr(
        "app.services.project_scan_service.build_semgrep_command",
        fake_semgrep_command,
    )
    monkeypatch.setattr("app.services.project_scan_service.run_analysis_command", fake_run)

    with pytest.raises(RuntimeError, match="Semgrep no generó informe"):
        analyze_directory(target, analysis_target_label="local:test")


def test_ai_status_endpoint() -> None:
    client = TestClient(app)
    r = client.get("/ai/status")
    assert r.status_code == 200
    data = r.json()
    assert "ai_explanations_enabled" in data
    assert "local_analysis_root_configured" in data
    assert "enable_local_path" in data
    assert "local_path_enabled" in data
    assert "zip_max_entries" in data
    assert "zip_max_uncompressed_bytes" in data
    assert "git_url_max_length" in data
    assert "local_path_max_length" in data
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


def test_resolve_allowed_analysis_path_rejects_dot(tmp_path) -> None:
    with pytest.raises(ValueError, match="subdirectorio"):
        resolve_allowed_analysis_path(".", tmp_path)


def test_resolve_allowed_analysis_path_rejects_whitespace(tmp_path) -> None:
    with pytest.raises(ValueError, match="inválida"):
        resolve_allowed_analysis_path(" proj ", tmp_path)


def test_resolve_allowed_analysis_path_rejects_symlink_escape(tmp_path) -> None:
    outside = tmp_path.parent / "outside-target"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "link"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="directorio raíz permitido"):
        resolve_allowed_analysis_path("link", tmp_path)


def test_analyze_local_path_relative_missing_dir(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="No es un directorio o no existe"):
        analyze_local_path_relative("missing", allowed_root=tmp_path)


def test_local_path_forbidden_without_env(monkeypatch) -> None:
    monkeypatch.delenv("TFG_LOCAL_ANALYSIS_ROOT", raising=False)
    get_settings.cache_clear()
    try:
        client = TestClient(app)
        r = client.post("/analysis/local-path", json={"relative_path": "x"})
        assert r.status_code == 403
    finally:
        get_settings.cache_clear()


def test_local_path_forbidden_when_disabled(monkeypatch, tmp_path) -> None:
    root = tmp_path / "allow-root"
    root.mkdir()
    monkeypatch.setenv("TFG_LOCAL_ANALYSIS_ROOT", str(root))
    monkeypatch.setenv("TFG_ENABLE_LOCAL_PATH", "0")
    get_settings.cache_clear()
    try:
        client = TestClient(app)
        r = client.post("/analysis/local-path", json={"relative_path": "proj"})
        assert r.status_code == 403
        assert "TFG_ENABLE_LOCAL_PATH" in r.json()["detail"]["message"]
    finally:
        get_settings.cache_clear()


def test_analysis_upload_zip_success(monkeypatch) -> None:
    def fake_analyze_zip(content: bytes) -> dict:
        assert content == b"PK\x03\x04zip-ok"
        return {"analysis_target": "upload.zip", "total_findings": 0, "findings": []}

    monkeypatch.setattr("app.main.analyze_zip_bytes", fake_analyze_zip)

    client = TestClient(app)
    r = client.post(
        "/analysis/upload-zip",
        files={"file": ("project.zip", b"PK\x03\x04zip-ok", "application/zip")},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["analysis_target"] == "upload.zip"
    assert isinstance(body["analysis_id"], str)
    assert body["analysis_id"]


def test_analysis_upload_zip_bad_request(monkeypatch) -> None:
    def fake_analyze_zip(_: bytes) -> dict:
        raise ValueError("zip invalido")

    monkeypatch.setattr("app.main.analyze_zip_bytes", fake_analyze_zip)

    client = TestClient(app)
    r = client.post(
        "/analysis/upload-zip",
        files={"file": ("bad.zip", b"PK\x03\x04bad", "application/zip")},
    )

    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["error_code"] == "ANALYSIS_BAD_REQUEST"
    assert "zip invalido" in detail["message"]


def test_analysis_upload_zip_runtime_error(monkeypatch) -> None:
    def fake_analyze_zip(_: bytes) -> dict:
        raise RuntimeError("bandit no disponible")

    monkeypatch.setattr("app.main.analyze_zip_bytes", fake_analyze_zip)

    client = TestClient(app)
    r = client.post(
        "/analysis/upload-zip",
        files={"file": ("bad.zip", b"PK\x03\x04bad", "application/zip")},
    )

    assert r.status_code == 502
    detail = r.json()["detail"]
    assert detail["error_code"] == "ANALYSIS_RUNTIME_ERROR"
    assert "bandit no disponible" in detail["message"]


def test_analysis_upload_zip_empty_content() -> None:
    client = TestClient(app)
    r = client.post(
        "/analysis/upload-zip",
        files={"file": ("project.zip", b"", "application/zip")},
    )
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["error_code"] == "ZIP_EMPTY_CONTENT"
    assert "No se recibió contenido ZIP" in detail["message"]


def test_analysis_upload_zip_rejects_non_zip_extension() -> None:
    client = TestClient(app)
    r = client.post(
        "/analysis/upload-zip",
        files={"file": ("project.txt", b"abc", "text/plain")},
    )
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["error_code"] == "ZIP_EXTENSION_REQUIRED"
    assert "extensión .zip" in detail["message"]


def test_analysis_upload_zip_rejects_invalid_content_type() -> None:
    client = TestClient(app)
    r = client.post(
        "/analysis/upload-zip",
        files={"file": ("project.zip", b"PK\x03\x04fake", "text/plain")},
    )
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["error_code"] == "ZIP_CONTENT_TYPE_INVALID"
    assert "Tipo de contenido no permitido" in detail["message"]


def test_analysis_upload_zip_rejects_invalid_signature() -> None:
    client = TestClient(app)
    r = client.post(
        "/analysis/upload-zip",
        files={"file": ("project.zip", b"not-a-zip", "application/zip")},
    )
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["error_code"] == "ZIP_INVALID_SIGNATURE"
    assert "firma ZIP válida" in detail["message"]


def test_api_error_contract_has_code_and_message() -> None:
    client = TestClient(app)
    r = client.post(
        "/analysis/upload-zip",
        files={"file": ("project.zip", b"not-a-zip", "application/zip")},
    )
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert set(detail.keys()) == {"error_code", "message", "analysis_id"}
    assert isinstance(detail["error_code"], str)
    assert isinstance(detail["message"], str)
    assert isinstance(detail["analysis_id"], str)


def test_analysis_upload_zip_payload_too_large(monkeypatch) -> None:
    def fake_analyze_zip(_: bytes) -> dict:
        raise PayloadTooLargeError("ZIP demasiado grande")

    monkeypatch.setattr("app.main.analyze_zip_bytes", fake_analyze_zip)
    client = TestClient(app)
    r = client.post(
        "/analysis/upload-zip",
        files={"file": ("big.zip", b"PK\x03\x04x", "application/zip")},
    )
    assert r.status_code == 413
    detail = r.json()["detail"]
    assert detail["error_code"] == "ZIP_TOO_LARGE"
    assert "ZIP demasiado grande" in detail["message"]


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
    body = r.json()
    assert body["analysis_target"].startswith("git:https://")
    assert isinstance(body["analysis_id"], str)


def test_analysis_git_clone_bad_request(monkeypatch) -> None:
    def fake_clone(_: str) -> dict:
        raise ValueError("URL invalida")

    monkeypatch.setattr("app.main.clone_and_analyze_repo", fake_clone)

    client = TestClient(app)
    r = client.post("/analysis/git-clone", json={"url": "https://example.com/r.git"})

    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["error_code"] == "ANALYSIS_BAD_REQUEST"
    assert "URL invalida" in detail["message"]


def test_analysis_git_clone_forbidden(monkeypatch) -> None:
    def fake_clone(_: str) -> dict:
        raise PermissionError("clonado desactivado")

    monkeypatch.setattr("app.main.clone_and_analyze_repo", fake_clone)

    client = TestClient(app)
    r = client.post("/analysis/git-clone", json={"url": "https://example.com/r.git"})

    assert r.status_code == 403
    detail = r.json()["detail"]
    assert detail["error_code"] == "GIT_CLONE_DISABLED"
    assert "clonado desactivado" in detail["message"]


def test_analysis_git_clone_runtime_error(monkeypatch) -> None:
    def fake_clone(_: str) -> dict:
        raise RuntimeError("git clone fallo")

    monkeypatch.setattr("app.main.clone_and_analyze_repo", fake_clone)

    client = TestClient(app)
    r = client.post("/analysis/git-clone", json={"url": "https://example.com/r.git"})

    assert r.status_code == 502
    detail = r.json()["detail"]
    assert detail["error_code"] == "GIT_CLONE_FAILED"
    assert "git clone fallo" in detail["message"]


def test_clone_and_analyze_repo_service_success(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TFG_ENABLE_GIT_CLONE", "1")
    monkeypatch.setenv("TFG_GIT_ALLOWED_HOSTS", "github.com")
    get_settings.cache_clear()
    try:
        def fake_run(cmd, capture_output, text, timeout, check):
            clone_dir = Path(cmd[-1])
            clone_dir.mkdir(parents=True, exist_ok=True)
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="ok",
                stderr="",
            )

        def fake_analyze_directory(target: Path, *, analysis_target_label: str) -> dict:
            assert target.is_dir()
            return {"analysis_target": analysis_target_label, "findings": [], "total_findings": 0}

        monkeypatch.setattr("app.services.project_scan_service.subprocess.run", fake_run)
        monkeypatch.setattr(
            "app.services.project_scan_service.analyze_directory",
            fake_analyze_directory,
        )

        out = clone_and_analyze_repo("https://github.com/octocat/Hello-World.git")
        assert out["analysis_target"].startswith("git:https://")
        assert out["meta"]["git_returncode"] == 0
        assert out["meta"]["git_command"][0] == "git"
    finally:
        get_settings.cache_clear()


def test_clone_and_analyze_repo_service_timeout(monkeypatch) -> None:
    monkeypatch.setenv("TFG_ENABLE_GIT_CLONE", "1")
    monkeypatch.setenv("TFG_GIT_ALLOWED_HOSTS", "github.com")
    get_settings.cache_clear()
    try:
        def fake_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=["git", "clone"], timeout=5)

        monkeypatch.setattr("app.services.project_scan_service.subprocess.run", fake_run)
        with pytest.raises(RuntimeError, match="tiempo límite"):
            clone_and_analyze_repo("https://github.com/octocat/Hello-World.git")
    finally:
        get_settings.cache_clear()


def test_clone_and_analyze_repo_service_git_missing(monkeypatch) -> None:
    monkeypatch.setenv("TFG_ENABLE_GIT_CLONE", "1")
    monkeypatch.setenv("TFG_GIT_ALLOWED_HOSTS", "github.com")
    get_settings.cache_clear()
    try:
        def fake_run(*args, **kwargs):
            raise FileNotFoundError("git")

        monkeypatch.setattr("app.services.project_scan_service.subprocess.run", fake_run)
        with pytest.raises(RuntimeError, match="comando 'git' no disponible"):
            clone_and_analyze_repo("https://github.com/octocat/Hello-World.git")
    finally:
        get_settings.cache_clear()


def test_clone_and_analyze_repo_service_nonzero_return(monkeypatch) -> None:
    monkeypatch.setenv("TFG_ENABLE_GIT_CLONE", "1")
    monkeypatch.setenv("TFG_GIT_ALLOWED_HOSTS", "github.com")
    get_settings.cache_clear()
    try:
        def fake_run(cmd, capture_output, text, timeout, check):
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=128,
                stdout="",
                stderr="fatal: repo not found",
            )

        monkeypatch.setattr("app.services.project_scan_service.subprocess.run", fake_run)
        with pytest.raises(RuntimeError, match="git clone falló"):
            clone_and_analyze_repo("https://github.com/octocat/missing.git")
    finally:
        get_settings.cache_clear()


def test_clone_and_analyze_repo_service_incomplete_clone(monkeypatch) -> None:
    monkeypatch.setenv("TFG_ENABLE_GIT_CLONE", "1")
    monkeypatch.setenv("TFG_GIT_ALLOWED_HOSTS", "github.com")
    get_settings.cache_clear()
    try:
        def fake_run(cmd, capture_output, text, timeout, check):
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="ok",
                stderr="",
            )

        monkeypatch.setattr("app.services.project_scan_service.subprocess.run", fake_run)
        with pytest.raises(RuntimeError, match="Clonado incompleto"):
            clone_and_analyze_repo("https://github.com/octocat/Hello-World.git")
    finally:
        get_settings.cache_clear()


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
        body = r.json()
        assert body["analysis_target"] == "local:proj"
        assert isinstance(body["analysis_id"], str)
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
        detail = r.json()["detail"]
        assert detail["error_code"] == "LOCAL_PATH_INVALID"
        assert "ruta invalida" in detail["message"]
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
        detail = r.json()["detail"]
        assert detail["error_code"] == "LOCAL_PATH_NOT_FOUND"
        assert "proyecto no encontrado" in detail["message"]
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
        detail = r.json()["detail"]
        assert detail["error_code"] == "ANALYSIS_RUNTIME_ERROR"
        assert "bandit timeout" in detail["message"]
    finally:
        get_settings.cache_clear()
