from fastapi.testclient import TestClient
import pytest

from backend.core.config import get_settings
from backend.main import app


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


client = TestClient(app)



def test_analysis_includes_threat_intel_enrichment() -> None:
    payload = {
        "source": "SIEM",
        "timestamp": "2026-03-07T12:30:00Z",
        "host": "FIN-WS-442",
        "user": "finance.admin",
        "ip_address": "203.0.113.56",
        "process_name": "mimikatz.exe",
        "command_line": "mimikatz.exe sekurlsa::logonpasswords",
        "description": "Potential credential dumping behavior detected on endpoint",
    }

    response = client.post("/api/v1/alerts/analyze", json=payload)
    assert response.status_code == 200

    body = response.json()
    threat_intel = body["investigation"]["threat_intel"]
    assert threat_intel["enabled"] is True
    assert threat_intel["match_count"] >= 1
    assert threat_intel["threat_score"] > 0
    assert body["case_id"].startswith("CASE-")



def test_phase3_dashboard_endpoints_shape() -> None:
    kpi_response = client.get("/api/v1/phase3/kpi/overview")
    assert kpi_response.status_code == 200
    assert "total_incidents" in kpi_response.json()
    assert "data_source" in kpi_response.json()

    trend_response = client.get("/api/v1/phase3/kpi/trends")
    assert trend_response.status_code == 200
    assert "daily_incidents" in trend_response.json()

    sla_response = client.get("/api/v1/phase3/sla/overview")
    assert sla_response.status_code == 200
    assert "compliance_percent" in sla_response.json()



def test_case_store_status_endpoint_shape() -> None:
    response = client.get("/api/v1/phase3/case-store/status")
    assert response.status_code == 200

    body = response.json()
    assert "configured" in body
    assert "driver_available" in body
    assert "ready" in body



def test_phase3_rbac_enforcement(monkeypatch) -> None:
    monkeypatch.setenv("PHASE3_RBAC_ENFORCED", "true")
    get_settings.cache_clear()

    denied = client.get("/api/v1/phase3/kpi/overview")
    assert denied.status_code == 403

    allowed_viewer = client.get(
        "/api/v1/phase3/kpi/overview",
        headers={"x-soc-role": "viewer"},
    )
    assert allowed_viewer.status_code == 200

    allowed_case_store = client.get(
        "/api/v1/phase3/case-store/status",
        headers={"x-soc-role": "viewer"},
    )
    assert allowed_case_store.status_code == 200

    denied_policy = client.get(
        "/api/v1/phase3/rbac/policy",
        headers={"x-soc-role": "viewer"},
    )
    assert denied_policy.status_code == 403

    allowed_admin = client.get(
        "/api/v1/phase3/rbac/policy",
        headers={"x-soc-role": "admin"},
    )
    assert allowed_admin.status_code == 200
