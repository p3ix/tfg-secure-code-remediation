from __future__ import annotations

import re

from app.models.remediation import RemediationProposal


DEBUG_TRUE_PATTERN = re.compile(r"\bdebug\s*=\s*True\b")


def propose_flask_debug_remediation(source_code: str) -> RemediationProposal:
    has_flask = "Flask" in source_code or "app.run(" in source_code
    match = DEBUG_TRUE_PATTERN.search(source_code)

    if not has_flask or match is None:
        return RemediationProposal(
            remediation_kind="flask_debug_true",
            applicable=False,
            confidence="low",
            summary="No se ha encontrado un patrón simple de debug=True remediable automáticamente.",
            rationale=(
                "La primera versión del remediador solo cubre casos simples de "
                "app.run(..., debug=True) en aplicaciones Flask."
            ),
            verification_hint=(
                "Revisar manualmente el caso o ampliar el remediador para cubrir "
                "patrones más complejos."
            ),
        )

    original_snippet = match.group(0)
    proposed_snippet = "debug=False"
    changed_content = source_code.replace(original_snippet, proposed_snippet, 1)

    return RemediationProposal(
        remediation_kind="flask_debug_true",
        applicable=True,
        confidence="high",
        summary="Se propone sustituir debug=True por debug=False.",
        rationale=(
            "El patrón detectado activa explícitamente el modo debug de Flask. "
            "En el contexto del MVP, sustituir debug=True por debug=False es una "
            "remediación conservadora y coherente con el objetivo de evitar exposición "
            "del depurador y configuraciones inseguras."
        ),
        original_snippet=original_snippet,
        proposed_snippet=proposed_snippet,
        changed_content=changed_content,
        verification_hint=(
            "Reejecutar Bandit y Semgrep y comprobar que el hallazgo de tipo "
            "flask_debug_true desaparece."
        ),
    )
