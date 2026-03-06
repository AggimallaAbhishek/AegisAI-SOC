from __future__ import annotations

from backend.services.connectors.jira import JiraConnector
from backend.services.connectors.postgres import PostgresCaseStoreConnector
from backend.services.connectors.slack import SlackConnector
from backend.services.connectors.splunk import SplunkConnector


def build_connectors() -> list[object]:
    return [
        SplunkConnector(),
        JiraConnector(),
        SlackConnector(),
        PostgresCaseStoreConnector(),
    ]


def integration_checks() -> list[dict[str, object]]:
    return [connector.check().as_dict() for connector in build_connectors()]
