from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from backend.core.config import get_settings
from backend.services.case_store import CaseStoreService


_DEFAULT_METRICS = [
    {
        "case_id": "CASE-1001",
        "severity": "critical",
        "status": "resolved",
        "created_at": "2026-03-06T09:00:00Z",
        "triaged_at": "2026-03-06T09:06:00Z",
        "resolved_at": "2026-03-06T10:02:00Z",
        "automated_containment": True,
        "false_positive": False,
    },
    {
        "case_id": "CASE-1002",
        "severity": "high",
        "status": "resolved",
        "created_at": "2026-03-05T07:40:00Z",
        "triaged_at": "2026-03-05T07:52:00Z",
        "resolved_at": "2026-03-05T09:11:00Z",
        "automated_containment": True,
        "false_positive": False,
    },
    {
        "case_id": "CASE-1003",
        "severity": "medium",
        "status": "resolved",
        "created_at": "2026-03-03T14:20:00Z",
        "triaged_at": "2026-03-03T14:42:00Z",
        "resolved_at": "2026-03-03T15:10:00Z",
        "automated_containment": False,
        "false_positive": True,
    },
    {
        "case_id": "CASE-1004",
        "severity": "critical",
        "status": "in_progress",
        "created_at": "2026-03-02T11:10:00Z",
        "triaged_at": "2026-03-02T11:21:00Z",
        "resolved_at": None,
        "automated_containment": True,
        "false_positive": False,
    },
    {
        "case_id": "CASE-1005",
        "severity": "high",
        "status": "resolved",
        "created_at": "2026-02-26T05:30:00Z",
        "triaged_at": "2026-02-26T05:47:00Z",
        "resolved_at": "2026-02-26T06:29:00Z",
        "automated_containment": False,
        "false_positive": False,
    },
    {
        "case_id": "CASE-1006",
        "severity": "low",
        "status": "resolved",
        "created_at": "2026-02-22T16:15:00Z",
        "triaged_at": "2026-02-22T16:44:00Z",
        "resolved_at": "2026-02-22T17:01:00Z",
        "automated_containment": False,
        "false_positive": True,
    },
]


class MetricsService:
    def __init__(
        self,
        metrics_file: Path | None = None,
        case_store_service: CaseStoreService | None = None,
    ) -> None:
        settings = get_settings()
        self.metrics_file = metrics_file or settings.resolve_path(settings.phase3_metrics_path)
        self.case_store_service = case_store_service or CaseStoreService()
        self._records = self._load_records()

    def _load_records(self) -> list[dict[str, Any]]:
        if self.metrics_file.exists():
            try:
                data = json.loads(self.metrics_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = _DEFAULT_METRICS
        else:
            data = _DEFAULT_METRICS

        if not isinstance(data, list):
            return list(_DEFAULT_METRICS)

        records: list[dict[str, Any]] = []
        for item in data:
            if isinstance(item, dict):
                records.append(item)

        return records or list(_DEFAULT_METRICS)

    def _parse_dt(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    def _window_sample_records(self, days: int) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)

        filtered: list[dict[str, Any]] = []
        for record in self._records:
            created_at = self._parse_dt(str(record.get("created_at", "")))
            if created_at and created_at >= cutoff:
                filtered.append(record)
        return filtered

    def _window_records(self, days: int) -> tuple[list[dict[str, Any]], str]:
        live_records = self.case_store_service.fetch_metric_records(days)
        if live_records is not None:
            return live_records, "postgres"
        return self._window_sample_records(days), "sample_file"

    def _percent(self, part: int, total: int) -> float:
        if total <= 0:
            return 0.0
        return round((part / total) * 100, 2)

    def kpi_overview(self, days: int = 30) -> dict[str, Any]:
        records, source = self._window_records(days)
        total = len(records)

        severity_breakdown = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        resolution_times: list[float] = []
        automated_count = 0
        false_positive_count = 0

        for record in records:
            severity = str(record.get("severity", "low")).lower()
            if severity in severity_breakdown:
                severity_breakdown[severity] += 1

            if bool(record.get("automated_containment", False)):
                automated_count += 1

            if bool(record.get("false_positive", False)):
                false_positive_count += 1

            created_at = self._parse_dt(record.get("created_at"))
            resolved_at = self._parse_dt(record.get("resolved_at"))
            if created_at and resolved_at and resolved_at >= created_at:
                resolution_times.append((resolved_at - created_at).total_seconds() / 60.0)

        resolved_incidents = len(resolution_times)
        mttr = round(sum(resolution_times) / resolved_incidents, 2) if resolved_incidents else 0.0

        return {
            "window_days": days,
            "data_source": source,
            "total_incidents": total,
            "resolved_incidents": resolved_incidents,
            "critical_incidents": severity_breakdown["critical"],
            "severity_breakdown": severity_breakdown,
            "mean_time_to_resolution_minutes": mttr,
            "automation_rate_percent": self._percent(automated_count, total),
            "false_positive_rate_percent": self._percent(false_positive_count, total),
        }

    def sla_overview(self, days: int = 30, target_minutes: int | None = None) -> dict[str, Any]:
        settings = get_settings()
        target = int(target_minutes or settings.phase3_sla_target_minutes)

        records, source = self._window_records(days)
        triaged_records = 0
        within_sla = 0
        breach_cases: list[dict[str, Any]] = []
        triage_durations: list[float] = []

        for record in records:
            created_at = self._parse_dt(record.get("created_at"))
            triaged_at = self._parse_dt(record.get("triaged_at"))
            if not (created_at and triaged_at and triaged_at >= created_at):
                continue

            triaged_records += 1
            triage_minutes = (triaged_at - created_at).total_seconds() / 60.0
            triage_durations.append(triage_minutes)

            if triage_minutes <= target:
                within_sla += 1
            else:
                breach_cases.append(
                    {
                        "case_id": str(record.get("case_id", "unknown")),
                        "triage_minutes": round(triage_minutes, 2),
                        "severity": str(record.get("severity", "unknown")),
                    }
                )

        triage_durations.sort()
        if triage_durations:
            p95_index = max(0, int(round((len(triage_durations) - 1) * 0.95)))
            p95 = round(triage_durations[p95_index], 2)
        else:
            p95 = 0.0

        return {
            "window_days": days,
            "data_source": source,
            "target_minutes": target,
            "total_triaged_cases": triaged_records,
            "within_sla": within_sla,
            "breaches": max(0, triaged_records - within_sla),
            "compliance_percent": self._percent(within_sla, triaged_records),
            "triage_time_p95_minutes": p95,
            "breach_cases": breach_cases[:10],
        }

    def trend_overview(self, days: int = 14) -> dict[str, Any]:
        records, source = self._window_records(days)
        buckets: dict[str, dict[str, int]] = {}

        for record in records:
            created_at = self._parse_dt(record.get("created_at"))
            if not created_at:
                continue
            key = created_at.date().isoformat()
            bucket = buckets.setdefault(key, {"incidents": 0, "critical": 0, "resolved": 0})
            bucket["incidents"] += 1
            if str(record.get("severity", "")).lower() == "critical":
                bucket["critical"] += 1
            if str(record.get("status", "")).lower() == "resolved":
                bucket["resolved"] += 1

        daily = [{"date": key, **buckets[key]} for key in sorted(buckets.keys())]
        return {
            "window_days": days,
            "data_source": source,
            "daily_incidents": daily,
        }
