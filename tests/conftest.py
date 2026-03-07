from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.config import get_settings


@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch) -> None:
    # Keep tests deterministic even when local .env enables strict RBAC.
    monkeypatch.setenv("PHASE3_RBAC_ENFORCED", "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
