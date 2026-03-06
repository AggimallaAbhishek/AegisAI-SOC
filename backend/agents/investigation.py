from __future__ import annotations

from backend.core.schemas import AlertEvent, InvestigationResult, TriageDecision
from backend.services.knowledge import KBEntry


_MITRE_MAP = {
    "mimikatz": "T1003 - OS Credential Dumping",
    "lsass": "T1003 - OS Credential Dumping",
    "powershell": "T1059.001 - Command and Scripting Interpreter: PowerShell",
    "wmic": "T1047 - Windows Management Instrumentation",
}



def run_investigation(
    alert: AlertEvent,
    triage: TriageDecision,
    knowledge_hits: list[KBEntry],
) -> InvestigationResult:
    text = " ".join(
        part
        for part in [alert.description, alert.process_name, alert.command_line]
        if part
    ).lower()

    mapped = sorted(
        {
            technique
            for keyword, technique in _MITRE_MAP.items()
            if keyword in text
        }
    )

    findings: list[str] = []
    if "mimikatz" in text or "lsass" in text:
        findings.append("Likely credential dumping activity observed on endpoint.")
    if alert.user:
        findings.append(f"Potentially affected account: {alert.user}.")
    if alert.host:
        findings.append(f"Impacted host: {alert.host}.")

    if not findings:
        findings.append("No concrete compromise artifacts were extracted from raw indicators.")

    confidence = 0.35
    if triage.severity.value == "critical":
        confidence += 0.35
    elif triage.severity.value == "high":
        confidence += 0.25
    elif triage.severity.value == "medium":
        confidence += 0.15

    confidence += min(len(knowledge_hits) * 0.08, 0.24)
    confidence = max(0.0, min(1.0, confidence))

    return InvestigationResult(
        findings=findings,
        mapped_techniques=mapped,
        confidence=confidence,
        knowledge_hits=[hit.entry_id for hit in knowledge_hits],
    )
