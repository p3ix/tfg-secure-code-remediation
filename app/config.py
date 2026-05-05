"""Configuración leída del entorno (análisis real, IA, límites)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

# Bandit `-x` acepta lista separada por comas (globs). Semgrep usa la misma
# lista para generar varios `--exclude` (ver `build_semgrep_command`).
_DEFAULT_ANALYSIS_EXCLUDE_DIRS = (
    ".git,.svn,CVS,.bzr,.hg,node_modules,__pycache__,.venv,venv,.tox,.eggs,"
    "*.egg,dist,build,.mypy_cache,.pytest_cache"
)


def _parse_int_env(name: str, default: int, *, minimum: int | None = None) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"Variable {name} inválida: se esperaba entero y se recibió {raw!r}") from exc
    if minimum is not None and value < minimum:
        raise ValueError(f"Variable {name} inválida: el valor mínimo permitido es {minimum}")
    return value


def _parse_bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(
        f"Variable {name} inválida: usar 1/0, true/false, yes/no u on/off"
    )


def _parse_csv_env(name: str, default: str) -> tuple[str, ...]:
    raw = os.environ.get(name, default)
    values = tuple(v.strip() for v in raw.split(",") if v.strip())
    return values


def _parse_allowed_hosts(name: str, default: str) -> frozenset[str]:
    hosts = set(_parse_csv_env(name, default))
    if not hosts:
        raise ValueError(f"Variable {name} inválida: debe incluir al menos un host")
    normalized: set[str] = set()
    for host in hosts:
        h = host.lower()
        if any(ch.isspace() for ch in h) or "/" in h:
            raise ValueError(f"Variable {name} inválida: host no válido {host!r}")
        normalized.add(h)
    return frozenset(normalized)


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings:
    """Valores por defecto seguros para desarrollo local; ajustar en despliegue."""

    def __init__(self) -> None:
        self.zip_max_bytes: int = _parse_int_env(
            "TFG_ZIP_MAX_BYTES",
            20 * 1024 * 1024,
            minimum=1024,
        )
        self.git_clone_timeout_sec: int = _parse_int_env(
            "TFG_GIT_CLONE_TIMEOUT",
            180,
            minimum=1,
        )
        self.git_allowed_hosts: frozenset[str] = _parse_allowed_hosts(
            "TFG_GIT_ALLOWED_HOSTS",
            "github.com,gitlab.com",
        )
        self.enable_git_clone: bool = _parse_bool_env("TFG_ENABLE_GIT_CLONE", True)
        self.ai_explanations_enabled: bool = _parse_bool_env(
            "TFG_AI_EXPLANATIONS_ENABLED",
            False,
        )
        _local_root = os.environ.get("TFG_LOCAL_ANALYSIS_ROOT", "").strip()
        self.local_analysis_root: Path | None = (
            Path(_local_root).resolve() if _local_root else None
        )
        # Por subproceso (Bandit o Semgrep). 0 = sin límite (solo entornos controlados).
        self.analysis_subprocess_timeout_sec: int = _parse_int_env(
            "TFG_ANALYSIS_TIMEOUT_SEC",
            600,
            minimum=0,
        )
        self.analysis_exclude_patterns: tuple[str, ...] = _parse_csv_env(
            "TFG_ANALYSIS_EXCLUDE_DIRS",
            _DEFAULT_ANALYSIS_EXCLUDE_DIRS,
        )
