from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Any

DEFAULT_SCAN_STORE_TTL_SEC = 3600.0


@dataclass(frozen=True)
class StoredScanResult:
    """Escaneo interno guardado tras un análisis web exitoso (WEB-5 / WEB v2)."""

    internal: dict[str, Any]
    analysis_mode: str
    hide_info: bool
    group_equivalent: bool
    enable_ai_explanations: bool
    stored_at_monotonic: float


class ScanResultStore:
    """
    Almacén efímero en memoria de escaneos internos indexados por analysis_id.

    Permite re-generar solo la capa IA sin repetir Bandit/Semgrep y servir
    `/results/{analysis_id}` sin re-ejecutar SAST. Caduca por TTL (~60 min).
    """

    def __init__(self, *, ttl_sec: float = DEFAULT_SCAN_STORE_TTL_SEC) -> None:
        self._ttl_sec = ttl_sec
        self._entries: dict[str, StoredScanResult] = {}

    def put(
        self,
        analysis_id: str,
        internal: dict[str, Any],
        *,
        analysis_mode: str,
        hide_info: bool = False,
        group_equivalent: bool = False,
        enable_ai_explanations: bool = False,
    ) -> None:
        self._purge_expired()
        self._entries[analysis_id] = StoredScanResult(
            internal=dict(internal),
            analysis_mode=analysis_mode,
            hide_info=hide_info,
            group_equivalent=group_equivalent,
            enable_ai_explanations=enable_ai_explanations,
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

    def mark_ai_enriched(self, analysis_id: str) -> StoredScanResult | None:
        entry = self.get(analysis_id)
        if entry is None:
            return None
        updated = replace(entry, enable_ai_explanations=True)
        self._entries[analysis_id] = updated
        return updated

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
