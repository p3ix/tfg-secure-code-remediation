from __future__ import annotations

from typing import Any

from app.services.remediations.verify_false_remediator import (
    propose_verify_false_remediation,
)
from app.services.verification._common import verify_remediation


def verify_verify_false_remediation(source_code: str) -> dict[str, Any]:
    return verify_remediation(
        source_code,
        kind="verify_false",
        propose_fn=propose_verify_false_remediation,
        include_other_categories=True,
    )
