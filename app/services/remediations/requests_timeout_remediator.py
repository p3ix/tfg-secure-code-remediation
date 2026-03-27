from __future__ import annotations

import re

from app.models.remediation import RemediationProposal


REQUESTS_CALL_PATTERN = re.compile(
    r"(?P<call>requests\.(get|post|put|delete|patch|head|options)\((?P<args>.*?)\))",
    re.DOTALL,
)


def propose_requests_timeout_remediation(source_code: str) -> RemediationProposal:
    for match in REQUESTS_CALL_PATTERN.finditer(source_code):
        full_call = match.group("call")
        args = match.group("args")

        if "timeout=" in args:
            continue

        proposed_call = f"{full_call[:-1]}, timeout=10)"
        changed_content = source_code.replace(full_call, proposed_call, 1)

        return RemediationProposal(
            remediation_kind="missing_timeout",
            applicable=True,
            confidence="high",
            summary="Se propone añadir timeout explícito a la llamada requests.",
            rationale=(
                "La documentación oficial de Requests recomienda usar el parámetro "
                "`timeout` en prácticamente todo código de producción y advierte de que, "
                "si no se especifica, la petición puede quedarse esperando indefinidamente."
            ),
            original_snippet=full_call,
            proposed_snippet=proposed_call,
            changed_content=changed_content,
            verification_hint=(
                "Reejecutar Bandit y comprobar que desaparece el hallazgo de tipo "
                "`missing_timeout` asociado a la llamada requests."
            ),
        )

    return RemediationProposal(
        remediation_kind="missing_timeout",
        applicable=False,
        confidence="low",
        summary="No se ha encontrado un patrón simple de requests sin timeout remediable automáticamente.",
        rationale=(
            "La primera versión del remediador solo cubre llamadas simples de `requests` "
            "sin parámetro `timeout`."
        ),
        verification_hint=(
            "Revisar manualmente el caso o ampliar el remediador para cubrir patrones más complejos."
        ),
    )
