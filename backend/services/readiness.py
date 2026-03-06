from __future__ import annotations

from datetime import datetime, timezone

from backend.core.config import get_settings


class ReadinessService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def integration_status(self) -> list[dict[str, object]]:
        settings = self.settings

        integrations = [
            {
                "name": "splunk_siem",
                "configured": bool(settings.splunk_base_url and settings.splunk_api_token),
                "required_fields": ["SPLUNK_BASE_URL", "SPLUNK_API_TOKEN"],
                "description": "SIEM pull/push integration for ingest and alert synchronization.",
            },
            {
                "name": "jira_ticketing",
                "configured": bool(settings.jira_base_url and settings.jira_project_key),
                "required_fields": ["JIRA_BASE_URL", "JIRA_PROJECT_KEY"],
                "description": "Case management and incident ticket automation.",
            },
            {
                "name": "slack_notifications",
                "configured": bool(settings.slack_webhook_url),
                "required_fields": ["SLACK_WEBHOOK_URL"],
                "description": "Notification channel for escalation and SOC updates.",
            },
            {
                "name": "postgres_case_store",
                "configured": bool(settings.postgres_dsn),
                "required_fields": ["POSTGRES_DSN"],
                "description": "Persistent incident and telemetry storage backend.",
            },
        ]
        return integrations

    def next_phases_status(self) -> dict[str, object]:
        integrations = self.integration_status()
        missing = [item["name"] for item in integrations if not item["configured"]]

        phase2_state = "ready" if len(missing) <= 1 else "in_progress"
        phase3_state = "planned"

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "phase2": {
                "enabled": self.settings.phase2_enabled,
                "state": phase2_state,
                "title": "Phase 2 - Integration and Automation",
                "goals": [
                    "Connect external SIEM/ticketing systems",
                    "Enable automated response workflows",
                    "Persist case history for audit and forensics",
                ],
                "blocking_items": missing,
            },
            "phase3": {
                "enabled": self.settings.phase3_enabled,
                "state": phase3_state,
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
                "Set POSTGRES_DSN and add persistence migrations",
                "Create integration adapters under backend/services/connectors",
            ],
            "phase3_next_steps": [
                "Define SOC roles and access policy matrix",
                "Add threat-intel ingestion job and enrichment hooks",
                "Build KPI dashboard endpoints and retention strategy",
                "Add SOC analyst feedback loop for model/rule tuning",
            ],
        }
