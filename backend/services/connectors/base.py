from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class IntegrationCheck:
    name: str
    configured: bool
    required_fields: list[str]
    missing_fields: list[str]
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def state(self) -> str:
        return "ready" if self.configured else "not_configured"

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "configured": self.configured,
            "state": self.state,
            "required_fields": self.required_fields,
            "missing_fields": self.missing_fields,
            "description": self.description,
            "metadata": self.metadata,
        }


class BaseConnector:
    integration_name: str = "unknown"
    required_fields: list[str] = []
    description: str = ""

    def check(self) -> IntegrationCheck:
        raise NotImplementedError
