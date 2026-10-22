"""AI reasoning engine.

Takes the vision inventory, the GIS context and the capture metadata and
produces a voltage class, a set of plausible nominal voltages, a conductor
estimate, an operating-current *range*, a utility attribution and — crucially —
the evidence chain behind each of those.

Design rules that the rest of the system depends on:

* **No fabricated numbers.** Every figure traces to either an observation, a
  published table in :mod:`knowledge`, or a closed-form model in :mod:`physics`.
* **Exact current is never asserted.** ``CurrentEstimate.is_measured`` is only
  true when a verified field measurement is supplied. Otherwise the output is a
  range derived from conductor thermal rating times published loading factors,
  and it carries a caveat.
* **Absence of evidence lowers confidence, it does not pick a default.** With
  no vision and no GIS the engine returns ``VoltageClass.UNKNOWN`` at low
  confidence rather than guessing "distribution because most lines are".
* **Conflicts are surfaced, not silently resolved.** When GIS says 115 kV and
  the imagery says wood pole with a transformer, both appear in the evidence and
  a warning is raised.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..schemas import (
    CaptureContext,
    ConductorCovering,
    ConductorEstimate,
    CrossarmConfig,
    CurrentEstimate,
    EvidenceItem,
    GISAsset,
    GISContext,
    InsulatorType,
    PoleMaterial,
    StructureType,
    UtilityEstimate,
    VisionAnalysis,
    VoltageEstimate,
    Warning,
)
from .knowledge import (
    HARDWARE_VOLTAGE_CONSTRAINTS,
    NOMINAL_VOLTAGES_V,
    PHASE_SPACING_M,
    PIN_INSULATOR_LENGTH_MM_TO_VOLTAGE_V,
    SUSPENSION_DISC_COUNT_TO_VOLTAGE_V,
    TYPICAL_LOADING_FRACTION,
    VOLTAGE_CLASS_BOUNDS_V,
    ClassScore,
    Conductor,
    UtilityStandard,
    VoltageClass,
    classify_voltage,
    conductors_near_diameter,
    find_utility_standard,
    minimum_approach_distance_m,
    typical_conductors_for_class,
)

#: Distance at which a GIS line is still considered to plausibly be the subject
#: of the photograph. Beyond this the tag is context, not identification.
GIS_SUBJECT_RADIUS_M = 120.0
GIS_CONTEXT_RADIUS_M = 500.0

STRUCTURE_TO_CLASSES: dict[StructureType, tuple[tuple[VoltageClass, float], ...]] = {
    StructureType.SERVICE_POLE: ((VoltageClass.SECONDARY, 0.8), (VoltageClass.DISTRIBUTION, 0.2)),
    StructureType.DISTRIBUTION_POLE: (
        (VoltageClass.DISTRIBUTION, 0.8),
        (VoltageClass.SECONDARY, 0.15),
        (VoltageClass.SUBTRANSMISSION, 0.05),
    ),
    StructureType.SUBTRANSMISSION_POLE: (
        (VoltageClass.SUBTRANSMISSION, 0.7),
        (VoltageClass.DISTRIBUTION, 0.2),
        (VoltageClass.TRANSMISSION, 0.1),
    ),
    StructureType.TRANSMISSION_TOWER: (
        (VoltageClass.TRANSMISSION, 0.6),
        (VoltageClass.SUBTRANSMISSION, 0.2),
        (VoltageClass.EHV, 0.2),
    ),
    StructureType.H_FRAME: (
        (VoltageClass.SUBTRANSMISSION, 0.45),
        (VoltageClass.TRANSMISSION, 0.45),
        (VoltageClass.DISTRIBUTION, 0.10),
    ),
}

MATERIAL_TO_CLASSES: dict[PoleMaterial, tuple[tuple[VoltageClass, float], ...]] = {
    PoleMaterial.WOOD: (
        (VoltageClass.DISTRIBUTION, 0.62),
        (VoltageClass.SECONDARY, 0.18),
        (VoltageClass.SUBTRANSMISSION, 0.18),
        (VoltageClass.TRANSMISSION, 0.02),
    ),
    PoleMaterial.LATTICE_STEEL: (
        (VoltageClass.TRANSMISSION, 0.6),
        (VoltageClass.EHV, 0.25),
        (VoltageClass.SUBTRANSMISSION, 0.15),
    ),
    PoleMaterial.STEEL: (
        (VoltageClass.DISTRIBUTION, 0.35),
        (VoltageClass.SUBTRANSMISSION, 0.35),
        (VoltageClass.TRANSMISSION, 0.30),
    ),
    PoleMaterial.CONCRETE: (
        (VoltageClass.DISTRIBUTION, 0.5),
        (VoltageClass.SUBTRANSMISSION, 0.3),
        (VoltageClass.TRANSMISSION, 0.2),
    ),
    PoleMaterial.COMPOSITE: (
        (VoltageClass.DISTRIBUTION, 0.7),
        (VoltageClass.SUBTRANSMISSION, 0.3),
    ),
}


@dataclass
class InferenceResult:
    utility: UtilityEstimate
    voltage: VoltageEstimate
    conductor: ConductorEstimate
    current: CurrentEstimate
    evidence: list[EvidenceItem]
    reasoning: list[str]
    warnings: list[Warning]
    overall_confidence: float


class InferenceEngine:
    """Deterministic, auditable fusion of vision + GIS + published standards."""

    def run(
        self,
        vision: VisionAnalysis,
        gis: GISContext,
        capture: CaptureContext,
    ) -> InferenceResult:
        evidence: list[EvidenceItem] = []
        warnings: list[Warning] = []
        reasoning: list[str] = []

        if not vision.is_power_infrastructure and vision.model_name != "vision_disabled":
            warnings.append(
                Warning(
                    severity="caution",
                    code="not_power_infrastructure",
                    message=(
                        "The image analyser did not find overhead electrical "
                        "infrastructure. The report below rests on location data only."
                    ),
                )
            )

        utility, standard = self._infer_utility(gis, evidence)
        voltage = self._infer_voltage(vision, gis, standard, evidence, reasoning, warnings)
        conductor = self._infer_conductor(vision, voltage, evidence, reasoning)
        current = self._infer_current(conductor, voltage, evidence, reasoning)

        self._quality_warnings(vision, gis, capture, voltage, warnings)

        overall = self._overall_confidence(vision, gis, voltage, utility, conductor)

        reasoning.insert(
            0,
            self._headline(voltage, utility, vision, gis),
        )

        return InferenceResult(
            utility=utility,
            voltage=voltage,
            conductor=conductor,
            current=current,
            evidence=evidence,
            reasoning=reasoning,
            warnings=warnings,
            overall_confidence=overall,
        )

    # -- Utility -----------------------------------------------------------

    def _infer_utility(
        self, gis: GISContext, evidence: list[EvidenceItem]
    ) -> tuple[UtilityEstimate, UtilityStandard | None]:
        tagged: dict[str, float] = {}
        for asset in gis.assets:
            if not asset.operator:
                continue
            distance = asset.distance_m if asset.distance_m is not None else GIS_CONTEXT_RADIUS_M
            # Weight by proximity: an operator tag on the pole you are standing
            # under is worth far more than one 400 m away.
            weight = 1.0 / (1.0 + distance / 100.0)
            if asset.asset_kind in {"line", "minor_line", "substation"}:
                weight *= 1.5
            tagged[asset.operator] = tagged.get(asset.operator, 0.0) + weight

        if not tagged:
            evidence.append(
                EvidenceItem(
                    source="gis",
                    observation="No operator tag on any nearby power asset",
                    implication="Utility ownership could not be attributed from public GIS data",
                    weight=0.0,
                    confidence=0.0,
                )
            )
            return UtilityEstimate(confidence=0.0, source="none"), None

        ranked = sorted(tagged.items(), key=lambda kv: -kv[1])
        best_name, best_weight = ranked[0]
        total = sum(tagged.values())
        share = best_weight / total if total else 0.0
        # Confidence rises with both share of tags and absolute evidence mass.
        confidence = min(0.95, share * (1 - math.exp(-best_weight)))

        standard = find_utility_standard(best_name)
        evidence.append(
            EvidenceItem(
                source="gis",
                observation=(
                    f"{len([a for a in gis.assets if a.operator == best_name])} nearby asset(s) "
                    f"tagged operator='{best_name}'"
                ),
                implication=f"Circuit is most likely owned by {best_name}",
                weight=0.6,
                confidence=round(confidence, 3),
                reference="OpenStreetMap operator tag",
            )
        )
        if standard:
            evidence.append(
                EvidenceItem(
                    source="standards",
                    observation=f"{standard.operator} construction standard is on file",
                    implication=(
                        "Primary distribution voltages "
                        + ", ".join(f"{v / 1000:g} kV" for v in standard.primary_distribution_v)
                        + (f". {standard.notes}" if standard.notes else "")
                    ),
                    weight=0.35,
                    confidence=0.8,
                    reference=f"{standard.operator} ({standard.region})",
                )
            )

        return (
            UtilityEstimate(
                name=standard.operator if standard else best_name,
                confidence=round(confidence, 3),
                source="osm_operator_tag",
                region=standard.region if standard else None,
                known_standard=standard is not None,
                alternatives=[name for name, _ in ranked[1:4]],
            ),
            standard,
        )

    # -- Voltage -----------------------------------------------------------

    def _infer_voltage(
        self,
        vision: VisionAnalysis,
        gis: GISContext,
        standard: UtilityStandard | None,
        evidence: list[EvidenceItem],
        reasoning: list[str],
        warnings: list[Warning],
    ) -> VoltageEstimate:
        scores: dict[VoltageClass, ClassScore] = {
            cls: ClassScore(cls) for cls in VoltageClass if cls != VoltageClass.UNKNOWN
        }

        confirmed_v: int | None = None
        confirmation_source: str | None = None

        # 1. GIS voltage tag — the strongest single signal available.
        subject = self._gis_subject_line(gis)
        if subject and subject.voltage_v:
            distance = subject.distance_m if subject.distance_m is not None else GIS_SUBJECT_RADIUS_M
            proximity = max(0.15, 1.0 - distance / GIS_CONTEXT_RADIUS_M)
            for volts in subject.voltage_v:
                cls = classify_voltage(volts)
                if cls in scores:
                    scores[cls].add(
                        3.2 * proximity,
                        f"OSM voltage tag {volts / 1000:g} kV on '{subject.name or subject.asset_kind}' "
                        f"{distance:.0f} m away",
                    )
            if distance <= GIS_SUBJECT_RADIUS_M:
                confirmed_v = subject.voltage_v[0]
                confirmation_source = (
                    f"OpenStreetMap voltage tag on {subject.element_type}/{subject.element_id} "
                    f"at {distance:.0f} m"
                )
            evidence.append(
                EvidenceItem(
                    source="gis",
                    observation=(
                        f"Nearest mapped power line ({subject.asset_kind}) is {distance:.0f} m away, "
                        f"tagged voltage {'/'.join(f'{v / 1000:g} kV' for v in subject.voltage_v)}"
                    ),
                    implication=(
                        "Direct voltage attribution from surveyed GIS data"
                        if distance <= GIS_SUBJECT_RADIUS_M
                        else "Nearby voltage context; too far to attribute to the photographed span"
                    ),
                    weight=round(0.9 * proximity, 3),
                    confidence=round(0.85 * proximity, 3),
                    reference=f"OSM {subject.element_type}/{subject.element_id}",
                )
            )
        elif subject:
            evidence.append(
                EvidenceItem(
                    source="gis",
                    observation=(
                        f"Nearest mapped power line ({subject.asset_kind}) has no voltage tag"
                    ),
                    implication="Voltage must be inferred from construction evidence alone",
                    weight=0.1,
                    confidence=0.4,
                    reference=f"OSM {subject.element_type}/{subject.element_id}",
                )
            )
            # ``minor_line`` in OSM specifically means distribution-scale.
            if subject.asset_kind == "minor_line":
                scores[VoltageClass.DISTRIBUTION].add(
                    0.9, "OSM classifies the nearest line as power=minor_line (distribution scale)"
                )

        # 2. Structure type and material.
        if vision.structure_type in STRUCTURE_TO_CLASSES:
            det_conf = self._structure_confidence(vision)
            for cls, share in STRUCTURE_TO_CLASSES[vision.structure_type]:
                scores[cls].add(
                    1.4 * share * det_conf,
                    f"Structure identified as {vision.structure_type.value.replace('_', ' ')}",
                )
            evidence.append(
                EvidenceItem(
                    source="vision",
                    observation=f"Structure type: {vision.structure_type.value.replace('_', ' ')}",
                    implication=self._structure_implication(vision.structure_type),
                    weight=0.45,
                    confidence=round(det_conf, 3),
                )
            )

        if vision.pole_material in MATERIAL_TO_CLASSES:
            for cls, share in MATERIAL_TO_CLASSES[vision.pole_material]:
                scores[cls].add(
                    0.9 * share * max(vision.overall_confidence, 0.3),
                    f"{vision.pole_material.value.replace('_', ' ').title()} structure",
                )
            evidence.append(
                EvidenceItem(
                    source="vision",
                    observation=f"Pole material: {vision.pole_material.value.replace('_', ' ')}",
                    implication=self._material_implication(vision.pole_material),
                    weight=0.3,
                    confidence=round(max(vision.overall_confidence, 0.3), 3),
                    reference="Utility construction practice",
                )
            )

        # 3. Insulator string length — the classic field method.
        self._score_insulators(vision, scores, evidence)

        # 4. Phase spacing.
        self._score_spacing(vision, scores, evidence)

        # 5. Hardware constraints.
        self._score_hardware(vision, scores, evidence)

        # 6. Utility construction prior.
        if standard:
            for volts in standard.primary_distribution_v:
                scores[classify_voltage(volts)].add(
                    0.15, f"{standard.operator} standard primary distribution"
                )
            for volts in standard.subtransmission_v:
                cls = classify_voltage(volts)
                if cls in scores:
                    scores[cls].add(0.10, f"{standard.operator} operates {volts / 1000:g} kV subtransmission")

        ranked = sorted(scores.values(), key=lambda s: -s.score)
        top = ranked[0]

        if top.score < 0.5:
            reasoning.append(
                "Evidence was too thin to distinguish a voltage class. Both the "
                "image analysis and the GIS lookup returned little usable signal."
            )
            return VoltageEstimate(
                voltage_class=VoltageClass.UNKNOWN,
                class_label=VoltageClass.UNKNOWN.label,
                class_confidence=0.0,
                possible_nominal_v=[],
                alternatives=[],
            )

        total_score = sum(max(s.score, 0.0) for s in ranked) or 1.0
        class_confidence = top.score / total_score
        # A clear margin over the runner-up matters as much as the raw share.
        runner_up = ranked[1].score if len(ranked) > 1 else 0.0
        margin = (top.score - runner_up) / (top.score or 1.0)
        class_confidence = min(0.97, class_confidence * (0.6 + 0.4 * margin))

        if confirmed_v is not None:
            confirmed_class = classify_voltage(confirmed_v)
            if confirmed_class != top.voltage_class:
                warnings.append(
                    Warning(
                        severity="caution",
                        code="gis_vision_conflict",
                        message=(
                            f"The surveyed GIS voltage tag ({confirmed_v / 1000:g} kV, "
                            f"{confirmed_class.label}) disagrees with the construction "
                            f"evidence in the photograph ({top.voltage_class.label}). "
                            "The GIS tag may belong to a different circuit on the same "
                            "right of way, or the tag may be stale."
                        ),
                    )
                )
                reasoning.append(
                    f"Conflict retained rather than resolved: GIS says {confirmed_class.label}, "
                    f"imagery says {top.voltage_class.label}. Confidence reduced accordingly."
                )
                class_confidence *= 0.6
                confirmed_v = None
                confirmation_source = None

        possible = self._possible_nominals(top.voltage_class, standard, gis, confirmed_v)
        most_likely = self._most_likely_nominal(possible, top.voltage_class, standard, gis, confirmed_v)

        reasoning.extend(
            f"{top.voltage_class.label}: {reason}" for reason in top.reasons[:6]
        )

        alternatives = [
            {
                "voltage_class": s.voltage_class.value,
                "label": s.voltage_class.label,
                "relative_score": round(s.score / total_score, 3),
                "top_reason": s.reasons[0] if s.reasons else None,
            }
            for s in ranked[1:4]
            if s.score > 0
        ]

        return VoltageEstimate(
            voltage_class=top.voltage_class,
            class_label=top.voltage_class.label,
            class_confidence=round(class_confidence, 3),
            possible_nominal_v=possible,
            most_likely_nominal_v=most_likely,
            is_confirmed=confirmed_v is not None,
            confirmation_source=confirmation_source,
            alternatives=alternatives,
        )

    def _gis_subject_line(self, gis: GISContext) -> GISAsset | None:
        """The mapped line most likely to be the one in the photograph."""
        candidates = [
            a
            for a in gis.assets
            if a.asset_kind in {"line", "minor_line", "cable"}
            and (a.distance_m is None or a.distance_m <= GIS_CONTEXT_RADIUS_M)
        ]
        if not candidates:
            return None
        # Prefer a tagged line at comparable distance over an untagged closer one.
        def key(asset: GISAsset) -> tuple[float, float]:
            distance = asset.distance_m if asset.distance_m is not None else GIS_CONTEXT_RADIUS_M
            return (0 if asset.voltage_v else 1, distance)

        return min(candidates, key=key)

    def _score_insulators(
        self,
        vision: VisionAnalysis,
        scores: dict[VoltageClass, ClassScore],
        evidence: list[EvidenceItem],
    ) -> None:
        discs = vision.insulator_disc_count
        if discs and discs > 0 and vision.insulator_type in {
            InsulatorType.SUSPENSION_DISC,
            InsulatorType.STRAIN,
            InsulatorType.UNKNOWN,
        }:
            low, high = self._disc_range(discs)
            weight = 2.0 if vision.insulator_type == InsulatorType.SUSPENSION_DISC else 1.0
            for cls in self._classes_spanning(low, high):
                scores[cls].add(
                    weight,
                    f"{discs}-disc insulator string implies roughly "
                    f"{low / 1000:g}-{high / 1000:g} kV",
                )
            evidence.append(
                EvidenceItem(
                    source="vision",
                    observation=f"Suspension string with {discs} disc(s)",
                    implication=(
                        f"Standard ANSI C29.2 discs are rated at roughly 10-15 kV of system "
                        f"voltage each with contamination margin, giving "
                        f"{low / 1000:g}-{high / 1000:g} kV"
                    ),
                    weight=0.7,
                    confidence=0.75,
                    reference="ANSI C29.2 / utility insulation coordination practice",
                )
            )

        length = vision.insulator_length
        measured = length.value or (
            (length.low + length.high) / 2 if length.low and length.high else None
        )
        if measured and vision.insulator_type in {
            InsulatorType.PIN,
            InsulatorType.POST,
            InsulatorType.POLYMER_LONGROD,
            InsulatorType.UNKNOWN,
        }:
            for min_mm, max_mm, min_v, max_v in PIN_INSULATOR_LENGTH_MM_TO_VOLTAGE_V:
                if min_mm <= measured <= max_mm:
                    for cls in self._classes_spanning(min_v, max_v):
                        scores[cls].add(
                            1.1 * max(length.confidence, 0.3),
                            f"{measured:.0f} mm pin/post insulator implies "
                            f"{min_v / 1000:g}-{max_v / 1000:g} kV",
                        )
                    evidence.append(
                        EvidenceItem(
                            source="vision",
                            observation=(
                                f"Insulator length estimated at {measured:.0f} mm"
                                + (f" (scaled from {length.basis})" if length.basis else "")
                            ),
                            implication=(
                                f"ANSI C29.1 pin/post insulators of that length are specified for "
                                f"{min_v / 1000:g}-{max_v / 1000:g} kV systems"
                            ),
                            weight=0.5,
                            confidence=round(max(length.confidence, 0.3), 3),
                            reference="ANSI C29.1",
                        )
                    )
                    break

    def _score_spacing(
        self,
        vision: VisionAnalysis,
        scores: dict[VoltageClass, ClassScore],
        evidence: list[EvidenceItem],
    ) -> None:
        spacing = vision.conductor_spacing
        value = spacing.value or (
            (spacing.low + spacing.high) / 2 if spacing.low and spacing.high else None
        )
        if not value:
            return
        matched: list[VoltageClass] = []
        for cls, (low, high) in PHASE_SPACING_M.items():
            if low <= value <= high:
                scores[cls].add(
                    0.8 * max(spacing.confidence, 0.3),
                    f"{value:.2f} m phase spacing is typical of {cls.label}",
                )
                matched.append(cls)
        if matched:
            evidence.append(
                EvidenceItem(
                    source="vision",
                    observation=f"Phase-to-phase spacing estimated at {value:.2f} m",
                    implication=(
                        "Consistent with "
                        + " or ".join(c.label for c in matched)
                        + " construction under NESC Rule 235 separation requirements"
                    ),
                    weight=0.4,
                    confidence=round(max(spacing.confidence, 0.3), 3),
                    reference="NESC (ANSI C2) Rule 235",
                )
            )

    def _score_hardware(
        self,
        vision: VisionAnalysis,
        scores: dict[VoltageClass, ClassScore],
        evidence: list[EvidenceItem],
    ) -> None:
        implied: dict[str, float] = {}

        for label, classes in HARDWARE_VOLTAGE_CONSTRAINTS.items():
            det = vision.detection(label)
            if det is None or not det.present or det.confidence < 0.45:
                continue
            implied[label] = det.confidence
            share = 1.0 / len(classes)
            for cls in classes:
                if cls in scores:
                    scores[cls].add(
                        1.6 * share * det.confidence,
                        f"{label.replace('_', ' ').title()} present, which only exists on "
                        + " / ".join(c.label for c in classes),
                    )

        if vision.conductor_covering == ConductorCovering.SPACER_CABLE:
            scores[VoltageClass.DISTRIBUTION].add(
                1.2, "Spacer cable construction, manufactured for 15/25/35 kV only"
            )
        elif vision.conductor_covering == ConductorCovering.TRIPLEX_SECONDARY:
            scores[VoltageClass.SECONDARY].add(1.5, "Triplex service conductor (120/240 V)")

        if (vision.bundled_subconductors or 1) > 1:
            scores[VoltageClass.TRANSMISSION].add(
                1.0, f"{vision.bundled_subconductors}-conductor bundle per phase"
            )
            scores[VoltageClass.EHV].add(
                1.2,
                f"{vision.bundled_subconductors}-conductor bundle per phase is used to control "
                "corona above 230 kV",
            )

        if vision.crossarm_config == CrossarmConfig.ARMLESS:
            scores[VoltageClass.DISTRIBUTION].add(
                0.4, "Armless (vertical post) construction is a distribution standard"
            )
        elif vision.crossarm_config == CrossarmConfig.H_FRAME:
            scores[VoltageClass.SUBTRANSMISSION].add(0.5, "H-frame construction")
            scores[VoltageClass.TRANSMISSION].add(0.5, "H-frame construction")

        if implied:
            evidence.append(
                EvidenceItem(
                    source="vision",
                    observation="Hardware detected: "
                    + ", ".join(sorted(f"{k.replace('_', ' ')}" for k in implied)),
                    implication=self._hardware_implication(implied),
                    weight=0.55,
                    confidence=round(sum(implied.values()) / len(implied), 3),
                    reference="Utility equipment voltage ratings",
                )
            )

    def _hardware_implication(self, implied: dict[str, float]) -> str:
        parts = []
        if "transformer" in implied:
            parts.append(
                "A pole-mounted distribution transformer bounds the primary at 34.5 kV — "
                "these units are not manufactured above that"
            )
        if "cutout_fuse" in implied:
            parts.append("Fused cutouts are distribution-class protection hardware")
        if "shield_wire" in implied:
            parts.append("An overhead shield wire is normal at 69 kV and above")
        if "corona_ring" in implied:
            parts.append("Corona rings are fitted at 230 kV and above")
        if "secondary_rack" in implied:
            parts.append("A secondary rack carries the 120/240 V service")
        if "spacer_cable" in implied:
            parts.append("Spacer cable is a 15-35 kV covered distribution product")
        return ". ".join(parts) if parts else "Hardware narrows the plausible voltage classes"

    def _disc_range(self, discs: int) -> tuple[int, int]:
        table = SUSPENSION_DISC_COUNT_TO_VOLTAGE_V
        if discs in table:
            return table[discs]
        keys = sorted(table)
        below = max((k for k in keys if k < discs), default=keys[0])
        above = min((k for k in keys if k > discs), default=keys[-1])
        return table[below][0], table[above][1]

    def _classes_spanning(self, low_v: float, high_v: float) -> list[VoltageClass]:
        out = []
        for cls, (cls_low, cls_high) in VOLTAGE_CLASS_BOUNDS_V.items():
            if high_v >= cls_low and low_v <= cls_high:
                out.append(cls)
        return out

    def _possible_nominals(
        self,
        cls: VoltageClass,
        standard: UtilityStandard | None,
        gis: GISContext,
        confirmed_v: int | None,
    ) -> list[int]:
        if confirmed_v is not None:
            return [confirmed_v]

        catalogue = set(NOMINAL_VOLTAGES_V.get(cls, ()))
        if not catalogue:
            return []

        # A known utility standard replaces the catalogue outright: if PG&E only
        # builds 12 kV, 17.2 kV and 21 kV primary, then 13.8 kV is not a live
        # option here no matter how common it is nationally. Note this can
        # introduce voltages absent from the ANSI list — PG&E's 12 kV and 60 kV
        # are real systems that ANSI C84.1 does not enumerate.
        if standard:
            standard_v = {
                v
                for v in (
                    standard.primary_distribution_v
                    + standard.subtransmission_v
                    + standard.transmission_v
                )
                if classify_voltage(v) == cls
            }
            if standard_v:
                catalogue = standard_v

        # Voltages actually observed in nearby GIS tags outrank the catalogue.
        observed = {v for v in gis.voltages_v if classify_voltage(v) == cls}
        if observed:
            catalogue = (catalogue & observed) or (catalogue | observed)

        return sorted(catalogue)

    def _most_likely_nominal(
        self,
        possible: list[int],
        cls: VoltageClass,
        standard: UtilityStandard | None,
        gis: GISContext,
        confirmed_v: int | None,
    ) -> int | None:
        if confirmed_v is not None:
            return confirmed_v
        if not possible:
            return None
        # Prefer a voltage observed nearby, then the utility's own standard,
        # then the most common value in the class.
        observed = [v for v in gis.voltages_v if v in possible]
        if observed:
            return observed[0]
        if standard:
            for v in standard.primary_distribution_v + standard.subtransmission_v:
                if v in possible:
                    return v
        return possible[len(possible) // 2]

    # -- Conductor ---------------------------------------------------------

    def _infer_conductor(
        self,
        vision: VisionAnalysis,
        voltage: VoltageEstimate,
        evidence: list[EvidenceItem],
        reasoning: list[str],
    ) -> ConductorEstimate:
        diameter = vision.conductor_diameter
        measured = diameter.value or (
            (diameter.low + diameter.high) / 2 if diameter.low and diameter.high else None
        )

        candidates: list[Conductor] = []
        confidence = 0.0
        basis = ""

        if measured:
            tolerance = 2.5
            if diameter.low and diameter.high:
                tolerance = max(2.0, (diameter.high - diameter.low) / 2)
            candidates = conductors_near_diameter(measured, tolerance)
            if voltage.voltage_class != VoltageClass.UNKNOWN:
                plausible = [c for c in candidates if voltage.voltage_class in c.typical_classes]
                if plausible:
                    candidates = plausible
            confidence = min(0.75, max(diameter.confidence, 0.25))
            basis = (
                f"Conductor diameter estimated at {measured:.1f} mm"
                + (f" (scaled from {diameter.basis})" if diameter.basis else "")
            )
            evidence.append(
                EvidenceItem(
                    source="vision",
                    observation=basis,
                    implication=(
                        "Matched against published ACSR/AAC diameters: "
                        + ", ".join(f"{c.codeword} ({c.size})" for c in candidates[:3])
                        if candidates
                        else "No catalogue conductor matches that diameter"
                    ),
                    weight=0.4,
                    confidence=round(confidence, 3),
                    reference="Aluminum Electrical Conductor Handbook",
                )
            )

        if not candidates and voltage.voltage_class != VoltageClass.UNKNOWN:
            candidates = typical_conductors_for_class(voltage.voltage_class)
            confidence = 0.2
            basis = (
                f"No usable diameter measurement; candidates are the conductors "
                f"commonly built at {voltage.class_label}"
            )
            evidence.append(
                EvidenceItem(
                    source="standards",
                    observation="Conductor size not measurable from the image",
                    implication=(
                        f"Fell back to the conductor population typical of {voltage.class_label}"
                    ),
                    weight=0.15,
                    confidence=0.2,
                    reference="Aluminum Electrical Conductor Handbook",
                )
            )

        if not candidates:
            return ConductorEstimate(confidence=0.0)

        # Rating is quoted from the *smallest* plausible candidate: it is the
        # binding constraint and quoting the largest would overstate capacity.
        binding = min(candidates, key=lambda c: c.ampacity_75c_a)
        best = candidates[0]

        if vision.conductor_covering == ConductorCovering.COVERED:
            reasoning.append(
                "Conductor appears covered (tree wire). Covered conductor runs hotter "
                "than bare for the same current, so the effective rating is roughly "
                "10-15% below the bare-conductor figure quoted here."
            )

        return ConductorEstimate(
            candidates=[
                {
                    "codeword": c.codeword,
                    "material": c.material,
                    "size": c.size,
                    "diameter_mm": c.diameter_mm,
                    "ampacity_75c_a": c.ampacity_75c_a,
                    "ampacity_100c_a": c.ampacity_100c_a,
                }
                for c in candidates[:5]
            ],
            most_likely_codeword=best.codeword,
            most_likely_material=best.material,
            most_likely_size=best.size,
            estimated_diameter_mm=round(measured, 1) if measured else best.diameter_mm,
            thermal_rating_a=binding.ampacity_75c_a,
            thermal_rating_basis=(
                f"{binding.material} {binding.size} ({binding.codeword}) at 75 C conductor, "
                "25 C ambient, 0.6 m/s crosswind. Quoted from the smallest plausible "
                "candidate because it is the binding limit. "
                + basis
            ),
            confidence=round(confidence, 3),
        )

    # -- Current -----------------------------------------------------------

    def _infer_current(
        self,
        conductor: ConductorEstimate,
        voltage: VoltageEstimate,
        evidence: list[EvidenceItem],
        reasoning: list[str],
    ) -> CurrentEstimate:
        if not conductor.thermal_rating_a:
            reasoning.append(
                "No operating current range is offered: without a conductor size "
                "there is no defensible basis for one."
            )
            return CurrentEstimate(
                basis="Insufficient evidence to bound operating current",
                confidence=0.0,
            )

        low_fraction, high_fraction = TYPICAL_LOADING_FRACTION.get(
            voltage.voltage_class, TYPICAL_LOADING_FRACTION[VoltageClass.UNKNOWN]
        )
        low = conductor.thermal_rating_a * low_fraction
        high = conductor.thermal_rating_a * high_fraction

        evidence.append(
            EvidenceItem(
                source="standards",
                observation=(
                    f"Conductor thermal rating {conductor.thermal_rating_a} A; "
                    f"{voltage.class_label} circuits typically run at "
                    f"{low_fraction:.0%}-{high_fraction:.0%} of rating"
                ),
                implication=(
                    f"Plausible operating current {low:.0f}-{high:.0f} A. This is a "
                    "population statistic, not a measurement of this circuit."
                ),
                weight=0.3,
                confidence=round(conductor.confidence * 0.7, 3),
                reference="Utility loading practice / N-1 planning headroom",
            )
        )

        reasoning.append(
            f"Operating current is presented as a range ({low:.0f}-{high:.0f} A) derived "
            f"from the {conductor.thermal_rating_a} A thermal rating and typical loading "
            "factors. Actual flow varies with time of day, season and switching state, "
            "and can be near zero on an open feeder."
        )

        return CurrentEstimate(
            low_a=round(low, 1),
            high_a=round(high, 1),
            basis=(
                f"{low_fraction:.0%}-{high_fraction:.0%} of a {conductor.thermal_rating_a} A "
                f"thermal rating ({conductor.most_likely_codeword or 'unknown conductor'})"
            ),
            is_measured=False,
            confidence=round(conductor.confidence * 0.6, 3),
        )

    # -- Warnings & confidence --------------------------------------------

    def _quality_warnings(
        self,
        vision: VisionAnalysis,
        gis: GISContext,
        capture: CaptureContext,
        voltage: VoltageEstimate,
        warnings: list[Warning],
    ) -> None:
        if capture.accuracy_m is not None and capture.accuracy_m > 30:
            warnings.append(
                Warning(
                    severity="caution",
                    code="poor_gps",
                    message=(
                        f"GPS accuracy is {capture.accuracy_m:.0f} m. GIS matching at this "
                        "accuracy may pick up the wrong circuit."
                    ),
                )
            )

        if vision.model_name == "vision_disabled":
            warnings.append(
                Warning(
                    severity="info",
                    code="vision_unavailable",
                    message=(
                        "Image analysis was not performed. Conclusions rest on GIS data alone."
                    ),
                )
            )
        elif vision.image_quality < 0.4:
            warnings.append(
                Warning(
                    severity="caution",
                    code="low_image_quality",
                    message=(
                        "Image quality is low. Dimensional estimates from this frame are "
                        "unreliable; re-shoot closer, with the crossarm and insulators in frame."
                    ),
                )
            )

        if vision.obstructed:
            warnings.append(
                Warning(
                    severity="info",
                    code="obstructed_view",
                    message="Part of the structure is obscured; some hardware may be missed.",
                )
            )

        if not gis.assets:
            warnings.append(
                Warning(
                    severity="info",
                    code="no_gis_coverage",
                    message=(
                        "No mapped power infrastructure was found near this location. "
                        "OpenStreetMap distribution coverage is sparse outside urban areas."
                    ),
                )
            )

        for error in gis.errors:
            warnings.append(
                Warning(
                    severity="info",
                    code="gis_source_error",
                    message=f"A GIS source did not respond ({error}); coverage may be incomplete.",
                )
            )

        if voltage.voltage_class != VoltageClass.UNKNOWN:
            reference_v = voltage.most_likely_nominal_v or max(
                voltage.possible_nominal_v or [0]
            )
            if reference_v:
                mad = minimum_approach_distance_m(reference_v)
                warnings.append(
                    Warning(
                        severity="danger",
                        code="approach_distance",
                        message=(
                            f"If this is a {reference_v / 1000:g} kV circuit, OSHA 1910.269 "
                            f"Table R-6 sets a {mad:.2f} m minimum approach distance for "
                            "qualified workers. Unqualified persons and uncertified aircraft "
                            "must stay much further back. This estimate is not a clearance "
                            "authorisation."
                        ),
                    )
                )

        warnings.append(
            Warning(
                severity="danger",
                code="treat_as_energised",
                message=(
                    "Treat every conductor as energised at the highest plausible voltage "
                    "until the operating utility confirms otherwise."
                ),
            )
        )

    def _overall_confidence(
        self,
        vision: VisionAnalysis,
        gis: GISContext,
        voltage: VoltageEstimate,
        utility: UtilityEstimate,
        conductor: ConductorEstimate,
    ) -> float:
        # Weighted mean over the components that actually contributed. An
        # absent component contributes zero rather than being skipped, so a
        # report built on one source cannot reach high confidence.
        components = [
            (voltage.class_confidence, 0.40),
            (utility.confidence, 0.20),
            (conductor.confidence, 0.15),
            (vision.overall_confidence, 0.15),
            (min(1.0, gis.asset_count / 8.0), 0.10),
        ]
        score = sum(value * weight for value, weight in components)
        if voltage.is_confirmed:
            score = min(1.0, score + 0.10)
        return round(min(0.97, max(0.0, score)), 3)

    def _headline(
        self,
        voltage: VoltageEstimate,
        utility: UtilityEstimate,
        vision: VisionAnalysis,
        gis: GISContext,
    ) -> str:
        who = utility.name or "an unidentified operator"
        if voltage.voltage_class == VoltageClass.UNKNOWN:
            return (
                f"Unable to determine a voltage class from the available evidence "
                f"({vision.model_name if vision.model_name != 'vision_disabled' else 'no image analysis'}, "
                f"{gis.asset_count} nearby mapped assets)."
            )
        nominal = (
            f", most likely {voltage.most_likely_nominal_v / 1000:g} kV"
            if voltage.most_likely_nominal_v
            else ""
        )
        confirmed = " (confirmed by a surveyed GIS tag)" if voltage.is_confirmed else " (estimated)"
        return (
            f"Assessed as {voltage.class_label}{nominal}{confirmed}, operated by {who}."
        )

    # -- Static implication text -------------------------------------------

    def _structure_implication(self, structure: StructureType) -> str:
        return {
            StructureType.SERVICE_POLE: "Service poles carry only the 120/240 V secondary.",
            StructureType.DISTRIBUTION_POLE: (
                "Distribution poles carry 4-35 kV primary, often with secondary below."
            ),
            StructureType.SUBTRANSMISSION_POLE: (
                "Subtransmission poles carry 46-115 kV between substations."
            ),
            StructureType.TRANSMISSION_TOWER: (
                "Lattice towers are effectively never built below 69 kV; 115 kV and above "
                "is the normal range."
            ),
            StructureType.H_FRAME: "H-frames carry 69-345 kV single circuits on long spans.",
            StructureType.DEAD_END: "Dead-end structures terminate conductor tension.",
            StructureType.SUSPENSION: "Suspension structures carry conductor through the span.",
        }.get(structure, "Structure type does not constrain voltage on its own.")

    def _material_implication(self, material: PoleMaterial) -> str:
        return {
            PoleMaterial.WOOD: (
                "Wood dominates 4-35 kV primary construction and is common up to 69 kV "
                "in rural subtransmission, but is rare above that."
            ),
            PoleMaterial.LATTICE_STEEL: (
                "Lattice steel is a transmission structure; it is not economic below 69 kV."
            ),
            PoleMaterial.STEEL: (
                "Tubular steel spans hardened distribution through 230 kV transmission."
            ),
            PoleMaterial.CONCRETE: (
                "Spun concrete appears in coastal and fire-hardening programmes across "
                "distribution and subtransmission."
            ),
            PoleMaterial.COMPOSITE: (
                "Composite poles are a distribution and light subtransmission product."
            ),
        }.get(material, "Material does not constrain voltage on its own.")

    def _structure_confidence(self, vision: VisionAnalysis) -> float:
        label_map = {
            StructureType.TRANSMISSION_TOWER: "transmission_tower",
            StructureType.DISTRIBUTION_POLE: "distribution_pole",
            StructureType.DEAD_END: "dead_end_pole",
            StructureType.SUSPENSION: "suspension_pole",
        }
        label = label_map.get(vision.structure_type)
        if label:
            det = vision.detection(label)
            if det and det.present:
                return det.confidence
        return max(vision.overall_confidence, 0.3)
