from __future__ import annotations

from datetime import datetime, timezone

from backend.core.config import get_settings
from backend.services.connectors import integration_checks


class ReadinessService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def integration_status(self) -> list[dict[str, object]]:
        return integration_checks()

    def next_phases_status(self) -> dict[str, object]:
        integrations = self.integration_status()
        missing = [item["name"] for item in integrations if not item["configured"]]

        completion_percent = 0
        if integrations:
            completion_percent = int(round(((len(integrations) - len(missing)) / len(integrations)) * 100))

        if not self.settings.phase2_enabled:
            phase2_state = "disabled"
            phase2_blocking = []
        elif completion_percent == 100:
            phase2_state = "ready"
            phase2_blocking = []
        else:
            phase2_state = "in_progress"
            phase2_blocking = missing

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "phase2": {
                "enabled": self.settings.phase2_enabled,
                "state": phase2_state,
                "completion_percent": completion_percent,
                "title": "Phase 2 - Integration and Automation",
                "goals": [
                    "Connect external SIEM/ticketing systems",
                    "Enable automated response workflows",
                    "Persist case history for audit and forensics",
                ],
                "blocking_items": phase2_blocking,
            },
            "phase3": {
                "enabled": self.settings.phase3_enabled,
                "state": "planned",
                "title": "Phase 3 - Intelligence and Scale",
                "goals": [
                    "Threat intel enrichment and correlation",
                    "Role-based access and team workflow controls",
                    "Trend dashboards, KPIs, and SLA reporting",
                ],
                "blocking_items": [
                    "phase2_completion",
                    "production_data_pipeline",
                ],
            },
            "integrations": integrations,
        }

    def quickstart_checklist(self) -> dict[str, object]:
        return {
            "phase2_next_steps": [
                "Set SPLUNK_BASE_URL and SPLUNK_API_TOKEN in .env",
                "Set JIRA_BASE_URL and JIRA_PROJECT_KEY in .env",
                "Set SLACK_WEBHOOK_URL for incident notifications",
                "Set POSTGRES_DSN and run scripts/migrate_case_store.sh",
                "Wire connector stubs in backend/services/connectors to live APIs",
            ],
            "phase3_next_steps": [
                "Define SOC roles and access policy matrix",
                "Add threat-intel ingestion job and enrichment hooks",
                "Build KPI dashboard endpoints and retention strategy",
                "Add SOC analyst feedback loop for model/rule tuning",
            ],
        }
