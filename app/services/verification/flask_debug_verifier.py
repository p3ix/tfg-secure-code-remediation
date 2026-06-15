from __future__ import annotations

from typing import Any

from app.services.remediations.flask_debug_remediator import (
    propose_flask_debug_remediation,
)
from app.services.verification._common import verify_remediation


def verify_flask_debug_remediation(source_code: str) -> dict[str, Any]:
    return verify_remediation(
        source_code,
        kind="flask_debug_true",
        propose_fn=propose_flask_debug_remediation,
    )
