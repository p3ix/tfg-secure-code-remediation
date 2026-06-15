from __future__ import annotations

from typing import Any

from app.services.remediations.requests_timeout_remediator import (
    propose_requests_timeout_remediation,
)
from app.services.verification._common import verify_remediation


def verify_requests_timeout_remediation(source_code: str) -> dict[str, Any]:
    return verify_remediation(
        source_code,
        kind="missing_timeout",
        propose_fn=propose_requests_timeout_remediation,
    )
