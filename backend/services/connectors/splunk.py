from __future__ import annotations

from backend.core.config import get_settings
from backend.services.connectors.base import BaseConnector, IntegrationCheck


class SplunkConnector(BaseConnector):
    integration_name = "splunk_siem"
    required_fields = ["SPLUNK_BASE_URL", "SPLUNK_API_TOKEN"]
    description = "SIEM pull/push integration for ingest and alert synchronization."

    def check(self) -> IntegrationCheck:
        settings = get_settings()
        values = {
            "SPLUNK_BASE_URL": settings.splunk_base_url.strip(),
            "SPLUNK_API_TOKEN": settings.splunk_api_token.strip(),
        }
        missing_fields = [field for field, value in values.items() if not value]

        return IntegrationCheck(
            name=self.integration_name,
            configured=not missing_fields,
            required_fields=self.required_fields,
            missing_fields=missing_fields,
            description=self.description,
            metadata={"base_url": values["SPLUNK_BASE_URL"]},
        )

    def pull_alerts(self, search: str, limit: int = 50) -> dict[str, object]:
        if not self.check().configured:
            raise RuntimeError("Splunk connector is not configured")

        return {
            "connector": self.integration_name,
            "status": "stub",
            "search": search,
            "limit": limit,
        }
