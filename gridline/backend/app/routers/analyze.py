"""POST /analyze — the primary endpoint.

Accepts either a multipart upload (what the PWA sends) or a JSON body with a
base64 image (what integrations and tests send).
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import get_db
from ..deps import PipelineDep, rate_limit_analyze
from ..schemas import AnalyzeRequest, CaptureContext, EngineeringReport

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])

#: Magic bytes for the formats a phone camera actually produces. Checked on the
#: bytes rather than the declared Content-Type, which a client controls freely.
IMAGE_SIGNATURES: tuple[bytes, ...] = (
    b"\xff\xd8\xff",  # JPEG
    b"\x89PNG\r\n\x1a\n",  # PNG
)


def _looks_like_image(data: bytes) -> bool:
    if any(data.startswith(sig) for sig in IMAGE_SIGNATURES):
        return True
    # RIFF container: WebP is RIFF....WEBP, and the brand has to be checked or
    # any RIFF file (WAV, AVI) would pass.
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True
    # ISO base media file format: HEIC/HEIF from iPhones. The box length occupies
    # the first four bytes, so the brand at offset 4 is what identifies it.
    return data[4:8] == b"ftyp" and data[8:12] in {
        b"heic",
        b"heix",
        b"hevc",
        b"heim",
        b"heis",
        b"mif1",
        b"msf1",
    }


def _validate_image(data: bytes) -> None:
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No image data supplied"
        )
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Image exceeds the {settings.max_upload_bytes // (1024 * 1024)} MB limit"
            ),
        )
    if not _looks_like_image(data):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported image format. Send JPEG, PNG, WebP or HEIC.",
        )


def _decode_base64_image(payload: str) -> bytes:
    # Accept both a bare base64 string and a full data URL.
    if payload.startswith("data:"):
        _, _, payload = payload.partition(",")
    try:
        return base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed base64 image"
        ) from exc


@router.post(
    "/analyze",
    response_model=EngineeringReport,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_analyze)],
    summary="Analyse a photograph of overhead line infrastructure",
)
async def analyze_multipart(
    pipeline: PipelineDep,
    session: Annotated[AsyncSession, Depends(get_db)],
    photo: Annotated[UploadFile, File(description="Photograph of the structure")],
    capture: Annotated[
        str, Form(description="JSON-encoded CaptureContext (GPS, heading, timestamp)")
    ],
    include_perch_score: Annotated[bool, Form()] = True,
    gis_radius_m: Annotated[int | None, Form()] = None,
) -> EngineeringReport:
    try:
        capture_context = CaptureContext.model_validate(json.loads(capture))
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid capture metadata: {exc}",
        ) from exc

    data = await photo.read()
    _validate_image(data)

    return await pipeline.run(
        session,
        data,
        capture_context,
        include_perch=include_perch_score,
        gis_radius_m=gis_radius_m,
    )


@router.post(
    "/analyze/json",
    response_model=EngineeringReport,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_analyze)],
    summary="Analyse a photograph supplied as base64 (integration clients)",
)
async def analyze_json(
    body: AnalyzeRequest,
    pipeline: PipelineDep,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> EngineeringReport:
    if not body.image_base64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="image_base64 is required for the JSON variant of /analyze",
        )
    data = _decode_base64_image(body.image_base64)
    _validate_image(data)

    return await pipeline.run(
        session,
        data,
        body.capture,
        include_perch=body.include_perch_score,
        gis_radius_m=body.gis_radius_m,
    )
