from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from backend.core.config import get_settings
from backend.core.schemas import AnalysisResult

try:
    import psycopg
except ImportError:  # pragma: no cover - optional runtime dependency
    psycopg = None


class CaseStoreService:
    def __init__(self, dsn: str | None = None) -> None:
        settings = get_settings()
        self.dsn = (dsn if dsn is not None else settings.postgres_dsn).strip()
        self.last_error = ""

    def _is_driver_available(self) -> bool:
        return psycopg is not None

    def is_configured(self) -> bool:
        return bool(self.dsn)

    def is_available(self) -> bool:
        return self.is_configured() and self._is_driver_available()

    def _connect(self):
        if not self.is_available():
            return None

        try:
            return psycopg.connect(self.dsn, connect_timeout=3)
        except Exception as exc:  # pragma: no cover - network/driver behavior
            self.last_error = str(exc)
            return None

    def _load_case_columns(self, conn: Any) -> set[str]:
        columns: set[str] = set()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name='soc_cases'
                """
            )
            for row in cur.fetchall():
                columns.add(str(row[0]))

        return columns

    def _derive_case_id(self, result: AnalysisResult) -> str:
        return result.case_id or f"CASE-{result.alert.alert_id[:8].upper()}"

    def _build_case_payload(self, result: AnalysisResult, case_id: str) -> dict[str, Any]:
        analyzed_at = datetime.now(timezone.utc)
        automated_containment = any(action.automated for action in result.response.actions)
        status = "resolved" if automated_containment else "in_progress"
        resolved_at = analyzed_at if automated_containment else None

        return {
            "case_id": case_id,
            "alert_id": result.alert.alert_id,
            "source": result.alert.source,
            "host": result.alert.host,
            "severity": result.triage.severity.value,
            "category": result.triage.category,
            "status": status,
            "triage_reason": result.triage.reason,
            "confidence": float(result.investigation.confidence),
            "summary": result.report.summary,
            "created_at": analyzed_at,
            "triaged_at": analyzed_at,
            "resolved_at": resolved_at,
            "automated_containment": automated_containment,
            "false_positive": not result.triage.suspicious,
            "updated_at": analyzed_at,
        }

    def persist_analysis(self, result: AnalysisResult) -> dict[str, Any]:
        case_id = self._derive_case_id(result)

        if not self.is_configured():
            return {"case_id": case_id, "persisted": False, "reason": "dsn_not_configured"}

        if not self._is_driver_available():
            return {"case_id": case_id, "persisted": False, "reason": "psycopg_not_installed"}

        conn = self._connect()
        if conn is None:
            return {"case_id": case_id, "persisted": False, "reason": "connection_failed"}

        payload = self._build_case_payload(result, case_id)

        try:
            with conn.cursor() as cur:
                columns = self._load_case_columns(conn)
                insert_columns = [name for name in payload.keys() if name in columns]
                insert_values = [payload[name] for name in insert_columns]

                if not insert_columns:
                    return {"case_id": case_id, "persisted": False, "reason": "schema_missing"}

                placeholders = ", ".join(["%s"] * len(insert_columns))
                columns_sql = ", ".join(insert_columns)

                update_columns = [name for name in insert_columns if name != "case_id"]
                updates_sql = ", ".join([f"{name}=EXCLUDED.{name}" for name in update_columns])
                if not updates_sql:
                    updates_sql = "case_id=EXCLUDED.case_id"

                cur.execute(
                    f"""
                    INSERT INTO soc_cases ({columns_sql})
                    VALUES ({placeholders})
                    ON CONFLICT (case_id) DO UPDATE SET {updates_sql}
                    """,
                    insert_values,
                )

                event_payload = json.dumps(
                    {
                        "triage": result.triage.model_dump(),
                        "investigation": result.investigation.model_dump(),
                        "response": result.response.model_dump(),
                        "report": result.report.model_dump(),
                    }
                )
                cur.execute(
                    """
                    INSERT INTO soc_case_events (case_id, event_type, payload)
                    VALUES (%s, %s, %s::jsonb)
                    """,
                    (case_id, "analysis_completed", event_payload),
                )

            conn.commit()
            self.last_error = ""
            return {"case_id": case_id, "persisted": True, "reason": "ok"}
        except Exception as exc:  # pragma: no cover - integration path
            conn.rollback()
            self.last_error = str(exc)
            return {"case_id": case_id, "persisted": False, "reason": "insert_failed"}
        finally:
            conn.close()

    def fetch_metric_records(self, days: int) -> list[dict[str, Any]] | None:
        if not self.is_available():
            return None

        conn = self._connect()
        if conn is None:
            return None

        try:
            with conn.cursor() as cur:
                columns = self._load_case_columns(conn)

                triaged_expr = "triaged_at" if "triaged_at" in columns else "NULL::timestamptz"
                resolved_expr = "resolved_at" if "resolved_at" in columns else "NULL::timestamptz"
                auto_expr = (
                    "automated_containment" if "automated_containment" in columns else "FALSE"
                )
                false_pos_expr = "false_positive" if "false_positive" in columns else "FALSE"

                cur.execute(
                    f"""
                    SELECT
                        case_id,
                        severity,
                        status,
                        created_at,
                        {triaged_expr} AS triaged_at,
                        {resolved_expr} AS resolved_at,
                        {auto_expr} AS automated_containment,
                        {false_pos_expr} AS false_positive
                    FROM soc_cases
                    WHERE created_at >= NOW() - (%s::int * INTERVAL '1 day')
                    """,
                    (days,),
                )
                rows = cur.fetchall()

            records: list[dict[str, Any]] = []
            for row in rows:
                (
                    case_id,
                    severity,
                    status,
                    created_at,
                    triaged_at,
                    resolved_at,
                    automated_containment,
                    false_positive,
                ) = row

                records.append(
                    {
                        "case_id": str(case_id),
                        "severity": str(severity).lower(),
                        "status": str(status).lower(),
                        "created_at": self._isoformat(created_at),
                        "triaged_at": self._isoformat(triaged_at),
                        "resolved_at": self._isoformat(resolved_at),
                        "automated_containment": bool(automated_containment),
                        "false_positive": bool(false_positive),
                    }
                )

            self.last_error = ""
            return records
        except Exception as exc:  # pragma: no cover - integration path
            self.last_error = str(exc)
            return None
        finally:
            conn.close()

    def _isoformat(self, value: datetime | None) -> str | None:
        if value is None:
            return None

        dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def status(self) -> dict[str, Any]:
        return {
            "configured": self.is_configured(),
            "driver_available": self._is_driver_available(),
            "ready": self.is_available(),
            "last_error": self.last_error,
        }
