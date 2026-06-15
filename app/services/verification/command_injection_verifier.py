from __future__ import annotations

from typing import Any

from app.services.remediations.command_injection_remediator import (
    propose_command_injection_remediation,
)
from app.services.verification._common import verify_remediation


def verify_command_injection_remediation(source_code: str) -> dict[str, Any]:
    return verify_remediation(
        source_code,
        kind="command_injection",
        propose_fn=propose_command_injection_remediation,
    )
