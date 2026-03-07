import pytest

from backend.core.config import get_settings
from backend.services.connectors import build_connectors
from backend.services.readiness import ReadinessService

INTEGRATION_ENV_VARS = [
    "SPLUNK_BASE_URL",
    "SPLUNK_API_TOKEN",
    "JIRA_BASE_URL",
    "JIRA_PROJECT_KEY",
    "SLACK_WEBHOOK_URL",
    "POSTGRES_DSN",
]


@pytest.fixture(autouse=True)
def _settings_cache_reset() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()



def _clear_integration_env(monkeypatch) -> None:
    # Override .env-backed settings with explicit empty values for deterministic tests.
    for name in INTEGRATION_ENV_VARS:
        monkeypatch.setenv(name, "")



def test_connectors_report_missing_fields_when_not_configured(monkeypatch) -> None:
    _clear_integration_env(monkeypatch)

    checks = [connector.check().as_dict() for connector in build_connectors()]
    assert all(item["configured"] is False for item in checks)

    splunk = next(item for item in checks if item["name"] == "splunk_siem")
    assert set(splunk["missing_fields"]) == {"SPLUNK_BASE_URL", "SPLUNK_API_TOKEN"}



def test_readiness_transitions_to_ready_when_all_integrations_configured(monkeypatch) -> None:
    _clear_integration_env(monkeypatch)

    monkeypatch.setenv("SPLUNK_BASE_URL", "https://splunk.example.com")
    monkeypatch.setenv("SPLUNK_API_TOKEN", "dummy-token")
    monkeypatch.setenv("JIRA_BASE_URL", "https://jira.example.com")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "SOC")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/T/B/C")
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://soc:soc@localhost:5432/aegis")

    readiness = ReadinessService()
    phase_status = readiness.next_phases_status()

    assert phase_status["phase2"]["state"] == "ready"
    assert phase_status["phase2"]["completion_percent"] == 100
    assert phase_status["phase2"]["blocking_items"] == []
