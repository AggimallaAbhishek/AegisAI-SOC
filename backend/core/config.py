from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    api_title: str = "AegisAI SOC API"
    api_version: str = "0.1.0"
    knowledge_base_path: str = "scripts/sample_data/knowledge_base.json"
    playbooks_path: str = "playbooks"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def resolve_path(self, path_value: str) -> Path:
        path = Path(path_value)
        if path.is_absolute():
            return path
        return self.repo_root / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
