from __future__ import annotations

import pytest

from backend.core.config import get_settings
from backend.core.orchestrator import SOCOrchestrator
from backend.services.automation import IntegrationAutomationService
from backend.services.case_store import CaseStoreService
from backend.services.connectors.base import IntegrationCheck
from backend.services.connectors.jira import JiraConnector
from backend.services.connectors.slack import SlackConnector


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_jira_connector_creates_ticket(monkeypatch) -> None:
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "SOC")
    monkeypatch.setenv("JIRA_USER_EMAIL", "soc@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token-value")
    monkeypatch.setenv("JIRA_ISSUE_TYPE", "Task")

    captured: dict[str, object] = {}

    class _FakeResponse:
        status_code = 201

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"key": "SOC-101"}

    class _FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            captured["timeout"] = kwargs.get("timeout")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def post(self, url, auth=None, headers=None, json=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            captured["auth"] = auth
            return _FakeResponse()

    monkeypatch.setattr("backend.services.connectors.jira.httpx.Client", _FakeClient)

    connector = JiraConnector()
    result = connector.create_incident_ticket(
        summary="[CRITICAL] CASE-123 credential_access on FIN-WS-442",
        description="Credential dump indicators found",
        priority="P1",
    )

    assert result["status"] == "created"
    assert result["ticket_key"] == "SOC-101"
    assert result["issue_url"] == "https://example.atlassian.net/browse/SOC-101"
    assert captured["url"] == "https://example.atlassian.net/rest/api/3/issue"
    assert captured["json"]["fields"]["project"]["key"] == "SOC"


def test_slack_connector_sends_webhook(monkeypatch) -> None:
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/T/B/C")

    captured: dict[str, object] = {}

    class _FakeResponse:
        status_code = 200
        text = "ok"

        def raise_for_status(self) -> None:
            return None

    def _fake_post(url, json=None, timeout=0):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr("backend.services.connectors.slack.httpx.post", _fake_post)

    connector = SlackConnector()
    result = connector.send_notification("AegisAI Slack integration test")

    assert result["status"] == "sent"
    assert result["status_code"] == 200
    assert captured["url"] == "https://hooks.slack.com/services/T/B/C"
    assert captured["json"]["text"] == "AegisAI Slack integration test"


def test_integration_automation_runs_for_critical_incident() -> None:
    jira_calls = {"count": 0}
    slack_calls = {"count": 0}

    class _FakeJiraConnector:
        def check(self) -> IntegrationCheck:
            return IntegrationCheck(
                name="jira_ticketing",
                configured=True,
                required_fields=[],
                missing_fields=[],
                description="",
                metadata={},
            )

        def auth_configured(self) -> bool:
            return True

        def create_incident_ticket(self, summary: str, description: str, priority: str = "P2"):
            jira_calls["count"] += 1
            return {
                "status": "created",
                "ticket_key": "SCRUM-77",
                "issue_url": "https://example.atlassian.net/browse/SCRUM-77",
            }

    class _FakeSlackConnector:
        def check(self) -> IntegrationCheck:
            return IntegrationCheck(
                name="slack_notifications",
                configured=True,
                required_fields=[],
                missing_fields=[],
                description="",
                metadata={},
            )

        def send_notification(self, message: str):
            slack_calls["count"] += 1
            return {"status": "sent", "status_code": 200}

    automation_service = IntegrationAutomationService(
        jira_connector=_FakeJiraConnector(),
        slack_connector=_FakeSlackConnector(),
        enabled_override=True,
    )

    orchestrator = SOCOrchestrator(
        case_store_service=CaseStoreService(dsn=""),
        automation_service=automation_service,
    )
    result = orchestrator.analyze_payload(
        {
            "source": "SIEM",
            "host": "FIN-WS-442",
            "description": "Potential credential dumping behavior detected",
            "process_name": "mimikatz.exe",
            "command_line": "sekurlsa::logonpasswords",
        }
    )

    assert jira_calls["count"] == 1
    assert slack_calls["count"] == 1
    assert result.automation["enabled"] is True
    assert result.automation["jira"]["status"] == "created"
    assert result.automation["slack"]["status"] == "sent"


def test_integration_automation_can_be_disabled() -> None:
    orchestrator = SOCOrchestrator(
        case_store_service=CaseStoreService(dsn=""),
        automation_service=IntegrationAutomationService(enabled_override=False),
    )
    result = orchestrator.analyze_payload(
        {
            "source": "SIEM",
            "host": "FIN-WS-442",
            "description": "Potential credential dumping behavior detected",
            "process_name": "mimikatz.exe",
            "command_line": "sekurlsa::logonpasswords",
        }
    )

    assert result.automation["enabled"] is False
    assert result.automation["jira"]["status"] == "disabled"
    assert result.automation["slack"]["status"] == "disabled"
