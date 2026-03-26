from __future__ import annotations

import re

from app.models.remediation import RemediationProposal


VERIFY_FALSE_PATTERN = re.compile(r"\bverify\s*=\s*False\b")


def propose_verify_false_remediation(source_code: str) -> RemediationProposal:
    has_http_client = "requests." in source_code or "httpx." in source_code
    match = VERIFY_FALSE_PATTERN.search(source_code)

    if not has_http_client or match is None:
        return RemediationProposal(
            remediation_kind="verify_false",
            applicable=False,
            confidence="low",
            summary="No se ha encontrado un patrón simple de verify=False remediable automáticamente.",
            rationale=(
                "La primera versión del remediador solo cubre casos simples de "
                "peticiones con requests o httpx donde aparece verify=False de forma explícita."
            ),
            verification_hint=(
                "Revisar manualmente el caso o ampliar el remediador para cubrir "
                "patrones más complejos."
            ),
        )

    original_snippet = match.group(0)
    proposed_snippet = "verify=True"
    changed_content = source_code.replace(original_snippet, proposed_snippet, 1)

    return RemediationProposal(
        remediation_kind="verify_false",
        applicable=True,
        confidence="high",
        summary="Se propone sustituir verify=False por verify=True.",
        rationale=(
            "El patrón detectado desactiva explícitamente la validación TLS. "
            "En este contexto controlado del MVP, sustituir verify=False por "
            "verify=True es una remediación conservadora y coherente con el objetivo "
            "de restaurar la validación de certificados."
        ),
        original_snippet=original_snippet,
        proposed_snippet=proposed_snippet,
        changed_content=changed_content,
        verification_hint=(
            "Reejecutar Bandit y Semgrep y comprobar que el hallazgo de tipo "
            "verify_false desaparece. Tener en cuenta que pueden quedar otros "
            "hallazgos no relacionados, como missing_timeout."
        ),
    )
