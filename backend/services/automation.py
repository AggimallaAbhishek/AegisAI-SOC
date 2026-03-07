from __future__ import annotations

from typing import Any

from backend.core.config import get_settings
from backend.core.schemas import AnalysisResult
from backend.services.connectors.jira import JiraConnector
from backend.services.connectors.slack import SlackConnector

_SLACK_ESCALATION_SEVERITIES = {"high", "critical"}


class IntegrationAutomationService:
    def __init__(
        self,
        jira_connector: JiraConnector | None = None,
        slack_connector: SlackConnector | None = None,
        enabled_override: bool | None = None,
    ) -> None:
        self.jira_connector = jira_connector or JiraConnector()
        self.slack_connector = slack_connector or SlackConnector()
        self.enabled_override = enabled_override

    def is_enabled(self) -> bool:
        if self.enabled_override is not None:
            return self.enabled_override
        return bool(get_settings().phase2_automation_enabled)

    def run_post_analysis(self, result: AnalysisResult) -> dict[str, Any]:
        if not self.is_enabled():
            return {
                "enabled": False,
                "jira": {"attempted": False, "status": "disabled"},
                "slack": {"attempted": False, "status": "disabled"},
            }

        severity = result.triage.severity.value
        automation: dict[str, Any] = {
            "enabled": True,
            "jira": {"attempted": False, "status": "skipped_not_suspicious"},
            "slack": {"attempted": False, "status": "skipped_not_escalation_severity"},
        }

        if result.triage.suspicious:
            automation["jira"] = self._create_jira_ticket(result)

        if severity in _SLACK_ESCALATION_SEVERITIES:
            automation["slack"] = self._send_slack_notification(result)

        return automation

    def _create_jira_ticket(self, result: AnalysisResult) -> dict[str, Any]:
        check = self.jira_connector.check()
        if not check.configured:
            return {"attempted": False, "status": "skipped_not_configured"}

        if not self.jira_connector.auth_configured():
            return {"attempted": False, "status": "skipped_missing_auth"}

        summary = self._jira_summary(result)
        description = self._jira_description(result)
        priority = result.response.containment_priority or "P2"

        try:
            ticket = self.jira_connector.create_incident_ticket(
                summary=summary,
                description=description,
                priority=priority,
            )
            return {
                "attempted": True,
                "status": str(ticket.get("status", "created")),
                "ticket_key": str(ticket.get("ticket_key", "")),
                "issue_url": str(ticket.get("issue_url", "")),
            }
        except Exception as exc:
            return {
                "attempted": True,
                "status": "failed",
                "error": str(exc)[:500],
            }

    def _send_slack_notification(self, result: AnalysisResult) -> dict[str, Any]:
        check = self.slack_connector.check()
        if not check.configured:
            return {"attempted": False, "status": "skipped_not_configured"}

        message = self._slack_message(result)
        try:
            delivery = self.slack_connector.send_notification(message)
            return {
                "attempted": True,
                "status": str(delivery.get("status", "sent")),
                "status_code": int(delivery.get("status_code", 0) or 0),
            }
        except Exception as exc:
            return {
                "attempted": True,
                "status": "failed",
                "error": str(exc)[:500],
            }

    def _jira_summary(self, result: AnalysisResult) -> str:
        severity = result.triage.severity.value.upper()
        return f"[{severity}] {result.case_id} {result.triage.category} on {result.alert.host}"

    def _jira_description(self, result: AnalysisResult) -> str:
        findings = "\n".join(f"- {item}" for item in result.investigation.findings)
        actions = "\n".join(f"- {item.title}: {item.reason}" for item in result.response.actions)
        return (
            f"Case ID: {result.case_id}\n"
            f"Host: {result.alert.host}\n"
            f"User: {result.alert.user or 'N/A'}\n"
            f"IP: {result.alert.ip_address or 'N/A'}\n"
            f"Severity: {result.triage.severity.value}\n"
            f"Category: {result.triage.category}\n"
            f"Containment priority: {result.response.containment_priority}\n"
            f"Triage reason: {result.triage.reason}\n"
            f"Summary: {result.report.summary}\n\n"
            f"Investigation findings:\n{findings or '- N/A'}\n\n"
            f"Recommended response actions:\n{actions or '- N/A'}"
        )

    def _slack_message(self, result: AnalysisResult) -> str:
        severity = result.triage.severity.value.upper()
        return (
            f"[AegisAI SOC] {severity} incident detected\n"
            f"Case: {result.case_id}\n"
            f"Host: {result.alert.host}\n"
            f"Category: {result.triage.category}\n"
            f"Priority: {result.response.containment_priority}\n"
            f"Reason: {result.triage.reason}"
        )
