from app.models.ai_explanation import AIExplanation
from app.models.finding import NormalizedFinding
from app.services.ai.provider import PROMPT_VERSION, AIProvider
from app.services.ai.stub_provider import STUB_MODEL, StubProvider


def _finding(category: str = "command_injection") -> NormalizedFinding:
    return NormalizedFinding(
        source_tool="bandit",
        source_rule_id="B602",
        file_path="app.py",
        line_start=1,
        raw_message="subprocess con shell=True",
        severity="low",
        mvp_category=category,
        candidate_for_remediation=True,
        remediation_mode="autofix_candidate",
    )


def test_stub_provider_satisfies_protocol() -> None:
    assert isinstance(StubProvider(), AIProvider)


def test_stub_provider_returns_explanation_for_known_category() -> None:
    explanation = StubProvider().explain(_finding("command_injection"))

    assert isinstance(explanation, AIExplanation)
    assert explanation.provider == "stub"
    assert explanation.model == STUB_MODEL
    assert explanation.prompt_version == PROMPT_VERSION
    assert "comando" in explanation.summary.lower()
    assert explanation.suggestion


def test_stub_provider_is_deterministic() -> None:
    finding = _finding("unsafe_yaml_load")
    first = StubProvider().explain(finding)
    second = StubProvider().explain(finding)

    assert first.to_dict() == second.to_dict()


def test_stub_provider_falls_back_for_unknown_category() -> None:
    explanation = StubProvider().explain(_finding("totally_unknown_category"))

    assert isinstance(explanation, AIExplanation)
    assert explanation.summary
    assert explanation.risk
    assert explanation.suggestion


def test_stub_provider_uses_real_mvp_category_keys() -> None:
    # Las categorías reales de los parsers reciben texto curado, no el genérico.
    explanation = StubProvider().explain(_finding("unsafe_yaml_load"))

    assert "yaml" in explanation.summary.lower()
    assert "safe_load" in explanation.suggestion.lower()


def test_stub_provider_includes_before_after_example_for_known_category() -> None:
    explanation = StubProvider().explain(_finding("unsafe_yaml_load"))

    assert explanation.example_before == "yaml.load(data, Loader=yaml.Loader)"
    assert explanation.example_after == "yaml.safe_load(data)"


def test_stub_provider_omits_example_for_unknown_category() -> None:
    explanation = StubProvider().explain(_finding("totally_unknown_category"))

    assert explanation.example_before is None
    assert explanation.example_after is None


def test_explanation_to_dict_keys() -> None:
    explanation = StubProvider().explain(_finding())
    keys = set(explanation.to_dict())

    assert keys == {
        "summary",
        "risk",
        "suggestion",
        "provider",
        "model",
        "prompt_version",
        "prompt_hash",
        "cached",
        "location_hint",
        "code_focus",
        "action_steps",
        "example_before",
        "example_after",
    }


def test_explanation_to_dict_reflects_before_after_example() -> None:
    explanation = AIExplanation(
        summary="s",
        risk="r",
        suggestion="sug",
        provider="stub",
        model="m",
        prompt_version="v3",
        example_before="yaml.load(data, Loader=yaml.Loader)",
        example_after="yaml.safe_load(data)",
    )

    payload = explanation.to_dict()

    assert payload["example_before"] == "yaml.load(data, Loader=yaml.Loader)"
    assert payload["example_after"] == "yaml.safe_load(data)"


def test_explanation_to_dict_example_defaults_to_none() -> None:
    explanation = AIExplanation(
        summary="s",
        risk="r",
        suggestion="sug",
        provider="stub",
        model="m",
        prompt_version="v3",
    )

    payload = explanation.to_dict()

    assert payload["example_before"] is None
    assert payload["example_after"] is None


def test_stub_provider_includes_location_and_steps() -> None:
    finding = NormalizedFinding(
        source_tool="bandit",
        source_rule_id="B602",
        file_path="pkg/handler.py",
        line_start=7,
        raw_message="subprocess con shell=True",
        severity="low",
        mvp_category="command_injection",
        candidate_for_remediation=True,
        remediation_mode="autofix_candidate",
        code_snippet="os.system(user_input)",
    )
    explanation = StubProvider().explain(finding)

    assert explanation.location_hint == "pkg/handler.py:7"
    assert explanation.code_focus == "os.system(user_input)"
    assert explanation.action_steps
    assert len(explanation.action_steps) >= 2
