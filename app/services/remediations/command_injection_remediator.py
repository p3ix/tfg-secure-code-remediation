from __future__ import annotations

import re

from app.models.remediation import RemediationProposal


SHELL_TRUE_PATTERN = re.compile(
    r"(?P<prefix>subprocess\.(?:run|call|Popen)\()"
    r"(?P<cmd>[^,]+),\s*shell\s*=\s*True"
    r"(?P<rest>[^)]*)\)"
)

OS_SYSTEM_PATTERN = re.compile(
    r"os\.system\((?P<cmd>[^)]+)\)"
)


def _ensure_import(source: str, module: str) -> str:
    if f"import {module}" in source:
        return source
    lines = source.split("\n")
    last_import_idx = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            last_import_idx = i
    if last_import_idx >= 0:
        lines.insert(last_import_idx + 1, f"import {module}")
    else:
        lines.insert(0, f"import {module}")
    return "\n".join(lines)


def _propose_shell_true_remediation(
    source_code: str,
    match: re.Match[str],
) -> RemediationProposal:
    original_snippet = match.group(0)
    prefix = match.group("prefix")
    cmd = match.group("cmd").strip()
    rest = match.group("rest")

    proposed_snippet = f"{prefix}shlex.split({cmd}), shell=False{rest})"
    changed_content = source_code.replace(original_snippet, proposed_snippet, 1)
    changed_content = _ensure_import(changed_content, "shlex")

    return RemediationProposal(
        remediation_kind="command_injection",
        applicable=True,
        confidence="high",
        summary=(
            "Se propone eliminar shell=True y usar shlex.split para evitar "
            "inyección de comandos vía intérprete de shell."
        ),
        rationale=(
            "El uso de shell=True pasa la cadena a un intérprete de shell, "
            "lo que permite que metacaracteres como ; | && sean interpretados. "
            "Sustituir por shell=False con shlex.split elimina ese vector "
            "en el contexto acotado del MVP."
        ),
        original_snippet=original_snippet,
        proposed_snippet=proposed_snippet,
        changed_content=changed_content,
        verification_hint=(
            "Reejecutar Bandit y Semgrep y comprobar que desaparece el hallazgo "
            "de command_injection asociado a shell=True (B602)."
        ),
    )


def _propose_os_system_remediation(
    source_code: str,
    match: re.Match[str],
) -> RemediationProposal:
    original_snippet = match.group(0)
    cmd = match.group("cmd").strip()

    proposed_snippet = f"subprocess.run(shlex.split({cmd}), check=False)"
    changed_content = source_code.replace(original_snippet, proposed_snippet, 1)
    changed_content = _ensure_import(changed_content, "shlex")
    changed_content = _ensure_import(changed_content, "subprocess")

    return RemediationProposal(
        remediation_kind="command_injection",
        applicable=True,
        confidence="high",
        summary=(
            "Se propone sustituir os.system por subprocess.run con shlex.split "
            "para evitar inyección de comandos vía shell."
        ),
        rationale=(
            "os.system ejecuta siempre a través de un intérprete de shell, "
            "lo que permite inyección de comandos mediante metacaracteres. "
            "Sustituir por subprocess.run con lista de argumentos elimina "
            "ese vector en el contexto acotado del MVP."
        ),
        original_snippet=original_snippet,
        proposed_snippet=proposed_snippet,
        changed_content=changed_content,
        verification_hint=(
            "Reejecutar Bandit y Semgrep y comprobar que desaparece el hallazgo "
            "de command_injection asociado a os.system (B605)."
        ),
    )


def propose_command_injection_remediation(
    source_code: str,
) -> RemediationProposal:
    match = SHELL_TRUE_PATTERN.search(source_code)
    if match:
        return _propose_shell_true_remediation(source_code, match)

    match = OS_SYSTEM_PATTERN.search(source_code)
    if match:
        return _propose_os_system_remediation(source_code, match)

    return RemediationProposal(
        remediation_kind="command_injection",
        applicable=False,
        confidence="low",
        summary=(
            "No se ha encontrado un patrón simple de command injection "
            "remediable automáticamente."
        ),
        rationale=(
            "La primera versión del remediador solo cubre patrones simples "
            "de subprocess con shell=True y os.system con argumentos directos."
        ),
        verification_hint=(
            "Revisar manualmente el caso o ampliar el remediador para cubrir "
            "patrones más complejos."
        ),
    )
