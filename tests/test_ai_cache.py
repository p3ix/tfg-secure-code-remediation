from app.models.ai_explanation import AIExplanation
from app.models.finding import NormalizedFinding
from app.services.ai.cache import (
    ExplanationCache,
    explain_cached,
    explanation_cache_key,
)
from app.services.ai.stub_provider import StubProvider


def _finding(category: str = "command_injection", rule: str = "B602") -> NormalizedFinding:
    return NormalizedFinding(
        source_tool="bandit",
        source_rule_id=rule,
        file_path="app.py",
        line_start=1,
        raw_message="msg",
        severity="low",
        mvp_category=category,
        candidate_for_remediation=True,
        remediation_mode="autofix_candidate",
        cwe_id=78,
    )


class _CountingProvider:
    name = "counting"
    model = "counting-model"

    def __init__(self) -> None:
        self.calls = 0

    def explain(self, finding: NormalizedFinding) -> AIExplanation:
        self.calls += 1
        return AIExplanation(
            summary="s",
            risk="r",
            suggestion="x",
            provider=self.name,
            model=self.model,
            prompt_version="v1",
        )


def test_cache_key_ignores_file_and_line() -> None:
    a = _finding()
    b = _finding()
    b.file_path = "other.py"
    b.line_start = 999
    assert explanation_cache_key("stub", "m", a) == explanation_cache_key("stub", "m", b)


def test_cache_key_differs_by_category() -> None:
    k1 = explanation_cache_key("stub", "m", _finding("command_injection"))
    k2 = explanation_cache_key("stub", "m", _finding("yaml_load"))
    assert k1 != k2


def test_explain_cached_hit_avoids_second_call() -> None:
    provider = _CountingProvider()
    cache = ExplanationCache()
    finding = _finding()

    first = explain_cached(provider, finding, cache)
    second = explain_cached(provider, finding, cache)

    assert provider.calls == 1
    assert first is not None and first.cached is False
    assert second is not None and second.cached is True
    assert len(cache) == 1


def test_explain_cached_stores_per_key() -> None:
    provider = _CountingProvider()
    cache = ExplanationCache()

    explain_cached(provider, _finding("command_injection"), cache)
    explain_cached(provider, _finding("yaml_load"), cache)

    assert provider.calls == 2
    assert len(cache) == 2


def test_explain_cached_reapplies_location_on_hit() -> None:
    provider = StubProvider()
    cache = ExplanationCache()
    first_finding = NormalizedFinding(
        source_tool="bandit",
        source_rule_id="B602",
        file_path="a.py",
        line_start=1,
        raw_message="shell=True",
        severity="high",
        mvp_category="command_injection",
        candidate_for_remediation=True,
        remediation_mode="autofix_candidate",
        cwe_id=78,
    )
    second_finding = NormalizedFinding(
        source_tool="bandit",
        source_rule_id="B602",
        file_path="b.py",
        line_start=9,
        raw_message="shell=True",
        severity="high",
        mvp_category="command_injection",
        candidate_for_remediation=True,
        remediation_mode="autofix_candidate",
        cwe_id=78,
    )
    first = explain_cached(provider, first_finding, cache)
    second = explain_cached(provider, second_finding, cache)

    assert first is not None and second is not None
    assert first.location_hint == "a.py:1"
    assert second.location_hint == "b.py:9"
    assert second.cached is True


def test_explain_cached_does_not_store_none() -> None:
    class _NoneProvider:
        name = "none"
        model = "none"

        def explain(self, finding: NormalizedFinding) -> None:
            return None

    cache = ExplanationCache()
    result = explain_cached(_NoneProvider(), _finding(), cache)

    assert result is None
    assert len(cache) == 0


def test_explain_cached_with_stub_provider() -> None:
    cache = ExplanationCache()
    result = explain_cached(StubProvider(), _finding(), cache)

    assert result is not None
    assert result.provider == "stub"
