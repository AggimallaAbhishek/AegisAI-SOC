from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.core.config import get_settings
from backend.core.orchestrator import SOCOrchestrator
from backend.core.schemas import AlertIn, AnalysisResult
from backend.services.readiness import ReadinessService

router = APIRouter(prefix="/api/v1", tags=["soc"])

orchestrator = SOCOrchestrator()
readiness = ReadinessService()


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "aegisai-soc",
        "version": settings.api_version,
    }


@router.post("/alerts/analyze", response_model=AnalysisResult)
def analyze_alert(alert: AlertIn) -> AnalysisResult:
    return orchestrator.analyze_request(alert)


@router.post("/alerts/analyze/raw", response_model=AnalysisResult)
def analyze_raw_alert(payload: dict[str, Any]) -> AnalysisResult:
    return orchestrator.analyze_payload(payload)


@router.get("/knowledge/search")
def search_knowledge(
    query: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=20),
) -> dict[str, Any]:
    results = [entry.as_dict() for entry in orchestrator.knowledge_service.search(query, limit)]
    return {"query": query, "results": results}


@router.get("/playbooks")
def list_playbooks() -> dict[str, Any]:
    return {"playbooks": orchestrator.playbook_service.list_playbooks()}


@router.get("/playbooks/{playbook_id}")
def get_playbook(playbook_id: str) -> dict[str, Any]:
    playbook = orchestrator.playbook_service.get_playbook(playbook_id)
    if not playbook:
        raise HTTPException(status_code=404, detail=f"Playbook '{playbook_id}' not found")
    return playbook


@router.get("/next-phases/status")
def next_phases_status() -> dict[str, Any]:
    return readiness.next_phases_status()


@router.get("/next-phases/quickstart")
def next_phases_quickstart() -> dict[str, Any]:
    return readiness.quickstart_checklist()


@router.get("/next-phases/integrations")
def next_phases_integrations() -> dict[str, Any]:
    return {"integrations": readiness.integration_status()}
