import pytest

from app.config import Settings, get_settings
from app.services.ai.factory import get_ai_provider
from app.services.ai.ollama_provider import OllamaProvider
from app.services.ai.stub_provider import StubProvider


def _settings_with(monkeypatch: pytest.MonkeyPatch, **env: str) -> Settings:
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    return Settings()


def test_factory_returns_none_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings_with(
        monkeypatch,
        TFG_AI_EXPLANATIONS_ENABLED="0",
        TFG_AI_PROVIDER="stub",
    )
    try:
        assert get_ai_provider(settings) is None
    finally:
        get_settings.cache_clear()


def test_factory_returns_stub_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings_with(
        monkeypatch,
        TFG_AI_EXPLANATIONS_ENABLED="1",
        TFG_AI_PROVIDER="stub",
    )
    try:
        assert isinstance(get_ai_provider(settings), StubProvider)
    finally:
        get_settings.cache_clear()


def test_factory_returns_ollama_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings_with(
        monkeypatch,
        TFG_AI_EXPLANATIONS_ENABLED="1",
        TFG_AI_PROVIDER="ollama",
    )
    try:
        provider = get_ai_provider(settings)
        assert isinstance(provider, OllamaProvider)
        assert provider.model == settings.ai_model
    finally:
        get_settings.cache_clear()


def test_factory_returns_none_for_unimplemented_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings_with(
        monkeypatch,
        TFG_AI_EXPLANATIONS_ENABLED="1",
        TFG_AI_PROVIDER="openai",
    )
    try:
        assert get_ai_provider(settings) is None
    finally:
        get_settings.cache_clear()
