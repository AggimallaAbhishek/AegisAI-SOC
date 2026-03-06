from __future__ import annotations

from backend.core.schemas import AlertEvent, Severity, TriageDecision

_CRITICAL_KEYWORDS = {
    "mimikatz",
    "lsass",
    "credential dumping",
    "pass-the-hash",
}

_HIGH_KEYWORDS = {
    "powershell -enc",
    "lateral movement",
    "ransomware",
    "privilege escalation",
}



def run_triage(alert: AlertEvent) -> TriageDecision:
    text = " ".join(
        part
        for part in [alert.description, alert.process_name, alert.command_line]
        if part
    ).lower()

    if any(keyword in text for keyword in _CRITICAL_KEYWORDS):
        return TriageDecision(
            severity=Severity.critical,
            category="credential_access",
            suspicious=True,
            reason="Indicators match credential dumping behavior (e.g., Mimikatz/LSASS).",
        )

    if any(keyword in text for keyword in _HIGH_KEYWORDS):
        return TriageDecision(
            severity=Severity.high,
            category="execution",
            suspicious=True,
            reason="Alert matches high-risk attack behavior keywords.",
        )

    if text:
        return TriageDecision(
            severity=Severity.medium,
            category="anomalous_activity",
            suspicious=True,
            reason="Alert has actionable indicators but no critical signatures.",
        )

    return TriageDecision(
        severity=Severity.low,
        category="informational",
        suspicious=False,
        reason="Insufficient risk indicators in alert content.",
    )
