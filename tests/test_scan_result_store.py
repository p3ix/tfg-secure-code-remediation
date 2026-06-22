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
