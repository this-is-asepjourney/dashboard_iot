"""Tests for IoT Dashboard API & Personal API Platform (Main API) integration."""

from fastapi.testclient import TestClient
from api.main import app


client = TestClient(app)


def test_health_and_pap_status_endpoints():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["api"] == "ok"
    assert "pap_api" in body

    res_api_health = client.get("/api/health")
    assert res_api_health.status_code == 200

    pap_status = client.get("/api/pap/status")
    assert pap_status.status_code == 200
    assert pap_status.json()["main_api"] == "Personal API Platform"


def test_devices_hierarchy_and_pap_sync():
    hier_res = client.get("/api/devices/hierarchy")
    assert hier_res.status_code == 200
    hier = hier_res.json()
    assert hier["category"] == "Heatpress"
    assert hier["summary"]["total_devices"] >= 3
    model_ids = {m["id"] for m in hier["models"]}
    assert {"HPM 55", "AF-450", "APM-LOGO", "comingsoon"}.issubset(model_ids)

    sync_res = client.post("/api/pap/sync")
    assert sync_res.status_code == 200
    assert sync_res.json()["status"] == "success"
    assert sync_res.json()["total_devices"] >= 3

