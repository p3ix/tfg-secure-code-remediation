from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AIExplanation:
    """
    Explicación asistida por IA de un hallazgo (ADR-003).

    No contiene parches de código: solo texto educativo y una sugerencia de
    remediación en lenguaje natural. La remediación verificada sigue siendo
    responsabilidad de los remediators deterministas.
    """

    summary: str
    risk: str
    suggestion: str
    provider: str
    model: str
    prompt_version: str
    prompt_hash: str | None = None
    cached: bool = False

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
        }
