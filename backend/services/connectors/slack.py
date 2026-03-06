from __future__ import annotations

from urllib.parse import urlparse

from backend.core.config import get_settings
from backend.services.connectors.base import BaseConnector, IntegrationCheck


class SlackConnector(BaseConnector):
    integration_name = "slack_notifications"
    required_fields = ["SLACK_WEBHOOK_URL"]
    description = "Notification channel for escalation and SOC updates."

    def check(self) -> IntegrationCheck:
        settings = get_settings()
        webhook = settings.slack_webhook_url.strip()
        missing_fields = [] if webhook else ["SLACK_WEBHOOK_URL"]
        parsed = urlparse(webhook) if webhook else None

        return IntegrationCheck(
            name=self.integration_name,
            configured=not missing_fields,
            required_fields=self.required_fields,
            missing_fields=missing_fields,
            description=self.description,
            metadata={"webhook_host": parsed.netloc if parsed else ""},
        )

    def send_notification(self, message: str) -> dict[str, object]:
        if not self.check().configured:
            raise RuntimeError("Slack connector is not configured")

        return {
            "connector": self.integration_name,
            "status": "stub",
            "message": message,
        }
