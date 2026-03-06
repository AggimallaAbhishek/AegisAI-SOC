from backend.core.orchestrator import SOCOrchestrator
from backend.core.schemas import Severity



def test_orchestrator_flags_mimikatz_as_high_risk() -> None:
    payload = {
        "source": "SIEM",
        "timestamp": "2026-03-07T12:30:00Z",
        "host": "FIN-WS-442",
        "user": "finance.admin",
        "ip_address": "203.0.113.56",
        "process_name": "mimikatz.exe",
        "command_line": "mimikatz.exe sekurlsa::logonpasswords",
        "description": "Potential credential dumping behavior detected on endpoint",
    }

    orchestrator = SOCOrchestrator()
    result = orchestrator.analyze_payload(payload)

    assert result.triage.suspicious is True
    assert result.triage.severity in {Severity.high, Severity.critical}
    assert any("T1003" in item for item in result.investigation.mapped_techniques)
    assert any(action.title == "Isolate compromised host" for action in result.response.actions)
