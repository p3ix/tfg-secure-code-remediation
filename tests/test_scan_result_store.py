import time

from app.services.scan_result_store import ScanResultStore


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
