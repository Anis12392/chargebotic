"""HTTP-layer tests: validation, error shapes and contract stability."""

from __future__ import annotations

import base64
import json

from .conftest import make_jpeg


def capture_json(**overrides) -> str:
    payload = {"latitude": 37.7749, "longitude": -122.4194, "accuracy_m": 6.0, "heading_deg": 270}
    payload.update(overrides)
    return json.dumps(payload)


class TestAnalyzeMultipart:
    async def test_happy_path_returns_a_report(self, client, stub_pipeline):
        response = await client.post(
            "/analyze",
            files={"photo": ("pole.jpg", make_jpeg(), "image/jpeg")},
            data={"capture": capture_json()},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["voltage"]["voltage_class"] == "distribution"
        assert body["current"]["is_measured"] is False
        assert body["disclaimer"]
        assert stub_pipeline.calls[0]["capture"].latitude == 37.7749

    async def test_capture_metadata_is_forwarded(self, client, stub_pipeline):
        await client.post(
            "/analyze",
            files={"photo": ("pole.jpg", make_jpeg(), "image/jpeg")},
            data={"capture": capture_json(heading_deg=91.5), "gis_radius_m": "1200"},
        )
        call = stub_pipeline.calls[0]
        assert call["capture"].heading_deg == 91.5
        assert call["gis_radius_m"] == 1200

    async def test_heading_is_normalised_into_range(self, client, stub_pipeline):
        await client.post(
            "/analyze",
            files={"photo": ("pole.jpg", make_jpeg(), "image/jpeg")},
            data={"capture": capture_json(heading_deg=370)},
        )
        assert stub_pipeline.calls[0]["capture"].heading_deg == 10.0

    async def test_non_image_upload_is_rejected(self, client):
        response = await client.post(
            "/analyze",
            files={"photo": ("payload.txt", b"this is not an image", "text/plain")},
            data={"capture": capture_json()},
        )
        assert response.status_code == 415

    async def test_empty_upload_is_rejected(self, client):
        response = await client.post(
            "/analyze",
            files={"photo": ("empty.jpg", b"", "image/jpeg")},
            data={"capture": capture_json()},
        )
        assert response.status_code == 400

    async def test_malformed_capture_json_is_rejected(self, client):
        response = await client.post(
            "/analyze",
            files={"photo": ("pole.jpg", make_jpeg(), "image/jpeg")},
            data={"capture": "{not json"},
        )
        assert response.status_code == 422

    async def test_out_of_range_coordinates_are_rejected(self, client):
        response = await client.post(
            "/analyze",
            files={"photo": ("pole.jpg", make_jpeg(), "image/jpeg")},
            data={"capture": capture_json(latitude=145.0)},
        )
        assert response.status_code == 422

    async def test_oversized_upload_is_rejected(self, client, monkeypatch):
        from app.config import settings

        monkeypatch.setattr(settings, "max_upload_bytes", 1024)
        response = await client.post(
            "/analyze",
            files={"photo": ("big.jpg", make_jpeg(600, 600), "image/jpeg")},
            data={"capture": capture_json()},
        )
        assert response.status_code == 413


class TestAnalyzeJson:
    async def test_accepts_a_bare_base64_string(self, client):
        response = await client.post(
            "/analyze/json",
            json={
                "capture": {"latitude": 37.77, "longitude": -122.41},
                "image_base64": base64.b64encode(make_jpeg()).decode(),
            },
        )
        assert response.status_code == 201

    async def test_accepts_a_data_url(self, client):
        encoded = base64.b64encode(make_jpeg()).decode()
        response = await client.post(
            "/analyze/json",
            json={
                "capture": {"latitude": 37.77, "longitude": -122.41},
                "image_base64": f"data:image/jpeg;base64,{encoded}",
            },
        )
        assert response.status_code == 201

    async def test_malformed_base64_is_rejected(self, client):
        response = await client.post(
            "/analyze/json",
            json={
                "capture": {"latitude": 37.77, "longitude": -122.41},
                "image_base64": "!!!not base64!!!",
            },
        )
        assert response.status_code == 400

    async def test_missing_image_is_rejected(self, client):
        response = await client.post(
            "/analyze/json", json={"capture": {"latitude": 37.77, "longitude": -122.41}}
        )
        assert response.status_code == 400


class TestOpenAPIContract:
    async def test_documented_endpoints_are_present(self, client):
        spec = (await client.get("/openapi.json")).json()
        paths = spec["paths"]
        assert "/analyze" in paths
        assert "/inspection/{inspection_id}" in paths
        assert "/verify" in paths
        assert "/map" in paths

    async def test_description_states_the_measurement_limitation(self, client):
        spec = (await client.get("/openapi.json")).json()
        assert "does not measure voltage" in spec["info"]["description"]


class TestAdminAuth:
    async def test_admin_is_open_in_development_without_a_key(self, monkeypatch):
        # Exercised against the dependency directly: the endpoint behind it
        # needs a real database, and what is under test here is only whether
        # the guard admits the request.
        from app.config import settings
        from app.deps import require_admin

        monkeypatch.setattr(settings, "admin_api_key", None)
        monkeypatch.setattr(settings, "environment", "development")
        assert await require_admin(None) is None

    async def test_correct_key_is_accepted(self, monkeypatch):
        from app.config import settings
        from app.deps import require_admin

        monkeypatch.setattr(settings, "admin_api_key", "correct-key")
        assert await require_admin("correct-key") is None

    async def test_admin_is_refused_in_production_without_a_key(self, client, monkeypatch):
        from app.config import settings

        monkeypatch.setattr(settings, "admin_api_key", None)
        monkeypatch.setattr(settings, "environment", "production")
        response = await client.get("/admin/stats")
        assert response.status_code == 503

    async def test_wrong_key_is_rejected(self, client, monkeypatch):
        from app.config import settings

        monkeypatch.setattr(settings, "admin_api_key", "correct-key")
        response = await client.get("/admin/stats", headers={"X-Admin-Key": "wrong-key"})
        assert response.status_code == 403

    async def test_missing_header_is_rejected_when_a_key_is_configured(self, client, monkeypatch):
        from app.config import settings

        monkeypatch.setattr(settings, "admin_api_key", "correct-key")
        response = await client.get("/admin/stats")
        assert response.status_code == 401
