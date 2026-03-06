from __future__ import annotations

from backend.agents.investigation import run_investigation
from backend.agents.reporting import build_report
from backend.agents.response import run_response
from backend.agents.triage import run_triage
from backend.core.schemas import AlertEvent, AlertIn, AnalysisResult
from backend.services.ingest import normalize_alert
from backend.services.knowledge import KnowledgeService
from backend.services.playbooks import PlaybookService


class SOCOrchestrator:
    def __init__(
        self,
        knowledge_service: KnowledgeService | None = None,
        playbook_service: PlaybookService | None = None,
    ) -> None:
        self.knowledge_service = knowledge_service or KnowledgeService()
        self.playbook_service = playbook_service or PlaybookService()

    def analyze_alert(self, alert: AlertEvent) -> AnalysisResult:
        knowledge_query = " ".join(
            part
            for part in [alert.description, alert.process_name, alert.command_line]
            if part
        )
        knowledge_hits = self.knowledge_service.search(knowledge_query)

        triage = run_triage(alert)
        investigation = run_investigation(alert, triage, knowledge_hits)
        response = run_response(alert, triage, investigation, self.playbook_service)
        report = build_report(alert, triage, investigation, response)

        return AnalysisResult(
            alert=alert,
            triage=triage,
            investigation=investigation,
            response=response,
            report=report,
        )

    def analyze_payload(self, payload: dict) -> AnalysisResult:
        return self.analyze_alert(normalize_alert(payload))

    def analyze_request(self, alert_in: AlertIn) -> AnalysisResult:
        return self.analyze_alert(AlertEvent(**alert_in.model_dump()))
