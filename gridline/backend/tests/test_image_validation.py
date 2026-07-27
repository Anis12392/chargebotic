"""Upload validation is checked on the bytes, never on the declared type."""

import pytest
from fastapi import HTTPException

from app.routers.analyze import _looks_like_image, _validate_image

from .conftest import make_jpeg


class TestSignatureDetection:
    def test_accepts_a_real_jpeg(self):
        assert _looks_like_image(make_jpeg()) is True

    def test_accepts_png(self):
        assert _looks_like_image(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32) is True

    def test_accepts_webp_but_not_other_riff_containers(self):
        assert _looks_like_image(b"RIFF\x00\x00\x00\x00WEBPVP8 ") is True
        # A WAV file is also RIFF; it must not slip through.
        assert _looks_like_image(b"RIFF\x00\x00\x00\x00WAVEfmt ") is False

    def test_accepts_heic_from_an_iphone(self):
        assert _looks_like_image(b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00") is True

    def test_rejects_an_mp4_that_shares_the_iso_container(self):
        assert _looks_like_image(b"\x00\x00\x00\x18ftypisom\x00\x00\x00\x00") is False

    def test_rejects_arbitrary_bytes(self):
        assert _looks_like_image(b"#!/bin/sh\nrm -rf /") is False
        assert _looks_like_image(b"") is False


class TestValidation:
    def test_empty_upload_is_a_400(self):
        with pytest.raises(HTTPException) as exc:
            _validate_image(b"")
        assert exc.value.status_code == 400

    def test_oversized_upload_is_a_413(self, monkeypatch):
        from app.config import settings

        monkeypatch.setattr(settings, "max_upload_bytes", 16)
        with pytest.raises(HTTPException) as exc:
            _validate_image(make_jpeg())
        assert exc.value.status_code == 413

    def test_wrong_format_is_a_415(self):
        with pytest.raises(HTTPException) as exc:
            _validate_image(b"not an image at all, just text")
        assert exc.value.status_code == 415

    def test_size_is_checked_before_format(self, monkeypatch):
        # A 40 MB text file should be rejected for its size, not decoded first.
        from app.config import settings

        monkeypatch.setattr(settings, "max_upload_bytes", 1024)
        with pytest.raises(HTTPException) as exc:
            _validate_image(b"x" * 4096)
        assert exc.value.status_code == 413
