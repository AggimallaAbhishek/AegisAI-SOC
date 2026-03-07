from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request

from backend.core.config import get_settings


_VALID_ROLES = {"admin", "manager", "analyst", "viewer"}

_DEFAULT_POLICY: dict[str, list[str]] = {
    "alert_analyze": ["admin", "manager", "analyst"],
    "alert_analyze_raw": ["admin", "manager", "analyst"],
    "knowledge_search": ["admin", "manager", "analyst", "viewer"],
    "playbooks_read": ["admin", "manager", "analyst", "viewer"],
    "phase_status_read": ["admin", "manager", "analyst", "viewer"],
    "threat_intel_view": ["admin", "manager", "analyst", "viewer"],
    "case_store_status_view": ["admin", "manager", "analyst", "viewer"],
    "kpi_view": ["admin", "manager", "analyst", "viewer"],
    "sla_view": ["admin", "manager", "analyst", "viewer"],
    "rbac_policy_view": ["admin", "manager"],
}


class RBACService:
    def __init__(self, policy: dict[str, list[str]] | None = None) -> None:
        self._policy = policy or _DEFAULT_POLICY

    def policy_matrix(self) -> dict[str, list[str]]:
        return {action: list(roles) for action, roles in self._policy.items()}

    def _normalize_role(self, role: str) -> str:
        return role.strip().lower()

    def _resolve_role(self, request: Request) -> str:
        settings = get_settings()
        header_name = settings.soc_role_header
        header_value = request.headers.get(header_name, "")

        if header_value:
            role = self._normalize_role(header_value)
            if role in _VALID_ROLES:
                return role
            if settings.phase3_rbac_enforced:
                raise HTTPException(
                    status_code=403,
                    detail=(
                        f"Invalid role '{header_value}'. Allowed roles: "
                        f"{', '.join(sorted(_VALID_ROLES))}."
                    ),
                )

        if settings.phase3_rbac_enforced:
            raise HTTPException(
                status_code=403,
                detail=f"Missing required role header '{header_name}'.",
            )

        fallback_role = self._normalize_role(settings.soc_default_role)
        return fallback_role if fallback_role in _VALID_ROLES else "analyst"

    def enforce(self, action: str, request: Request) -> str:
        settings = get_settings()
        role = self._resolve_role(request)
        allowed_roles = self._policy.get(action, sorted(_VALID_ROLES))

        if settings.phase3_rbac_enforced and role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Role '{role}' is not authorized for action '{action}'. "
                    f"Allowed: {', '.join(allowed_roles)}."
                ),
            )

        return role

    def policy_payload(self, request_role: str) -> dict[str, Any]:
        settings = get_settings()
        return {
            "phase3_enabled": settings.phase3_enabled,
            "rbac_enforced": settings.phase3_rbac_enforced,
            "role_header": settings.soc_role_header,
            "default_role": settings.soc_default_role,
            "request_role": request_role,
            "policy_matrix": self.policy_matrix(),
        }
