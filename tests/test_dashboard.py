from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_redirects_to_dashboard() -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


def test_dashboard_renders_html_when_reports_exist() -> None:
    bandit = Path("reports/bandit/fixtures-mvp-bandit.json")
    semgrep = Path("reports/semgrep/fixtures-mvp-semgrep.json")
    if not bandit.exists() or not semgrep.exists():
        return

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Resultado del escaneo" in response.text
    assert "Nuevo análisis" in response.text
    assert "Subir ZIP (real)" in response.text
    assert "Clonar repositorio Git (real)" in response.text
    assert "Ruta local permitida (real)" in response.text
    assert "Informes guardados (MVP/demo)" in response.text
    assert "schema_version" in response.text or "Total hallazgos" in response.text


def test_dashboard_renders_notice_when_reports_missing(monkeypatch) -> None:
    def fake_analyze() -> dict:
        raise FileNotFoundError("no report")

    monkeypatch.setattr("app.main.analyze_fixtures_reports", fake_analyze)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "No se encontraron informes estáticos del corpus MVP" in response.text
    assert "Estado inicial" in response.text


def test_dashboard_analyze_runtime_renders_presentable_result(monkeypatch) -> None:
    def fake_runtime_analysis() -> dict:
        return {
            "analysis_target": "fixtures/mvp",
            "execution_mode": "runtime",
            "generated_reports": {
                "bandit": "reports/runtime/bandit.json",
                "semgrep": "reports/runtime/semgrep.json",
            },
            "findings": [
                {
                    "source_tool": "bandit",
                    "source_rule_id": "B501",
                    "file_path": "fixtures/mvp/example.py",
                    "line_start": 12,
                    "raw_message": "verify false",
                    "severity": "high",
                    "mvp_category": "verify_false",
                    "candidate_for_remediation": True,
                    "remediation_mode": "autofix_candidate",
                    "cwe_id": 295,
                    "owasp_top10": "A04",
                }
            ],
        }

    monkeypatch.setattr("app.main.analyze_fixtures_runtime", fake_runtime_analysis)

    response = client.post(
        "/dashboard/analyze",
        data={
            "analysis_mode": "fixture_runtime",
            "hide_info": "true",
            "group_equivalent": "true",
        },
    )

    assert response.status_code == 200
    assert "fixtures/mvp" in response.text
    assert "verify_false" in response.text
    assert "Remediación asistida posible" in response.text


def test_dashboard_analyze_zip_uses_uploaded_file(monkeypatch) -> None:
    def fake_analyze_zip(content: bytes) -> dict:
        assert content == b"PK\x03\x04zip-content"
        return {
            "analysis_target": "upload.zip",
            "execution_mode": "runtime",
            "generated_reports": {
                "bandit": "(temporal)",
                "semgrep": "(temporal)",
            },
            "findings": [
                {
                    "source_tool": "semgrep",
                    "source_rule_id": "yaml.load",
                    "file_path": "src/app.py",
                    "line_start": 3,
                    "raw_message": "unsafe yaml",
                    "severity": "medium",
                    "mvp_category": "unsafe_yaml_load",
                    "candidate_for_remediation": True,
                    "remediation_mode": "autofix_candidate",
                }
            ],
        }

    monkeypatch.setattr("app.main.analyze_zip_bytes", fake_analyze_zip)

    response = client.post(
        "/dashboard/analyze",
        data={"analysis_mode": "upload_zip"},
        files={"file": ("project.zip", b"PK\x03\x04zip-content", "application/zip")},
    )

    assert response.status_code == 200
    assert "upload.zip" in response.text
    assert "unsafe_yaml_load" in response.text


def test_dashboard_analyze_zip_rejects_non_zip_file() -> None:
    response = client.post(
        "/dashboard/analyze",
        data={"analysis_mode": "upload_zip"},
        files={"file": ("project.txt", b"txt-content", "text/plain")},
    )
    assert response.status_code == 200
    assert "No se pudo completar el análisis" in response.text
    assert "terminar en .zip" in response.text


def test_dashboard_analyze_zip_rejects_invalid_signature() -> None:
    response = client.post(
        "/dashboard/analyze",
        data={"analysis_mode": "upload_zip"},
        files={"file": ("project.zip", b"not-a-zip", "application/zip")},
    )
    assert response.status_code == 200
    assert "No se pudo completar el análisis" in response.text
    assert "firma ZIP válida" in response.text


def test_dashboard_analyze_local_path_requires_value(monkeypatch, tmp_path) -> None:
    from app.config import get_settings

    monkeypatch.setenv("TFG_LOCAL_ANALYSIS_ROOT", str(tmp_path))
    get_settings.cache_clear()
    try:
        response = client.post(
            "/dashboard/analyze",
            data={
                "analysis_mode": "local_path",
                "local_path": "   ",
            },
        )
        assert response.status_code == 200
        assert "Indica una ruta relativa" in response.text
    finally:
        get_settings.cache_clear()


def test_dashboard_renders_empty_findings_state(monkeypatch) -> None:
    def fake_runtime_analysis() -> dict:
        return {
            "analysis_target": "fixtures/mvp",
            "execution_mode": "runtime",
            "generated_reports": {"bandit": "x", "semgrep": "y"},
            "findings": [],
        }

    monkeypatch.setattr("app.main.analyze_fixtures_runtime", fake_runtime_analysis)
    response = client.post(
        "/dashboard/analyze",
        data={"analysis_mode": "fixture_runtime"},
    )
    assert response.status_code == 200
    assert "Sin hallazgos en esta ejecución" in response.text


def test_dashboard_analyze_local_path_error_is_rendered(monkeypatch) -> None:
    response = client.post(
        "/dashboard/analyze",
        data={
            "analysis_mode": "local_path",
            "local_path": "demo-project",
        },
    )

    assert response.status_code == 200
    assert "No se pudo completar el análisis" in response.text
    assert "ruta local" in response.text.lower()


def test_dashboard_analyze_git_clone_success(monkeypatch) -> None:
    def fake_clone(url: str) -> dict:
        assert url == "https://github.com/octocat/Hello-World.git"
        return {
            "analysis_target": f"git:{url}",
            "execution_mode": "runtime",
            "generated_reports": {"bandit": "(temporal)", "semgrep": "(temporal)"},
            "findings": [],
        }

    monkeypatch.setattr("app.main.clone_and_analyze_repo", fake_clone)
    response = client.post(
        "/dashboard/analyze",
        data={
            "analysis_mode": "git_clone",
            "git_url": "https://github.com/octocat/Hello-World.git",
        },
    )
    assert response.status_code == 200
    assert "git:https://github.com/octocat/Hello-World.git" in response.text


def test_dashboard_analyze_git_clone_requires_url(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("TFG_ENABLE_GIT_CLONE", "1")
    get_settings.cache_clear()
    try:
        response = client.post(
            "/dashboard/analyze",
            data={"analysis_mode": "git_clone", "git_url": "   "},
        )
        assert response.status_code == 200
        assert "Indica una URL HTTPS para el modo git_clone" in response.text
    finally:
        get_settings.cache_clear()


def test_dashboard_analyze_git_clone_disabled(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("TFG_ENABLE_GIT_CLONE", "0")
    get_settings.cache_clear()
    try:
        response = client.post(
            "/dashboard/analyze",
            data={
                "analysis_mode": "git_clone",
                "git_url": "https://github.com/octocat/Hello-World.git",
            },
        )
        assert response.status_code == 200
        assert "git clone está desactivado" in response.text
    finally:
        get_settings.cache_clear()
