"""End-to-end pipeline test with the database and both external services stubbed.

This is the closest thing to an integration test that runs without Postgres: it
exercises photo normalisation, storage, the null vision path, the disabled-GIS
path, inference, perch scoring and ORM row construction in one go.
"""

from __future__ import annotations

import pytest

from app.schemas import CaptureContext
from app.services import storage
from app.services.pipeline import AnalysisPipeline

from .conftest import make_jpeg


class FakeResult:
    def all(self):
        return []

    def scalar_one_or_none(self):
        return None


class RecordingSession:
    """Captures the ORM instance the pipeline builds without touching a database."""

    def __init__(self) -> None:
        self.added: list[object] = []

    async def execute(self, *_args, **_kwargs):
        return FakeResult()

    async def flush(self) -> None:
        return None

    def add(self, obj) -> None:
        self.added.append(obj)


@pytest.fixture
def offline(monkeypatch, tmp_path):
    from app.config import settings

    monkeypatch.setattr(settings, "external_gis_enabled", False)
    monkeypatch.setattr(settings, "vision_enabled", False)
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "local_storage_dir", str(tmp_path / "storage"))
    storage.reset_backend()
    yield
    storage.reset_backend()


class TestOfflinePipeline:
    async def test_produces_a_complete_report(self, offline):
        session = RecordingSession()
        report = await AnalysisPipeline().run(
            session,
            make_jpeg(400, 300),
            CaptureContext(latitude=37.7749, longitude=-122.4194, accuracy_m=8.0),
        )

        assert report.inspection_id
        assert report.photo_url
        assert report.thumbnail_url
        assert report.disclaimer
        assert report.processing_ms >= 0
        # With neither vision nor GIS there is nothing to conclude from.
        assert report.voltage.voltage_class.value == "unknown"
        assert report.overall_confidence < 0.2
        assert report.current.is_measured is False

    async def test_disclosure_warnings_are_raised(self, offline):
        report = await AnalysisPipeline().run(
            RecordingSession(),
            make_jpeg(),
            CaptureContext(latitude=37.7749, longitude=-122.4194),
        )
        codes = {w.code for w in report.warnings}
        assert "vision_unavailable" in codes
        assert "no_gis_coverage" in codes
        assert "treat_as_energised" in codes

    async def test_photo_is_written_to_storage(self, offline):
        report = await AnalysisPipeline().run(
            RecordingSession(),
            make_jpeg(),
            CaptureContext(latitude=37.7749, longitude=-122.4194),
        )
        key = report.photo_url.removeprefix("/media/")
        assert await storage.get_backend().get(key) is not None

    async def test_inspection_row_is_populated(self, offline):
        session = RecordingSession()
        report = await AnalysisPipeline().run(
            session,
            make_jpeg(),
            CaptureContext(
                latitude=37.7749,
                longitude=-122.4194,
                heading_deg=185.0,
                altitude_m=42.0,
                device_model="Pixel 9",
            ),
        )
        assert len(session.added) == 1
        row = session.added[0]
        assert row.id == report.inspection_id
        assert row.latitude == 37.7749
        assert row.heading_deg == 185.0
        assert row.device_model == "Pixel 9"
        assert row.geom == "SRID=4326;POINT(-122.4194 37.7749)"
        assert row.report["voltage"]["voltage_class"] == "unknown"
        assert row.photo_sha256 and len(row.photo_sha256) == 64

    async def test_perch_score_can_be_skipped(self, offline):
        report = await AnalysisPipeline().run(
            RecordingSession(),
            make_jpeg(),
            CaptureContext(latitude=37.7749, longitude=-122.4194),
            include_perch=False,
        )
        assert report.perch is None

    async def test_oversized_photo_is_downscaled_before_analysis(self, offline):
        import io

        from PIL import Image

        report = await AnalysisPipeline().run(
            RecordingSession(),
            make_jpeg(4000, 3000),
            CaptureContext(latitude=37.7749, longitude=-122.4194),
        )
        key = report.photo_url.removeprefix("/media/")
        data = await storage.get_backend().get(key)
        with Image.open(io.BytesIO(data)) as img:
            assert max(img.size) <= storage.ANALYSIS_MAX_EDGE
