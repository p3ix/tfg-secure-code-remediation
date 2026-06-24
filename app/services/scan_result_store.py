from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from app.services.ai.cache import ExplanationCache

logger = logging.getLogger(__name__)

DEFAULT_SCAN_STORE_TTL_SEC = 3600.0
_PERSIST_VERSION = 1


@dataclass(frozen=True)
class StoredScanResult:
    """Escaneo interno guardado tras un análisis web exitoso (WEB-5 / WEB v2).

    `created_at` es tiempo de reloj de pared (epoch) para que el TTL sea coherente
    también tras reiniciar el proceso cuando hay persistencia en disco.
    """

    internal: dict[str, Any]
    analysis_mode: str
    hide_info: bool
    group_equivalent: bool
    enable_ai_explanations: bool
    created_at: float


class ScanResultStore:
    """
    Almacén de escaneos internos indexados por analysis_id.

    Permite re-generar solo la capa IA sin repetir Bandit/Semgrep y servir
    `/results/{analysis_id}` sin re-ejecutar SAST. Caduca por TTL.

    Si `storage_dir` es None el almacén es solo en memoria (por defecto). Con un
    directorio, cada análisis se persiste como `{analysis_id}.json` y sobrevive a
    reinicios; se purgan los caducados (TTL) y, si se supera `max_entries`, los más
    antiguos (LRU por fecha de creación).
    """

    def __init__(
        self,
        *,
        ttl_sec: float = DEFAULT_SCAN_STORE_TTL_SEC,
        storage_dir: Path | str | None = None,
        max_entries: int | None = None,
    ) -> None:
        self._ttl_sec = ttl_sec
        self._max_entries = max_entries
        self._entries: dict[str, StoredScanResult] = {}
        # Caché de explicaciones IA por análisis: el enriquecido se hace una vez y
        # se reutiliza en cada render de /results y /report (sin recomputar Ollama).
        self._ai_caches: dict[str, ExplanationCache] = {}
        # Índice ligero analysis_id -> created_at de TODO lo persistido (memoria + disco),
        # para purgar por TTL y aplicar el tope sin recargar los blobs completos.
        self._created: dict[str, float] = {}
        self._storage_dir = Path(storage_dir) if storage_dir is not None else None
        if self._storage_dir is not None:
            self._storage_dir.mkdir(parents=True, exist_ok=True)
            self._index_existing()

    # ------------------------------------------------------------------ API

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
        entry = StoredScanResult(
            internal=dict(internal),
            analysis_mode=analysis_mode,
            hide_info=hide_info,
            group_equivalent=group_equivalent,
            enable_ai_explanations=enable_ai_explanations,
            created_at=time.time(),
        )
        self._entries[analysis_id] = entry
        self._created[analysis_id] = entry.created_at
        self._write_file(analysis_id, entry)
        self._purge_expired()
        self._enforce_max_entries()

    def get(self, analysis_id: str) -> StoredScanResult | None:
        self._purge_expired()
        entry = self._entries.get(analysis_id)
        if entry is None:
            entry = self._load_file(analysis_id)
            if entry is not None:
                self._entries[analysis_id] = entry
                self._created[analysis_id] = entry.created_at
        if entry is None:
            return None
        if self._is_expired(entry):
            self._drop(analysis_id)
            return None
        return entry

    def get_ai_cache(self, analysis_id: str) -> ExplanationCache:
        """Caché IA del análisis; se crea la primera vez y se reutiliza después."""
        cache = self._ai_caches.get(analysis_id)
        if cache is None:
            cache = ExplanationCache()
            self._ai_caches[analysis_id] = cache
        return cache

    def mark_ai_enriched(self, analysis_id: str) -> StoredScanResult | None:
        entry = self.get(analysis_id)
        if entry is None:
            return None
        updated = replace(entry, enable_ai_explanations=True)
        self._entries[analysis_id] = updated
        self._write_file(analysis_id, updated)
        return updated

    def update_view_prefs(
        self,
        analysis_id: str,
        *,
        hide_info: bool | None = None,
        group_equivalent: bool | None = None,
    ) -> StoredScanResult | None:
        entry = self.get(analysis_id)
        if entry is None:
            return None
        updates: dict[str, bool] = {}
        if hide_info is not None:
            updates["hide_info"] = hide_info
        if group_equivalent is not None:
            updates["group_equivalent"] = group_equivalent
        if not updates:
            return entry
        updated = replace(entry, **updates)
        self._entries[analysis_id] = updated
        self._write_file(analysis_id, updated)
        return updated

    def clear(self) -> None:
        self._entries.clear()
        self._ai_caches.clear()
        if self._storage_dir is not None:
            for analysis_id in list(self._created):
                self._delete_file(analysis_id)
        self._created.clear()

    def __len__(self) -> int:
        return len(self._created)

    # -------------------------------------------------------------- internos

    def _is_expired(self, entry: StoredScanResult) -> bool:
        return time.time() - entry.created_at > self._ttl_sec

    def _drop(self, analysis_id: str) -> None:
        self._entries.pop(analysis_id, None)
        self._ai_caches.pop(analysis_id, None)
        self._created.pop(analysis_id, None)
        self._delete_file(analysis_id)

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [
            key
            for key, created in self._created.items()
            if now - created > self._ttl_sec
        ]
        for key in expired:
            self._drop(key)

    def _enforce_max_entries(self) -> None:
        if self._max_entries is None or len(self._created) <= self._max_entries:
            return
        # Conserva los más recientes; descarta los más antiguos por created_at.
        ordered = sorted(self._created.items(), key=lambda kv: kv[1])
        overflow = len(self._created) - self._max_entries
        for key, _created in ordered[:overflow]:
            self._drop(key)

    # ------------------------------------------------------------ persistencia

    def _path_for(self, analysis_id: str) -> Path | None:
        if self._storage_dir is None:
            return None
        # analysis_id procede de uuid4().hex en el flujo web; se valida para evitar
        # escritura/lectura fuera del directorio (path traversal).
        if not analysis_id or any(
            ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            for ch in analysis_id
        ):
            return None
        return self._storage_dir / f"{analysis_id}.json"

    def _write_file(self, analysis_id: str, entry: StoredScanResult) -> None:
        path = self._path_for(analysis_id)
        if path is None:
            return
        payload = {
            "version": _PERSIST_VERSION,
            "analysis_id": analysis_id,
            "created_at": entry.created_at,
            "analysis_mode": entry.analysis_mode,
            "hide_info": entry.hide_info,
            "group_equivalent": entry.group_equivalent,
            "enable_ai_explanations": entry.enable_ai_explanations,
            "internal": entry.internal,
        }
        tmp = path.with_name(path.name + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, default=str)
            os.replace(tmp, path)  # escritura atómica
        except OSError as exc:
            logger.warning("No se pudo persistir el análisis %s: %s", analysis_id, exc)
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass

    def _load_file(self, analysis_id: str) -> StoredScanResult | None:
        path = self._path_for(analysis_id)
        if path is None or not path.exists():
            return None
        try:
            with path.open(encoding="utf-8") as fh:
                data = json.load(fh)
            return StoredScanResult(
                internal=data["internal"],
                analysis_mode=str(data["analysis_mode"]),
                hide_info=bool(data.get("hide_info", False)),
                group_equivalent=bool(data.get("group_equivalent", False)),
                enable_ai_explanations=bool(data.get("enable_ai_explanations", False)),
                created_at=float(data.get("created_at", 0.0)),
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            logger.warning("Análisis persistido %s ilegible: %s", analysis_id, exc)
            return None

    def _delete_file(self, analysis_id: str) -> None:
        path = self._path_for(analysis_id)
        if path is None:
            return
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("No se pudo borrar el análisis %s: %s", analysis_id, exc)

    def _index_existing(self) -> None:
        """Indexa created_at de los ficheros existentes al arrancar (una vez)."""
        assert self._storage_dir is not None
        for path in self._storage_dir.glob("*.json"):
            analysis_id = path.stem
            entry = self._load_file(analysis_id)
            if entry is None:
                continue
            self._created[analysis_id] = entry.created_at
        self._purge_expired()
        self._enforce_max_entries()


_scan_result_store: ScanResultStore | None = None


def get_scan_result_store() -> ScanResultStore:
    global _scan_result_store
    if _scan_result_store is None:
        from app.config import get_settings

        settings = get_settings()
        _scan_result_store = ScanResultStore(
            ttl_sec=settings.scan_store_ttl_sec,
            storage_dir=settings.scan_store_dir,
            max_entries=settings.scan_store_max_entries,
        )
    return _scan_result_store
