"""GridLine AI — FastAPI application entrypoint."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .db import dispose_engine
from .routers import admin, analyze, health, inspections, verify
from .routers import map as map_router

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

DESCRIPTION = """\
GridLine AI identifies overhead electrical power lines by fusing computer
vision, GPS, public GIS data and a rule-based reasoning engine.

**What this API does not do:** it does not measure voltage or current. Every
figure it returns is an estimate with an explicit confidence and a traceable
evidence chain. `current.is_measured` is `false` unless a verified field
measurement was supplied through `POST /verify`. Nothing here is a clearance
authorisation or a substitute for contacting the operating utility.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Starting %s %s (environment=%s, vision=%s, gis=%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
        "on" if (settings.vision_enabled and settings.openai_api_key) else "off",
        "on" if settings.external_gis_enabled else "off",
    )
    if settings.is_production and not settings.admin_api_key:
        logger.warning(
            "ADMIN_API_KEY is not set; the admin API will refuse all requests in production."
        )
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    app.include_router(health.router)
    app.include_router(analyze.router)
    app.include_router(inspections.router)
    app.include_router(verify.router)
    app.include_router(map_router.router)
    app.include_router(admin.router)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log the detail, return an opaque message: stack contents can carry
        # connection strings and API keys.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
        }

    return app


app = create_app()
