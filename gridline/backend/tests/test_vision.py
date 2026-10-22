from app.schemas import VISION_DETECTION_LABELS, PoleMaterial, StructureType
from app.services.vision import (
    VisionAnalyzer,
    _parse_provider_payload,
    build_response_schema,
    null_analysis,
)


class TestResponseSchema:
    def test_schema_is_strict_and_covers_every_field(self):
        schema = build_response_schema()
        assert schema["additionalProperties"] is False
        for key in ("detections", "insulator_disc_count", "conductor_diameter"):
            assert key in schema["properties"]
            assert key in schema["required"]

    def test_detection_labels_are_constrained_to_the_checklist(self):
        schema = build_response_schema()
        enum = schema["properties"]["detections"]["items"]["properties"]["label"]["enum"]
        assert set(enum) == set(VISION_DETECTION_LABELS)


class TestPayloadParsing:
    def test_missing_labels_are_backfilled_as_explicit_non_observations(self):
        analysis = _parse_provider_payload(
            {
                "is_power_infrastructure": True,
                "pole_material": "wood",
                "detections": [{"label": "transformer", "present": True, "confidence": 0.9}],
            },
            "test-model",
        )
        assert len(analysis.detections) == len(VISION_DETECTION_LABELS)
        assert analysis.has("transformer")
        assert analysis.detection("recloser").present is False

    def test_out_of_range_confidence_is_clamped(self):
        analysis = _parse_provider_payload(
            {"detections": [{"label": "transformer", "present": True, "confidence": 4.2}]},
            "test-model",
        )
        assert analysis.detection("transformer").confidence == 1.0

    def test_unknown_enum_values_degrade_to_unknown(self):
        analysis = _parse_provider_payload(
            {"pole_material": "unobtanium", "structure_type": "space_elevator"}, "test-model"
        )
        assert analysis.pole_material is PoleMaterial.UNKNOWN
        assert analysis.structure_type is StructureType.UNKNOWN

    def test_duplicate_detections_are_deduplicated(self):
        analysis = _parse_provider_payload(
            {
                "detections": [
                    {"label": "transformer", "present": True, "confidence": 0.9},
                    {"label": "transformer", "present": False, "confidence": 0.1},
                ]
            },
            "test-model",
        )
        matches = [d for d in analysis.detections if d.label == "transformer"]
        assert len(matches) == 1
        assert matches[0].confidence == 0.9


class TestSanityChecks:
    def test_bundled_conductors_on_a_wood_pole_are_suppressed(self):
        analysis = _parse_provider_payload(
            {"pole_material": "wood", "bundled_subconductors": 4}, "test-model"
        )
        assert analysis.bundled_subconductors == 1
        assert "implausible" in (analysis.raw_notes or "")

    def test_conflicting_transformer_and_tower_keeps_the_stronger_claim(self):
        analysis = _parse_provider_payload(
            {
                "detections": [
                    {"label": "transformer", "present": True, "confidence": 0.4},
                    {"label": "transmission_tower", "present": True, "confidence": 0.95},
                ]
            },
            "test-model",
        )
        assert analysis.detection("transmission_tower").present is True
        assert analysis.detection("transformer").present is False

    def test_phase_count_cannot_exceed_conductor_count(self):
        analysis = _parse_provider_payload(
            {"phase_count": 6, "conductor_count": 3}, "test-model"
        )
        assert analysis.phase_count == 3

    def test_non_power_image_gets_zero_confidence(self):
        analysis = _parse_provider_payload(
            {"is_power_infrastructure": False, "overall_confidence": 0.9}, "test-model"
        )
        assert analysis.overall_confidence == 0.0


class TestDegradation:
    def test_null_analysis_observes_nothing(self):
        analysis = null_analysis("vision_disabled")
        assert analysis.overall_confidence == 0.0
        assert all(not d.present for d in analysis.detections)
        assert "GIS evidence alone" in analysis.raw_notes

    async def test_analyzer_without_a_key_returns_the_null_analysis(self):
        analyzer = VisionAnalyzer(api_key=None)
        assert analyzer.enabled is False
        analysis = await analyzer.analyze(b"\xff\xd8\xffnot-a-real-jpeg")
        assert analysis.model_name == "vision_disabled"
