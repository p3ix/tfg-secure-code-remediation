import json
import urllib.error

import pytest

from app.models.finding import NormalizedFinding
from app.services.ai import ollama_provider as mod
from app.services.ai.ollama_provider import OllamaProvider, _build_prompt


def _finding(snippet: str | None = None) -> NormalizedFinding:
    return NormalizedFinding(
        source_tool="bandit",
        source_rule_id="B602",
        file_path="app.py",
        line_start=1,
        raw_message="subprocess con shell=True",
        severity="high",
        mvp_category="command_injection",
        candidate_for_remediation=True,
        remediation_mode="autofix_candidate",
        cwe_id=78,
        code_snippet=snippet,
    )


def _provider(include_snippet: bool = False) -> OllamaProvider:
    return OllamaProvider(
        url="http://127.0.0.1:11434",
        model="llama3.2:3b",
        timeout_sec=5.0,
        include_snippet=include_snippet,
    )


def test_explain_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        assert url.endswith("/api/generate")
        assert payload["model"] == "llama3.2:3b"
        assert payload["format"] == "json"
        return {
            "response": json.dumps(
                {
                    "summary": "resumen",
                    "risk": "riesgo",
                    "suggestion": "sugerencia",
                    "action_steps": ["paso 1", "paso 2"],
                }
            )
        }

    monkeypatch.setattr(mod, "_http_post_json", fake_post)
    explanation = _provider().explain(_finding())

    assert explanation is not None
    assert explanation.provider == "ollama"
    assert explanation.model == "llama3.2:3b"
    assert explanation.summary == "resumen"
    assert explanation.suggestion == "sugerencia"
    assert explanation.action_steps == ["paso 1", "paso 2"]
    assert explanation.location_hint == "app.py:1"
    assert explanation.prompt_version == "v3"
    assert explanation.prompt_hash and len(explanation.prompt_hash) == 16


def test_explain_degrades_on_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(mod, "_http_post_json", fake_post)
    assert _provider().explain(_finding()) is None


def test_explain_degrades_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        raise TimeoutError("timed out")

    monkeypatch.setattr(mod, "_http_post_json", fake_post)
    assert _provider().explain(_finding()) is None


def test_explain_degrades_on_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        return {"response": "no es json"}

    monkeypatch.setattr(mod, "_http_post_json", fake_post)
    assert _provider().explain(_finding()) is None


def test_explain_degrades_on_missing_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        return {"response": json.dumps({"summary": "solo summary"})}

    monkeypatch.setattr(mod, "_http_post_json", fake_post)
    assert _provider().explain(_finding()) is None


def test_explain_tolerates_missing_suggestion(monkeypatch: pytest.MonkeyPatch) -> None:
    # Modelos pequeños a veces omiten 'suggestion'; no debe descartarse la explicación.
    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        return {
            "response": json.dumps(
                {
                    "summary": "resumen",
                    "risk": "riesgo",
                    "action_steps": ["paso 1"],
                }
            )
        }

    monkeypatch.setattr(mod, "_http_post_json", fake_post)
    explanation = _provider().explain(_finding())

    assert explanation is not None
    assert explanation.summary == "resumen"
    assert explanation.risk == "riesgo"
    assert explanation.suggestion == ""
    assert explanation.action_steps == ["paso 1"]


def test_prompt_includes_file_and_line() -> None:
    prompt = _build_prompt(_finding(), include_snippet=False)
    assert "fichero: app.py" in prompt
    assert "línea: 1" in prompt
    assert "categoría MVP: command_injection" in prompt


def test_prompt_excludes_snippet_by_default() -> None:
    prompt = _build_prompt(_finding(snippet="import os"), include_snippet=False)
    assert "import os" not in prompt
    assert "dato no confiable" in prompt


def test_prompt_includes_snippet_when_enabled() -> None:
    prompt = _build_prompt(_finding(snippet="import os"), include_snippet=True)
    assert "import os" in prompt


def test_prompt_contains_anti_injection_hardening() -> None:
    prompt = _build_prompt(_finding(), include_snippet=False)
    assert "no confiables" in prompt
    assert "ignóralo" in prompt or "ignora" in prompt.lower()
