from app.services.knowledge import (
    CONDUCTOR_CATALOGUE,
    NOMINAL_VOLTAGES_V,
    VoltageClass,
    classify_voltage,
    conductors_near_diameter,
    find_utility_standard,
    minimum_approach_distance_m,
    nearest_nominal_voltages,
    typical_conductors_for_class,
)


class TestVoltageClassification:
    def test_class_boundaries_are_contiguous_and_ordered(self):
        assert classify_voltage(480) is VoltageClass.SECONDARY
        assert classify_voltage(12_470) is VoltageClass.DISTRIBUTION
        assert classify_voltage(34_500) is VoltageClass.DISTRIBUTION
        assert classify_voltage(69_000) is VoltageClass.SUBTRANSMISSION
        assert classify_voltage(115_000) is VoltageClass.SUBTRANSMISSION
        assert classify_voltage(230_000) is VoltageClass.TRANSMISSION
        assert classify_voltage(500_000) is VoltageClass.EHV

    def test_every_catalogued_nominal_maps_into_a_real_class(self):
        for voltages in NOMINAL_VOLTAGES_V.values():
            for volts in voltages:
                assert classify_voltage(volts) is not VoltageClass.UNKNOWN

    def test_nearest_nominal_snaps_to_standard_values(self):
        assert nearest_nominal_voltages(12_500, limit=1) == [12_470]
        assert 13_800 in nearest_nominal_voltages(13_700, limit=3)


class TestConductorCatalogue:
    def test_diameter_and_ampacity_increase_together(self):
        by_diameter = sorted(CONDUCTOR_CATALOGUE, key=lambda c: c.diameter_mm)
        ampacities = [c.ampacity_75c_a for c in by_diameter]
        assert ampacities == sorted(ampacities), "larger conductor must carry more current"

    def test_emergency_rating_always_exceeds_normal_rating(self):
        for conductor in CONDUCTOR_CATALOGUE:
            if conductor.ampacity_100c_a is not None:
                assert conductor.ampacity_100c_a > conductor.ampacity_75c_a

    def test_lookup_by_diameter_returns_closest_first(self):
        matches = conductors_near_diameter(28.0, tolerance_mm=3.0)
        assert matches, "795 kcmil Drake is 28.14 mm and must be found"
        assert matches[0].codeword == "Drake"

    def test_lookup_respects_tolerance(self):
        assert conductors_near_diameter(28.0, tolerance_mm=0.05) == []

    def test_transmission_class_has_candidates(self):
        assert typical_conductors_for_class(VoltageClass.TRANSMISSION)
        assert typical_conductors_for_class(VoltageClass.DISTRIBUTION)


class TestUtilityStandards:
    def test_alias_lookup(self):
        assert find_utility_standard("PG&E").operator == "Pacific Gas and Electric Company"
        assert find_utility_standard("Southern California Edison").operator == (
            "Southern California Edison"
        )

    def test_unknown_operator_returns_none(self):
        assert find_utility_standard("Wakanda Power Authority") is None
        assert find_utility_standard(None) is None
        assert find_utility_standard("   ") is None

    def test_pge_standard_carries_its_unusual_60kv_subtransmission(self):
        std = find_utility_standard("pge")
        assert 60_000 in std.subtransmission_v


class TestApproachDistance:
    def test_distance_increases_with_voltage(self):
        distances = [minimum_approach_distance_m(v) for v in (750, 15_000, 115_000, 500_000)]
        assert distances == sorted(distances)

    def test_above_table_falls_back_to_the_largest_value(self):
        assert minimum_approach_distance_m(2_000_000) == minimum_approach_distance_m(800_000)
