import time
from pathlib import Path

from app.services.scan_result_store import ScanResultStore


def _internal(target: str = "x") -> dict:
    return {"analysis_target": target, "analysis_id": "id", "findings": []}


def test_scan_result_store_put_and_get() -> None:
    store = ScanResultStore(ttl_sec=60.0)
    internal = {"analysis_target": "x", "findings": []}
    store.put("abc123", internal, analysis_mode="fixture_runtime")
    stored = store.get("abc123")

    assert stored is not None
    assert stored.analysis_mode == "fixture_runtime"
    assert stored.internal["analysis_target"] == "x"


def test_scan_result_store_returns_none_for_unknown_id() -> None:
    store = ScanResultStore()
    assert store.get("missing") is None


def test_scan_result_store_expires_entries() -> None:
    store = ScanResultStore(ttl_sec=0.01)
    store.put("expired", {"findings": []}, analysis_mode="fixture_reports")
    time.sleep(0.02)
    assert store.get("expired") is None


def test_scan_result_store_clear() -> None:
    store = ScanResultStore()
    store.put("one", {"findings": []}, analysis_mode="fixture_reports")
    store.clear()
    assert store.get("one") is None


def test_ai_cache_is_stable_per_analysis() -> None:
    store = ScanResultStore(ttl_sec=60.0)
    cache_a = store.get_ai_cache("abc")
    # Misma instancia para el mismo análisis (persiste entre renders/peticiones).
    assert store.get_ai_cache("abc") is cache_a
    # Distinto análisis -> distinta caché.
    assert store.get_ai_cache("xyz") is not cache_a


def test_ai_cache_dropped_on_expiry_and_clear() -> None:
    store = ScanResultStore(ttl_sec=0.01)
    store.put("e", {"findings": []}, analysis_mode="fixture_reports")
    first = store.get_ai_cache("e")
    time.sleep(0.02)
    store.get("e")  # dispara la purga por TTL
    assert store.get_ai_cache("e") is not first

    store.clear()
    assert store.get_ai_cache("e") is not first


# --------------------------- persistencia en disco ---------------------------


def test_persistent_store_survives_new_instance(tmp_path: Path) -> None:
    store = ScanResultStore(storage_dir=tmp_path)
    store.put("abc123", _internal("proj"), analysis_mode="upload_zip", hide_info=True)
    assert (tmp_path / "abc123.json").exists()

    # Nueva instancia sobre el mismo directorio = "reinicio del proceso".
    revived = ScanResultStore(storage_dir=tmp_path)
    got = revived.get("abc123")
    assert got is not None
    assert got.analysis_mode == "upload_zip"
    assert got.hide_info is True
    assert got.internal["analysis_target"] == "proj"


def test_persistent_store_respects_ttl_across_instances(tmp_path: Path) -> None:
    store = ScanResultStore(storage_dir=tmp_path, ttl_sec=0.01)
    store.put("old", _internal(), analysis_mode="upload_zip")
    time.sleep(0.02)
    # Al indexar, la nueva instancia purga lo caducado y borra el fichero.
    revived = ScanResultStore(storage_dir=tmp_path, ttl_sec=0.01)
    assert revived.get("old") is None
    assert not (tmp_path / "old.json").exists()


def test_persistent_store_enforces_max_entries_lru(tmp_path: Path) -> None:
    store = ScanResultStore(storage_dir=tmp_path, max_entries=2)
    for analysis_id in ("a", "b", "c"):
        store.put(analysis_id, _internal(), analysis_mode="upload_zip")
        time.sleep(0.01)  # created_at estrictamente creciente
    # El más antiguo se descarta (LRU por created_at).
    assert store.get("a") is None
    assert not (tmp_path / "a.json").exists()
    assert store.get("b") is not None
    assert store.get("c") is not None


def test_persistent_store_persists_view_prefs_and_ai_flag(tmp_path: Path) -> None:
    store = ScanResultStore(storage_dir=tmp_path)
    store.put("p1", _internal(), analysis_mode="upload_zip")
    store.update_view_prefs("p1", group_equivalent=True)
    store.mark_ai_enriched("p1")

    revived = ScanResultStore(storage_dir=tmp_path)
    got = revived.get("p1")
    assert got is not None
    assert got.group_equivalent is True
    assert got.enable_ai_explanations is True


def test_persistent_store_clear_removes_files(tmp_path: Path) -> None:
    store = ScanResultStore(storage_dir=tmp_path)
    store.put("one", _internal(), analysis_mode="upload_zip")
    store.clear()
    assert list(tmp_path.glob("*.json")) == []
    assert ScanResultStore(storage_dir=tmp_path).get("one") is None


def test_persistent_store_rejects_path_traversal_ids(tmp_path: Path) -> None:
    store = ScanResultStore(storage_dir=tmp_path)
    # Un id con traversal/extraños no escribe fuera del directorio: no se persiste.
    store.put("../evil", _internal(), analysis_mode="upload_zip")
    assert list(tmp_path.parent.glob("evil*")) == []
    assert list(tmp_path.glob("*.json")) == []
    # Nueva instancia no lo recupera (nunca tocó disco).
    assert ScanResultStore(storage_dir=tmp_path).get("../evil") is None
