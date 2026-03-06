from __future__ import annotations

from backend.core.orchestrator import SOCOrchestrator


orchestrator = SOCOrchestrator()



def process_alert(payload: dict) -> dict:
    """Background worker entry-point for queue-based integration."""
    result = orchestrator.analyze_payload(payload)
    return result.model_dump(mode="json")
