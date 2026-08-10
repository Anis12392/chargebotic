"""Builders for realistic vision/GIS fixtures used across the test suite."""

from __future__ import annotations

from datetime import UTC, datetime

from app.schemas import (
    VISION_DETECTION_LABELS,
    CaptureContext,
    ConductorCovering,
    CrossarmConfig,
    Detection,
    GISAsset,
    GISContext,
    InsulatorType,
    MeasurementEstimate,
    PoleMaterial,
    StructureType,
    VisionAnalysis,
)


def capture(
    lat: float = 37.7749,
    lon: float = -122.4194,
    accuracy_m: float | None = 6.0,
    **kwargs,
) -> CaptureContext:
    return CaptureContext(
        latitude=lat,
        longitude=lon,
        accuracy_m=accuracy_m,
        heading_deg=kwargs.pop("heading_deg", 270.0),
        altitude_m=kwargs.pop("altitude_m", 15.0),
        captured_at=kwargs.pop("captured_at", datetime.now(UTC)),
        **kwargs,
    )


def _detections(present: dict[str, float] | None = None) -> list[Detection]:
    present = present or {}
    out = []
    for label in VISION_DETECTION_LABELS:
        if label in present:
            out.append(Detection(label=label, present=True, confidence=present[label]))
        else:
            out.append(Detection(label=label, present=False, confidence=0.8))
    return out


def vision_distribution_pole() -> VisionAnalysis:
    """A textbook 12 kV wood distribution pole with a pole-mounted transformer."""
    return VisionAnalysis(
        phase_count=3,
        conductor_count=4,
        pole_material=PoleMaterial.WOOD,
        structure_type=StructureType.DISTRIBUTION_POLE,
        crossarm_config=CrossarmConfig.SINGLE,
        crossarm_count=1,
        insulator_type=InsulatorType.PIN,
        insulator_length=MeasurementEstimate(
            value=180.0, low=160.0, high=200.0, unit="mm", confidence=0.7, basis="cutout body"
        ),
        conductor_spacing=MeasurementEstimate(
            value=0.9, low=0.8, high=1.0, unit="m", confidence=0.6, basis="crossarm length"
        ),
        conductor_diameter=MeasurementEstimate(
            value=14.3, low=13.0, high=16.0, unit="mm", confidence=0.5, basis="insulator groove"
        ),
        conductor_covering=ConductorCovering.BARE,
        detections=_detections(
            {
                "transformer": 0.92,
                "cutout_fuse": 0.88,
                "distribution_pole": 0.95,
                "neutral_conductor": 0.8,
                "guy_wire": 0.6,
            }
        ),
        image_quality=0.82,
        overall_confidence=0.85,
        model_name="test-vision",
    )


def vision_transmission_tower() -> VisionAnalysis:
    """A 230 kV lattice tower with 9-disc strings and bundled conductors."""
    return VisionAnalysis(
        phase_count=3,
        conductor_count=8,
        pole_material=PoleMaterial.LATTICE_STEEL,
        structure_type=StructureType.TRANSMISSION_TOWER,
        crossarm_config=CrossarmConfig.DOUBLE,
        insulator_type=InsulatorType.SUSPENSION_DISC,
        insulator_disc_count=9,
        insulator_length=MeasurementEstimate(
            value=1314.0, unit="mm", confidence=0.6, basis="disc count x 146 mm"
        ),
        conductor_spacing=MeasurementEstimate(value=6.0, unit="m", confidence=0.5),
        conductor_diameter=MeasurementEstimate(value=28.1, unit="mm", confidence=0.45),
        conductor_covering=ConductorCovering.BARE,
        bundled_subconductors=2,
        detections=_detections(
            {
                "transmission_tower": 0.96,
                "shield_wire": 0.85,
                "suspension_pole": 0.7,
                "vibration_damper": 0.6,
                "corona_ring": 0.55,
            }
        ),
        image_quality=0.9,
        overall_confidence=0.88,
        model_name="test-vision",
    )


def vision_secondary_service() -> VisionAnalysis:
    return VisionAnalysis(
        phase_count=1,
        conductor_count=3,
        pole_material=PoleMaterial.WOOD,
        structure_type=StructureType.SERVICE_POLE,
        crossarm_config=CrossarmConfig.NONE,
        insulator_type=InsulatorType.SPOOL,
        conductor_covering=ConductorCovering.TRIPLEX_SECONDARY,
        detections=_detections({"secondary_rack": 0.9, "streetlight": 0.8}),
        image_quality=0.75,
        overall_confidence=0.8,
        model_name="test-vision",
    )


def empty_gis(lat: float = 37.7749, lon: float = -122.4194) -> GISContext:
    return GISContext(query_latitude=lat, query_longitude=lon, radius_m=400)


def gis_with_line(
    voltage_v: list[int] | None = None,
    operator: str | None = "Pacific Gas and Electric Company",
    distance_m: float = 25.0,
    asset_kind: str = "minor_line",
    lat: float = 37.7749,
    lon: float = -122.4194,
) -> GISContext:
    assets = [
        GISAsset(
            source="overpass",
            element_type="way",
            element_id="123456",
            asset_kind=asset_kind,
            operator=operator,
            voltage_v=voltage_v or [],
            latitude=lat,
            longitude=lon,
            distance_m=distance_m,
            ref="1234-5678",
        ),
        GISAsset(
            source="overpass",
            element_type="node",
            element_id="99001",
            asset_kind="pole",
            operator=operator,
            latitude=lat,
            longitude=lon,
            distance_m=distance_m + 10,
        ),
    ]
    context = GISContext(query_latitude=lat, query_longitude=lon, radius_m=400, assets=assets)
    context.nearest_line = assets[0]
    context.nearest_structure = assets[1]
    context.operators = [operator] if operator else []
    context.voltages_v = sorted(voltage_v or [], reverse=True)
    context.sources_queried = ["overpass"]
    return context
