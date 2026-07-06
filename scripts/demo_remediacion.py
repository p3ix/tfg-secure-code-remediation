#!/usr/bin/env python3
"""
Demo en vivo de la remediación determinista del MVP (detecta -> corrige -> reverifica).

Recorre los fixtures canónicos de autofix y, para cada uno, muestra:
  1. El fragmento vulnerable (antes).
  2. La propuesta de remediación determinista (después).
  3. El resultado de la verificación: se reejecutan Bandit + Semgrep sobre el
     código parcheado y se comprueba que el hallazgo de la categoría desaparece.

La remediación NO ocurre en el dashboard web (que se detiene en detección,
clasificación y explicación IA); vive en esta vía aparte del MVP, por diseño.
sql_injection queda fuera del autofix a propósito (solo detección y propuesta).

Uso (desde la raíz del repositorio, con el entorno virtual activo):

    python -m scripts.demo_remediacion
    # o bien
    python scripts/demo_remediacion.py

Requiere Bandit y Semgrep instalados (entorno Linux o WSL; en Windows nativo
Semgrep no funciona de forma fiable).
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.models.remediation import RemediationProposal
from app.services.pipeline_orchestrator import MVP_AUTOFIX_FIXTURES
from app.services.remediations.command_injection_remediator import (
    propose_command_injection_remediation,
)
from app.services.remediations.flask_debug_remediator import (
    propose_flask_debug_remediation,
)
from app.services.remediations.requests_timeout_remediator import (
    propose_requests_timeout_remediation,
)
from app.services.remediations.verify_false_remediator import (
    propose_verify_false_remediation,
)
from app.services.remediations.yaml_load_remediator import (
    propose_yaml_load_remediation,
)
from app.services.verification.command_injection_verifier import (
    verify_command_injection_remediation,
)
from app.services.verification.flask_debug_verifier import (
    verify_flask_debug_remediation,
)
from app.services.verification.requests_timeout_verifier import (
    verify_requests_timeout_remediation,
)
from app.services.verification.verify_false_verifier import (
    verify_verify_false_remediation,
)
from app.services.verification.yaml_load_verifier import verify_yaml_load_remediation

# Cada categoría MVP con su remediador (propone el cambio) y su verificador
# (reanaliza el código parcheado). Las claves coinciden con MVP_AUTOFIX_FIXTURES.
REMEDIATORS: dict[str, Callable[[str], RemediationProposal]] = {
    "unsafe_yaml_load": propose_yaml_load_remediation,
    "verify_false": propose_verify_false_remediation,
    "flask_debug_true": propose_flask_debug_remediation,
    "missing_timeout": propose_requests_timeout_remediation,
    "command_injection": propose_command_injection_remediation,
}

VERIFIERS: dict[str, Callable[[str], dict[str, Any]]] = {
    "unsafe_yaml_load": verify_yaml_load_remediation,
    "verify_false": verify_verify_false_remediation,
    "flask_debug_true": verify_flask_debug_remediation,
    "missing_timeout": verify_requests_timeout_remediation,
    "command_injection": verify_command_injection_remediation,
}

# Colores ANSI (se desactivan si la salida no es un terminal, p. ej. al redirigir).
_TTY = sys.stdout.isatty()


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _TTY else text


def _bold(text: str) -> str:
    return _c(text, "1")


def _green(text: str) -> str:
    return _c(text, "32")


def _red(text: str) -> str:
    return _c(text, "31")


def _cyan(text: str) -> str:
    return _c(text, "36")


def _print_case(category: str, fixture: Path) -> bool:
    """Muestra antes/después/verificación de un fixture. Devuelve True si verified."""
    print()
    print(_bold(f"  Categoría: {_cyan(category)}   ·   Fixture: {fixture.name}"))
    print("  " + "-" * 68)

    if not fixture.exists():
        print(_red(f"  [!] Fixture no encontrado: {fixture}"))
        return False

    source = fixture.read_text(encoding="utf-8")

    proposal = REMEDIATORS[category](source)
    if not proposal.applicable or not proposal.changed_content:
        print(_red("  [!] El remediador no generó una propuesta aplicable."))
        print(f"      {proposal.summary}")
        return False

    print(_bold("  ANTES (vulnerable):"))
    print(f"      {proposal.original_snippet}")
    print(_bold("  DESPUÉS (remediación determinista):"))
    print(f"      {_green(proposal.proposed_snippet or '')}")
    print(f"      confianza: {proposal.confidence}")

    # Verificación real: reejecuta Bandit + Semgrep sobre el código parcheado.
    print("  Reanalizando el código corregido con Bandit + Semgrep...")
    verification = VERIFIERS[category](source)
    verified = bool(verification.get("verified"))
    remaining = verification.get("remaining_findings", [])

    estado = _green("VERIFICADO") if verified else _red("NO VERIFICADO")
    print(f"  Resultado: {_bold(estado)}  ·  hallazgos restantes de la categoría: {len(remaining)}")
    print(f"      {verification.get('reason', '')}")
    return verified


def main() -> int:
    print()
    print(_bold("=" * 72))
    print(_bold("  DEMO · Remediación determinista del MVP (detecta -> corrige -> reverifica)"))
    print(_bold("=" * 72))
    print("  El código original NUNCA se modifica: cada parche se aplica sobre una")
    print("  copia temporal y se reanaliza. sql_injection queda fuera por diseño.")

    total = 0
    verified_count = 0
    for category, fixtures in sorted(MVP_AUTOFIX_FIXTURES.items()):
        for fixture in fixtures:
            total += 1
            if _print_case(category, fixture):
                verified_count += 1

    print()
    print(_bold("=" * 72))
    resumen = f"  RESUMEN: {verified_count}/{total} fixtures corregidos y verificados"
    print(_bold(_green(resumen) if verified_count == total else _red(resumen)))
    print(_bold("=" * 72))
    print()

    # Código de salida distinto de 0 si algún fixture no se verificó (útil en CI).
    return 0 if verified_count == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
