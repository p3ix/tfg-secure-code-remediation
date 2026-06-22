from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import get_settings
from app.services.analysis_service import analyze_fixtures_reports
from app.services.project_scan_service import (
    PayloadTooLargeError,
    analyze_local_path_relative,
    analyze_zip_bytes,
    clone_and_analyze_repo,
)
from app.services.runtime_analysis_service import analyze_fixtures_runtime

if TYPE_CHECKING:
    from fastapi import UploadFile

REAL_ANALYSIS_MODES = frozenset({"upload_zip", "git_clone", "local_path"})
LEGACY_DEMO_MODES = frozenset({"fixture_reports", "fixture_runtime"})

_ALLOWED_ZIP_CONTENT_TYPES = {
    "application/zip",
    "application/x-zip-compressed",
    "application/octet-stream",
}


def looks_like_zip(content: bytes) -> bool:
    return content.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"))


async def execute_web_analysis(
    *,
    analysis_mode: str,
    analysis_id: str,
    local_path: str = "",
    git_url: str = "",
    file: UploadFile | None = None,
    allow_demo_modes: bool = False,
) -> dict:
    """
    Ejecuta un análisis web y devuelve el payload interno (sin presentable).

    Por defecto solo modos reales; `allow_demo_modes=True` para rutas legacy `/dashboard`.
    """
    if analysis_mode in LEGACY_DEMO_MODES:
        if not allow_demo_modes:
            raise ValueError(
                f"Modo de análisis no disponible en la interfaz v2: {analysis_mode}"
            )
        if analysis_mode == "fixture_reports":
            return analyze_fixtures_reports()
        return analyze_fixtures_runtime(analysis_id=analysis_id)

    if analysis_mode == "upload_zip":
        if file is None or not file.filename:
            raise ValueError("Selecciona un fichero ZIP antes de lanzar el análisis.")
        if not file.filename.lower().endswith(".zip"):
            raise ValueError("El fichero seleccionado debe terminar en .zip")
        if file.content_type and file.content_type not in _ALLOWED_ZIP_CONTENT_TYPES:
            raise ValueError(
                "Tipo de contenido no permitido para ZIP. "
                f"Recibido: {file.content_type}"
            )
        content = await file.read()
        if not content:
            raise ValueError("El fichero ZIP está vacío")
        if not looks_like_zip(content):
            raise ValueError("El contenido subido no tiene firma ZIP válida")
        return analyze_zip_bytes(content, analysis_id=analysis_id)

    if analysis_mode == "local_path":
        settings = get_settings()
        if not settings.enable_local_path:
            raise PermissionError(
                "Análisis por ruta local desactivado (TFG_ENABLE_LOCAL_PATH=0). "
                "Activar solo en entornos controlados."
            )
        if settings.local_analysis_root is None:
            raise PermissionError(
                "El análisis por ruta local está desactivado en este entorno."
            )
        if not local_path.strip():
            raise ValueError("Indica una ruta relativa para el modo local_path")
        return analyze_local_path_relative(
            local_path,
            allowed_root=settings.local_analysis_root,
            analysis_id=analysis_id,
        )

    if analysis_mode == "git_clone":
        settings = get_settings()
        if not settings.enable_git_clone:
            raise PermissionError(
                "El análisis por git clone está desactivado en este entorno."
            )
        if not git_url.strip():
            raise ValueError("Indica una URL HTTPS para el modo git_clone")
        return clone_and_analyze_repo(git_url.strip(), analysis_id=analysis_id)

    raise ValueError(f"Modo de análisis no soportado: {analysis_mode}")


__all__ = [
    "REAL_ANALYSIS_MODES",
    "LEGACY_DEMO_MODES",
    "execute_web_analysis",
    "looks_like_zip",
    "PayloadTooLargeError",
]
