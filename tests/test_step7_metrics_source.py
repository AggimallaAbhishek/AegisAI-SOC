from pathlib import Path

from backend.core.orchestrator import SOCOrchestrator
from backend.services.case_store import CaseStoreService
from backend.services.metrics import MetricsService


class _CaseStoreWithRecords:
    def fetch_metric_records(self, days: int):
        return [
            {
                "case_id": "CASE-LIVE-1",
                "severity": "critical",
                "status": "resolved",
                "created_at": "2026-03-07T10:00:00Z",
                "triaged_at": "2026-03-07T10:10:00Z",
                "resolved_at": "2026-03-07T10:50:00Z",
                "automated_containment": True,
                "false_positive": False,
            }
        ]


class _CaseStoreUnavailable:
    def fetch_metric_records(self, days: int):
        return None



def test_metrics_prefers_postgres_records_when_available() -> None:
    service = MetricsService(
        metrics_file=Path("/tmp/nonexistent_phase3_metrics.json"),
        case_store_service=_CaseStoreWithRecords(),
    )

    payload = service.kpi_overview(days=30)
    assert payload["data_source"] == "postgres"
    assert payload["total_incidents"] == 1
    assert payload["critical_incidents"] == 1



def test_metrics_falls_back_to_sample_file_when_postgres_unavailable() -> None:
    service = MetricsService(
        metrics_file=Path("/tmp/nonexistent_phase3_metrics.json"),
        case_store_service=_CaseStoreUnavailable(),
    )

    payload = service.kpi_overview(days=30)
    assert payload["data_source"] == "sample_file"
    assert payload["total_incidents"] >= 1



def test_case_store_uses_enum_value_for_severity() -> None:
    orchestrator = SOCOrchestrator(case_store_service=CaseStoreService(dsn=""))
    result = orchestrator.analyze_payload(
        {
            "source": "SIEM",
            "host": "FIN-WS-442",
            "description": "mimikatz behavior",
            "process_name": "mimikatz.exe",
            "command_line": "sekurlsa::logonpasswords",
        }
    )

    service = CaseStoreService(dsn="")
    payload = service._build_case_payload(result, "CASE-TEST-1")
    assert payload["severity"] in {"low", "medium", "high", "critical"}
