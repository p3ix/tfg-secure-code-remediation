from __future__ import annotations

from typing import Any

from app.services.remediations.yaml_load_remediator import (
    propose_yaml_load_remediation,
)
from app.services.verification._common import verify_remediation


def verify_yaml_load_remediation(source_code: str) -> dict[str, Any]:
    return verify_remediation(
        source_code,
        kind="unsafe_yaml_load",
        propose_fn=propose_yaml_load_remediation,
    )
