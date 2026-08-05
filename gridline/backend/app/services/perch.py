"""Perch Suitability Score — Chargebotic's ranking of a span for autonomous
energy harvesting.

Ten weighted factors, each scored 0-100 with its own confidence and a written
rationale, combined into a single 0-100 score. A factor with no supporting
evidence scores at a neutral 50 with confidence 0, so an evidence-free span
lands mid-scale with low confidence rather than looking attractive.

Two factors are hard blockers rather than contributors: if the conductor is
above the perch hardware's voltage envelope, or if the estimated harvestable
power cannot sustain the aircraft, the span is marked unsuitable regardless of
everything else.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..schemas import (
    CaptureContext,
    ConductorCovering,
    ConductorEstimate,
    CurrentEstimate,
    GISContext,
    PerchFactor,
    PerchSuitability,
    StructureType,
    VisionAnalysis,
    VoltageEstimate,
)
from .knowledge import VoltageClass, minimum_approach_distance_m
from .physics import (
    aeolian_vibration_frequency_hz,
    flux_density_ut,
    inductive_harvest_power_w,
    three_phase_flux_density_t,
)

#: Factor weights. They sum to 1.0.
WEIGHTS: dict[str, float] = {
    "magnetic_field": 0.20,
    "harvest_potential": 0.15,
    "line_accessibility": 0.10,
    "vegetation_clearance": 0.10,
    "wind_exposure": 0.08,
    "safe_drone_approach": 0.12,
    "gps_quality": 0.07,
    "nearby_obstacles": 0.08,
    "landing_risk": 0.06,
    "historical_success": 0.04,
}

#: Voltage envelope the perch coupler is designed for. Above this the span is
#: rejected: clearance and creepage requirements exceed the hardware.
MAX_PERCH_VOLTAGE_V = 35_000

#: Minimum continuous power the aircraft needs from a perch to be worth landing.
MIN_VIABLE_HARVEST_W = 2.0


@dataclass
class HistoricalStats:
    """Aggregated outcomes from previous perch attempts nearby."""

    attempts: int = 0
    successes: int = 0
    mean_harvested_w: float | None = None

    @property
    def success_rate(self) -> float | None:
        if self.attempts == 0:
            return None
        return self.successes / self.attempts


class PerchScorer:
    def score(
        self,
        vision: VisionAnalysis,
        gis: GISContext,
        capture: CaptureContext,
        voltage: VoltageEstimate,
        conductor: ConductorEstimate,
        current: CurrentEstimate,
        history: HistoricalStats | None = None,
    ) -> PerchSuitability:
        history = history or HistoricalStats()
        factors: list[PerchFactor] = []
        blockers: list[str] = []

        representative_current = self._representative_current(current)
        phase_spacing = self._phase_spacing_m(vision, voltage)

        flux_t = (
            three_phase_flux_density_t(representative_current, 0.05, phase_spacing)
            if representative_current
            else None
        )
        flux_ut = round(flux_density_ut(flux_t), 2) if flux_t else None

        harvest = (
            inductive_harvest_power_w(representative_current)
            if representative_current
            else None
        )

        factors.append(self._magnetic_field(flux_ut, current))
        factors.append(self._harvest_potential(harvest, current, conductor))
        factors.append(self._line_accessibility(vision, voltage))
        factors.append(self._vegetation_clearance(vision))
        factors.append(self._wind_exposure(vision, conductor, capture))
        factors.append(self._safe_drone_approach(vision, voltage, gis))
        factors.append(self._gps_quality(capture))
        factors.append(self._nearby_obstacles(vision, gis))
        factors.append(self._landing_risk(vision, conductor))
        factors.append(self._historical_success(history))

        # --- Hard blockers ---------------------------------------------------
        reference_v = voltage.most_likely_nominal_v or (
            max(voltage.possible_nominal_v) if voltage.possible_nominal_v else None
        )
        if reference_v and reference_v > MAX_PERCH_VOLTAGE_V:
            blockers.append(
                f"Estimated {reference_v / 1000:g} kV exceeds the {MAX_PERCH_VOLTAGE_V / 1000:g} kV "
                f"design envelope of the perch coupler (minimum approach distance "
                f"{minimum_approach_distance_m(reference_v):.2f} m)."
            )
        if voltage.voltage_class in {VoltageClass.TRANSMISSION, VoltageClass.EHV}:
            blockers.append(
                f"{voltage.class_label} spans are out of scope for perching hardware."
            )
        if harvest and harvest.coupled_power_w < MIN_VIABLE_HARVEST_W:
            blockers.append(
                f"Estimated {harvest.coupled_power_w:.2f} W coupled power is below the "
                f"{MIN_VIABLE_HARVEST_W:.0f} W needed to make a perch worthwhile."
            )
        if vision.conductor_covering == ConductorCovering.SPACER_CABLE:
            blockers.append(
                "Spacer cable geometry leaves no clear conductor run for a clamp coupler."
            )

        raw_score = sum(f.score * f.weight for f in factors)
        confidence = self._confidence(factors, voltage, current)

        score = 0.0 if blockers else round(raw_score, 1)
        grade = self._grade(score, bool(blockers))

        return PerchSuitability(
            score=score,
            grade=grade,
            confidence=round(confidence, 3),
            factors=factors,
            estimated_flux_density_ut=flux_ut,
            estimated_harvest_power_w=harvest.coupled_power_w if harvest else None,
            harvest_assumptions=harvest.assumptions if harvest else [],
            blockers=blockers,
            recommendation=self._recommendation(score, grade, blockers, factors, confidence),
        )

    # -- Factors -----------------------------------------------------------

    def _magnetic_field(self, flux_ut: float | None, current: CurrentEstimate) -> PerchFactor:
        if flux_ut is None:
            return self._neutral(
                "magnetic_field",
                "Magnetic field strength",
                "No current estimate available, so field strength cannot be modelled.",
            )
        # 5 uT at the coupler is marginal, 200 uT is excellent. Log scale
        # because coupled power goes as the square of current.
        score = self._log_scale(flux_ut, low=5.0, high=200.0)
        return PerchFactor(
            key="magnetic_field",
            label="Magnetic field strength",
            score=score,
            weight=WEIGHTS["magnetic_field"],
            confidence=current.confidence,
            rationale=(
                f"Modelled {flux_ut:.1f} uT at 50 mm from the conductor using Ampere's law "
                f"with three-phase cancellation, based on the estimated "
                f"{current.low_a:.0f}-{current.high_a:.0f} A operating range. "
                "Field scales linearly with current, which is not measured here."
            ),
        )

    def _harvest_potential(
        self,
        harvest: object | None,
        current: CurrentEstimate,
        conductor: ConductorEstimate,
    ) -> PerchFactor:
        if harvest is None:
            return self._neutral(
                "harvest_potential",
                "Harvest potential",
                "Without a current estimate there is no basis for a power figure.",
            )
        power = getattr(harvest, "coupled_power_w", 0.0)
        score = self._log_scale(power, low=1.0, high=60.0)
        return PerchFactor(
            key="harvest_potential",
            label="Harvest potential",
            score=score,
            weight=WEIGHTS["harvest_potential"],
            confidence=round(current.confidence * 0.8, 3),
            rationale=(
                f"A split-core coupler on this conductor would see roughly {power:.1f} W "
                f"at the midpoint of the estimated load range. Power scales with the "
                f"square of line current, so a lightly loaded feeder yields far less. "
                f"Conductor assumed {conductor.most_likely_codeword or 'unknown'}."
            ),
        )

    def _line_accessibility(self, vision: VisionAnalysis, voltage: VoltageEstimate) -> PerchFactor:
        score = 50.0
        notes: list[str] = []
        confidence = max(vision.overall_confidence, 0.2)

        if vision.conductor_covering == ConductorCovering.BARE:
            score += 15
            notes.append("bare conductor gives a clean clamp surface")
        elif vision.conductor_covering == ConductorCovering.COVERED:
            score -= 10
            notes.append("covered conductor adds insulation between coupler and current path")

        if vision.crossarm_config.value in {"single", "armless"}:
            score += 10
            notes.append("simple crossarm leaves clear conductor runs")
        elif vision.crossarm_config.value in {"double", "triangular"}:
            score -= 5
            notes.append("congested crossarm reduces clear approach lanes")

        if vision.has("vibration_damper"):
            score -= 8
            notes.append("vibration dampers occupy conductor near the structure")
        if vision.has("bird_diverter") or vision.has("bird_guard"):
            score -= 5
            notes.append("bird hardware occupies otherwise usable conductor")

        if (vision.bundled_subconductors or 1) > 1:
            score -= 20
            notes.append("bundled subconductors are hard to clamp")

        if voltage.voltage_class == VoltageClass.SECONDARY:
            score -= 15
            notes.append("secondary conductors carry too little current to be worth a perch")

        return PerchFactor(
            key="line_accessibility",
            label="Line accessibility",
            score=self._clamp(score),
            weight=WEIGHTS["line_accessibility"],
            confidence=round(confidence, 3),
            rationale="; ".join(notes) if notes else "No accessibility features observed.",
        )

    def _vegetation_clearance(self, vision: VisionAnalysis) -> PerchFactor:
        contact = vision.detection("vegetation_contact")
        if contact is None or contact.confidence < 0.2:
            return self._neutral(
                "vegetation_clearance",
                "Vegetation clearance",
                "Vegetation proximity could not be assessed from this frame.",
            )
        if contact.present:
            return PerchFactor(
                key="vegetation_clearance",
                label="Vegetation clearance",
                score=self._clamp(30 - 25 * contact.confidence),
                weight=WEIGHTS["vegetation_clearance"],
                confidence=contact.confidence,
                rationale=(
                    "Vegetation encroaching on the span. Branch strike risk on approach "
                    "and departure, and a higher chance of an unplanned outage on this feeder."
                ),
            )
        return PerchFactor(
            key="vegetation_clearance",
            label="Vegetation clearance",
            score=self._clamp(60 + 30 * contact.confidence),
            weight=WEIGHTS["vegetation_clearance"],
            confidence=contact.confidence,
            rationale="No vegetation encroachment visible in the span.",
        )

    def _wind_exposure(
        self,
        vision: VisionAnalysis,
        conductor: ConductorEstimate,
        capture: CaptureContext,
    ) -> PerchFactor:
        diameter = conductor.estimated_diameter_mm
        notes: list[str] = []
        score = 60.0
        confidence = 0.25

        if diameter:
            # A 7 m/s wind is a common perch-abort threshold for small aircraft.
            frequency = aeolian_vibration_frequency_hz(7.0, diameter)
            notes.append(
                f"Aeolian vibration at 7 m/s wind would excite the conductor near "
                f"{frequency:.0f} Hz (Strouhal relation, St=0.185)"
            )
            confidence = 0.4
            # Larger conductors vibrate lower and are steadier to sit on.
            score = 45 + min(35.0, diameter)

        if capture.altitude_m and capture.altitude_m > 1500:
            score -= 10
            notes.append(
                f"Site altitude {capture.altitude_m:.0f} m reduces air density and rotor margin"
            )

        if vision.structure_type == StructureType.TRANSMISSION_TOWER:
            score -= 10
            notes.append("Long transmission spans see higher sustained wind loading")

        if not notes:
            notes.append("No wind-relevant features could be assessed; local conditions govern.")

        return PerchFactor(
            key="wind_exposure",
            label="Wind exposure",
            score=self._clamp(score),
            weight=WEIGHTS["wind_exposure"],
            confidence=confidence,
            rationale="; ".join(notes),
        )

    def _safe_drone_approach(
        self, vision: VisionAnalysis, voltage: VoltageEstimate, gis: GISContext
    ) -> PerchFactor:
        score = 65.0
        notes: list[str] = []

        reference_v = voltage.most_likely_nominal_v or (
            max(voltage.possible_nominal_v) if voltage.possible_nominal_v else None
        )
        if reference_v:
            mad = minimum_approach_distance_m(reference_v)
            score -= mad * 20
            notes.append(
                f"OSHA 1910.269 minimum approach distance at {reference_v / 1000:g} kV is {mad:.2f} m"
            )

        if vision.has("shield_wire"):
            score -= 15
            notes.append("Overhead shield wire sits above the phase conductors on the approach path")
        if vision.has("communication_cable"):
            score -= 10
            notes.append("Communication cables below the power space narrow the approach corridor")
        if vision.has("guy_wire"):
            score -= 12
            notes.append("Guy wires are thin, hard to see and a serious strike hazard")

        substation = gis.nearest_substation
        if substation and substation.distance_m is not None and substation.distance_m < 200:
            score -= 15
            notes.append(
                f"A substation is {substation.distance_m:.0f} m away; congested conductor "
                "geometry and restricted airspace"
            )

        return PerchFactor(
            key="safe_drone_approach",
            label="Safe drone approach",
            score=self._clamp(score),
            weight=WEIGHTS["safe_drone_approach"],
            confidence=0.5 if notes else 0.15,
            rationale=(
                "; ".join(notes)
                if notes
                else "Approach geometry could not be assessed from the available evidence."
            ),
        )

    def _gps_quality(self, capture: CaptureContext) -> PerchFactor:
        if capture.accuracy_m is None:
            return self._neutral(
                "gps_quality", "GPS quality", "The handset did not report a GPS accuracy figure."
            )
        # 3 m is excellent for a phone, 30 m is unusable for autonomous return.
        score = self._clamp(100 - (capture.accuracy_m - 3) * (100 / 27))
        return PerchFactor(
            key="gps_quality",
            label="GPS quality",
            score=score,
            weight=WEIGHTS["gps_quality"],
            confidence=0.8,
            rationale=(
                f"Capture GPS accuracy {capture.accuracy_m:.1f} m. Autonomous return to a "
                "specific span needs metre-level accuracy; poor accuracy here suggests "
                "an RTK or visual fix will be required on site."
            ),
        )

    def _nearby_obstacles(self, vision: VisionAnalysis, gis: GISContext) -> PerchFactor:
        score = 70.0
        notes: list[str] = []

        structures = [
            a
            for a in gis.assets
            if a.asset_kind in {"pole", "tower", "portal"}
            and a.distance_m is not None
            and a.distance_m < 60
        ]
        if structures:
            score -= min(30.0, 6.0 * len(structures))
            notes.append(f"{len(structures)} mapped structure(s) within 60 m")

        if vision.has("streetlight"):
            score -= 8
            notes.append("Streetlight arm projects into the approach volume")
        if vision.has("riser_cable"):
            score -= 6
            notes.append("Riser cable and standoffs on the pole face")
        if vision.has("secondary_rack"):
            score -= 6
            notes.append("Secondary rack adds conductors below the primary")

        return PerchFactor(
            key="nearby_obstacles",
            label="Nearby obstacles",
            score=self._clamp(score),
            weight=WEIGHTS["nearby_obstacles"],
            confidence=0.45 if notes else 0.2,
            rationale="; ".join(notes) if notes else "No obstacles identified near the span.",
        )

    def _landing_risk(self, vision: VisionAnalysis, conductor: ConductorEstimate) -> PerchFactor:
        score = 55.0
        notes: list[str] = []
        diameter = conductor.estimated_diameter_mm

        if diameter:
            if diameter < 8:
                score -= 20
                notes.append(
                    f"{diameter:.1f} mm conductor is thin; it will deflect substantially "
                    "under aircraft mass"
                )
            elif diameter > 20:
                score += 20
                notes.append(f"{diameter:.1f} mm conductor is stiff enough to perch on")
            else:
                score += 8
                notes.append(f"{diameter:.1f} mm conductor is workable for a clamp")

        if vision.structure_type == StructureType.DEAD_END or vision.has("dead_end_pole"):
            score += 10
            notes.append("Dead-end structure gives a high-tension, low-sag conductor to land on")
        if vision.has("suspension_pole"):
            score -= 5
            notes.append("Suspension span has more mid-span movement")

        if vision.obstructed or vision.image_quality < 0.4:
            score -= 10
            notes.append("Frame quality limits confidence in the landing assessment")

        return PerchFactor(
            key="landing_risk",
            label="Landing risk",
            score=self._clamp(score),
            weight=WEIGHTS["landing_risk"],
            confidence=0.4 if diameter else 0.15,
            rationale="; ".join(notes) if notes else "Landing risk could not be assessed.",
        )

    def _historical_success(self, history: HistoricalStats) -> PerchFactor:
        rate = history.success_rate
        if rate is None:
            return self._neutral(
                "historical_success",
                "Historical success rate",
                "No previous perch attempts recorded near this location.",
            )
        return PerchFactor(
            key="historical_success",
            label="Historical success rate",
            score=self._clamp(rate * 100),
            weight=WEIGHTS["historical_success"],
            # Confidence in a rate grows with sample size, saturating around 20.
            confidence=round(min(0.9, history.attempts / 20.0), 3),
            rationale=(
                f"{history.successes} of {history.attempts} logged perch attempts within "
                f"1 km succeeded"
                + (
                    f", averaging {history.mean_harvested_w:.1f} W harvested"
                    if history.mean_harvested_w
                    else ""
                )
                + "."
            ),
        )

    # -- Helpers -----------------------------------------------------------

    def _neutral(self, key: str, label: str, rationale: str) -> PerchFactor:
        return PerchFactor(
            key=key,
            label=label,
            score=50.0,
            weight=WEIGHTS[key],
            confidence=0.0,
            rationale=rationale,
        )

    def _representative_current(self, current: CurrentEstimate) -> float | None:
        if current.is_measured and current.low_a is not None:
            return current.low_a
        if current.low_a is None or current.high_a is None:
            return None
        # Geometric mean: the range spans an order of magnitude and the
        # arithmetic mean would over-weight the high end.
        return (current.low_a * current.high_a) ** 0.5

    def _phase_spacing_m(self, vision: VisionAnalysis, voltage: VoltageEstimate) -> float:
        spacing = vision.conductor_spacing
        value = spacing.value or (
            (spacing.low + spacing.high) / 2 if spacing.low and spacing.high else None
        )
        if value:
            return value
        return {
            VoltageClass.SECONDARY: 0.25,
            VoltageClass.DISTRIBUTION: 1.0,
            VoltageClass.SUBTRANSMISSION: 2.4,
            VoltageClass.TRANSMISSION: 5.0,
            VoltageClass.EHV: 10.0,
        }.get(voltage.voltage_class, 1.0)

    def _log_scale(self, value: float, low: float, high: float) -> float:
        """Map ``value`` onto 0-100 on a log scale between low and high."""
        import math

        if value <= 0:
            return 0.0
        if value <= low:
            return max(0.0, 25.0 * value / low)
        if value >= high:
            return 100.0
        span = math.log(high) - math.log(low)
        return 25.0 + 75.0 * (math.log(value) - math.log(low)) / span

    def _clamp(self, value: float) -> float:
        return max(0.0, min(100.0, value))

    def _confidence(
        self,
        factors: list[PerchFactor],
        voltage: VoltageEstimate,
        current: CurrentEstimate,
    ) -> float:
        weighted = sum(f.confidence * f.weight for f in factors)
        # The whole score is downstream of the voltage/current chain, so it can
        # never be more trustworthy than that chain.
        ceiling = max(voltage.class_confidence, 0.1)
        return min(weighted, ceiling)

    def _grade(self, score: float, blocked: bool) -> str:
        if blocked:
            return "unsuitable"
        if score >= 80:
            return "excellent"
        if score >= 65:
            return "good"
        if score >= 45:
            return "marginal"
        return "poor"

    def _recommendation(
        self,
        score: float,
        grade: str,
        blockers: list[str],
        factors: list[PerchFactor],
        confidence: float,
    ) -> str:
        if blockers:
            return "Do not attempt. " + " ".join(blockers)

        weakest = min(factors, key=lambda f: f.score)
        base = {
            "excellent": (
                f"Strong candidate span (score {score:.0f}/100). Schedule a survey flight."
            ),
            "good": (
                f"Workable span (score {score:.0f}/100). Worth a survey once better "
                "candidates are exhausted."
            ),
            "marginal": (
                f"Marginal span (score {score:.0f}/100). Only worth attempting if no "
                "better site exists in the corridor."
            ),
            "poor": f"Not recommended (score {score:.0f}/100).",
        }[grade]

        detail = f" Weakest factor is {weakest.label.lower()} at {weakest.score:.0f}/100."
        if confidence < 0.35:
            detail += (
                " Confidence in this score is low — it rests on estimated rather than "
                "measured line current. A field measurement would change it materially."
            )
        return base + detail
