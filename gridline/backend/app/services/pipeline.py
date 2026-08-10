"""End-to-end analysis pipeline: photo + location -> stored engineering report."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Inspection, Verification
from ..schemas import (
    CaptureContext,
    EngineeringReport,
    GISContext,
    PerchSuitability,
    VisionAnalysis,
)
from . import storage
from .gis import GISEngine, haversine_m
from .inference import InferenceEngine, InferenceResult
from .perch import HistoricalStats, PerchScorer
from .vision import VisionAnalyzer

logger = logging.getLogger(__name__)

#: Radius over which past perch outcomes are considered representative.
HISTORY_RADIUS_M = 1_000.0


class AnalysisPipeline:
    def __init__(
        self,
        vision: VisionAnalyzer | None = None,
        gis: GISEngine | None = None,
        inference: InferenceEngine | None = None,
        perch: PerchScorer | None = None,
    ) -> None:
        self.vision = vision or VisionAnalyzer()
        self.gis = gis or GISEngine()
        self.inference = inference or InferenceEngine()
        self.perch = perch or PerchScorer()

    async def run(
        self,
        session: AsyncSession,
        image_bytes: bytes,
        capture: CaptureContext,
        include_perch: bool = True,
        gis_radius_m: int | None = None,
    ) -> EngineeringReport:
        started = time.perf_counter()
        inspection_id = uuid.uuid4()

        normalised, mime = storage.normalise_for_analysis(image_bytes)

        # Vision and GIS are independent; run them concurrently. The GIS call
        # gets its own session-free path because it may outlive the request's
        # transaction boundary on a slow Overpass day.
        vision_task = asyncio.create_task(self.vision.analyze(normalised, mime))
        gis_task = asyncio.create_task(
            self.gis.collect(session, capture.latitude, capture.longitude, gis_radius_m)
        )
        stored_task = asyncio.create_task(storage.store_photo(normalised, inspection_id))

        vision_result, gis_result, stored = await asyncio.gather(
            vision_task, gis_task, stored_task
        )

        inference = self.inference.run(vision_result, gis_result, capture)

        perch_result: PerchSuitability | None = None
        if include_perch:
            history = await self._history(session, capture.latitude, capture.longitude)
            perch_result = self.perch.score(
                vision_result,
                gis_result,
                capture,
                inference.voltage,
                inference.conductor,
                inference.current,
                history,
            )

        elapsed_ms = int((time.perf_counter() - started) * 1000)

        report = EngineeringReport(
            inspection_id=inspection_id,
            created_at=datetime.now(UTC),
            capture=capture,
            photo_url=stored.url,
            thumbnail_url=stored.thumbnail_url,
            utility=inference.utility,
            voltage=inference.voltage,
            conductor=inference.conductor,
            current=inference.current,
            perch=perch_result,
            overall_confidence=inference.overall_confidence,
            reasoning=inference.reasoning,
            evidence=inference.evidence,
            nearby_assets=gis_result.assets[:40],
            warnings=inference.warnings,
            vision=vision_result,
            gis_sources=gis_result.sources_queried,
            processing_ms=elapsed_ms,
        )

        await self._persist(
            session, inspection_id, report, vision_result, gis_result, inference, stored, perch_result
        )
        return report

    async def _history(
        self, session: AsyncSession, latitude: float, longitude: float
    ) -> HistoricalStats:
        """Aggregate previous perch outcomes near this location.

        Uses a bounding-box prefilter in SQL and an exact haversine in Python,
        which keeps the query portable across PostGIS and plain Postgres.
        """
        try:
            delta_lat = HISTORY_RADIUS_M / 111_320.0
            cos_lat = max(0.01, abs(__import__("math").cos(__import__("math").radians(latitude))))
            delta_lon = delta_lat / cos_lat

            stmt = (
                select(Verification, Inspection.latitude, Inspection.longitude)
                .join(Inspection, Verification.inspection_id == Inspection.id)
                .where(
                    Inspection.latitude.between(latitude - delta_lat, latitude + delta_lat),
                    Inspection.longitude.between(longitude - delta_lon, longitude + delta_lon),
                    Verification.perch_outcome.isnot(None),
                )
                .limit(500)
            )
            rows = (await session.execute(stmt)).all()
        except Exception as exc:  # pragma: no cover - history must never block analysis
            logger.warning("Perch history lookup failed: %s", exc)
            return HistoricalStats()

        attempts = 0
        successes = 0
        harvested: list[float] = []
        for verification, lat, lon in rows:
            if haversine_m(latitude, longitude, lat, lon) > HISTORY_RADIUS_M:
                continue
            if verification.perch_outcome == "not_attempted":
                continue
            attempts += 1
            if verification.perch_outcome == "success":
                successes += 1
            if verification.harvested_power_w:
                harvested.append(verification.harvested_power_w)

        return HistoricalStats(
            attempts=attempts,
            successes=successes,
            mean_harvested_w=(sum(harvested) / len(harvested)) if harvested else None,
        )

    async def _persist(
        self,
        session: AsyncSession,
        inspection_id: uuid.UUID,
        report: EngineeringReport,
        vision: VisionAnalysis,
        gis: GISContext,
        inference: InferenceResult,
        stored: storage.StoredPhoto,
        perch: PerchSuitability | None,
    ) -> None:
        detected = {
            det.label: {"present": det.present, "confidence": det.confidence, "count": det.count}
            for det in vision.detections
            if det.present
        }

        inspection = Inspection(
            id=inspection_id,
            latitude=report.capture.latitude,
            longitude=report.capture.longitude,
            geom=f"SRID=4326;POINT({report.capture.longitude} {report.capture.latitude})",
            accuracy_m=report.capture.accuracy_m,
            altitude_m=report.capture.altitude_m,
            altitude_accuracy_m=report.capture.altitude_accuracy_m,
            heading_deg=report.capture.heading_deg,
            speed_ms=report.capture.speed_ms,
            captured_at=report.capture.captured_at,
            device_model=report.capture.device_model,
            capture_notes=report.capture.notes,
            photo_key=stored.key,
            photo_url=stored.url,
            thumbnail_key=stored.thumbnail_key,
            thumbnail_url=stored.thumbnail_url,
            photo_sha256=stored.sha256,
            photo_bytes=stored.size_bytes,
            predicted_voltage_class=inference.voltage.voltage_class.value,
            predicted_nominal_v=inference.voltage.most_likely_nominal_v,
            predicted_current_low_a=inference.current.low_a,
            predicted_current_high_a=inference.current.high_a,
            predicted_utility=inference.utility.name,
            predicted_conductor=inference.conductor.most_likely_codeword,
            overall_confidence=inference.overall_confidence,
            voltage_confidence=inference.voltage.class_confidence,
            utility_confidence=inference.utility.confidence,
            pole_material=vision.pole_material.value,
            structure_type=vision.structure_type.value,
            phase_count=vision.phase_count,
            conductor_count=vision.conductor_count,
            perch_score=perch.score if perch else None,
            perch_grade=perch.grade if perch else None,
            estimated_flux_density_ut=perch.estimated_flux_density_ut if perch else None,
            estimated_harvest_power_w=perch.estimated_harvest_power_w if perch else None,
            report=report.model_dump(mode="json"),
            vision=vision.model_dump(mode="json"),
            gis=gis.model_dump(mode="json"),
            detected_hardware=detected,
            processing_ms=report.processing_ms,
            model_name=vision.model_name,
        )
        session.add(inspection)
        await session.flush()


async def count_inspections(session: AsyncSession) -> int:
    return int((await session.execute(select(func.count(Inspection.id)))).scalar_one())
