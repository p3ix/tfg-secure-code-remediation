from app.models.ai_explanation import AIExplanation
from app.models.finding import NormalizedFinding
from app.services.ai.cache import ExplanationCache
from app.services.ai.stub_provider import StubProvider
from app.services.presentable_scan import build_presentable_scan


class _CountingProvider:
    """Proveedor que cuenta las llamadas reales a explain (para verificar caché)."""

    name = "counting"
    model = "test"

    def __init__(self) -> None:
        self.calls = 0

    def explain(self, finding: NormalizedFinding) -> AIExplanation:
        self.calls += 1
        return AIExplanation(
            summary="s",
            risk="r",
            suggestion="g",
            provider=self.name,
            model=self.model,
            prompt_version="v3",
        )


def _findings() -> list[NormalizedFinding]:
    return [
        NormalizedFinding(
            source_tool="bandit",
            source_rule_id="B602",
            file_path="app.py",
            line_start=1,
            raw_message="subprocess shell=True",
            severity="high",
            mvp_category="command_injection",
            candidate_for_remediation=True,
            remediation_mode="autofix_candidate",
            cwe_id=78,
        ),
        NormalizedFinding(
            source_tool="bandit",
            source_rule_id="B506",
            file_path="conf.py",
            line_start=4,
            raw_message="yaml.load",
            severity="medium",
            mvp_category="yaml_load",
            candidate_for_remediation=True,
            remediation_mode="autofix_candidate",
            cwe_id=20,
        ),
    ]


def test_presentable_without_provider_has_null_explanation() -> None:
    out = build_presentable_scan(
        _findings(),
        analysis_target="x",
        execution_mode="runtime",
    )
    assert out["schema_version"] == "1.2"
    for row in out["findings"]:
        assert row["ai_explanation"] is None


def test_presentable_with_stub_provider_adds_explanation() -> None:
    out = build_presentable_scan(
        _findings(),
        analysis_target="x",
        execution_mode="runtime",
        ai_provider=StubProvider(),
    )
    rows = out["findings"]
    assert all(row["ai_explanation"] is not None for row in rows)
    first = rows[0]["ai_explanation"]
    assert first["provider"] == "stub"
    assert "comando" in first["summary"].lower()
    assert first["suggestion"]
    assert first["location_hint"] == "app.py:1"
    assert first["action_steps"]


def test_presentable_grouped_with_stub_provider() -> None:
    findings = _findings() + _findings()  # duplica → grupos equivalentes
    out = build_presentable_scan(
        findings,
        analysis_target="x",
        execution_mode="runtime",
        group_equivalent=True,
        ai_provider=StubProvider(),
    )
    for row in out["findings"]:
        assert row["ai_explanation"] is not None
        assert row["ai_explanation"]["provider"] == "stub"


def test_presentable_explanation_uses_cache_marker() -> None:
    # Dos hallazgos de la misma categoría/regla/cwe: el segundo viene de caché.
    findings = [_findings()[0], _findings()[0]]
    out = build_presentable_scan(
        findings,
        analysis_target="x",
        execution_mode="runtime",
        ai_provider=StubProvider(),
    )
    cached_flags = [row["ai_explanation"]["cached"] for row in out["findings"]]
    assert cached_flags == [False, True]


def test_shared_cache_avoids_recomputing_across_renders() -> None:
    # Caché compartida entre dos renders del mismo análisis: el proveedor solo se
    # invoca en el primero; el segundo (p. ej. /report) reutiliza la caché.
    provider = _CountingProvider()
    cache = ExplanationCache()
    findings = _findings()

    first = build_presentable_scan(
        findings,
        analysis_target="x",
        execution_mode="runtime",
        ai_provider=provider,
        ai_cache=cache,
    )
    assert provider.calls == len(findings)

    second = build_presentable_scan(
        findings,
        analysis_target="x",
        execution_mode="runtime",
        ai_provider=provider,
        ai_cache=cache,
    )
    # No hay nuevas llamadas al proveedor: todo viene de la caché compartida.
    assert provider.calls == len(findings)
    assert all(row["ai_explanation"]["cached"] for row in second["findings"])
    assert all(row["ai_explanation"] is not None for row in first["findings"])
