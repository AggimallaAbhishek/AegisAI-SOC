from __future__ import annotations

from fastapi import FastAPI

from backend.api.routes import router
from backend.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="AI-assisted SOC incident triage and response orchestration API.",
)

app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "AegisAI SOC backend is running",
        "docs": "/docs",
    }
