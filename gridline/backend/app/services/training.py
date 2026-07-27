"""Turn engineer verifications into training data.

Two consumers:

1. **Fine-tuning a vision model.** Each example pairs the stored photograph
   with the corrected hardware inventory an engineer signed off on.
2. **Recalibrating the rule engine.** The predicted/actual pairs feed a
   confusion matrix that tells us which evidence rules are systematically
   wrong, which is a far cheaper fix than retraining anything.

Only *verified* inspections are ever exported. A prediction the model made and
nobody checked is not training data — it is the model's own output, and
training on it is how a system convinces itself of its own mistakes.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Inspection, Verification
from ..schemas import TrainingExample


async def build_training_examples(
    session: AsyncSession,
    limit: int = 500,
    only_corrections: bool = False,
) -> list[TrainingExample]:
    """Export verified inspections.

    ``only_corrections`` keeps just the examples where the engineer disagreed
    with the model. Those carry most of the learning signal, but training on
    them alone skews the model toward the hard cases, so the default exports
    everything verified.
    """
    stmt = (
        select(Verification, Inspection)
        .join(Inspection, Verification.inspection_id == Inspection.id)
        .order_by(Verification.created_at.desc())
        .limit(limit)
    )
    if only_corrections:
        stmt = stmt.where(Verification.prediction_was_correct.is_(False))

    rows = (await session.execute(stmt)).all()

    examples: list[TrainingExample] = []
    for verification, inspection in rows:
        ground_truth: dict[str, Any] = {
            "voltage_v": verification.actual_voltage_v,
            "voltage_class": verification.actual_voltage_class,
            "utility": verification.actual_utility,
            "conductor": verification.actual_conductor,
            "measured_current_a": verification.measured_current_a,
            "measured_field_ut": verification.measured_field_ut,
            "harvested_power_w": verification.harvested_power_w,
            "perch_outcome": verification.perch_outcome,
            "hardware": _merge_hardware(
                inspection.detected_hardware, verification.corrected_hardware
            ),
            "field_measurements": verification.field_measurements,
        }
        ground_truth = {k: v for k, v in ground_truth.items() if v is not None}

        vision_payload = inspection.vision or {}
        gis_payload = inspection.gis or {}

        examples.append(
            TrainingExample(
                inspection_id=inspection.id,
                photo_url=inspection.photo_url,
                latitude=inspection.latitude,
                longitude=inspection.longitude,
                predicted=verification.predicted_snapshot or {},
                ground_truth=ground_truth,
                vision_features={
                    "phase_count": vision_payload.get("phase_count"),
                    "conductor_count": vision_payload.get("conductor_count"),
                    "pole_material": vision_payload.get("pole_material"),
                    "structure_type": vision_payload.get("structure_type"),
                    "crossarm_config": vision_payload.get("crossarm_config"),
                    "insulator_type": vision_payload.get("insulator_type"),
                    "insulator_disc_count": vision_payload.get("insulator_disc_count"),
                    "conductor_covering": vision_payload.get("conductor_covering"),
                    "image_quality": vision_payload.get("image_quality"),
                },
                gis_features={
                    "asset_count": len(gis_payload.get("assets", []) or []),
                    "operators": gis_payload.get("operators", []),
                    "voltages_v": gis_payload.get("voltages_v", []),
                    "sources": gis_payload.get("sources_queried", []),
                },
                verified_by=verification.verified_by,
                verified_at=verification.created_at,
            )
        )
    return examples


def _merge_hardware(
    detected: dict[str, Any] | None, corrected: dict[str, Any] | None
) -> dict[str, bool]:
    """Corrections win; anything the engineer did not touch keeps the detection."""
    merged: dict[str, bool] = {}
    for label, payload in (detected or {}).items():
        if isinstance(payload, dict):
            merged[label] = bool(payload.get("present"))
        else:
            merged[label] = bool(payload)
    for label, present in (corrected or {}).items():
        merged[label] = bool(present)
    return merged


def training_jsonl(examples: list[TrainingExample]) -> str:
    """Newline-delimited JSON, one example per line."""
    return "\n".join(json.dumps(e.model_dump(mode="json"), sort_keys=True) for e in examples)


def calibration_report(examples: list[TrainingExample]) -> dict[str, Any]:
    """Where the rule engine is systematically wrong.

    Returns per-predicted-class accuracy plus the mean confidence the model had
    when it was right versus wrong. A model whose confidence does not separate
    those two populations is not calibrated, whatever its accuracy.
    """
    by_class: dict[str, dict[str, float]] = {}
    confident_when_right: list[float] = []
    confident_when_wrong: list[float] = []

    for example in examples:
        predicted_class = example.predicted.get("voltage_class") or "unknown"
        actual_class = example.ground_truth.get("voltage_class")
        if not actual_class:
            continue
        bucket = by_class.setdefault(predicted_class, {"correct": 0, "total": 0})
        bucket["total"] += 1
        confidence = float(example.predicted.get("voltage_confidence") or 0.0)
        if predicted_class == actual_class:
            bucket["correct"] += 1
            confident_when_right.append(confidence)
        else:
            confident_when_wrong.append(confidence)

    return {
        "per_class_accuracy": {
            cls: round(vals["correct"] / vals["total"], 3) if vals["total"] else None
            for cls, vals in by_class.items()
        },
        "sample_counts": {cls: int(vals["total"]) for cls, vals in by_class.items()},
        "mean_confidence_when_correct": (
            round(sum(confident_when_right) / len(confident_when_right), 3)
            if confident_when_right
            else None
        ),
        "mean_confidence_when_wrong": (
            round(sum(confident_when_wrong) / len(confident_when_wrong), 3)
            if confident_when_wrong
            else None
        ),
        "is_calibrated": (
            bool(
                confident_when_right
                and confident_when_wrong
                and (sum(confident_when_right) / len(confident_when_right))
                > (sum(confident_when_wrong) / len(confident_when_wrong)) + 0.1
            )
        ),
    }
