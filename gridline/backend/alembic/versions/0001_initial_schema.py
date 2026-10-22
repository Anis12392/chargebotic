"""Initial GridLine AI schema

Revision ID: 0001
Revises:
Create Date: 2026-07-27
"""

from __future__ import annotations

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "inspections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geography(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=True,
        ),
        sa.Column("accuracy_m", sa.Float()),
        sa.Column("altitude_m", sa.Float()),
        sa.Column("altitude_accuracy_m", sa.Float()),
        sa.Column("heading_deg", sa.Float()),
        sa.Column("speed_ms", sa.Float()),
        sa.Column("captured_at", sa.DateTime(timezone=True)),
        sa.Column("device_model", sa.String(120)),
        sa.Column("capture_notes", sa.Text()),
        sa.Column("photo_key", sa.String(512)),
        sa.Column("photo_url", sa.String(1024)),
        sa.Column("thumbnail_key", sa.String(512)),
        sa.Column("thumbnail_url", sa.String(1024)),
        sa.Column("photo_sha256", sa.String(64)),
        sa.Column("photo_bytes", sa.Integer()),
        sa.Column("predicted_voltage_class", sa.String(32)),
        sa.Column("predicted_nominal_v", sa.Integer()),
        sa.Column("predicted_current_low_a", sa.Float()),
        sa.Column("predicted_current_high_a", sa.Float()),
        sa.Column("predicted_utility", sa.String(200)),
        sa.Column("predicted_conductor", sa.String(120)),
        sa.Column("overall_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("voltage_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("utility_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("pole_material", sa.String(32)),
        sa.Column("structure_type", sa.String(40)),
        sa.Column("phase_count", sa.Integer()),
        sa.Column("conductor_count", sa.Integer()),
        sa.Column("perch_score", sa.Float()),
        sa.Column("perch_grade", sa.String(20)),
        sa.Column("estimated_flux_density_ut", sa.Float()),
        sa.Column("estimated_harvest_power_w", sa.Float()),
        sa.Column("report", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("vision", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("gis", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("detected_hardware", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("processing_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("model_name", sa.String(80)),
    )
    op.create_index("ix_inspections_created_at", "inspections", ["created_at"])
    op.create_index("ix_inspections_photo_sha256", "inspections", ["photo_sha256"])
    op.create_index("ix_inspections_predicted_voltage_class", "inspections", ["predicted_voltage_class"])
    op.create_index("ix_inspections_predicted_nominal_v", "inspections", ["predicted_nominal_v"])
    op.create_index("ix_inspections_predicted_utility", "inspections", ["predicted_utility"])
    op.create_index("ix_inspections_pole_material", "inspections", ["pole_material"])
    op.create_index("ix_inspections_structure_type", "inspections", ["structure_type"])
    op.create_index("ix_inspections_perch_score", "inspections", ["perch_score"])
    op.create_index("ix_inspections_is_verified", "inspections", ["is_verified"])
    op.create_index("ix_inspections_created_confidence", "inspections", ["created_at", "overall_confidence"])
    op.create_index("ix_inspections_geom", "inspections", ["geom"], postgresql_using="gist")

    op.create_table(
        "verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "inspection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inspections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("verified_by", sa.String(200), nullable=False),
        sa.Column("actual_voltage_v", sa.Integer()),
        sa.Column("actual_voltage_class", sa.String(32)),
        sa.Column("actual_utility", sa.String(200)),
        sa.Column("actual_conductor", sa.String(120)),
        sa.Column("measured_current_a", sa.Float()),
        sa.Column("measured_field_ut", sa.Float()),
        sa.Column("harvested_power_w", sa.Float()),
        sa.Column("prediction_was_correct", sa.Boolean()),
        sa.Column("perch_outcome", sa.String(20)),
        sa.Column("corrected_hardware", postgresql.JSONB()),
        sa.Column("field_measurements", postgresql.JSONB()),
        sa.Column("drone_notes", sa.Text()),
        sa.Column("pilot_notes", sa.Text()),
        sa.Column("comments", sa.Text()),
        sa.Column("predicted_snapshot", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("exported_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_verifications_inspection_id", "verifications", ["inspection_id"])
    op.create_index("ix_verifications_created_at", "verifications", ["created_at"])

    op.create_table(
        "gis_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cache_key", sa.String(160), nullable=False, unique=True),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("radius_m", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gis_cache_cache_key", "gis_cache", ["cache_key"], unique=True)
    op.create_index("ix_gis_cache_expires_at", "gis_cache", ["expires_at"])

    op.create_table(
        "utility_territories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("holding_company", sa.String(200)),
        sa.Column("state", sa.String(40)),
        sa.Column("source", sa.String(60), nullable=False),
        sa.Column(
            "boundary",
            geoalchemy2.types.Geography(
                geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False
            ),
            nullable=True,
        ),
        sa.Column("attributes", postgresql.JSONB(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_utility_territories_name", "utility_territories", ["name"])
    op.create_index("ix_utility_territories_state", "utility_territories", ["state"])
    op.create_index(
        "ix_utility_territories_boundary",
        "utility_territories",
        ["boundary"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_table("utility_territories")
    op.drop_table("gis_cache")
    op.drop_table("verifications")
    op.drop_table("inspections")
