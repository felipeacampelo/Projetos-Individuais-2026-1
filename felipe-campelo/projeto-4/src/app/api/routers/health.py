from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.dependencies import get_app_settings
from app.api.schemas.health import HealthResponse
from app.config import Settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def healthcheck(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        generated_at=datetime.now(timezone.utc),
    )
