"""Behavioural tests for the reasoning engine.

These encode the promises the product makes: no invented numbers, no asserted
current, honest degradation when evidence is missing, and conflicts surfaced
rather than smoothed over.
"""

from app.schemas import VisionAnalysis
from app.services.inference import InferenceEngine
from app.services.knowledge import VoltageClass
from app.services.vision import null_analysis

from . import factories as f

engine = InferenceEngine()


class TestVoltageClassInference:
    def test_wood_pole_with_transformer_is_distribution(self):
        result = engine.run(f.vision_distribution_pole(), f.empty_gis(), f.capture())
        assert result.voltage.voltage_class is VoltageClass.DISTRIBUTION
        assert result.voltage.class_confidence > 0.4

    def test_lattice_tower_with_nine_discs_is_transmission_or_above(self):
        result = engine.run(f.vision_transmission_tower(), f.empty_gis(), f.capture())
        assert result.voltage.voltage_class in {VoltageClass.TRANSMISSION, VoltageClass.EHV}

    def test_triplex_service_is_secondary(self):
        result = engine.run(f.vision_secondary_service(), f.empty_gis(), f.capture())
        assert result.voltage.voltage_class is VoltageClass.SECONDARY

    def test_no_evidence_yields_unknown_not_a_guess(self):
        result = engine.run(null_analysis("vision_disabled"), f.empty_gis(), f.capture())
        assert result.voltage.voltage_class is VoltageClass.UNKNOWN
        assert result.voltage.class_confidence == 0.0
        assert result.voltage.possible_nominal_v == []
        assert result.overall_confidence < 0.2

    def test_gis_voltage_tag_alone_can_carry_the_call(self):
        gis = f.gis_with_line(voltage_v=[115_000], asset_kind="line", distance_m=20.0)
        result = engine.run(null_analysis("vision_disabled"), gis, f.capture())
        assert result.voltage.voltage_class is VoltageClass.SUBTRANSMISSION
        assert result.voltage.is_confirmed is True
        assert result.voltage.confirmation_source is not None

    def test_distant_gis_tag_is_context_not_confirmation(self):
        gis = f.gis_with_line(voltage_v=[115_000], asset_kind="line", distance_m=400.0)
        result = engine.run(f.vision_distribution_pole(), gis, f.capture())
        assert result.voltage.is_confirmed is False


class TestConflictHandling:
    def test_gis_vision_conflict_is_surfaced_and_lowers_confidence(self):
        # GIS says 230 kV; the photo is unambiguously a wood distribution pole.
        gis = f.gis_with_line(voltage_v=[230_000], asset_kind="line", distance_m=30.0)
        result = engine.run(f.vision_distribution_pole(), gis, f.capture())

        codes = {w.code for w in result.warnings}
        assert "gis_vision_conflict" in codes
        assert result.voltage.is_confirmed is False, (
            "a contested tag must not be presented as confirmed"
        )

    def test_conflict_appears_in_the_written_reasoning(self):
        gis = f.gis_with_line(voltage_v=[230_000], asset_kind="line", distance_m=30.0)
        result = engine.run(f.vision_distribution_pole(), gis, f.capture())
        assert any("conflict" in line.lower() for line in result.reasoning)


class TestNominalVoltages:
    def test_utility_standard_narrows_the_candidate_set(self):
        gis = f.gis_with_line(operator="PG&E")
        result = engine.run(f.vision_distribution_pole(), gis, f.capture())
        assert result.voltage.possible_nominal_v
        # PG&E does not build 13.8 kV primary, so it must not be offered.
        assert 13_800 not in result.voltage.possible_nominal_v
        assert 12_000 in result.voltage.possible_nominal_v

    def test_confirmed_tag_collapses_the_candidate_set(self):
        gis = f.gis_with_line(voltage_v=[12_470], distance_m=15.0)
        result = engine.run(f.vision_distribution_pole(), gis, f.capture())
        assert result.voltage.possible_nominal_v == [12_470]
        assert result.voltage.most_likely_nominal_v == 12_470

    def test_every_offered_nominal_belongs_to_the_chosen_class(self):
        from app.services.knowledge import classify_voltage

        result = engine.run(f.vision_transmission_tower(), f.empty_gis(), f.capture())
        for volts in result.voltage.possible_nominal_v:
            assert classify_voltage(volts) is result.voltage.voltage_class


class TestCurrentIsNeverAsserted:
    def test_current_is_always_a_range_and_never_measured(self):
        result = engine.run(f.vision_distribution_pole(), f.gis_with_line(), f.capture())
        assert result.current.is_measured is False
        assert result.current.caveat
        if result.current.low_a is not None:
            assert result.current.high_a > result.current.low_a

    def test_no_conductor_means_no_current_range_at_all(self):
        vision = VisionAnalysis(model_name="test-vision")
        result = engine.run(vision, f.empty_gis(), f.capture())
        assert result.current.low_a is None
        assert result.current.high_a is None
        assert result.current.confidence == 0.0

    def test_current_range_sits_below_the_thermal_rating(self):
        result = engine.run(f.vision_distribution_pole(), f.gis_with_line(), f.capture())
        assert result.conductor.thermal_rating_a is not None
        assert result.current.high_a < result.conductor.thermal_rating_a


class TestConductorEstimate:
    def test_diameter_match_finds_the_catalogue_conductor(self):
        result = engine.run(f.vision_distribution_pole(), f.empty_gis(), f.capture())
        # 14.3 mm is 4/0 ACSR "Penguin"; the 13-16 mm range also admits 3/0.
        assert result.conductor.most_likely_codeword == "Penguin"
        assert {c["codeword"] for c in result.conductor.candidates} == {"Penguin", "Pigeon"}
        # The rating quoted is the smallest candidate's — the binding limit.
        assert result.conductor.thermal_rating_a == 315

    def test_thermal_rating_quotes_the_binding_smallest_candidate(self):
        result = engine.run(f.vision_transmission_tower(), f.empty_gis(), f.capture())
        ratings = [c["ampacity_75c_a"] for c in result.conductor.candidates]
        assert result.conductor.thermal_rating_a == min(ratings)

    def test_rating_basis_is_always_stated(self):
        result = engine.run(f.vision_distribution_pole(), f.empty_gis(), f.capture())
        assert "75 C" in result.conductor.thermal_rating_basis


class TestUtilityAttribution:
    def test_operator_tag_is_resolved_to_a_known_standard(self):
        result = engine.run(f.vision_distribution_pole(), f.gis_with_line(operator="PG&E"), f.capture())
        assert result.utility.name == "Pacific Gas and Electric Company"
        assert result.utility.known_standard is True
        assert result.utility.confidence > 0.0

    def test_no_operator_tag_means_no_attribution(self):
        result = engine.run(f.vision_distribution_pole(), f.gis_with_line(operator=None), f.capture())
        assert result.utility.name is None
        assert result.utility.confidence == 0.0

    def test_unknown_operator_is_reported_verbatim(self):
        gis = f.gis_with_line(operator="Kauai Island Utility Cooperative")
        result = engine.run(f.vision_distribution_pole(), gis, f.capture())
        assert result.utility.name == "Kauai Island Utility Cooperative"
        assert result.utility.known_standard is False


class TestEvidenceAndWarnings:
    def test_every_evidence_item_carries_an_implication(self):
        result = engine.run(f.vision_distribution_pole(), f.gis_with_line([12_470]), f.capture())
        assert result.evidence
        for item in result.evidence:
            assert item.observation and item.implication
            assert 0.0 <= item.confidence <= 1.0

    def test_energised_warning_is_always_present(self):
        result = engine.run(f.vision_distribution_pole(), f.empty_gis(), f.capture())
        assert "treat_as_energised" in {w.code for w in result.warnings}

    def test_approach_distance_warning_quotes_osha(self):
        result = engine.run(f.vision_distribution_pole(), f.gis_with_line([12_470]), f.capture())
        approach = next(w for w in result.warnings if w.code == "approach_distance")
        assert "1910.269" in approach.message
        assert approach.severity == "danger"

    def test_poor_gps_raises_a_warning(self):
        result = engine.run(
            f.vision_distribution_pole(), f.empty_gis(), f.capture(accuracy_m=85.0)
        )
        assert "poor_gps" in {w.code for w in result.warnings}

    def test_missing_gis_coverage_is_disclosed(self):
        result = engine.run(f.vision_distribution_pole(), f.empty_gis(), f.capture())
        assert "no_gis_coverage" in {w.code for w in result.warnings}


class TestConfidenceBehaviour:
    def test_more_evidence_raises_confidence(self):
        thin = engine.run(f.vision_distribution_pole(), f.empty_gis(), f.capture())
        rich = engine.run(
            f.vision_distribution_pole(), f.gis_with_line([12_470], distance_m=12.0), f.capture()
        )
        assert rich.overall_confidence > thin.overall_confidence

    def test_confidence_never_reaches_certainty(self):
        rich = engine.run(
            f.vision_distribution_pole(), f.gis_with_line([12_470], distance_m=5.0), f.capture()
        )
        assert rich.overall_confidence <= 0.97

    def test_headline_states_whether_the_call_is_confirmed(self):
        estimated = engine.run(f.vision_distribution_pole(), f.empty_gis(), f.capture())
        assert "estimated" in estimated.reasoning[0].lower() or "unable" in estimated.reasoning[0].lower()

        confirmed = engine.run(
            f.vision_distribution_pole(), f.gis_with_line([12_470], distance_m=10.0), f.capture()
        )
        assert "confirmed" in confirmed.reasoning[0].lower()
