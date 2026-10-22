"""Pydantic contracts for the public API and for the internal service layer."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .services.knowledge import VoltageClass


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Capture metadata
# ---------------------------------------------------------------------------


class CaptureContext(BaseModel):
    """Everything the handset records at the moment the shutter fires."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy_m: float | None = Field(default=None, ge=0, description="GPS horizontal accuracy")
    altitude_m: float | None = None
    altitude_accuracy_m: float | None = Field(default=None, ge=0)
    heading_deg: float | None = Field(default=None)
    speed_ms: float | None = Field(default=None, ge=0)
    captured_at: datetime | None = None
    device_model: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("heading_deg", mode="before")
    @classmethod
    def _normalise_heading(cls, value: float | None) -> float | None:
        """Wrap into [0, 360).

        Compass headings arrive from the Web Orientation API and from EXIF, and
        both occasionally overshoot (370, -5) after the client applies its own
        magnetic declination correction. Wrapping is the right response;
        rejecting the whole capture over it is not.
        """
        if value is None:
            return None
        return float(value) % 360.0


# ---------------------------------------------------------------------------
# Vision
# ---------------------------------------------------------------------------


class PoleMaterial(str, Enum):
    WOOD = "wood"
    STEEL = "steel"
    CONCRETE = "concrete"
    COMPOSITE = "composite"
    LATTICE_STEEL = "lattice_steel"
    UNKNOWN = "unknown"


class StructureType(str, Enum):
    DISTRIBUTION_POLE = "distribution_pole"
    SUBTRANSMISSION_POLE = "subtransmission_pole"
    TRANSMISSION_TOWER = "transmission_tower"
    H_FRAME = "h_frame"
    DEAD_END = "dead_end"
    SUSPENSION = "suspension"
    SERVICE_POLE = "service_pole"
    UNKNOWN = "unknown"


class InsulatorType(str, Enum):
    PIN = "pin"
    POST = "post"
    SUSPENSION_DISC = "suspension_disc"
    POLYMER_LONGROD = "polymer_longrod"
    STRAIN = "strain"
    SPOOL = "spool"
    UNKNOWN = "unknown"


class CrossarmConfig(str, Enum):
    NONE = "none"
    SINGLE = "single"
    DOUBLE = "double"
    ARMLESS = "armless"
    TRIANGULAR = "triangular"
    H_FRAME = "h_frame"
    DAVIT = "davit"
    UNKNOWN = "unknown"


class ConductorCovering(str, Enum):
    BARE = "bare"
    COVERED = "covered"
    SPACER_CABLE = "spacer_cable"
    TRIPLEX_SECONDARY = "triplex_secondary"
    UNKNOWN = "unknown"


class Detection(BaseModel):
    """One thing the vision model claims to see, with its own confidence."""

    label: str
    present: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    count: int | None = Field(default=None, ge=0)
    note: str | None = None
    bbox: list[float] | None = Field(
        default=None,
        description="Normalised [x_min, y_min, x_max, y_max] if the model localised it",
    )

    @field_validator("bbox")
    @classmethod
    def _check_bbox(cls, value: list[float] | None) -> list[float] | None:
        if value is None:
            return None
        if len(value) != 4:
            raise ValueError("bbox must have exactly 4 values")
        return value


class MeasurementEstimate(BaseModel):
    """A dimensional estimate from imagery, always with an explicit range."""

    value: float | None = None
    low: float | None = None
    high: float | None = None
    unit: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    basis: str | None = Field(
        default=None, description="What reference object the scale was derived from"
    )


class VisionAnalysis(BaseModel):
    """Structured output of the image understanding stage."""

    phase_count: int | None = Field(default=None, ge=0, le=12)
    conductor_count: int | None = Field(default=None, ge=0, le=48)
    pole_material: PoleMaterial = PoleMaterial.UNKNOWN
    structure_type: StructureType = StructureType.UNKNOWN
    crossarm_config: CrossarmConfig = CrossarmConfig.UNKNOWN
    crossarm_count: int | None = Field(default=None, ge=0, le=8)
    insulator_type: InsulatorType = InsulatorType.UNKNOWN
    insulator_disc_count: int | None = Field(
        default=None, ge=0, le=40, description="Discs per suspension string, if a string is visible"
    )
    insulator_length: MeasurementEstimate = Field(
        default_factory=lambda: MeasurementEstimate(unit="mm")
    )
    conductor_spacing: MeasurementEstimate = Field(
        default_factory=lambda: MeasurementEstimate(unit="m")
    )
    conductor_diameter: MeasurementEstimate = Field(
        default_factory=lambda: MeasurementEstimate(unit="mm")
    )
    conductor_covering: ConductorCovering = ConductorCovering.UNKNOWN
    bundled_subconductors: int | None = Field(default=None, ge=1, le=8)

    detections: list[Detection] = Field(default_factory=list)

    image_quality: float = Field(default=0.5, ge=0.0, le=1.0)
    obstructed: bool = False
    is_power_infrastructure: bool = True
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    model_name: str = "unavailable"
    raw_notes: str | None = None

    def detection(self, label: str) -> Detection | None:
        for det in self.detections:
            if det.label == label:
                return det
        return None

    def has(self, label: str, min_confidence: float = 0.5) -> bool:
        det = self.detection(label)
        return bool(det and det.present and det.confidence >= min_confidence)


#: The canonical checklist the vision stage must answer for every image.
VISION_DETECTION_LABELS: tuple[str, ...] = (
    "transformer",
    "recloser",
    "capacitor_bank",
    "switch",
    "cutout_fuse",
    "dead_end_pole",
    "suspension_pole",
    "transmission_tower",
    "distribution_pole",
    "shield_wire",
    "neutral_conductor",
    "secondary_rack",
    "streetlight",
    "guy_wire",
    "riser_cable",
    "warning_marker",
    "bird_diverter",
    "bird_guard",
    "corona_ring",
    "vibration_damper",
    "spacer_cable",
    "covered_conductor",
    "communication_cable",
    "vegetation_contact",
    "pole_id_tag",
)


# ---------------------------------------------------------------------------
# GIS
# ---------------------------------------------------------------------------


class GISAsset(BaseModel):
    """A nearby piece of infrastructure discovered in a GIS dataset."""

    source: Literal["overpass", "hifld", "usgs", "state_gis", "local"] = "overpass"
    element_type: str = Field(..., description="node | way | relation | feature")
    element_id: str
    asset_kind: str = Field(
        ..., description="line | minor_line | tower | pole | substation | portal | cable | plant"
    )
    name: str | None = None
    operator: str | None = None
    voltage_v: list[int] = Field(default_factory=list)
    circuits: int | None = None
    cables: int | None = None
    wires: str | None = None
    ref: str | None = Field(default=None, description="Pole ID / circuit reference")
    frequency_hz: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance_m: float | None = None
    bearing_deg: float | None = None
    tags: dict[str, Any] = Field(default_factory=dict)
    geometry: dict[str, Any] | None = Field(default=None, description="GeoJSON geometry")


class GISContext(BaseModel):
    """Everything the GIS engine found around the capture point."""

    query_latitude: float
    query_longitude: float
    radius_m: int
    assets: list[GISAsset] = Field(default_factory=list)
    nearest_line: GISAsset | None = None
    nearest_substation: GISAsset | None = None
    nearest_structure: GISAsset | None = None
    operators: list[str] = Field(default_factory=list)
    voltages_v: list[int] = Field(default_factory=list)
    sources_queried: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    cached: bool = False

    @property
    def asset_count(self) -> int:
        return len(self.assets)


# ---------------------------------------------------------------------------
# Inference output
# ---------------------------------------------------------------------------


class EvidenceItem(BaseModel):
    """One traceable observation feeding a conclusion."""

    source: Literal["vision", "gis", "standards", "physics", "history", "user"]
    observation: str
    implication: str
    weight: float = Field(..., ge=0.0, le=1.0, description="Relative influence on the conclusion")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reference: str | None = Field(default=None, description="Standard or dataset citation")


class VoltageEstimate(BaseModel):
    voltage_class: VoltageClass
    class_label: str
    class_confidence: float = Field(..., ge=0.0, le=1.0)
    possible_nominal_v: list[int] = Field(default_factory=list)
    most_likely_nominal_v: int | None = None
    is_confirmed: bool = Field(
        default=False, description="True only when a GIS voltage tag or field measurement backs it"
    )
    confirmation_source: str | None = None
    alternatives: list[dict[str, Any]] = Field(default_factory=list)


class ConductorEstimate(BaseModel):
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    most_likely_codeword: str | None = None
    most_likely_material: str | None = None
    most_likely_size: str | None = None
    estimated_diameter_mm: float | None = None
    thermal_rating_a: int | None = None
    thermal_rating_basis: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class CurrentEstimate(BaseModel):
    """Never a measurement unless ``is_measured`` is true."""

    low_a: float | None = None
    high_a: float | None = None
    basis: str
    is_measured: bool = False
    measurement_source: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    caveat: str = (
        "Operating current is inferred from conductor thermal rating and typical "
        "utility loading factors. It is not a measurement of the current flowing "
        "in this circuit."
    )


class UtilityEstimate(BaseModel):
    name: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str | None = None
    region: str | None = None
    known_standard: bool = False
    alternatives: list[str] = Field(default_factory=list)


class Warning(BaseModel):
    severity: Literal["info", "caution", "danger"]
    code: str
    message: str


class PerchFactor(BaseModel):
    key: str
    label: str
    score: float = Field(..., ge=0.0, le=100.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    rationale: str


class PerchSuitability(BaseModel):
    """0-100 ranking of how good this span is for autonomous energy harvesting."""

    score: float = Field(..., ge=0.0, le=100.0)
    grade: Literal["excellent", "good", "marginal", "poor", "unsuitable"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    factors: list[PerchFactor] = Field(default_factory=list)
    estimated_flux_density_ut: float | None = None
    estimated_harvest_power_w: float | None = None
    harvest_assumptions: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    recommendation: str


class EngineeringReport(BaseModel):
    """The complete answer returned by POST /analyze."""

    inspection_id: uuid.UUID
    created_at: datetime
    capture: CaptureContext
    photo_url: str | None = None
    thumbnail_url: str | None = None

    utility: UtilityEstimate
    voltage: VoltageEstimate
    conductor: ConductorEstimate
    current: CurrentEstimate
    perch: PerchSuitability | None = None

    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    nearby_assets: list[GISAsset] = Field(default_factory=list)
    warnings: list[Warning] = Field(default_factory=list)
    vision: VisionAnalysis
    gis_sources: list[str] = Field(default_factory=list)
    processing_ms: int = 0
    disclaimer: str = (
        "GridLine AI produces evidence-based estimates from imagery and public "
        "GIS data. It does not measure voltage or current and must never be used "
        "as the basis for energised work, clearance decisions, or flight "
        "authorisation. Treat every conductor as energised at the highest "
        "plausible voltage until the operating utility confirms otherwise."
    )


# ---------------------------------------------------------------------------
# Requests / responses
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    """JSON body variant of /analyze (image supplied as a data URL or key)."""

    capture: CaptureContext
    image_base64: str | None = None
    image_key: str | None = None
    include_perch_score: bool = True
    gis_radius_m: int | None = Field(default=None, ge=25, le=5000)


class VerifyRequest(BaseModel):
    """An engineer confirming, correcting or enriching a prediction."""

    inspection_id: uuid.UUID
    verified_by: str = Field(..., min_length=1, max_length=200)
    actual_voltage_v: int | None = Field(default=None, ge=0, le=1_200_000)
    actual_utility: str | None = Field(default=None, max_length=200)
    actual_voltage_class: VoltageClass | None = None
    actual_conductor: str | None = Field(default=None, max_length=120)
    measured_current_a: float | None = Field(default=None, ge=0)
    measured_field_ut: float | None = Field(default=None, ge=0)
    harvested_power_w: float | None = Field(default=None, ge=0)
    corrected_hardware: dict[str, bool] | None = None
    prediction_was_correct: bool | None = None
    perch_outcome: Literal["success", "partial", "failure", "not_attempted"] | None = None
    drone_notes: str | None = Field(default=None, max_length=4000)
    pilot_notes: str | None = Field(default=None, max_length=4000)
    field_measurements: dict[str, Any] | None = None
    comments: str | None = Field(default=None, max_length=4000)


class VerificationRead(ORMModel):
    id: uuid.UUID
    inspection_id: uuid.UUID
    verified_by: str
    created_at: datetime
    actual_voltage_v: int | None
    actual_utility: str | None
    actual_conductor: str | None
    measured_current_a: float | None
    measured_field_ut: float | None
    harvested_power_w: float | None
    prediction_was_correct: bool | None
    perch_outcome: str | None
    drone_notes: str | None
    pilot_notes: str | None
    comments: str | None
    corrected_hardware: dict[str, Any] | None
    field_measurements: dict[str, Any] | None


class InspectionSummary(ORMModel):
    id: uuid.UUID
    created_at: datetime
    latitude: float
    longitude: float
    photo_url: str | None
    thumbnail_url: str | None
    predicted_voltage_class: str | None
    predicted_nominal_v: int | None
    predicted_utility: str | None
    overall_confidence: float
    perch_score: float | None
    is_verified: bool


class InspectionDetail(InspectionSummary):
    heading_deg: float | None
    altitude_m: float | None
    accuracy_m: float | None
    captured_at: datetime | None
    device_model: str | None
    report: dict[str, Any]
    vision: dict[str, Any]
    gis: dict[str, Any]
    verifications: list[VerificationRead] = Field(default_factory=list)


class MapResponse(BaseModel):
    center: dict[str, float]
    radius_m: int
    assets: list[GISAsset]
    inspections: list[InspectionSummary]
    sources: list[str]
    errors: list[str] = Field(default_factory=list)


class AdminStats(BaseModel):
    total_inspections: int
    total_verifications: int
    verified_fraction: float
    prediction_success_rate: float | None
    mean_confidence: float
    confidence_histogram: dict[str, int]
    voltage_class_distribution: dict[str, int]
    utility_distribution: dict[str, int]
    pole_material_distribution: dict[str, int]
    structure_type_distribution: dict[str, int]
    hardware_frequency: dict[str, int]
    perch_score_distribution: dict[str, int]
    mean_perch_score: float | None
    top_perch_sites: list[InspectionSummary]
    inspections_per_day: dict[str, int]
    confusion: dict[str, dict[str, int]]


class TrainingExample(BaseModel):
    """One row exported for model fine-tuning."""

    inspection_id: uuid.UUID
    photo_url: str | None
    latitude: float
    longitude: float
    predicted: dict[str, Any]
    ground_truth: dict[str, Any]
    vision_features: dict[str, Any]
    gis_features: dict[str, Any]
    verified_by: str
    verified_at: datetime


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    environment: str
    database: str
    storage: str
    vision: str
    gis: str
