"""Admin dashboard API.

Every endpoint here is behind ``require_admin``. Aggregations are done in SQL
where the shape allows it and in Python where portability matters more than the
last millisecond — these are dashboard queries, not hot paths.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..deps import require_admin
from ..models import Inspection, Verification
from ..schemas import AdminStats, InspectionSummary, TrainingExample
from ..services.training import build_training_examples, training_jsonl

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

CONFIDENCE_BUCKETS = ((0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.01))
PERCH_BUCKETS = ((0, 20), (20, 40), (40, 60), (60, 80), (80, 101))


def _bucket_label(low: float, high: float, scale: int = 1) -> str:
    return f"{low * scale:g}-{high * scale:g}"


@router.get("/stats", response_model=AdminStats, summary="Fleet-wide statistics")
async def stats(
    session: Annotated[AsyncSession, Depends(get_db)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> AdminStats:
    total_inspections = int(
        (await session.execute(select(func.count(Inspection.id)))).scalar_one()
    )
    total_verifications = int(
        (await session.execute(select(func.count(Verification.id)))).scalar_one()
    )
    verified_inspections = int(
        (
            await session.execute(
                select(func.count(Inspection.id)).where(Inspection.is_verified.is_(True))
            )
        ).scalar_one()
    )

    mean_confidence = float(
        (await session.execute(select(func.avg(Inspection.overall_confidence)))).scalar()
        or 0.0
    )
    mean_perch = (await session.execute(select(func.avg(Inspection.perch_score)))).scalar()

    async def distribution(column: Any) -> dict[str, int]:
        rows = (
            await session.execute(
                select(column, func.count()).where(column.isnot(None)).group_by(column)
            )
        ).all()
        return {str(value): int(count) for value, count in rows}

    voltage_distribution = await distribution(Inspection.predicted_voltage_class)
    utility_distribution = await distribution(Inspection.predicted_utility)
    material_distribution = await distribution(Inspection.pole_material)
    structure_distribution = await distribution(Inspection.structure_type)

    # Success rate: fraction of verifications where the class call held up.
    verdicts = (
        await session.execute(
            select(Verification.prediction_was_correct).where(
                Verification.prediction_was_correct.isnot(None)
            )
        )
    ).scalars().all()
    success_rate = (sum(1 for v in verdicts if v) / len(verdicts)) if verdicts else None

    # Confidence histogram and hardware frequency need row access.
    rows = (
        await session.execute(
            select(
                Inspection.overall_confidence,
                Inspection.perch_score,
                Inspection.detected_hardware,
                Inspection.created_at,
            )
        )
    ).all()

    confidence_hist = {
        _bucket_label(low, high): 0 for low, high in CONFIDENCE_BUCKETS
    }
    perch_hist = {_bucket_label(low, high): 0 for low, high in PERCH_BUCKETS}
    hardware: Counter[str] = Counter()
    per_day: Counter[str] = Counter()
    cutoff = datetime.now(UTC) - timedelta(days=days)

    for confidence, perch_score, detected, created_at in rows:
        for low, high in CONFIDENCE_BUCKETS:
            if low <= (confidence or 0.0) < high:
                confidence_hist[_bucket_label(low, high)] += 1
                break
        if perch_score is not None:
            for low, high in PERCH_BUCKETS:
                if low <= perch_score < high:
                    perch_hist[_bucket_label(low, high)] += 1
                    break
        for label, payload in (detected or {}).items():
            if isinstance(payload, dict) and payload.get("present"):
                hardware[label] += 1
        if created_at and created_at >= cutoff:
            per_day[created_at.date().isoformat()] += 1

    # Confusion matrix: predicted class vs verified class.
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    pairs = (
        await session.execute(
            select(Verification.predicted_snapshot, Verification.actual_voltage_class).where(
                Verification.actual_voltage_class.isnot(None)
            )
        )
    ).all()
    for snapshot, actual in pairs:
        predicted = (snapshot or {}).get("voltage_class") or "unknown"
        confusion[predicted][actual] += 1

    top_perch = (
        await session.execute(
            select(Inspection)
            .where(Inspection.perch_score.isnot(None))
            .order_by(Inspection.perch_score.desc())
            .limit(10)
        )
    ).scalars().all()

    return AdminStats(
        total_inspections=total_inspections,
        total_verifications=total_verifications,
        verified_fraction=(
            verified_inspections / total_inspections if total_inspections else 0.0
        ),
        prediction_success_rate=success_rate,
        mean_confidence=round(mean_confidence, 3),
        confidence_histogram=confidence_hist,
        voltage_class_distribution=voltage_distribution,
        utility_distribution=dict(
            sorted(utility_distribution.items(), key=lambda kv: -kv[1])[:20]
        ),
        pole_material_distribution=material_distribution,
        structure_type_distribution=structure_distribution,
        hardware_frequency=dict(hardware.most_common(25)),
        perch_score_distribution=perch_hist,
        mean_perch_score=round(float(mean_perch), 1) if mean_perch is not None else None,
        top_perch_sites=[
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
            for row in top_perch
        ],
        inspections_per_day=dict(sorted(per_day.items())),
        confusion={k: dict(v) for k, v in confusion.items()},
    )


@router.get(
    "/training-data",
    response_model=list[TrainingExample],
    summary="Verified inspections as training examples",
)
async def training_data(
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
    only_corrections: bool = False,
) -> list[TrainingExample]:
    return await build_training_examples(session, limit=limit, only_corrections=only_corrections)


@router.get(
    "/training-data.jsonl",
    summary="Training examples as newline-delimited JSON for a fine-tuning run",
    response_class=PlainTextResponse,
)
async def training_data_jsonl(
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=20000)] = 5000,
    only_corrections: bool = False,
) -> PlainTextResponse:
    examples = await build_training_examples(
        session, limit=limit, only_corrections=only_corrections
    )
    return PlainTextResponse(
        training_jsonl(examples),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": 'attachment; filename="gridline-training.jsonl"'},
    )
