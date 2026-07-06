from __future__ import annotations

import re

from app.models.remediation import RemediationProposal

UNSAFE_YAML_LOAD_PATTERN = re.compile(
    r"yaml\.load\(\s*(?P<data>[^,\n]+?)\s*,\s*Loader\s*=\s*yaml\.(?P<loader>Loader|UnsafeLoader|CLoader)\s*\)"
)


def propose_yaml_load_remediation(source_code: str) -> RemediationProposal:
    match = UNSAFE_YAML_LOAD_PATTERN.search(source_code)

    if match is None:
        return RemediationProposal(
            remediation_kind="unsafe_yaml_load",
            applicable=False,
            confidence="low",
            summary="El yaml.load detectado no encaja con el patrón que el remediador sabe reescribir.",
            rationale=(
                "Solo se reescriben llamadas a yaml.load con un Loader inseguro "
                "indicado de forma explícita (Loader=yaml.Loader y equivalentes)."
            ),
            verification_hint=(
                "Revisar el caso a mano o extender la expresión para cubrir "
                "variantes menos directas de yaml.load."
            ),
        )

    original_snippet = match.group(0)
    data_expr = match.group("data").strip()
    proposed_snippet = f"yaml.safe_load({data_expr})"
    changed_content = source_code.replace(original_snippet, proposed_snippet, 1)

    return RemediationProposal(
        remediation_kind="unsafe_yaml_load",
        applicable=True,
        confidence="high",
        summary="Se propone sustituir yaml.load inseguro por yaml.safe_load.",
        rationale=(
            "El patrón detectado usa yaml.load con un loader inseguro explícito. "
            "En este contexto controlado, la sustitución por yaml.safe_load es una "
            "remediación conservadora y coherente con el alcance del MVP."
        ),
        original_snippet=original_snippet,
        proposed_snippet=proposed_snippet,
        changed_content=changed_content,
        verification_hint=(
            "Reejecutar Bandit y Semgrep y comprobar que el hallazgo asociado a "
            "yaml.load inseguro desaparece."
        ),
    )
