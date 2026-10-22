"""Inspection retrieval and listing."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import Inspection
from ..schemas import InspectionDetail, InspectionSummary

router = APIRouter(tags=["inspections"])


def _summary(row: Inspection) -> InspectionSummary:
    return InspectionSummary(
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


@router.get(
    "/inspection/{inspection_id}",
    response_model=InspectionDetail,
    summary="Retrieve a stored inspection with its full report",
)
async def get_inspection(
    inspection_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> InspectionDetail:
    row = await session.get(Inspection, inspection_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found"
        )

    return InspectionDetail(
        **_summary(row).model_dump(),
        heading_deg=row.heading_deg,
        altitude_m=row.altitude_m,
        accuracy_m=row.accuracy_m,
        captured_at=row.captured_at,
        device_model=row.device_model,
        report=row.report,
        vision=row.vision,
        gis=row.gis,
        verifications=list(row.verifications),
    )


@router.get(
    "/inspections",
    response_model=list[InspectionSummary],
    summary="List inspections, newest first",
)
async def list_inspections(
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    verified_only: bool = False,
    voltage_class: str | None = None,
    utility: str | None = None,
    min_perch_score: Annotated[float | None, Query(ge=0, le=100)] = None,
) -> list[InspectionSummary]:
    stmt = select(Inspection).order_by(Inspection.created_at.desc())
    if verified_only:
        stmt = stmt.where(Inspection.is_verified.is_(True))
    if voltage_class:
        stmt = stmt.where(Inspection.predicted_voltage_class == voltage_class)
    if utility:
        stmt = stmt.where(Inspection.predicted_utility.ilike(f"%{utility}%"))
    if min_perch_score is not None:
        stmt = stmt.where(Inspection.perch_score >= min_perch_score)

    rows = (await session.execute(stmt.limit(limit).offset(offset))).scalars().all()
    return [_summary(row) for row in rows]


@router.get(
    "/perch/ranking",
    response_model=list[InspectionSummary],
    summary="Best-ranked spans for autonomous energy harvesting",
)
async def perch_ranking(
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    min_score: Annotated[float, Query(ge=0, le=100)] = 0.0,
) -> list[InspectionSummary]:
    stmt = (
        select(Inspection)
        .where(Inspection.perch_score.isnot(None), Inspection.perch_score >= min_score)
        .order_by(Inspection.perch_score.desc(), Inspection.overall_confidence.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [_summary(row) for row in rows]
