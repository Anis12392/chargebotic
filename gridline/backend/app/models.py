"""SQLAlchemy ORM models.

Spatial columns use PostGIS ``geography(Point, 4326)`` so distance queries are
metric without a projection step. Plain ``latitude``/``longitude`` floats are
kept alongside because every client needs them and it keeps the API layer free
of WKB decoding.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

#: JSONB on Postgres, plain JSON elsewhere (keeps unit tests dialect agnostic).
JSONType = JSONB().with_variant(JSON(), "sqlite")


class Inspection(Base):
    """One photo + location + the full engineering report generated from it."""

    __tablename__ = "inspections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # --- Capture ----------------------------------------------------------
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geom: Mapped[object | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    accuracy_m: Mapped[float | None] = mapped_column(Float)
    altitude_m: Mapped[float | None] = mapped_column(Float)
    altitude_accuracy_m: Mapped[float | None] = mapped_column(Float)
    heading_deg: Mapped[float | None] = mapped_column(Float)
    speed_ms: Mapped[float | None] = mapped_column(Float)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    device_model: Mapped[str | None] = mapped_column(String(120))
    capture_notes: Mapped[str | None] = mapped_column(Text)

    # --- Media ------------------------------------------------------------
    photo_key: Mapped[str | None] = mapped_column(String(512))
    photo_url: Mapped[str | None] = mapped_column(String(1024))
    thumbnail_key: Mapped[str | None] = mapped_column(String(512))
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024))
    photo_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    photo_bytes: Mapped[int | None] = mapped_column(Integer)

    # --- Predictions (denormalised for fast dashboards) -------------------
    predicted_voltage_class: Mapped[str | None] = mapped_column(String(32), index=True)
    predicted_nominal_v: Mapped[int | None] = mapped_column(Integer, index=True)
    predicted_current_low_a: Mapped[float | None] = mapped_column(Float)
    predicted_current_high_a: Mapped[float | None] = mapped_column(Float)
    predicted_utility: Mapped[str | None] = mapped_column(String(200), index=True)
    predicted_conductor: Mapped[str | None] = mapped_column(String(120))
    overall_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    voltage_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    utility_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    pole_material: Mapped[str | None] = mapped_column(String(32), index=True)
    structure_type: Mapped[str | None] = mapped_column(String(40), index=True)
    phase_count: Mapped[int | None] = mapped_column(Integer)
    conductor_count: Mapped[int | None] = mapped_column(Integer)

    # --- Perch suitability -------------------------------------------------
    perch_score: Mapped[float | None] = mapped_column(Float, index=True)
    perch_grade: Mapped[str | None] = mapped_column(String(20))
    estimated_flux_density_ut: Mapped[float | None] = mapped_column(Float)
    estimated_harvest_power_w: Mapped[float | None] = mapped_column(Float)

    # --- Full payloads ----------------------------------------------------
    report: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    vision: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    gis: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    detected_hardware: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    processing_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(80))

    verifications: Mapped[list[Verification]] = relationship(
        back_populates="inspection",
        cascade="all, delete-orphan",
        order_by="Verification.created_at.desc()",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_inspections_geom", "geom", postgresql_using="gist"),
        Index("ix_inspections_created_confidence", "created_at", "overall_confidence"),
    )


class Verification(Base):
    """An engineer's ground truth for an inspection. This is the training signal."""

    __tablename__ = "verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    verified_by: Mapped[str] = mapped_column(String(200), nullable=False)

    actual_voltage_v: Mapped[int | None] = mapped_column(Integer)
    actual_voltage_class: Mapped[str | None] = mapped_column(String(32))
    actual_utility: Mapped[str | None] = mapped_column(String(200))
    actual_conductor: Mapped[str | None] = mapped_column(String(120))
    measured_current_a: Mapped[float | None] = mapped_column(Float)
    measured_field_ut: Mapped[float | None] = mapped_column(Float)
    harvested_power_w: Mapped[float | None] = mapped_column(Float)

    prediction_was_correct: Mapped[bool | None] = mapped_column(Boolean)
    perch_outcome: Mapped[str | None] = mapped_column(String(20))

    corrected_hardware: Mapped[dict | None] = mapped_column(JSONType)
    field_measurements: Mapped[dict | None] = mapped_column(JSONType)
    drone_notes: Mapped[str | None] = mapped_column(Text)
    pilot_notes: Mapped[str | None] = mapped_column(Text)
    comments: Mapped[str | None] = mapped_column(Text)

    #: Frozen copy of what the model said, so a later model change cannot
    #: rewrite history for the training set.
    predicted_snapshot: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    inspection: Mapped[Inspection] = relationship(back_populates="verifications")


class GISCacheEntry(Base):
    """Cached Overpass / feature-service responses keyed by rounded location."""

    __tablename__ = "gis_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cache_key: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radius_m: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class UtilityTerritory(Base):
    """Optional local territory polygons, loaded from HIFLD or a state portal.

    When populated this beats operator-name guessing from nearby OSM tags.
    """

    __tablename__ = "utility_territories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    holding_company: Mapped[str | None] = mapped_column(String(200))
    state: Mapped[str | None] = mapped_column(String(40), index=True)
    source: Mapped[str] = mapped_column(String(60), nullable=False)
    boundary: Mapped[object | None] = mapped_column(
        Geography(geometry_type="MULTIPOLYGON", srid=4326), nullable=True
    )
    attributes: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    __table_args__ = (Index("ix_utility_territories_boundary", "boundary", postgresql_using="gist"),)
