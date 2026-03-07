from __future__ import annotations

from typing import Any

import httpx

from backend.core.config import get_settings
from backend.services.connectors.base import BaseConnector, IntegrationCheck


class JiraConnector(BaseConnector):
    integration_name = "jira_ticketing"
    required_fields = ["JIRA_BASE_URL", "JIRA_PROJECT_KEY"]
    description = "Case management and incident ticket automation."

    def _values(self) -> dict[str, str]:
        settings = get_settings()
        return {
            "JIRA_BASE_URL": settings.jira_base_url.strip().rstrip("/"),
            "JIRA_PROJECT_KEY": settings.jira_project_key.strip(),
            "JIRA_USER_EMAIL": settings.jira_user_email.strip(),
            "JIRA_API_TOKEN": settings.jira_api_token.strip(),
            "JIRA_ISSUE_TYPE": settings.jira_issue_type.strip() or "Task",
        }

    def check(self) -> IntegrationCheck:
        values = self._values()
        missing_fields = [field for field, value in values.items() if not value]
        missing_fields = [item for item in missing_fields if item in self.required_fields]

        return IntegrationCheck(
            name=self.integration_name,
            configured=not missing_fields,
            required_fields=self.required_fields,
            missing_fields=missing_fields,
            description=self.description,
            metadata={
                "project_key": values["JIRA_PROJECT_KEY"],
                "auth_configured": self.auth_configured(),
                "issue_type": values["JIRA_ISSUE_TYPE"],
            },
        )

    def auth_configured(self) -> bool:
        values = self._values()
        return bool(values["JIRA_USER_EMAIL"] and values["JIRA_API_TOKEN"])

    def _to_adf(self, text: str) -> dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            lines = ["No description provided."]

        content = []
        for line in lines:
            content.append(
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": line[:2000]}],
                }
            )

        return {
            "type": "doc",
            "version": 1,
            "content": content,
        }

    def _to_jira_priority(self, priority: str) -> str:
        mapping = {
            "P1": "Highest",
            "P2": "High",
            "P3": "Medium",
            "P4": "Low",
        }
        return mapping.get(priority.strip().upper(), "Medium")

    def create_incident_ticket(
        self,
        summary: str,
        description: str,
        priority: str = "P2",
    ) -> dict[str, object]:
        if not self.check().configured:
            raise RuntimeError("Jira connector is not configured")

        values = self._values()
        if not self.auth_configured():
            raise RuntimeError("Jira API credentials are not configured")

        jira_url = f"{values['JIRA_BASE_URL']}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": values["JIRA_PROJECT_KEY"]},
                "summary": summary[:255],
                "description": self._to_adf(description),
                "issuetype": {"name": values["JIRA_ISSUE_TYPE"]},
                "priority": {"name": self._to_jira_priority(priority)},
            }
        }

        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(
                    jira_url,
                    auth=httpx.BasicAuth(values["JIRA_USER_EMAIL"], values["JIRA_API_TOKEN"]),
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500] if exc.response is not None else str(exc)
            raise RuntimeError(f"Jira API request failed: {detail}") from exc
        except Exception as exc:
            raise RuntimeError(f"Jira API request failed: {exc}") from exc

        ticket_key = str(body.get("key", ""))
        issue_url = f"{values['JIRA_BASE_URL']}/browse/{ticket_key}" if ticket_key else ""

        return {
            "connector": self.integration_name,
            "status": "created",
            "ticket_key": ticket_key,
            "issue_url": issue_url,
            "summary": summary,
            "priority": priority,
            "issue_type": values["JIRA_ISSUE_TYPE"],
        }
