from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from backend.core.schemas import AlertEvent


def _pick(payload: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return value
    return default


def _parse_timestamp(value: Any) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value

    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def normalize_alert(payload: dict[str, Any]) -> AlertEvent:
    timestamp = _parse_timestamp(_pick(payload, ("timestamp", "event_time", "@timestamp")))

    host = _pick(payload, ("host", "hostname", "device", "endpoint"), default="unknown-host")
    source = _pick(payload, ("source", "vendor", "product"), default="siem")
    description = _pick(payload, ("description", "message", "title"), default="")

    return AlertEvent(
        source=str(source),
        timestamp=timestamp,
        host=str(host),
        user=_pick(payload, ("user", "username", "account")),
        ip_address=_pick(payload, ("ip_address", "src_ip", "source_ip")),
        process_name=_pick(payload, ("process_name", "process", "image")),
        command_line=_pick(payload, ("command_line", "cmdline", "command")),
        description=str(description),
        raw=payload,
    )
