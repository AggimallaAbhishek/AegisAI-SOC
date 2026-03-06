from __future__ import annotations

from backend.core.schemas import (
    AlertEvent,
    InvestigationResult,
    ResponseAction,
    ResponsePlan,
    Severity,
    TriageDecision,
)
from backend.services.playbooks import PlaybookService



def _supports_playbook(playbooks: PlaybookService, playbook_id: str) -> bool:
    return playbooks.get_playbook(playbook_id) is not None



def run_response(
    alert: AlertEvent,
    triage: TriageDecision,
    investigation: InvestigationResult,
    playbooks: PlaybookService,
) -> ResponsePlan:
    actions: list[ResponseAction] = []

    if alert.ip_address and triage.severity in {Severity.high, Severity.critical}:
        actions.append(
            ResponseAction(
                action_id="ACT-001",
                title="Block suspicious source IP",
                playbook="block_ip" if _supports_playbook(playbooks, "block_ip") else None,
                automated=True,
                parameters={"ip_address": alert.ip_address},
                reason="Network containment reduces immediate external threat propagation.",
            )
        )

    if alert.host and triage.severity == Severity.critical:
        actions.append(
            ResponseAction(
                action_id="ACT-002",
                title="Isolate compromised host",
                playbook=(
                    "isolate_host" if _supports_playbook(playbooks, "isolate_host") else None
                ),
                automated=True,
                parameters={"host": alert.host},
                reason="Critical severity with credential-access indicators warrants immediate isolation.",
            )
        )

    actions.append(
        ResponseAction(
            action_id="ACT-003",
            title="Collect volatile evidence",
            automated=False,
            parameters={"host": alert.host},
            reason="Capture memory/process/network artifacts before full remediation.",
        )
    )

    actions.append(
        ResponseAction(
            action_id="ACT-004",
            title="Trigger credential reset workflow",
            automated=False,
            parameters={"user": alert.user},
            reason="Credential theft risk requires containment of account compromise.",
        )
    )

    priority = {
        Severity.critical: "P1",
        Severity.high: "P2",
        Severity.medium: "P3",
        Severity.low: "P4",
    }[triage.severity]

    return ResponsePlan(containment_priority=priority, actions=actions)
