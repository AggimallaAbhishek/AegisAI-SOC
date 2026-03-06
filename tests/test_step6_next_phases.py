from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_next_phases_status_shape() -> None:
    response = client.get("/api/v1/next-phases/status")
    assert response.status_code == 200

    body = response.json()
    assert "generated_at" in body
    assert "phase2" in body
    assert "phase3" in body
    assert "integrations" in body
    assert isinstance(body["integrations"], list)



def test_next_phases_status_includes_expected_integrations() -> None:
    response = client.get("/api/v1/next-phases/status")
    assert response.status_code == 200

    names = {item["name"] for item in response.json()["integrations"]}
    assert {"splunk_siem", "jira_ticketing", "slack_notifications", "postgres_case_store"}.issubset(
        names
    )



def test_next_phases_quickstart_shape() -> None:
    response = client.get("/api/v1/next-phases/quickstart")
    assert response.status_code == 200

    body = response.json()
    assert isinstance(body["phase2_next_steps"], list)
    assert isinstance(body["phase3_next_steps"], list)
    assert len(body["phase2_next_steps"]) > 0
    assert len(body["phase3_next_steps"]) > 0
