"""Humo visual WEB v2 (fase 2): identidad, a11y y formulario progresivo."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home_has_how_it_works_steps() -> None:
    html = client.get("/").text
    assert "Cómo funciona" in html or "Elige el origen" in html
    assert 'class="steps-flow"' in html
    assert "Lanza el escaneo" in html


def test_base_skip_link_and_main_landmark() -> None:
    for path in ("/", "/analyze"):
        html = client.get(path).text
        assert 'class="skip-link"' in html
        assert 'id="main-content"' in html
        assert 'class="site-footer"' in html


def test_analyze_form_has_progressive_sections() -> None:
    html = client.get("/analyze").text
    assert "Origen del código" in html
    assert 'data-mode-field="upload_zip"' in html
    assert 'data-mode-field="git_clone"' in html
    assert "Ejecutar" in html
    assert 'aria-busy' not in html or 'id="analyze-submit"' in html


def test_analyze_form_status_element_for_loading() -> None:
    html = client.get("/analyze").text
    assert 'id="analyze-form-status"' in html
    assert 'role="status"' in html
    assert 'aria-live="polite"' in html


def test_results_page_has_breadcrumb() -> None:
    html = client.get("/results/expired-id").text
    assert 'class="breadcrumb"' in html
    assert "Resultado del escaneo" in html
    assert "Nuevo análisis" in html


def test_public_pages_avoid_mvp_demo_wording() -> None:
    for path in ("/", "/analyze"):
        html = client.get(path).text
        assert "Informes guardados (MVP/demo)" not in html
        assert "fixture_reports" not in html
