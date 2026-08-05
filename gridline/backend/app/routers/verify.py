"""POST /verify — engineers close the loop on a prediction.

A verification is the system's only source of ground truth, so it is stored
immutably alongside a frozen snapshot of what the model predicted at the time.
That snapshot is what makes the record usable as a training example later: if
the model changes, the historical pairing must not change with it.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import Inspection, Verification
from ..schemas import VerificationRead, VerifyRequest
from ..services.knowledge import classify_voltage

router = APIRouter(tags=["learning"])


@router.post(
    "/verify",
    response_model=VerificationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record an engineer's ground truth for an inspection",
)
async def verify(
    body: VerifyRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> VerificationRead:
    inspection = await session.get(Inspection, body.inspection_id)
    if inspection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found"
        )

    actual_class = body.actual_voltage_class
    if actual_class is None and body.actual_voltage_v is not None:
        actual_class = classify_voltage(body.actual_voltage_v)

    # When the engineer supplies a voltage but no explicit verdict, derive the
    # verdict by comparing classes rather than exact volts: predicting
    # "distribution, probably 12.47 kV" against an actual 13.2 kV is a correct
    # class call, and scoring it as a miss would poison the success metric.
    was_correct = body.prediction_was_correct
    if was_correct is None and actual_class is not None:
        was_correct = inspection.predicted_voltage_class == actual_class.value

    verification = Verification(
        inspection_id=inspection.id,
        verified_by=body.verified_by,
        actual_voltage_v=body.actual_voltage_v,
        actual_voltage_class=actual_class.value if actual_class else None,
        actual_utility=body.actual_utility,
        actual_conductor=body.actual_conductor,
        measured_current_a=body.measured_current_a,
        measured_field_ut=body.measured_field_ut,
        harvested_power_w=body.harvested_power_w,
        prediction_was_correct=was_correct,
        perch_outcome=body.perch_outcome,
        corrected_hardware=body.corrected_hardware,
        field_measurements=body.field_measurements,
        drone_notes=body.drone_notes,
        pilot_notes=body.pilot_notes,
        comments=body.comments,
        predicted_snapshot={
            "voltage_class": inspection.predicted_voltage_class,
            "nominal_v": inspection.predicted_nominal_v,
            "utility": inspection.predicted_utility,
            "conductor": inspection.predicted_conductor,
            "current_low_a": inspection.predicted_current_low_a,
            "current_high_a": inspection.predicted_current_high_a,
            "overall_confidence": inspection.overall_confidence,
            "voltage_confidence": inspection.voltage_confidence,
            "perch_score": inspection.perch_score,
            "detected_hardware": inspection.detected_hardware,
            "model_name": inspection.model_name,
        },
    )
    session.add(verification)

    inspection.is_verified = True
    await session.flush()
    await session.refresh(verification)

    return VerificationRead.model_validate(verification)


@router.get(
    "/inspection/{inspection_id}/verifications",
    response_model=list[VerificationRead],
    summary="All ground-truth records for an inspection",
)
async def list_verifications(
    inspection_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[VerificationRead]:
    inspection = await session.get(Inspection, inspection_id)
    if inspection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found"
        )
    return [VerificationRead.model_validate(v) for v in inspection.verifications]
