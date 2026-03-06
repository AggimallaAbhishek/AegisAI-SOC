from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)



def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "aegisai-soc"



def test_alert_analysis_endpoint() -> None:
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
    assert body["triage"]["suspicious"] is True
    assert body["response"]["containment_priority"] in {"P1", "P2"}
