from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.models.ai_explanation import AIExplanation
from app.models.finding import NormalizedFinding

PROMPT_VERSION = "v3"


@runtime_checkable
class AIProvider(Protocol):
    """
    Contrato de un proveedor de explicaciones (ADR-003).

    Implementaciones previstas: StubProvider (determinista, tests/CI),
    OllamaProvider (local, por defecto en uso real) y un proveedor API opcional.

    `explain` debe ser degradable: si no puede generar una explicación, devuelve
    None en lugar de propagar una excepción que tumbe el análisis.
    """

    name: str
    model: str

    def explain(self, finding: NormalizedFinding) -> AIExplanation | None:
        ...
