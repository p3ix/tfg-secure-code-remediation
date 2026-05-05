from __future__ import annotations

import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from shutil import which
from typing import Any

from app.services.findings_loader import load_all_findings
from app.services.findings_mapper import enrich_findings_with_classification
from app.services.pipeline_orchestrator import build_pipeline_view

FIXTURES_TARGET = Path("fixtures/mvp")
RUNTIME_REPORTS_DIR = Path("reports/runtime")
BANDIT_RUNTIME_REPORT = RUNTIME_REPORTS_DIR / "fixtures-mvp-bandit-runtime.json"
SEMGREP_RUNTIME_REPORT = RUNTIME_REPORTS_DIR / "fixtures-mvp-semgrep-runtime.json"


def _resolve_tool_command(binary_name: str, module_name: str) -> list[str]:
    """
    Prefiere binario en PATH; si no está, usa `python -m <module>`.
    """
    if which(binary_name):
        return [binary_name]
    return [sys.executable, "-m", module_name]


def build_bandit_command(target_path: str | Path, output_path: str | Path) -> list[str]:
    from app.config import get_settings

    merged = ",".join(get_settings().analysis_exclude_patterns)
    cmd = [
        *_resolve_tool_command("bandit", "bandit"),
        "-c",
        "pyproject.toml",
        "-r",
        str(target_path),
    ]
    if merged:
        cmd.extend(["-x", merged])
    cmd.extend(["-f", "json", "-o", str(output_path)])
    return cmd


def _semgrep_exclude_cli_args() -> list[str]:
    """Patrones desde `TFG_ANALYSIS_EXCLUDE_DIRS` como flags --exclude de Semgrep."""
    from app.config import get_settings

    args: list[str] = []
    for p in get_settings().analysis_exclude_patterns:
        if "*" in p:
            args.append(f"--exclude={p}")
        else:
            args.append(f"--exclude=**/{p}/**")
    return args


def build_semgrep_command(target_path: str | Path, output_path: str | Path) -> list[str]:
    cmd = [
        *_resolve_tool_command("semgrep", "semgrep"),
        "scan",
        "--config",
        "p/default",
        "--metrics",
        "off",
    ]
    cmd.extend(_semgrep_exclude_cli_args())
    cmd.extend(
        [
            "--json-output",
            str(output_path),
            str(target_path),
        ]
    )
    return cmd


def run_command(
    command: list[str],
    *,
    timeout_sec: float | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_sec,
    )


def _preview_output(text: str, limit: int = 600) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit] + "...(truncado)"


def run_analysis_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """
    Ejecuta Bandit o Semgrep con el límite de tiempo global (`TFG_ANALYSIS_TIMEOUT_SEC`).
    """
    from app.config import get_settings

    limit = get_settings().analysis_subprocess_timeout_sec
    timeout_sec = None if limit <= 0 else float(limit)
    try:
        return run_command(command, timeout_sec=timeout_sec)
    except FileNotFoundError as exc:
        tool = command[0] if command else "herramienta"
        raise RuntimeError(
            f"No se pudo ejecutar {tool}: comando no encontrado en PATH"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        tool = command[0] if command else "herramienta"
        raise RuntimeError(
            f"{tool} superó el tiempo límite ({limit}s). "
            "Ajustar TFG_ANALYSIS_TIMEOUT_SEC o reducir el árbol analizado."
        ) from exc


def analyze_fixtures_runtime() -> dict[str, Any]:
    if not FIXTURES_TARGET.exists():
        raise FileNotFoundError(f"Analysis target not found: {FIXTURES_TARGET}")

    RUNTIME_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    bandit_cmd = build_bandit_command(FIXTURES_TARGET, BANDIT_RUNTIME_REPORT)
    semgrep_cmd = build_semgrep_command(FIXTURES_TARGET, SEMGREP_RUNTIME_REPORT)

    bandit_result = run_analysis_command(bandit_cmd)
    semgrep_result = run_analysis_command(semgrep_cmd)

    if not BANDIT_RUNTIME_REPORT.exists():
        raise RuntimeError(
            "Bandit execution did not produce the expected runtime report."
        )

    if not SEMGREP_RUNTIME_REPORT.exists():
        raise RuntimeError(
            "Semgrep execution did not produce the expected runtime report."
        )

    findings = load_all_findings(
        bandit_report_path=BANDIT_RUNTIME_REPORT,
        semgrep_report_path=SEMGREP_RUNTIME_REPORT,
    )
    enriched_findings = enrich_findings_with_classification(findings)

    return {
        "analysis_target": str(FIXTURES_TARGET),
        "execution_mode": "runtime",
        "generated_reports": {
            "bandit": str(BANDIT_RUNTIME_REPORT),
            "semgrep": str(SEMGREP_RUNTIME_REPORT),
        },
        "tool_runs": {
            "bandit": {
                "returncode": bandit_result.returncode,
                "command": bandit_cmd,
                "stderr_preview": _preview_output(bandit_result.stderr),
            },
            "semgrep": {
                "returncode": semgrep_result.returncode,
                "command": semgrep_cmd,
                "stderr_preview": _preview_output(semgrep_result.stderr),
            },
        },
        "total_findings": len(enriched_findings),
        "findings": [asdict(finding) for finding in enriched_findings],
        "pipeline": build_pipeline_view(enriched_findings),
    }
