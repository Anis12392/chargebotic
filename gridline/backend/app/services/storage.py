"""Photo storage.

S3-compatible object storage (AWS S3, MinIO, Cloudflare R2) when credentials
are configured; otherwise the local filesystem so the stack runs with nothing
but ``docker compose up``. Both backends expose the same three operations, so
nothing upstream knows which is in use.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from ..config import settings

logger = logging.getLogger(__name__)

THUMBNAIL_MAX_EDGE = 512
#: Long edge the vision model receives. Larger costs more tokens for no gain;
#: smaller loses the insulator detail the whole inference depends on.
ANALYSIS_MAX_EDGE = 1568


class StoredPhoto:
    def __init__(
        self,
        key: str,
        url: str | None,
        thumbnail_key: str | None,
        thumbnail_url: str | None,
        sha256: str,
        size_bytes: int,
    ) -> None:
        self.key = key
        self.url = url
        self.thumbnail_key = thumbnail_key
        self.thumbnail_url = thumbnail_url
        self.sha256 = sha256
        self.size_bytes = size_bytes


class StorageBackend(Protocol):
    async def put(self, key: str, data: bytes, content_type: str) -> str | None: ...
    async def get(self, key: str) -> bytes | None: ...
    async def url_for(self, key: str) -> str | None: ...


class LocalStorage:
    """Filesystem backend. Files are served by the API's /media route."""

    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Keys are generated internally, but normalise anyway so a crafted key
        # can never escape the storage root.
        safe = Path(key).as_posix().lstrip("/")
        resolved = (self.root / safe).resolve()
        if not str(resolved).startswith(str(self.root.resolve())):
            raise ValueError("Invalid storage key")
        return resolved

    async def put(self, key: str, data: bytes, content_type: str) -> str | None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)
        return f"/media/{key}"

    async def get(self, key: str) -> bytes | None:
        path = self._path(key)
        if not path.exists():
            return None
        return await asyncio.to_thread(path.read_bytes)

    async def url_for(self, key: str) -> str | None:
        return f"/media/{key}"


class S3Storage:
    """S3-compatible backend using boto3 off the event loop."""

    def __init__(self) -> None:
        import boto3  # imported lazily so local dev needs no AWS SDK

        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            config=__import__("botocore.config", fromlist=["Config"]).Config(
                s3={"addressing_style": "path" if settings.s3_force_path_style else "auto"},
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )
        self.bucket = settings.s3_bucket

    async def put(self, key: str, data: bytes, content_type: str) -> str | None:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return await self.url_for(key)

    async def get(self, key: str) -> bytes | None:
        try:
            response = await asyncio.to_thread(
                self._client.get_object, Bucket=self.bucket, Key=key
            )
            return response["Body"].read()
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("S3 get failed for %s: %s", key, exc)
            return None

    async def url_for(self, key: str) -> str | None:
        if settings.s3_public_base_url:
            return f"{settings.s3_public_base_url.rstrip('/')}/{key}"
        try:
            return await asyncio.to_thread(
                self._client.generate_presigned_url,
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=7 * 24 * 3600,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("Presign failed for %s: %s", key, exc)
            return None


_backend: StorageBackend | None = None


def get_backend() -> StorageBackend:
    global _backend
    if _backend is None:
        if settings.storage_is_s3:
            try:
                _backend = S3Storage()
                logger.info("Using S3 storage backend (bucket=%s)", settings.s3_bucket)
            except Exception as exc:
                logger.error("S3 backend unavailable, falling back to local disk: %s", exc)
                _backend = LocalStorage(settings.local_storage_dir)
        else:
            logger.info("Using local disk storage at %s", settings.local_storage_dir)
            _backend = LocalStorage(settings.local_storage_dir)
    return _backend


def reset_backend() -> None:
    """Test hook."""
    global _backend
    _backend = None


def normalise_for_analysis(data: bytes) -> tuple[bytes, str]:
    """Downscale and re-encode for the vision model. Strips EXIF as a side effect.

    Stripping EXIF matters: field photos carry the operator's device serial and
    a second copy of the GPS fix, and neither should leave the system inside an
    image sent to a third-party model.
    """
    try:
        from PIL import Image, ImageOps
    except ImportError:  # pragma: no cover
        return data, "image/jpeg"

    try:
        with Image.open(io.BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            img.thumbnail((ANALYSIS_MAX_EDGE, ANALYSIS_MAX_EDGE), Image.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=88, optimize=True)
            return buffer.getvalue(), "image/jpeg"
    except Exception as exc:
        logger.warning("Image normalisation failed, using original bytes: %s", exc)
        return data, "image/jpeg"


def make_thumbnail(data: bytes) -> bytes | None:
    try:
        from PIL import Image, ImageOps
    except ImportError:  # pragma: no cover
        return None
    try:
        with Image.open(io.BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            img.thumbnail((THUMBNAIL_MAX_EDGE, THUMBNAIL_MAX_EDGE), Image.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=75, optimize=True)
            return buffer.getvalue()
    except Exception as exc:
        logger.warning("Thumbnail generation failed: %s", exc)
        return None


async def store_photo(data: bytes, inspection_id: uuid.UUID) -> StoredPhoto:
    backend = get_backend()
    digest = hashlib.sha256(data).hexdigest()
    stamp = datetime.now(UTC).strftime("%Y/%m/%d")
    key = f"inspections/{stamp}/{inspection_id}.jpg"

    url = await backend.put(key, data, "image/jpeg")

    thumbnail_key = None
    thumbnail_url = None
    thumbnail = make_thumbnail(data)
    if thumbnail:
        thumbnail_key = f"inspections/{stamp}/{inspection_id}_thumb.jpg"
        thumbnail_url = await backend.put(thumbnail_key, thumbnail, "image/jpeg")

    return StoredPhoto(
        key=key,
        url=url,
        thumbnail_key=thumbnail_key,
        thumbnail_url=thumbnail_url,
        sha256=digest,
        size_bytes=len(data),
    )
