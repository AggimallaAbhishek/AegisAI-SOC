from __future__ import annotations

from pathlib import Path

from backend.core.config import get_settings
from backend.services.connectors.base import BaseConnector, IntegrationCheck


class PostgresCaseStoreConnector(BaseConnector):
    integration_name = "postgres_case_store"
    required_fields = ["POSTGRES_DSN"]
    description = "Persistent incident and telemetry storage backend."

    def check(self) -> IntegrationCheck:
        settings = get_settings()
        dsn = settings.postgres_dsn.strip()
        missing_fields = [] if dsn else ["POSTGRES_DSN"]

        return IntegrationCheck(
            name=self.integration_name,
            configured=not missing_fields,
            required_fields=self.required_fields,
            missing_fields=missing_fields,
            description=self.description,
            metadata={"migration_path": "backend/migrations"},
        )

    def migration_files(self) -> list[Path]:
        settings = get_settings()
        migration_dir = settings.repo_root / "backend" / "migrations"
        return sorted(migration_dir.glob("*.sql"))
