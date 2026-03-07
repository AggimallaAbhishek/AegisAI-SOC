from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AlertIn(BaseModel):
    source: str = "siem"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    host: str
    user: Optional[str] = None
    ip_address: Optional[str] = None
    process_name: Optional[str] = None
    command_line: Optional[str] = None
    description: str = ""
    raw: Dict[str, Any] = Field(default_factory=dict)


class AlertEvent(AlertIn):
    alert_id: str = Field(default_factory=lambda: str(uuid4()))


class TriageDecision(BaseModel):
    severity: Severity
    category: str
    suspicious: bool
    reason: str


class InvestigationResult(BaseModel):
    findings: List[str] = Field(default_factory=list)
    mapped_techniques: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    knowledge_hits: List[str] = Field(default_factory=list)
    threat_intel: Dict[str, Any] = Field(default_factory=dict)


class ResponseAction(BaseModel):
    action_id: str
    title: str
    playbook: Optional[str] = None
    automated: bool = False
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reason: str


class ResponsePlan(BaseModel):
    containment_priority: str
    actions: List[ResponseAction] = Field(default_factory=list)


class ReportResult(BaseModel):
    summary: str
    timeline: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    case_id: Optional[str] = None
    alert: AlertEvent
    triage: TriageDecision
    investigation: InvestigationResult
    response: ResponsePlan
    report: ReportResult
