"""Configuración leída del entorno (análisis real, IA, límites)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings:
    """Valores por defecto seguros para desarrollo local; ajustar en despliegue."""

    def __init__(self) -> None:
        self.zip_max_bytes: int = int(os.environ.get("TFG_ZIP_MAX_BYTES", str(20 * 1024 * 1024)))
        self.git_clone_timeout_sec: int = int(os.environ.get("TFG_GIT_CLONE_TIMEOUT", "180"))
        self.git_allowed_hosts: frozenset[str] = frozenset(
            h.strip()
            for h in os.environ.get("TFG_GIT_ALLOWED_HOSTS", "github.com,gitlab.com").split(",")
            if h.strip()
        )
        self.enable_git_clone: bool = os.environ.get("TFG_ENABLE_GIT_CLONE", "1") == "1"
        self.ai_explanations_enabled: bool = os.environ.get("TFG_AI_EXPLANATIONS_ENABLED", "0") == "1"
        _local_root = os.environ.get("TFG_LOCAL_ANALYSIS_ROOT", "").strip()
        self.local_analysis_root: Path | None = (
            Path(_local_root).resolve() if _local_root else None
        )
