"""
Escaneo Bandit + Semgrep sobre un directorio arbitrario (proyectos reales).

Usado por subida ZIP y clonado Git. Los informes temporales no se persisten
en `reports/runtime/` para evitar colisiones entre peticiones.
"""

from __future__ import annotations

import io
import subprocess
import tempfile
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.config import get_settings
from app.services.findings_loader import load_all_findings
from app.services.findings_mapper import enrich_findings_with_classification
from app.services.pipeline_orchestrator import build_pipeline_view
from app.services.runtime_analysis_service import (
    build_bandit_command,
    build_semgrep_command,
    run_command,
)


def _validate_https_git_url(url: str, allowed_hosts: frozenset[str]) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("La URL del repositorio debe usar https://")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("URL inválida: sin hostname")
    if host not in allowed_hosts:
        raise ValueError(
            f"Host no permitido: {host}. Configurar TFG_GIT_ALLOWED_HOSTS si es necesario."
        )


def extract_zip_safely(zip_bytes: bytes, dest: Path, *, max_uncompressed_bytes: int) -> None:
    """
    Extrae un ZIP bajo `dest` comprobando path traversal y límite de tamaño descomprimido.
    """
    written = 0
    base = dest.resolve()
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            target = (dest / info.filename).resolve()
            if not target.is_relative_to(base):
                raise ValueError(f"Ruta sospechosa en el ZIP: {info.filename!r}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src, open(target, "wb") as out:
                while True:
                    chunk = src.read(65536)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_uncompressed_bytes:
                        raise ValueError(
                            f"Contenido descomprimido supera el límite ({max_uncompressed_bytes} bytes)"
                        )
                    out.write(chunk)


def analyze_directory(
    target: Path,
    *,
    analysis_target_label: str,
) -> dict[str, Any]:
    """
    Ejecuta Bandit y Semgrep sobre `target` (directorio) y devuelve el mismo
    tipo de payload que `analyze_fixtures_runtime`.
    """
    root = target.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"No es un directorio: {root}")

    with tempfile.TemporaryDirectory(prefix="tfg-scan-") as td:
        td_path = Path(td)
        bandit_report = td_path / "bandit.json"
        semgrep_report = td_path / "semgrep.json"
        bandit_cmd = build_bandit_command(root, bandit_report)
        semgrep_cmd = build_semgrep_command(root, semgrep_report)

        bandit_result = run_command(bandit_cmd)
        semgrep_result = run_command(semgrep_cmd)

        if not bandit_report.exists():
            raise RuntimeError(
                "Bandit no generó informe. Comprueba que está instalado y que el directorio es analizable."
            )
        if not semgrep_report.exists():
            raise RuntimeError(
                "Semgrep no generó informe. Comprueba red/reglas si aplica."
            )

        findings = load_all_findings(
            bandit_report_path=bandit_report,
            semgrep_report_path=semgrep_report,
        )
        enriched = enrich_findings_with_classification(findings)

        return {
            "analysis_target": analysis_target_label,
            "execution_mode": "runtime",
            "generated_reports": {
                "bandit": "(temporal, no persistido)",
                "semgrep": "(temporal, no persistido)",
            },
            "tool_runs": {
                "bandit": {
                    "returncode": bandit_result.returncode,
                    "command": bandit_cmd,
                },
                "semgrep": {
                    "returncode": semgrep_result.returncode,
                    "command": semgrep_cmd,
                },
            },
            "total_findings": len(enriched),
            "findings": [asdict(f) for f in enriched],
            "pipeline": build_pipeline_view(enriched),
        }


def analyze_zip_bytes(zip_bytes: bytes) -> dict[str, Any]:
    settings = get_settings()
    if len(zip_bytes) > settings.zip_max_bytes:
        raise ValueError(
            f"ZIP demasiado grande (máx. {settings.zip_max_bytes} bytes). "
            "Ajustar TFG_ZIP_MAX_BYTES si es necesario."
        )
    max_uncompressed = min(settings.zip_max_bytes * 5, 100 * 1024 * 1024)
    with tempfile.TemporaryDirectory(prefix="tfg-unzip-") as td:
        dest = Path(td) / "src"
        dest.mkdir(parents=True)
        extract_zip_safely(zip_bytes, dest, max_uncompressed_bytes=max_uncompressed)
        label = "upload.zip (contenido extraído)"
        return analyze_directory(dest, analysis_target_label=label)


def clone_and_analyze_repo(url: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.enable_git_clone:
        raise PermissionError(
            "Clonado Git desactivado (TFG_ENABLE_GIT_CLONE=0). Activar solo en entornos de confianza."
        )
    _validate_https_git_url(url, settings.git_allowed_hosts)

    with tempfile.TemporaryDirectory(prefix="tfg-git-") as td:
        clone_dir = Path(td) / "repo"
        cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            url,
            str(clone_dir),
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.git_clone_timeout_sec,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"git clone falló ({proc.returncode}): {proc.stderr or proc.stdout}"
            )
        if not clone_dir.is_dir():
            raise RuntimeError("Clonado incompleto: no existe el directorio del repositorio.")

        out = analyze_directory(clone_dir, analysis_target_label=f"git:{url}")
        out["meta"] = {
            "clone_url": url,
            "git_returncode": proc.returncode,
        }
        return out
