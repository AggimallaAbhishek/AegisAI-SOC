from __future__ import annotations

from datetime import datetime, timezone

from backend.core.schemas import (
    AlertEvent,
    InvestigationResult,
    ReportResult,
    ResponsePlan,
    TriageDecision,
)



def build_report(
    alert: AlertEvent,
    triage: TriageDecision,
    investigation: InvestigationResult,
    response: ResponsePlan,
) -> ReportResult:
    timestamp = datetime.now(timezone.utc).isoformat()
    summary = (
        f"{triage.severity.value.upper()} incident on {alert.host}. "
        f"Category: {triage.category}. Reason: {triage.reason}"
    )

    timeline = [
        f"{timestamp} - Alert ingested from {alert.source}.",
        f"{timestamp} - Triage labeled severity as {triage.severity.value}.",
        f"{timestamp} - Investigation confidence scored at {investigation.confidence:.2f}.",
        f"{timestamp} - Response plan created with priority {response.containment_priority}.",
    ]

    next_steps = [action.title for action in response.actions]
    next_steps.append("Review detection logic and tune rules to reduce false positives.")

    return ReportResult(summary=summary, timeline=timeline, recommended_next_steps=next_steps)
