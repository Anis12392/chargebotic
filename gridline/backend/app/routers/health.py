"""Health, readiness and local media serving."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import get_db
from ..schemas import HealthResponse
from ..services import storage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Liveness and dependency status")
async def health(session: Annotated[AsyncSession, Depends(get_db)]) -> HealthResponse:
    database = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        database = f"error: {type(exc).__name__}"

    vision_status = "ok" if (settings.vision_enabled and settings.openai_api_key) else "disabled"
    gis_status = "ok" if settings.external_gis_enabled else "disabled"
    storage_status = "s3" if settings.storage_is_s3 else "local"

    degraded = database != "ok"
    return HealthResponse(
        status="degraded" if degraded else "ok",
        version=settings.app_version,
        environment=settings.environment,
        database=database,
        storage=storage_status,
        vision=vision_status,
        gis=gis_status,
    )


@router.get("/ready", summary="Readiness probe", include_in_schema=False)
async def ready(session: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="database unavailable"
        ) from exc
    return {"status": "ready"}


@router.get("/media/{key:path}", summary="Serve a locally stored photo", include_in_schema=False)
async def media(key: str) -> Response:
    """Only used with the local storage backend; S3 deployments serve directly."""
    if settings.storage_is_s3:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        data = await storage.get_backend().get(key)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return Response(
        content=data,
        media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=86400"},
    )
