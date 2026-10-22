"""GET /map — infrastructure and past inspections around a point."""

from __future__ import annotations

import math
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import get_db
from ..models import Inspection
from ..schemas import InspectionSummary, MapResponse
from ..services.gis import GISEngine, haversine_m

router = APIRouter(tags=["map"])


@router.get(
    "/map",
    response_model=MapResponse,
    summary="Nearby power infrastructure and previous inspections",
)
async def get_map(
    session: Annotated[AsyncSession, Depends(get_db)],
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    radius_m: Annotated[int, Query(ge=50, le=5000)] = 800,
    include_inspections: bool = True,
    max_inspections: Annotated[int, Query(ge=0, le=500)] = 200,
) -> MapResponse:
    radius = min(radius_m, settings.gis_max_radius_m)
    gis = await GISEngine().collect(session, lat, lon, radius)

    inspections: list[InspectionSummary] = []
    if include_inspections and max_inspections:
        # Bounding-box prefilter in SQL, exact circle in Python. Keeps the query
        # identical whether or not PostGIS is present.
        delta_lat = radius / 111_320.0
        cos_lat = max(0.01, abs(math.cos(math.radians(lat))))
        delta_lon = delta_lat / cos_lat

        stmt = (
            select(Inspection)
            .where(
                Inspection.latitude.between(lat - delta_lat, lat + delta_lat),
                Inspection.longitude.between(lon - delta_lon, lon + delta_lon),
            )
            .order_by(Inspection.created_at.desc())
            .limit(max_inspections * 2)
        )
        rows = (await session.execute(stmt)).scalars().all()
        for row in rows:
            if haversine_m(lat, lon, row.latitude, row.longitude) > radius:
                continue
            inspections.append(
                InspectionSummary(
                    id=row.id,
                    created_at=row.created_at,
                    latitude=row.latitude,
                    longitude=row.longitude,
                    photo_url=row.photo_url,
                    thumbnail_url=row.thumbnail_url,
                    predicted_voltage_class=row.predicted_voltage_class,
                    predicted_nominal_v=row.predicted_nominal_v,
                    predicted_utility=row.predicted_utility,
                    overall_confidence=row.overall_confidence,
                    perch_score=row.perch_score,
                    is_verified=row.is_verified,
                )
            )
            if len(inspections) >= max_inspections:
                break

    return MapResponse(
        center={"lat": lat, "lon": lon},
        radius_m=radius,
        assets=gis.assets,
        inspections=inspections,
        sources=gis.sources_queried,
        errors=gis.errors,
    )
