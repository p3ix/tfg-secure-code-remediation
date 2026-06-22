from __future__ import annotations

from dataclasses import replace

from app.models.ai_explanation import AIExplanation
from app.models.finding import NormalizedFinding
from app.services.ai.enrichment import apply_finding_enrichment
from app.services.ai.provider import AIProvider

ExplanationKey = tuple[str, str, str, int | None, str]


def explanation_cache_key(
    provider_name: str,
    model: str,
    finding: NormalizedFinding,
) -> ExplanationKey:
    """
    Clave de caché por categoría/estándar/regla (no por fichero/línea), de modo que
    hallazgos equivalentes comparten explicación y son reproducibles (ADR-003).
    """
    return (
        provider_name,
        model,
        finding.mvp_category,
        finding.cwe_id,
        finding.source_rule_id,
    )


class ExplanationCache:
    """Caché en memoria de explicaciones IA, válida durante un escaneo."""

    def __init__(self) -> None:
        self._store: dict[ExplanationKey, AIExplanation] = {}

    def get(self, key: ExplanationKey) -> AIExplanation | None:
        return self._store.get(key)

    def set(self, key: ExplanationKey, explanation: AIExplanation) -> None:
        self._store[key] = explanation

    def __len__(self) -> int:
        return len(self._store)


def explain_cached(
    provider: AIProvider,
    finding: NormalizedFinding,
    cache: ExplanationCache,
) -> AIExplanation | None:
    """
    Devuelve la explicación del hallazgo usando la caché. En un acierto marca
    `cached=True`; en un fallo llama al proveedor y guarda el resultado. Si el
    proveedor devuelve None (degradación), no cachea.
    """
    key = explanation_cache_key(provider.name, provider.model, finding)
    hit = cache.get(key)
    if hit is not None:
        return replace(
            apply_finding_enrichment(hit, finding),
            cached=True,
        )
    explanation = provider.explain(finding)
    if explanation is None:
        return None
    enriched = apply_finding_enrichment(explanation, finding)
    cache.set(key, enriched)
    return enriched
