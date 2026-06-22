from __future__ import annotations

from dataclasses import replace

from app.models.ai_explanation import AIExplanation
from app.models.finding import NormalizedFinding

_CODE_FOCUS_MAX_LEN = 500


def build_location_hint(finding: NormalizedFinding) -> str:
    """Referencia legible a fichero y línea del hallazgo."""
    if finding.line_end is not None and finding.line_end != finding.line_start:
        return f"{finding.file_path}:{finding.line_start}-{finding.line_end}"
    return f"{finding.file_path}:{finding.line_start}"


def build_code_focus(finding: NormalizedFinding) -> str | None:
    """
    Fragmento relevante desde el parser (snippet) o, en su defecto, el mensaje crudo.
    No depende del modelo de IA.
    """
    if finding.code_snippet and finding.code_snippet.strip():
        text = finding.code_snippet.strip()
    elif finding.raw_message and finding.raw_message.strip():
        text = finding.raw_message.strip()
    else:
        return None
    if len(text) > _CODE_FOCUS_MAX_LEN:
        return text[: _CODE_FOCUS_MAX_LEN - 1] + "…"
    return text


def apply_finding_enrichment(
    explanation: AIExplanation,
    finding: NormalizedFinding,
) -> AIExplanation:
    """Añade ubicación y fragmento del hallazgo actual (incluso en aciertos de caché)."""
    return replace(
        explanation,
        location_hint=build_location_hint(finding),
        code_focus=build_code_focus(finding),
    )
