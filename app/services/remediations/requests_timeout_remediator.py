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
        summary="La llamada a requests analizada no encaja con el patrón al que añadir un timeout.",
        rationale=(
            "Se añade timeout únicamente a llamadas directas de `requests` "
            "(get, post, etc.) que aún no lo declaran."
        ),
        verification_hint=(
            "Añadir el timeout a mano si la petición se construye de forma "
            "dinámica o a través de una sesión."
        ),
    )
