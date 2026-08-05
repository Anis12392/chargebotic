"""Vision stage: turn a photograph into a structured hardware inventory.

Primary path is an OpenAI vision model constrained by a JSON schema. The prompt
is written to make abstention cheap: the model is told to return ``unknown``
and a low confidence rather than guess, because a wrong hardware detection
propagates into a wrong voltage class.

If no API key is configured, or the call fails, we fall back to a deterministic
analyzer that reports *nothing observed* with zero confidence. That is the
honest degradation: the report then rests entirely on GIS evidence and says so.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

import httpx
from pydantic import ValidationError

from ..config import settings
from ..schemas import (
    VISION_DETECTION_LABELS,
    ConductorCovering,
    CrossarmConfig,
    Detection,
    InsulatorType,
    MeasurementEstimate,
    PoleMaterial,
    StructureType,
    VisionAnalysis,
)

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """\
You are a transmission and distribution line inspector with 25 years of field
experience in North American utility construction. You are looking at a single
photograph of overhead electrical infrastructure taken from the ground.

Your job is to inventory what is physically visible. You are NOT asked to state
the voltage — a separate engine does that from your observations plus GIS data.

Hard rules:
1. Report only what you can actually see. If a feature is occluded, out of
   frame, or ambiguous, set it to "unknown" and give a low confidence.
2. Confidence is calibrated: 0.9+ means you would stake a report on it, 0.5
   means a coin flip, below 0.3 means you are guessing. Guessing is worse than
   abstaining here.
3. Dimensional estimates (insulator length, conductor spacing, conductor
   diameter) must be given as a low/high range and must name the reference
   object you scaled from (a standard suspension disc is 146 mm tall, a
   distribution crossarm is typically 2.4 m long, a standard cutout is about
   500 mm). If there is no usable scale reference, return nulls.
4. Count conductors carefully. Distinguish phase conductors from the neutral
   (usually lowest on a distribution pole), from shield/static wire (topmost on
   transmission), and from communication cables (lowest overall, usually thick
   and black, often in a bundle well below the power space).
5. If the image does not contain overhead electrical infrastructure, set
   is_power_infrastructure to false and leave everything else unknown.

Distinguishing features worth attention:
- Suspension disc strings: count the discs. Each disc is a separate porcelain
  or glass unit in the string.
- Pin/post insulators sit on top of a crossarm; suspension insulators hang
  below it; strain/dead-end insulators are in line with the conductor pull.
- Spacer cable: three covered conductors held in a triangle by insulated
  spacers hung from a messenger wire.
- Covered conductor (tree wire) looks matte and slightly thicker than bare
  conductor, and terminates at a bare section near hardware.
- Corona rings (metal hoops at insulator ends) only appear at high voltage.
- Bundled subconductors (2, 3 or 4 conductors per phase held by spacers) only
  appear at 230 kV and above.
"""

USER_PROMPT = """\
Analyse this photograph of overhead electrical infrastructure and return the
structured inventory. Include an entry in `detections` for EVERY label in this
list, even when absent (present=false, with your confidence in that absence):

{labels}

Return only the structured object.
"""


def _detection_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["label", "present", "confidence", "count", "note"],
        "properties": {
            "label": {"type": "string", "enum": list(VISION_DETECTION_LABELS)},
            "present": {"type": "boolean"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "count": {"type": ["integer", "null"], "minimum": 0},
            "note": {"type": ["string", "null"]},
        },
    }


def _measurement_schema(unit: str) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["value", "low", "high", "unit", "confidence", "basis"],
        "properties": {
            "value": {"type": ["number", "null"]},
            "low": {"type": ["number", "null"]},
            "high": {"type": ["number", "null"]},
            "unit": {"type": "string", "enum": [unit]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "basis": {"type": ["string", "null"]},
        },
    }


def build_response_schema() -> dict[str, Any]:
    """JSON schema handed to the model so the response is machine-checkable."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "is_power_infrastructure",
            "phase_count",
            "conductor_count",
            "pole_material",
            "structure_type",
            "crossarm_config",
            "crossarm_count",
            "insulator_type",
            "insulator_disc_count",
            "insulator_length",
            "conductor_spacing",
            "conductor_diameter",
            "conductor_covering",
            "bundled_subconductors",
            "detections",
            "image_quality",
            "obstructed",
            "overall_confidence",
            "raw_notes",
        ],
        "properties": {
            "is_power_infrastructure": {"type": "boolean"},
            "phase_count": {"type": ["integer", "null"], "minimum": 0, "maximum": 12},
            "conductor_count": {"type": ["integer", "null"], "minimum": 0, "maximum": 48},
            "pole_material": {"type": "string", "enum": [m.value for m in PoleMaterial]},
            "structure_type": {"type": "string", "enum": [s.value for s in StructureType]},
            "crossarm_config": {"type": "string", "enum": [c.value for c in CrossarmConfig]},
            "crossarm_count": {"type": ["integer", "null"], "minimum": 0, "maximum": 8},
            "insulator_type": {"type": "string", "enum": [i.value for i in InsulatorType]},
            "insulator_disc_count": {"type": ["integer", "null"], "minimum": 0, "maximum": 40},
            "insulator_length": _measurement_schema("mm"),
            "conductor_spacing": _measurement_schema("m"),
            "conductor_diameter": _measurement_schema("mm"),
            "conductor_covering": {
                "type": "string",
                "enum": [c.value for c in ConductorCovering],
            },
            "bundled_subconductors": {"type": ["integer", "null"], "minimum": 1, "maximum": 8},
            "detections": {"type": "array", "items": _detection_schema()},
            "image_quality": {"type": "number", "minimum": 0, "maximum": 1},
            "obstructed": {"type": "boolean"},
            "overall_confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "raw_notes": {"type": ["string", "null"]},
        },
    }


class VisionUnavailable(RuntimeError):
    """Raised when the vision provider cannot be reached or is disabled."""


class VisionAnalyzer:
    """Thin, testable wrapper over the vision provider."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.model = model or settings.vision_model
        self.base_url = (base_url or settings.openai_base_url or "https://api.openai.com/v1").rstrip(
            "/"
        )
        self._client = client

    @property
    def enabled(self) -> bool:
        return bool(settings.vision_enabled and self.api_key)

    async def analyze(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> VisionAnalysis:
        """Return a structured inventory, degrading to an empty one on failure."""
        if not self.enabled:
            logger.info("Vision provider disabled or unconfigured; using null analyzer")
            return null_analysis("vision_disabled")

        last_error: Exception | None = None
        for attempt in range(settings.vision_max_retries + 1):
            try:
                payload = await self._call_provider(image_bytes, mime_type)
                return _parse_provider_payload(payload, self.model)
            except (httpx.HTTPError, ValidationError, ValueError, KeyError) as exc:
                last_error = exc
                logger.warning(
                    "Vision attempt %s/%s failed: %s",
                    attempt + 1,
                    settings.vision_max_retries + 1,
                    exc,
                )

        logger.error("Vision analysis failed after retries: %s", last_error)
        return null_analysis(f"vision_error: {type(last_error).__name__}")

    async def _call_provider(self, image_bytes: bytes, mime_type: str) -> dict[str, Any]:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        body = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": USER_PROMPT.format(
                                labels="\n".join(f"- {label}" for label in VISION_DETECTION_LABELS)
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "overhead_line_inventory",
                    "strict": True,
                    "schema": build_response_schema(),
                },
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        client = self._client
        owns_client = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=settings.vision_timeout_seconds)
        try:
            response = await client.post(
                f"{self.base_url}/chat/completions", json=body, headers=headers
            )
            response.raise_for_status()
            data = response.json()
        finally:
            if owns_client:
                await client.aclose()

        content = data["choices"][0]["message"]["content"]
        return json.loads(content)


def _parse_provider_payload(payload: dict[str, Any], model_name: str) -> VisionAnalysis:
    """Validate and normalise the provider payload into ``VisionAnalysis``."""
    detections: list[Detection] = []
    seen: set[str] = set()
    for item in payload.get("detections", []) or []:
        label = item.get("label")
        if not label or label in seen:
            continue
        seen.add(label)
        detections.append(
            Detection(
                label=label,
                present=bool(item.get("present")),
                confidence=_clamp(item.get("confidence", 0.0)),
                count=item.get("count"),
                note=item.get("note"),
            )
        )

    # Any label the model skipped is recorded as an explicit non-observation so
    # downstream code never has to distinguish "absent" from "not asked".
    for label in VISION_DETECTION_LABELS:
        if label not in seen:
            detections.append(
                Detection(label=label, present=False, confidence=0.0, note="not reported by model")
            )

    analysis = VisionAnalysis(
        phase_count=payload.get("phase_count"),
        conductor_count=payload.get("conductor_count"),
        pole_material=_enum(PoleMaterial, payload.get("pole_material")),
        structure_type=_enum(StructureType, payload.get("structure_type")),
        crossarm_config=_enum(CrossarmConfig, payload.get("crossarm_config")),
        crossarm_count=payload.get("crossarm_count"),
        insulator_type=_enum(InsulatorType, payload.get("insulator_type")),
        insulator_disc_count=payload.get("insulator_disc_count"),
        insulator_length=_measurement(payload.get("insulator_length"), "mm"),
        conductor_spacing=_measurement(payload.get("conductor_spacing"), "m"),
        conductor_diameter=_measurement(payload.get("conductor_diameter"), "mm"),
        conductor_covering=_enum(ConductorCovering, payload.get("conductor_covering")),
        bundled_subconductors=payload.get("bundled_subconductors"),
        detections=detections,
        image_quality=_clamp(payload.get("image_quality", 0.5)),
        obstructed=bool(payload.get("obstructed", False)),
        is_power_infrastructure=bool(payload.get("is_power_infrastructure", True)),
        overall_confidence=_clamp(payload.get("overall_confidence", 0.0)),
        model_name=model_name,
        raw_notes=payload.get("raw_notes"),
    )
    return _sanity_check(analysis)


def _sanity_check(analysis: VisionAnalysis) -> VisionAnalysis:
    """Suppress internally inconsistent claims rather than propagate them."""
    # Bundled conductors and corona rings on a wood distribution pole is a
    # contradiction; drop the high-voltage marker rather than the structure.
    if analysis.pole_material == PoleMaterial.WOOD and (analysis.bundled_subconductors or 1) > 1:
        analysis.bundled_subconductors = 1
        analysis.raw_notes = _append_note(
            analysis.raw_notes,
            "Bundled subconductors reported on a wood pole; suppressed as implausible.",
        )

    # A transformer implies distribution; a transmission tower detection at the
    # same time is contradictory, so demote whichever has lower confidence.
    transformer = analysis.detection("transformer")
    tower = analysis.detection("transmission_tower")
    if transformer and tower and transformer.present and tower.present:
        weaker = transformer if transformer.confidence < tower.confidence else tower
        weaker.present = False
        weaker.note = _append_note(weaker.note, "suppressed: conflicts with the stronger detection")
        analysis.raw_notes = _append_note(
            analysis.raw_notes,
            f"Conflicting detections transformer/transmission_tower; suppressed {weaker.label}.",
        )

    if (
        analysis.conductor_count is not None
        and analysis.phase_count is not None
        and analysis.phase_count > analysis.conductor_count
    ):
        analysis.phase_count = analysis.conductor_count

    if not analysis.is_power_infrastructure:
        analysis.overall_confidence = 0.0

    return analysis


def _append_note(existing: str | None, addition: str) -> str:
    return f"{existing} {addition}".strip() if existing else addition


def null_analysis(reason: str) -> VisionAnalysis:
    """An analysis that observes nothing — used when vision is unavailable."""
    return VisionAnalysis(
        detections=[
            Detection(label=label, present=False, confidence=0.0, note=reason)
            for label in VISION_DETECTION_LABELS
        ],
        image_quality=0.0,
        overall_confidence=0.0,
        model_name=reason,
        raw_notes=(
            "No image analysis was performed. Every conclusion in this report "
            "rests on GIS evidence alone."
        ),
    )


def _clamp(value: Any, low: float = 0.0, high: float = 1.0) -> float:
    try:
        return max(low, min(high, float(value)))
    except (TypeError, ValueError):
        return low


def _enum(enum_cls: type, value: Any) -> Any:
    try:
        return enum_cls(value)
    except (ValueError, KeyError, TypeError):
        return enum_cls("unknown")


def _measurement(payload: Any, unit: str) -> MeasurementEstimate:
    if not isinstance(payload, dict):
        return MeasurementEstimate(unit=unit)
    return MeasurementEstimate(
        value=_optional_float(payload.get("value")),
        low=_optional_float(payload.get("low")),
        high=_optional_float(payload.get("high")),
        unit=unit,
        confidence=_clamp(payload.get("confidence", 0.0)),
        basis=payload.get("basis"),
    )


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
