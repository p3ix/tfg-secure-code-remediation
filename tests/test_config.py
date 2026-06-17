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


def test_settings_zip_and_path_limits_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TFG_ZIP_MAX_ENTRIES", raising=False)
    monkeypatch.delenv("TFG_ENABLE_LOCAL_PATH", raising=False)
    get_settings.cache_clear()
    try:
        s = Settings()
        assert s.zip_max_entries == 10_000
        assert s.enable_local_path is True
        assert s.git_url_max_length == 2048
    finally:
        get_settings.cache_clear()


def test_settings_ai_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "TFG_AI_PROVIDER",
        "TFG_AI_MODEL",
        "TFG_AI_OLLAMA_URL",
        "TFG_AI_TIMEOUT_SEC",
        "TFG_AI_INCLUDE_SNIPPET",
    ):
        monkeypatch.delenv(var, raising=False)
    get_settings.cache_clear()
    try:
        s = Settings()
        assert s.ai_provider == "ollama"
        assert s.ai_model == "llama3.2:3b"
        assert s.ai_ollama_url == "http://127.0.0.1:11434"
        assert s.ai_timeout_sec == 30
        assert s.ai_include_snippet is False
    finally:
        get_settings.cache_clear()


def test_settings_rejects_invalid_ai_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TFG_AI_PROVIDER", "gemini")
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="TFG_AI_PROVIDER"):
            Settings()
    finally:
        get_settings.cache_clear()


def test_settings_ai_provider_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TFG_AI_PROVIDER", "STUB")
    get_settings.cache_clear()
    try:
        assert Settings().ai_provider == "stub"
    finally:
        get_settings.cache_clear()
