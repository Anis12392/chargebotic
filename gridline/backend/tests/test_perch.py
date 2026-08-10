from app.services.inference import InferenceEngine
from app.services.perch import WEIGHTS, HistoricalStats, PerchScorer
from app.services.vision import null_analysis

from . import factories as f

engine = InferenceEngine()
scorer = PerchScorer()


def _score(vision, gis, capture=None, history=None):
    capture = capture or f.capture()
    result = engine.run(vision, gis, capture)
    return scorer.score(
        vision, gis, capture, result.voltage, result.conductor, result.current, history
    )


class TestScoreShape:
    def test_weights_sum_to_one(self):
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    def test_every_weighted_factor_is_reported(self):
        perch = _score(f.vision_distribution_pole(), f.gis_with_line([12_470]))
        assert {factor.key for factor in perch.factors} == set(WEIGHTS)

    def test_score_stays_within_bounds(self):
        for vision in (
            f.vision_distribution_pole(),
            f.vision_transmission_tower(),
            f.vision_secondary_service(),
            null_analysis("vision_disabled"),
        ):
            perch = _score(vision, f.empty_gis())
            assert 0.0 <= perch.score <= 100.0
            assert 0.0 <= perch.confidence <= 1.0

    def test_every_factor_carries_a_written_rationale(self):
        perch = _score(f.vision_distribution_pole(), f.gis_with_line([12_470]))
        for factor in perch.factors:
            assert factor.rationale.strip()


class TestBlockers:
    def test_transmission_span_is_blocked_outright(self):
        perch = _score(f.vision_transmission_tower(), f.gis_with_line([230_000], distance_m=20.0))
        assert perch.grade == "unsuitable"
        assert perch.score == 0.0
        assert perch.blockers
        assert perch.recommendation.startswith("Do not attempt")

    def test_blocker_explains_the_voltage_envelope(self):
        perch = _score(f.vision_transmission_tower(), f.gis_with_line([230_000], distance_m=20.0))
        assert any("envelope" in b or "out of scope" in b for b in perch.blockers)

    def test_distribution_span_is_not_blocked(self):
        perch = _score(f.vision_distribution_pole(), f.gis_with_line([12_470], distance_m=15.0))
        assert perch.grade != "unsuitable"
        assert perch.score > 0.0


class TestEvidenceSensitivity:
    def test_no_evidence_lands_mid_scale_with_low_confidence(self):
        perch = _score(null_analysis("vision_disabled"), f.empty_gis())
        assert perch.confidence < 0.3
        assert 20.0 <= perch.score <= 70.0

    def test_poor_gps_lowers_the_gps_factor(self):
        good = _score(f.vision_distribution_pole(), f.gis_with_line([12_470]), f.capture(accuracy_m=3.0))
        bad = _score(f.vision_distribution_pole(), f.gis_with_line([12_470]), f.capture(accuracy_m=45.0))
        good_gps = next(x for x in good.factors if x.key == "gps_quality")
        bad_gps = next(x for x in bad.factors if x.key == "gps_quality")
        assert good_gps.score > bad_gps.score

    def test_history_raises_confidence_in_the_historical_factor(self):
        without = _score(f.vision_distribution_pole(), f.gis_with_line([12_470]))
        with_history = _score(
            f.vision_distribution_pole(),
            f.gis_with_line([12_470]),
            history=HistoricalStats(attempts=18, successes=15, mean_harvested_w=9.4),
        )
        a = next(x for x in without.factors if x.key == "historical_success")
        b = next(x for x in with_history.factors if x.key == "historical_success")
        assert a.confidence == 0.0
        assert b.confidence > 0.5
        assert b.score > a.score

    def test_confidence_cannot_exceed_the_voltage_call_it_rests_on(self):
        perch = _score(null_analysis("vision_disabled"), f.empty_gis())
        assert perch.confidence <= 0.1


class TestHarvestDisclosure:
    def test_harvest_assumptions_accompany_any_power_figure(self):
        perch = _score(f.vision_distribution_pole(), f.gis_with_line([12_470]))
        if perch.estimated_harvest_power_w is not None:
            assert perch.harvest_assumptions

    def test_low_confidence_is_called_out_in_the_recommendation(self):
        perch = _score(f.vision_distribution_pole(), f.empty_gis())
        if perch.confidence < 0.35 and not perch.blockers:
            assert "confidence" in perch.recommendation.lower()

    def test_field_estimate_is_reported_when_current_is(self):
        perch = _score(f.vision_distribution_pole(), f.gis_with_line([12_470]))
        assert perch.estimated_flux_density_ut is not None
        assert perch.estimated_flux_density_ut > 0
