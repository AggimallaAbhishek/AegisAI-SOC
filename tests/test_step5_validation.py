from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_raw_alert_endpoint_normalizes_alias_fields() -> None:
    payload = {
        "source": "SIEM",
        "event_time": "2026-03-07T12:30:00Z",
        "hostname": "FIN-WS-442",
        "username": "finance.admin",
        "src_ip": "203.0.113.56",
        "process": "mimikatz.exe",
        "cmdline": "mimikatz.exe sekurlsa::logonpasswords",
        "message": "Potential credential dumping behavior detected on endpoint",
    }

    response = client.post("/api/v1/alerts/analyze/raw", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["alert"]["host"] == "FIN-WS-442"
    assert body["alert"]["ip_address"] == "203.0.113.56"
    assert body["triage"]["severity"] == "critical"


def test_knowledge_search_returns_expected_entry() -> None:
    response = client.get("/api/v1/knowledge/search", params={"query": "mimikatz"})
    assert response.status_code == 200

    body = response.json()
    assert body["results"]
    assert any("Mimikatz" in item["title"] for item in body["results"])


def test_playbooks_list_and_fetch() -> None:
    list_response = client.get("/api/v1/playbooks")
    assert list_response.status_code == 200
    ids = {item["id"] for item in list_response.json()["playbooks"]}

    assert {"block_ip", "isolate_host"}.issubset(ids)

    get_response = client.get("/api/v1/playbooks/block_ip")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == "block_ip"


def test_playbook_not_found_returns_404() -> None:
    response = client.get("/api/v1/playbooks/does_not_exist")
    assert response.status_code == 404


def test_alert_analysis_validation_error_on_missing_required_fields() -> None:
    payload = {
        "source": "SIEM",
        "description": "Missing host should fail",
    }

    response = client.post("/api/v1/alerts/analyze", json=payload)
    assert response.status_code == 422
