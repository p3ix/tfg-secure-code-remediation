from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

DEFAULT_SCAN_STORE_TTL_SEC = 3600.0


@dataclass(frozen=True)
class StoredScanResult:
    """Escaneo interno guardado tras un análisis web exitoso (WEB-5)."""

    internal: dict[str, Any]
    analysis_mode: str
    stored_at_monotonic: float


class ScanResultStore:
    """
    Almacén efímero en memoria de escaneos internos indexados por analysis_id.

    Permite re-generar solo la capa IA sin repetir Bandit/Semgrep. Caduca por TTL
    (por defecto 60 minutos); no persiste en disco.
    """

    def __init__(self, *, ttl_sec: float = DEFAULT_SCAN_STORE_TTL_SEC) -> None:
        self._ttl_sec = ttl_sec
        self._entries: dict[str, StoredScanResult] = {}

    def put(self, analysis_id: str, internal: dict[str, Any], *, analysis_mode: str) -> None:
        self._purge_expired()
        self._entries[analysis_id] = StoredScanResult(
            internal=dict(internal),
            analysis_mode=analysis_mode,
            stored_at_monotonic=time.monotonic(),
        )

    def get(self, analysis_id: str) -> StoredScanResult | None:
        self._purge_expired()
        entry = self._entries.get(analysis_id)
        if entry is None:
            return None
        if time.monotonic() - entry.stored_at_monotonic > self._ttl_sec:
            del self._entries[analysis_id]
            return None
        return entry

    def clear(self) -> None:
        self._entries.clear()

    def _purge_expired(self) -> None:
        now = time.monotonic()
        expired = [
            key
            for key, entry in self._entries.items()
            if now - entry.stored_at_monotonic > self._ttl_sec
        ]
        for key in expired:
            del self._entries[key]


_scan_result_store = ScanResultStore()


def get_scan_result_store() -> ScanResultStore:
    return _scan_result_store
