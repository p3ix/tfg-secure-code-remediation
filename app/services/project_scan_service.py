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
    run_analysis_command,
)


class PayloadTooLargeError(ValueError):
    """Error de validación cuando la entrada supera un límite de tamaño."""


def _safe_stem(path: str) -> str:
    return path.strip().strip("/")


def _preview_output(text: str, limit: int = 600) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit] + "...(truncado)"


def _validate_analysis_tree_size(
    root: Path,
    *,
    max_files: int,
    max_bytes: int,
) -> None:
    file_count = 0
    total_bytes = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        file_count += 1
        if file_count > max_files:
            raise ValueError(
                f"Árbol demasiado grande: supera el límite de ficheros ({max_files}). "
                "Ajustar TFG_ANALYSIS_MAX_FILES si es necesario."
            )
        try:
            total_bytes += path.stat().st_size
        except OSError:
            # Ignora ficheros inaccesibles puntuales; Bandit/Semgrep los tratarán aparte.
            continue
        if total_bytes > max_bytes:
            raise ValueError(
                f"Árbol demasiado grande: supera el límite de bytes ({max_bytes}). "
                "Ajustar TFG_ANALYSIS_MAX_BYTES si es necesario."
            )


def _validate_https_git_url(url: str, allowed_hosts: frozenset[str]) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("La URL del repositorio debe usar https://")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("URL inválida: sin hostname")
    if parsed.username or parsed.password:
        raise ValueError("URL inválida: no se permiten credenciales embebidas")
    if parsed.query or parsed.fragment:
        raise ValueError("URL inválida: no se permiten query params ni fragment")
    clean_path = _safe_stem(parsed.path)
    if "/" not in clean_path:
        raise ValueError("URL inválida: se esperaba formato https://host/owner/repo(.git)")
    if host not in allowed_hosts:
        raise ValueError(
            f"Host no permitido: {host}. Configurar TFG_GIT_ALLOWED_HOSTS si es necesario."
        )


def extract_zip_safely(
    zip_bytes: bytes,
    dest: Path,
    *,
    max_uncompressed_bytes: int,
    max_entries: int = 10_000,
) -> None:
    """
    Extrae un ZIP bajo `dest` comprobando path traversal y límite de tamaño descomprimido.
    """
    if not zip_bytes:
        raise ValueError("ZIP vacío: no hay contenido para analizar")
    written = 0
    base = dest.resolve()
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError("El archivo subido no es un ZIP válido") from exc
    with zf:
        if not zf.infolist():
            raise ValueError("ZIP vacío: no contiene ficheros")
        if len(zf.infolist()) > max_entries:
            raise ValueError(
                f"ZIP con demasiadas entradas ({len(zf.infolist())}). "
                f"Límite actual: {max_entries}"
            )
        for info in zf.infolist():
            if info.is_dir():
                continue
            if info.compress_size < 0 or info.file_size < 0:
                raise ValueError(f"Entrada ZIP inválida: {info.filename!r}")
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
    settings = get_settings()
    _validate_analysis_tree_size(
        root,
        max_files=settings.analysis_max_files,
        max_bytes=settings.analysis_max_bytes,
    )

    with tempfile.TemporaryDirectory(prefix="tfg-scan-") as td:
        td_path = Path(td)
        bandit_report = td_path / "bandit.json"
        semgrep_report = td_path / "semgrep.json"
        bandit_cmd = build_bandit_command(root, bandit_report)
        semgrep_cmd = build_semgrep_command(root, semgrep_report)

        bandit_result = run_analysis_command(bandit_cmd)
        semgrep_result = run_analysis_command(semgrep_cmd)

        if not bandit_report.exists():
            raise RuntimeError(
                "Bandit no generó informe. "
                f"returncode={bandit_result.returncode}. "
                "Comprueba instalación/configuración y el árbol analizado."
            )
        if not semgrep_report.exists():
            raise RuntimeError(
                "Semgrep no generó informe. "
                f"returncode={semgrep_result.returncode}. "
                "Comprueba red/reglas/configuración si aplica."
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
                    "stderr_preview": _preview_output(bandit_result.stderr),
                },
                "semgrep": {
                    "returncode": semgrep_result.returncode,
                    "command": semgrep_cmd,
                    "stderr_preview": _preview_output(semgrep_result.stderr),
                },
            },
            "total_findings": len(enriched),
            "findings": [asdict(f) for f in enriched],
            "pipeline": build_pipeline_view(enriched),
        }


def resolve_allowed_analysis_path(relative_path: str, allowed_root: Path) -> Path:
    """
    Resuelve una ruta relativa estrictamente bajo ``allowed_root`` (sin ``..``).
    """
    root_res = allowed_root.resolve()
    if not root_res.exists() or not root_res.is_dir():
        raise ValueError("El directorio raíz permitido no existe o no es un directorio válido")
    if not relative_path or relative_path.strip() != relative_path:
        raise ValueError("Ruta relativa inválida")
    if "\\" in relative_path:
        raise ValueError("La ruta relativa no puede contener separadores '\\'")
    p = Path(relative_path)
    if str(p) in {".", ""}:
        raise ValueError("La ruta relativa debe apuntar a un subdirectorio concreto")
    if p.is_absolute():
        raise ValueError("La ruta debe ser relativa al directorio permitido (no rutas absolutas)")
    if ".." in p.parts:
        raise ValueError("La ruta no puede contener componentes '..'")
    target = (root_res / p).resolve()
    try:
        target.relative_to(root_res)
    except ValueError as exc:
        raise ValueError(
            "La ruta debe permanecer bajo el directorio raíz permitido"
        ) from exc
    if not target.is_dir():
        raise FileNotFoundError(f"No es un directorio o no existe: {target}")
    return target


def analyze_local_path_relative(relative_path: str, *, allowed_root: Path) -> dict[str, Any]:
    target = resolve_allowed_analysis_path(relative_path, allowed_root)
    normalized = str(target.relative_to(allowed_root.resolve()))
    label = f"local:{normalized}"
    return analyze_directory(target, analysis_target_label=label)


def analyze_zip_bytes(zip_bytes: bytes) -> dict[str, Any]:
    settings = get_settings()
    if len(zip_bytes) > settings.zip_max_bytes:
        raise PayloadTooLargeError(
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
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.git_clone_timeout_sec,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "No se pudo ejecutar git clone: comando 'git' no disponible en PATH"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                "git clone superó el tiempo límite "
                f"({settings.git_clone_timeout_sec}s)"
            ) from exc
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
            "git_command": cmd,
            "git_stdout_preview": _preview_output(proc.stdout),
            "git_stderr_preview": _preview_output(proc.stderr),
        }
        return out
