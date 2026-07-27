"""Electromagnetic and mechanical estimates used by the perch scorer.

Every function here is a closed-form textbook model with stated assumptions.
None of them is a measurement, and callers must present the results as
estimates with the assumptions attached.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

MU_0 = 4 * math.pi * 1e-7  # H/m, vacuum permeability


def single_conductor_flux_density_t(current_a: float, distance_m: float) -> float:
    """Ampere's law for an infinite straight conductor: B = mu0*I / (2*pi*r).

    Valid when the distance is small compared with the span length, which holds
    for a drone perched on or beside a conductor mid-span.
    """
    if distance_m <= 0:
        raise ValueError("distance_m must be positive")
    return MU_0 * current_a / (2 * math.pi * distance_m)


def three_phase_flux_density_t(
    current_a: float,
    distance_m: float,
    phase_spacing_m: float,
) -> float:
    """Resultant field near one phase of a balanced three-phase flat circuit.

    A balanced three-phase set partially cancels. Close to a single conductor
    the near field dominates; far away the field decays as 1/r^2 (flat
    configuration). This models the crossover with a geometric attenuation
    factor derived from the ratio of observation distance to phase spacing.
    """
    if distance_m <= 0:
        raise ValueError("distance_m must be positive")
    near = single_conductor_flux_density_t(current_a, distance_m)
    if phase_spacing_m <= 0:
        return near
    # Attenuation from the two return phases. At r << s the factor tends to 1,
    # at r >> s it tends to s/r which reproduces the 1/r^2 far-field decay.
    ratio = distance_m / phase_spacing_m
    attenuation = 1.0 / math.sqrt(1.0 + ratio**2)
    return near * max(attenuation, 0.02)


def flux_density_ut(tesla: float) -> float:
    """Convert tesla to microtesla."""
    return tesla * 1e6


@dataclass(frozen=True)
class HarvestEstimate:
    """Inductive harvest estimate for a split-core / clamp coupler."""

    coupled_power_w: float
    flux_density_ut: float
    assumptions: list[str]


def inductive_harvest_power_w(
    current_a: float,
    turns: int = 100,
    core_area_m2: float = 4.0e-4,
    core_relative_permeability: float = 2_000.0,
    coupling_efficiency: float = 0.55,
    frequency_hz: float = 60.0,
    burden_matched: bool = True,
) -> HarvestEstimate:
    """Estimate power available to a clamp-on current transformer.

    Model: a split core encircling the conductor sees the full conductor
    current as one primary turn. The open-circuit secondary EMF is

        E = 2*pi*f * N * A * B_core / sqrt(2)

    with ``B_core = mu0 * mu_r * H`` and ``H = I / l_magnetic``. Rather than
    modelling the magnetic path length explicitly we use the standard CT
    relation ``I_secondary = I_primary / N`` and a matched burden, which gives

        P = eta * I_s^2 * R_burden

    The result is bounded by core saturation, so we cap the delivered power at
    the value where the core reaches 1.6 T (typical silicon steel knee).

    Defaults describe the Chargebotic split-core coupler design point: 100
    turns on a 4 cm2 nanocrystalline core. Fewer turns raise secondary current
    and therefore power, up to the saturation ceiling — which is why the
    default is not the 300-turn winding of a metering CT.
    """
    if current_a <= 0:
        return HarvestEstimate(0.0, 0.0, ["No current estimate available"])

    secondary_current = current_a / max(turns, 1)
    # Matched burden for a typical split-core CT winding resistance.
    burden_ohms = 20.0 if burden_matched else 5.0
    raw_power = coupling_efficiency * (secondary_current**2) * burden_ohms

    # Saturation ceiling: P_max = eta * E_sat * I_s where E_sat comes from the
    # core knee flux density.
    b_sat_t = 1.6
    e_sat = 2 * math.pi * frequency_hz * turns * core_area_m2 * b_sat_t / math.sqrt(2)
    power_ceiling = coupling_efficiency * e_sat * secondary_current

    power = min(raw_power, power_ceiling)

    b_near = three_phase_flux_density_t(current_a, 0.05, 1.0)

    return HarvestEstimate(
        coupled_power_w=round(power, 2),
        flux_density_ut=round(flux_density_ut(b_near), 2),
        assumptions=[
            f"Split-core CT with {turns} turns on a {core_area_m2 * 1e4:.1f} cm2 core",
            f"Relative permeability {core_relative_permeability:.0f}, "
            f"coupling efficiency {coupling_efficiency:.0%}",
            f"System frequency {frequency_hz:.0f} Hz, matched {burden_ohms:.0f} ohm burden",
            "Power scales with the square of line current; a lightly loaded "
            "feeder yields far less than this figure",
            f"Capped at core saturation ({b_sat_t} T)",
        ],
    )


def catenary_sag_m(span_m: float, tension_n: float, weight_n_per_m: float) -> float:
    """Parabolic approximation of conductor sag: s = w*L^2 / (8*T)."""
    if tension_n <= 0:
        raise ValueError("tension_n must be positive")
    return weight_n_per_m * span_m**2 / (8 * tension_n)


def midspan_height_m(attachment_height_m: float, sag_m: float) -> float:
    """Ground clearance at mid-span given attachment height and sag."""
    return max(attachment_height_m - sag_m, 0.0)


def wind_pressure_pa(wind_speed_ms: float) -> float:
    """Dynamic pressure q = 0.5 * rho * v^2 at sea-level air density."""
    rho = 1.225
    return 0.5 * rho * wind_speed_ms**2


def aeolian_vibration_frequency_hz(wind_speed_ms: float, diameter_mm: float) -> float:
    """Strouhal relation f = St * v / d with St = 0.185 for a cylinder.

    Perching hardware has to tolerate the conductor's own vibration; this gives
    the dominant excitation frequency.
    """
    if diameter_mm <= 0:
        raise ValueError("diameter_mm must be positive")
    return 0.185 * wind_speed_ms / (diameter_mm / 1000.0)
