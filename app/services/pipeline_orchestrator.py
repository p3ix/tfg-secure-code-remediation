from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from app.models.finding import NormalizedFinding


def build_pipeline_view(findings: list[NormalizedFinding]) -> dict[str, Any]:
    """
    Vista unificada post-clasificación: conteos y agrupación por categoría MVP.

    Encaja el paso detect → classify del flujo; la remediación y verificación
    van aparte (ver run_mvp_autofix_verification_roundtrip).
    """
    counts_by_cat = Counter(f.mvp_category for f in findings)
    counts_by_mode = Counter(f.remediation_mode for f in findings)

    by_category: dict[str, list[dict[str, Any]]] = {}
    for f in findings:
        by_category.setdefault(f.mvp_category, []).append(asdict(f))

    return {
        "pipeline_step": "classified",
        "total_findings": len(findings),
        "counts_by_mvp_category": dict(sorted(counts_by_cat.items())),
        "counts_by_remediation_mode": dict(sorted(counts_by_mode.items())),
        "findings_by_mvp_category": dict(sorted(by_category.items())),
    }


MVP_AUTOFIX_FIXTURES: dict[str, list[Path]] = {
    "unsafe_yaml_load": [Path("fixtures/mvp/unsafe_yaml_load/vuln_yaml_load.py")],
    "verify_false": [Path("fixtures/mvp/https_verify_false/vuln_requests_verify_false.py")],
    "flask_debug_true": [Path("fixtures/mvp/flask_debug_true/vuln_flask_debug_true.py")],
    "missing_timeout": [Path("fixtures/mvp/missing_timeout/vuln_requests_no_timeout.py")],
    "command_injection": [
        Path("fixtures/mvp/command_injection/vuln_shell_true.py"),
        Path("fixtures/mvp/command_injection/vuln_os_system.py"),
    ],
}


def _load_verifier_map() -> dict[str, Callable[[str], dict[str, Any]]]:
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

    return {
        "unsafe_yaml_load": verify_yaml_load_remediation,
        "verify_false": verify_verify_false_remediation,
        "flask_debug_true": verify_flask_debug_remediation,
        "missing_timeout": verify_requests_timeout_remediation,
        "command_injection": verify_command_injection_remediation,
    }


def run_mvp_autofix_verification_roundtrip() -> dict[str, Any]:
    """
    Ejecuta el ciclo repair → verify sobre los fixtures canónicos del MVP
    (solo categorías autofix_candidate). sql_injection queda fuera por diseño.
    """
    verifiers = _load_verifier_map()
    results: dict[str, Any] = {
        "pipeline_step": "mvp_autofix_verify",
        "categories": {},
    }

    for category, paths in sorted(MVP_AUTOFIX_FIXTURES.items()):
        verify_fn = verifiers[category]
        per_file: list[dict[str, Any]] = []
        for rel_path in paths:
            if not rel_path.exists():
                per_file.append(
                    {
                        "fixture": str(rel_path),
                        "error": "fixture no encontrado",
                    }
                )
                continue
            source = rel_path.read_text(encoding="utf-8")
            per_file.append(
                {
                    "fixture": str(rel_path),
                    "verification": verify_fn(source),
                }
            )
        results["categories"][category] = per_file

    return results
