from __future__ import annotations

import logging

from app.config import Settings, get_settings
from app.services.ai.ollama_provider import OllamaProvider
from app.services.ai.provider import AIProvider
from app.services.ai.stub_provider import StubProvider

logger = logging.getLogger(__name__)


def get_ai_provider(settings: Settings | None = None) -> AIProvider | None:
    """
    Resuelve el proveedor de IA según la configuración (ADR-003).

    Devuelve None (capa desactivada / degradación) cuando:
    - `TFG_AI_EXPLANATIONS_ENABLED` está desactivado, o
    - el proveedor configurado aún no está implementado en esta fase.

    El resto del sistema trata None como "sin explicación", sin romper el análisis.
    """
    s = settings or get_settings()
    if not s.ai_explanations_enabled:
        return None

    if s.ai_provider == "stub":
        return StubProvider()

    if s.ai_provider == "ollama":
        return OllamaProvider(
            url=s.ai_ollama_url,
            model=s.ai_model,
            timeout_sec=float(s.ai_timeout_sec),
            include_snippet=s.ai_include_snippet,
        )

    # Proveedor API opcional (openai) aún no implementado.
    logger.warning(
        "Proveedor de IA '%s' no implementado todavía; la capa IA queda inactiva.",
        s.ai_provider,
    )
    return None
