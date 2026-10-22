import math

import pytest

from app.services.physics import (
    MU_0,
    aeolian_vibration_frequency_hz,
    catenary_sag_m,
    flux_density_ut,
    inductive_harvest_power_w,
    midspan_height_m,
    single_conductor_flux_density_t,
    three_phase_flux_density_t,
    wind_pressure_pa,
)


class TestFluxDensity:
    def test_matches_ampere_law_closed_form(self):
        # 100 A at 1 m: B = 2e-7 * 100 / 1 = 20 uT
        b = single_conductor_flux_density_t(100.0, 1.0)
        assert flux_density_ut(b) == pytest.approx(20.0, rel=1e-6)
        assert b == pytest.approx(MU_0 * 100 / (2 * math.pi), rel=1e-9)

    def test_inverse_distance_law(self):
        near = single_conductor_flux_density_t(100.0, 0.5)
        far = single_conductor_flux_density_t(100.0, 1.0)
        assert near == pytest.approx(2 * far, rel=1e-9)

    def test_zero_distance_is_rejected(self):
        with pytest.raises(ValueError):
            single_conductor_flux_density_t(100.0, 0.0)

    def test_three_phase_cancellation_reduces_far_field(self):
        close = three_phase_flux_density_t(200.0, 0.05, 1.0)
        distant = three_phase_flux_density_t(200.0, 5.0, 1.0)
        single_distant = single_conductor_flux_density_t(200.0, 5.0)
        assert close > distant
        assert distant < single_distant, "balanced phases must partially cancel"

    def test_near_field_approaches_the_single_conductor_value(self):
        b_three = three_phase_flux_density_t(100.0, 0.01, 2.0)
        b_one = single_conductor_flux_density_t(100.0, 0.01)
        assert b_three == pytest.approx(b_one, rel=0.01)


class TestHarvest:
    def test_zero_current_yields_zero_power(self):
        estimate = inductive_harvest_power_w(0.0)
        assert estimate.coupled_power_w == 0.0
        assert estimate.assumptions

    def test_power_grows_with_current(self):
        low = inductive_harvest_power_w(50.0).coupled_power_w
        high = inductive_harvest_power_w(400.0).coupled_power_w
        assert high > low

    def test_saturation_ceiling_bounds_the_result(self):
        # Without a ceiling, I^2 scaling would produce an absurd figure here.
        huge = inductive_harvest_power_w(5_000.0).coupled_power_w
        assert huge < 10_000, "core saturation must bound the estimate"

    def test_assumptions_are_always_disclosed(self):
        estimate = inductive_harvest_power_w(200.0)
        assert len(estimate.assumptions) >= 4
        assert any("saturation" in a.lower() for a in estimate.assumptions)


class TestMechanics:
    def test_sag_follows_the_parabolic_approximation(self):
        # s = w L^2 / (8 T)
        assert catenary_sag_m(100.0, 10_000.0, 8.0) == pytest.approx(8 * 10_000 / 80_000)

    def test_sag_grows_with_the_square_of_span(self):
        short = catenary_sag_m(50.0, 10_000.0, 8.0)
        long = catenary_sag_m(100.0, 10_000.0, 8.0)
        assert long == pytest.approx(4 * short)

    def test_zero_tension_is_rejected(self):
        with pytest.raises(ValueError):
            catenary_sag_m(100.0, 0.0, 8.0)

    def test_midspan_height_never_goes_negative(self):
        assert midspan_height_m(5.0, 12.0) == 0.0

    def test_wind_pressure_is_quadratic(self):
        assert wind_pressure_pa(20.0) == pytest.approx(4 * wind_pressure_pa(10.0))

    def test_aeolian_frequency_follows_strouhal(self):
        # f = 0.185 * v / d
        assert aeolian_vibration_frequency_hz(5.0, 20.0) == pytest.approx(0.185 * 5.0 / 0.02)

    def test_thin_conductors_vibrate_faster(self):
        assert aeolian_vibration_frequency_hz(5.0, 8.0) > aeolian_vibration_frequency_hz(5.0, 30.0)
