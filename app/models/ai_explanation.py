from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AIExplanation:
    """
    Explicación asistida por IA de un hallazgo (ADR-003).

    No contiene parches de código: solo texto educativo y una sugerencia de
    remediación en lenguaje natural. La remediación verificada sigue siendo
    responsabilidad de los remediators deterministas.

    `location_hint` y `code_focus` se derivan del hallazgo normalizado (parser),
    no del modelo. `action_steps` aporta pasos concretos de remediación.

    `example_before` / `example_after` son un ejemplo ilustrativo del patrón
    (fragmento vulnerable → corregido) con fines pedagógicos. Es material educativo
    mostrado en la UI: la IA no aplica ese cambio al proyecto del usuario ni lo
    verifica (la remediación verificada la dan los remediators deterministas).
    """

    summary: str
    risk: str
    suggestion: str
    provider: str
    model: str
    prompt_version: str
    prompt_hash: str | None = None
    cached: bool = False
    location_hint: str | None = None
    code_focus: str | None = None
    action_steps: list[str] | None = None
    example_before: str | None = None
    example_after: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary,
            "risk": self.risk,
            "suggestion": self.suggestion,
            "provider": self.provider,
            "model": self.model,
            "prompt_version": self.prompt_version,
            "prompt_hash": self.prompt_hash,
            "cached": self.cached,
            "location_hint": self.location_hint,
            "code_focus": self.code_focus,
            "action_steps": list(self.action_steps) if self.action_steps else [],
            "example_before": self.example_before,
            "example_after": self.example_after,
        }
