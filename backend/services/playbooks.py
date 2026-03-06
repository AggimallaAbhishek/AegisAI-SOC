from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from backend.core.config import get_settings


class PlaybookService:
    def __init__(self, playbooks_dir: Path | None = None) -> None:
        settings = get_settings()
        self.playbooks_dir = playbooks_dir or settings.resolve_path(settings.playbooks_path)

    def _load_file(self, path: Path) -> dict[str, Any] | None:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except OSError:
            return None
        if not isinstance(data, dict):
            return None
        return data

    def list_playbooks(self) -> list[dict[str, Any]]:
        if not self.playbooks_dir.exists():
            return []

        playbooks: list[dict[str, Any]] = []
        for path in sorted(self.playbooks_dir.glob("*.yaml")):
            data = self._load_file(path)
            if not data:
                continue
            playbooks.append(
                {
                    "id": data.get("id", path.stem),
                    "name": data.get("name", path.stem),
                    "description": data.get("description", ""),
                    "path": str(path),
                }
            )
        return playbooks

    def get_playbook(self, playbook_id: str) -> dict[str, Any] | None:
        if not self.playbooks_dir.exists():
            return None

        for path in sorted(self.playbooks_dir.glob("*.yaml")):
            data = self._load_file(path)
            if not data:
                continue
            resolved_id = str(data.get("id", path.stem))
            if resolved_id == playbook_id:
                return data
        return None
