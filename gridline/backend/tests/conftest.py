from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.db import get_db
from app.deps import get_pipeline
from app.main import create_app
from app.schemas import (
    ConductorEstimate,
    CurrentEstimate,
    EngineeringReport,
    UtilityEstimate,
    VoltageEstimate,
)
from app.services.knowledge import VoltageClass

from . import factories as f


class StubSession:
    """Enough of AsyncSession for the HTTP layer tests, which never touch SQL."""

    async def execute(self, *args, **kwargs):
        raise AssertionError("StubSession does not run queries")

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    async def flush(self) -> None:
        return None

    def add(self, _obj) -> None:
        return None

    async def get(self, *_args, **_kwargs):
        return None


class StubPipeline:
    """Records what it was called with and returns a fixed report."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def run(self, session, image_bytes, capture, include_perch=True, gis_radius_m=None):
        self.calls.append(
            {
                "bytes": len(image_bytes),
                "capture": capture,
                "include_perch": include_perch,
                "gis_radius_m": gis_radius_m,
            }
        )
        return EngineeringReport(
            inspection_id=uuid.uuid4(),
            created_at=datetime.now(UTC),
            capture=capture,
            utility=UtilityEstimate(name="Test Utility", confidence=0.5),
            voltage=VoltageEstimate(
                voltage_class=VoltageClass.DISTRIBUTION,
                class_label=VoltageClass.DISTRIBUTION.label,
                class_confidence=0.7,
                possible_nominal_v=[12_470],
                most_likely_nominal_v=12_470,
            ),
            conductor=ConductorEstimate(confidence=0.4, most_likely_codeword="Penguin"),
            current=CurrentEstimate(low_a=35.0, high_a=196.0, basis="test", confidence=0.3),
            overall_confidence=0.6,
            vision=f.vision_distribution_pole(),
        )


def make_jpeg(width: int = 64, height: int = 64) -> bytes:
    """A real, decodable JPEG so image validation and Pillow both succeed."""
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (90, 110, 130)).save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def stub_pipeline() -> StubPipeline:
    return StubPipeline()


@pytest.fixture
async def client(stub_pipeline: StubPipeline):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: StubSession()
    app.dependency_overrides[get_pipeline] = lambda: stub_pipeline

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http

    app.dependency_overrides.clear()
