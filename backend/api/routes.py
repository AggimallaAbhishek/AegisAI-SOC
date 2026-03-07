from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from backend.core.config import get_settings
from backend.core.orchestrator import SOCOrchestrator
from backend.core.schemas import AlertIn, AnalysisResult
from backend.services.case_store import CaseStoreService
from backend.services.metrics import MetricsService
from backend.services.rbac import RBACService
from backend.services.readiness import ReadinessService

router = APIRouter(prefix="/api/v1", tags=["soc"])

case_store = CaseStoreService()
orchestrator = SOCOrchestrator(case_store_service=case_store)
readiness = ReadinessService()
rbac = RBACService()
metrics = MetricsService(case_store_service=case_store)


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "aegisai-soc",
        "version": settings.api_version,
    }


@router.post("/alerts/analyze", response_model=AnalysisResult)
def analyze_alert(request: Request, alert: AlertIn) -> AnalysisResult:
    rbac.enforce("alert_analyze", request)
    return orchestrator.analyze_request(alert)


@router.post("/alerts/analyze/raw", response_model=AnalysisResult)
def analyze_raw_alert(request: Request, payload: dict[str, Any]) -> AnalysisResult:
    rbac.enforce("alert_analyze_raw", request)
    return orchestrator.analyze_payload(payload)


@router.get("/knowledge/search")
def search_knowledge(
    request: Request,
    query: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=20),
) -> dict[str, Any]:
    rbac.enforce("knowledge_search", request)
    results = [entry.as_dict() for entry in orchestrator.knowledge_service.search(query, limit)]
    return {"query": query, "results": results}


@router.get("/playbooks")
def list_playbooks(request: Request) -> dict[str, Any]:
    rbac.enforce("playbooks_read", request)
    return {"playbooks": orchestrator.playbook_service.list_playbooks()}


@router.get("/playbooks/{playbook_id}")
def get_playbook(request: Request, playbook_id: str) -> dict[str, Any]:
    rbac.enforce("playbooks_read", request)
    playbook = orchestrator.playbook_service.get_playbook(playbook_id)
    if not playbook:
        raise HTTPException(status_code=404, detail=f"Playbook '{playbook_id}' not found")
    return playbook


@router.get("/next-phases/status")
def next_phases_status(request: Request) -> dict[str, Any]:
    rbac.enforce("phase_status_read", request)
    return readiness.next_phases_status()


@router.get("/next-phases/quickstart")
def next_phases_quickstart(request: Request) -> dict[str, Any]:
    rbac.enforce("phase_status_read", request)
    return readiness.quickstart_checklist()


@router.get("/next-phases/integrations")
def next_phases_integrations(request: Request) -> dict[str, Any]:
    rbac.enforce("phase_status_read", request)
    return {"integrations": readiness.integration_status()}


@router.get("/phase3/rbac/policy")
def phase3_rbac_policy(request: Request) -> dict[str, Any]:
    role = rbac.enforce("rbac_policy_view", request)
    return rbac.policy_payload(request_role=role)


@router.get("/phase3/threat-intel/status")
def phase3_threat_intel_status(request: Request) -> dict[str, Any]:
    role = rbac.enforce("threat_intel_view", request)
    payload = orchestrator.threat_intel_service.status()
    payload["request_role"] = role
    return payload


@router.get("/phase3/case-store/status")
def phase3_case_store_status(request: Request) -> dict[str, Any]:
    role = rbac.enforce("case_store_status_view", request)
    payload = case_store.status()
    payload["request_role"] = role
    return payload


@router.get("/phase3/kpi/overview")
def phase3_kpi_overview(
    request: Request,
    days: int = Query(30, ge=1, le=365),
) -> dict[str, Any]:
    role = rbac.enforce("kpi_view", request)
    payload = metrics.kpi_overview(days=days)
    payload["request_role"] = role
    return payload


@router.get("/phase3/kpi/trends")
def phase3_kpi_trends(
    request: Request,
    days: int = Query(14, ge=1, le=90),
) -> dict[str, Any]:
    role = rbac.enforce("kpi_view", request)
    payload = metrics.trend_overview(days=days)
    payload["request_role"] = role
    return payload


@router.get("/phase3/sla/overview")
def phase3_sla_overview(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    target_minutes: int | None = Query(None, ge=1, le=1440),
) -> dict[str, Any]:
    role = rbac.enforce("sla_view", request)
    payload = metrics.sla_overview(days=days, target_minutes=target_minutes)
    payload["request_role"] = role
    return payload
