from __future__ import annotations

from backend.core.config import get_settings
from backend.services.connectors.base import BaseConnector, IntegrationCheck


class JiraConnector(BaseConnector):
    integration_name = "jira_ticketing"
    required_fields = ["JIRA_BASE_URL", "JIRA_PROJECT_KEY"]
    description = "Case management and incident ticket automation."

    def check(self) -> IntegrationCheck:
        settings = get_settings()
        values = {
            "JIRA_BASE_URL": settings.jira_base_url.strip(),
            "JIRA_PROJECT_KEY": settings.jira_project_key.strip(),
        }
        missing_fields = [field for field, value in values.items() if not value]

        return IntegrationCheck(
            name=self.integration_name,
            configured=not missing_fields,
            required_fields=self.required_fields,
            missing_fields=missing_fields,
            description=self.description,
            metadata={"project_key": values["JIRA_PROJECT_KEY"]},
        )

    def create_incident_ticket(
        self,
        summary: str,
        description: str,
        priority: str = "P2",
    ) -> dict[str, object]:
        if not self.check().configured:
            raise RuntimeError("Jira connector is not configured")

        return {
            "connector": self.integration_name,
            "status": "stub",
            "ticket_key": "SOC-000",
            "summary": summary,
            "priority": priority,
            "description": description,
        }
