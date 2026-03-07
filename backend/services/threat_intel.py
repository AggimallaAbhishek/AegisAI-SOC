from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.core.config import get_settings
from backend.core.schemas import AlertEvent


_DEFAULT_IOCS = [
    {
        "ioc_type": "ip",
        "value": "203.0.113.56",
        "threat_family": "credential_theft",
        "confidence": 0.96,
        "source": "internal_feed",
        "mapped_techniques": ["T1003 - OS Credential Dumping"],
        "tags": ["known_bad_ip", "credential_access"],
    },
    {
        "ioc_type": "process",
        "value": "mimikatz.exe",
        "threat_family": "credential_theft",
        "confidence": 0.93,
        "source": "community_ioc",
        "mapped_techniques": ["T1003 - OS Credential Dumping"],
        "tags": ["mimikatz", "lsass"],
    },
    {
        "ioc_type": "command_substring",
        "value": "sekurlsa::logonpasswords",
        "threat_family": "credential_theft",
        "confidence": 0.9,
        "source": "behavioral_rules",
        "mapped_techniques": ["T1003 - OS Credential Dumping"],
        "tags": ["credential_dumping"],
    },
]


class ThreatIntelService:
    def __init__(self, ioc_file: Path | None = None) -> None:
        settings = get_settings()
        self.ioc_file = ioc_file or settings.resolve_path(settings.threat_intel_ioc_path)
        self._iocs = self._load_iocs()
        self._loaded_at = datetime.now(timezone.utc).isoformat()

    def _load_iocs(self) -> list[dict[str, Any]]:
        if self.ioc_file.exists():
            try:
                data = json.loads(self.ioc_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = _DEFAULT_IOCS
        else:
            data = _DEFAULT_IOCS

        if not isinstance(data, list):
            data = _DEFAULT_IOCS

        normalized: list[dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "ioc_type": str(item.get("ioc_type", "")).lower(),
                    "value": str(item.get("value", "")).lower(),
                    "threat_family": str(item.get("threat_family", "unknown")),
                    "confidence": float(item.get("confidence", 0.5)),
                    "source": str(item.get("source", "local_ioc_store")),
                    "mapped_techniques": [str(x) for x in item.get("mapped_techniques", [])],
                    "tags": [str(x) for x in item.get("tags", [])],
                }
            )

        return normalized

    def _matches_ioc(self, alert: AlertEvent, ioc: dict[str, Any]) -> bool:
        ioc_type = ioc.get("ioc_type", "")
        value = ioc.get("value", "")

        if not value:
            return False

        if ioc_type == "ip":
            return bool(alert.ip_address and alert.ip_address.lower() == value)

        if ioc_type == "process":
            return bool(alert.process_name and alert.process_name.lower() == value)

        if ioc_type == "command_substring":
            return bool(alert.command_line and value in alert.command_line.lower())

        if ioc_type == "user":
            return bool(alert.user and alert.user.lower() == value)

        return False

    def enrich(self, alert: AlertEvent) -> dict[str, Any]:
        settings = get_settings()
        if not settings.threat_intel_enabled:
            return {
                "enabled": False,
                "provider": "local_ioc_store",
                "match_count": 0,
                "matches": [],
                "mapped_techniques": [],
                "tags": [],
                "threat_score": 0,
                "recommended_escalation": "intel_disabled",
            }

        matches: list[dict[str, Any]] = []
        for ioc in self._iocs:
            if not self._matches_ioc(alert, ioc):
                continue
            matches.append(
                {
                    "ioc_type": ioc["ioc_type"],
                    "value": ioc["value"],
                    "threat_family": ioc["threat_family"],
                    "confidence": ioc["confidence"],
                    "source": ioc["source"],
                    "mapped_techniques": ioc["mapped_techniques"],
                    "tags": ioc["tags"],
                }
            )

        mapped_techniques = sorted(
            {
                technique
                for match in matches
                for technique in match.get("mapped_techniques", [])
            }
        )
        tags = sorted({tag for match in matches for tag in match.get("tags", [])})

        if matches:
            average_confidence = sum(float(match["confidence"]) for match in matches) / len(matches)
            threat_score = min(100, int(round((average_confidence * 100) + min(20, len(matches) * 5))))
        else:
            threat_score = 0

        if threat_score >= 80:
            recommended_escalation = "immediate_containment"
        elif threat_score >= 60:
            recommended_escalation = "priority_investigation"
        elif threat_score > 0:
            recommended_escalation = "enhanced_monitoring"
        else:
            recommended_escalation = "none"

        return {
            "enabled": True,
            "provider": "local_ioc_store",
            "match_count": len(matches),
            "matches": matches,
            "mapped_techniques": mapped_techniques,
            "tags": tags,
            "threat_score": threat_score,
            "recommended_escalation": recommended_escalation,
        }

    def status(self) -> dict[str, Any]:
        settings = get_settings()
        return {
            "enabled": settings.threat_intel_enabled,
            "provider": "local_ioc_store",
            "ioc_count": len(self._iocs),
            "ioc_path": str(self.ioc_file),
            "last_loaded_at": self._loaded_at,
        }
