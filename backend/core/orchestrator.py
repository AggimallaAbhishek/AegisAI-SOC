from __future__ import annotations

from backend.agents.investigation import run_investigation
from backend.agents.reporting import build_report
from backend.agents.response import run_response
from backend.agents.triage import run_triage
from backend.core.schemas import AlertEvent, AlertIn, AnalysisResult, InvestigationResult
from backend.services.case_store import CaseStoreService
from backend.services.ingest import normalize_alert
from backend.services.knowledge import KnowledgeService
from backend.services.playbooks import PlaybookService
from backend.services.threat_intel import ThreatIntelService


class SOCOrchestrator:
    def __init__(
        self,
        knowledge_service: KnowledgeService | None = None,
        playbook_service: PlaybookService | None = None,
        threat_intel_service: ThreatIntelService | None = None,
        case_store_service: CaseStoreService | None = None,
    ) -> None:
        self.knowledge_service = knowledge_service or KnowledgeService()
        self.playbook_service = playbook_service or PlaybookService()
        self.threat_intel_service = threat_intel_service or ThreatIntelService()
        self.case_store_service = case_store_service or CaseStoreService()

    def _merge_threat_intel(
        self,
        investigation: InvestigationResult,
        enrichment: dict[str, object],
    ) -> InvestigationResult:
        match_count = int(enrichment.get("match_count", 0) or 0)
        if match_count <= 0:
            return investigation.model_copy(update={"threat_intel": enrichment})

        additional_finding = f"Threat-intel enrichment matched {match_count} indicator(s)."
        findings = list(investigation.findings)
        findings.append(additional_finding)

        mapped = sorted(
            {
                *investigation.mapped_techniques,
                *[str(item) for item in enrichment.get("mapped_techniques", [])],
            }
        )

        threat_score = float(enrichment.get("threat_score", 0.0) or 0.0)
        confidence_boost = min(0.2, threat_score / 500.0)
        boosted_confidence = max(0.0, min(1.0, investigation.confidence + confidence_boost))

        return investigation.model_copy(
            update={
                "findings": findings,
                "mapped_techniques": mapped,
                "confidence": boosted_confidence,
                "threat_intel": enrichment,
            }
        )

    def analyze_alert(self, alert: AlertEvent) -> AnalysisResult:
        knowledge_query = " ".join(
            part
            for part in [alert.description, alert.process_name, alert.command_line]
            if part
        )
        knowledge_hits = self.knowledge_service.search(knowledge_query)

        triage = run_triage(alert)
        investigation = run_investigation(alert, triage, knowledge_hits)
        threat_enrichment = self.threat_intel_service.enrich(alert)
        investigation = self._merge_threat_intel(investigation, threat_enrichment)

        response = run_response(alert, triage, investigation, self.playbook_service)
        report = build_report(alert, triage, investigation, response)

        case_id = f"CASE-{alert.alert_id[:8].upper()}"
        result = AnalysisResult(
            case_id=case_id,
            alert=alert,
            triage=triage,
            investigation=investigation,
            response=response,
            report=report,
        )

        # Persistence is best-effort. API response should still return even when case store is unavailable.
        self.case_store_service.persist_analysis(result)
        return result

    def analyze_payload(self, payload: dict) -> AnalysisResult:
        return self.analyze_alert(normalize_alert(payload))

    def analyze_request(self, alert_in: AlertIn) -> AnalysisResult:
        return self.analyze_alert(AlertEvent(**alert_in.model_dump()))
