import pytest

from app.config import Settings, get_settings


def test_settings_accept_bool_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TFG_ENABLE_GIT_CLONE", "false")
    monkeypatch.setenv("TFG_AI_EXPLANATIONS_ENABLED", "yes")
    get_settings.cache_clear()
    try:
        s = Settings()
        assert s.enable_git_clone is False
        assert s.ai_explanations_enabled is True
    finally:
        get_settings.cache_clear()


def test_settings_rejects_invalid_integer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TFG_ANALYSIS_TIMEOUT_SEC", "abc")
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="TFG_ANALYSIS_TIMEOUT_SEC"):
            Settings()
    finally:
        get_settings.cache_clear()


def test_settings_rejects_negative_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TFG_ANALYSIS_TIMEOUT_SEC", "-2")
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="mínimo"):
            Settings()
    finally:
        get_settings.cache_clear()


def test_settings_rejects_invalid_allowed_hosts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TFG_GIT_ALLOWED_HOSTS", "github.com, bad host")
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="host no válido"):
            Settings()
    finally:
        get_settings.cache_clear()
