"""Domain knowledge base for overhead line identification.

Everything in this module is a *published engineering reference* or an
explicitly-labelled heuristic. The inference engine is only allowed to draw on
values defined here, which is what keeps the system from inventing numbers.

Sources of the reference values:
  * ANSI C84.1 — nominal system voltages.
  * IEEE Std 516 / OSHA 1910.269 Table R-6 — minimum approach distances and
    the voltage classes used by US utilities.
  * ANSI C29.1/C29.2 — porcelain insulator dimensions (suspension discs are
    5.75 in / 146 mm spacing, each rated roughly 10-15 kV of line-to-line
    system voltage in typical strings).
  * Aluminum Electrical Conductor Handbook (The Aluminum Association) and
    Southwire Overhead Conductor Manual — ACSR/AAC codeword diameters and
    75 C ampacity in still air.
  * NESC (ANSI C2) Rule 235 — conductor separation vs voltage.

Nothing here should be read as a claim about a specific line: these are
population statistics used to bound an estimate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class VoltageClass(str, Enum):
    """Coarse classes utilities actually use when talking about a circuit."""

    SECONDARY = "secondary"  # < 1 kV, customer service / streetlight
    DISTRIBUTION = "distribution"  # 2.4 - 34.5 kV primary
    SUBTRANSMISSION = "subtransmission"  # 46 - 115 kV
    TRANSMISSION = "transmission"  # 115 - 345 kV
    EHV = "ehv"  # > 345 kV
    UNKNOWN = "unknown"

    @property
    def label(self) -> str:
        return {
            VoltageClass.SECONDARY: "Secondary / service (<1 kV)",
            VoltageClass.DISTRIBUTION: "Primary distribution (2.4-34.5 kV)",
            VoltageClass.SUBTRANSMISSION: "Subtransmission (46-115 kV)",
            VoltageClass.TRANSMISSION: "Transmission (115-345 kV)",
            VoltageClass.EHV: "Extra high voltage (>345 kV)",
            VoltageClass.UNKNOWN: "Undetermined",
        }[self]


#: Nominal line-to-line voltages in volts, ANSI C84.1 plus the legacy systems
#: still in service across North America.
NOMINAL_VOLTAGES_V: dict[VoltageClass, tuple[int, ...]] = {
    VoltageClass.SECONDARY: (120, 208, 240, 277, 480, 600),
    VoltageClass.DISTRIBUTION: (
        2_400,
        4_160,
        4_800,
        7_200,
        11_000,
        12_470,
        13_200,
        13_800,
        20_000,
        22_900,
        24_940,
        34_500,
    ),
    VoltageClass.SUBTRANSMISSION: (46_000, 69_000, 115_000),
    # 115 kV is called both "subtransmission" and "transmission" depending on
    # the utility. It is listed once, under subtransmission, so that a nominal
    # voltage maps to exactly one class and the two never disagree.
    VoltageClass.TRANSMISSION: (138_000, 161_000, 230_000, 345_000),
    VoltageClass.EHV: (500_000, 765_000),
}

#: Inclusive volt bounds per class, used to reconcile GIS voltage tags.
VOLTAGE_CLASS_BOUNDS_V: dict[VoltageClass, tuple[int, int]] = {
    VoltageClass.SECONDARY: (0, 1_000),
    VoltageClass.DISTRIBUTION: (1_001, 34_500),
    VoltageClass.SUBTRANSMISSION: (34_501, 115_000),
    VoltageClass.TRANSMISSION: (115_001, 345_000),
    VoltageClass.EHV: (345_001, 1_200_000),
}


def classify_voltage(volts: float) -> VoltageClass:
    """Map a nominal voltage in volts onto a class."""
    for cls, (low, high) in VOLTAGE_CLASS_BOUNDS_V.items():
        if low <= volts <= high:
            return cls
    return VoltageClass.UNKNOWN


def nearest_nominal_voltages(volts: float, limit: int = 3) -> list[int]:
    """Snap an arbitrary voltage onto the closest standard nominal values."""
    catalogue = sorted({v for values in NOMINAL_VOLTAGES_V.values() for v in values})
    return sorted(catalogue, key=lambda v: abs(v - volts))[:limit]


# ---------------------------------------------------------------------------
# Insulators
# ---------------------------------------------------------------------------

#: A standard ANSI C29.2 suspension disc is 146 mm (5.75 in) tall and a string
#: is sized at roughly one disc per 10-15 kV of system voltage plus one or two
#: discs of contamination margin. Ranges are line-to-line volts.
SUSPENSION_DISC_COUNT_TO_VOLTAGE_V: dict[int, tuple[int, int]] = {
    1: (12_470, 34_500),
    2: (34_500, 69_000),
    3: (46_000, 69_000),
    4: (69_000, 115_000),
    5: (115_000, 138_000),
    6: (115_000, 161_000),
    7: (138_000, 230_000),
    8: (161_000, 230_000),
    9: (230_000, 230_000),
    10: (230_000, 345_000),
    12: (345_000, 345_000),
    16: (500_000, 500_000),
    18: (500_000, 765_000),
    24: (765_000, 765_000),
}

SUSPENSION_DISC_HEIGHT_MM = 146.0

#: Pin / post insulator overall length (mm) against the distribution class it
#: is normally specified for. ANSI C29.1 class 55-x / 57-x families.
PIN_INSULATOR_LENGTH_MM_TO_VOLTAGE_V: tuple[tuple[float, float, int, int], ...] = (
    # (min_mm, max_mm, min_volts, max_volts)
    (80.0, 140.0, 2_400, 7_200),
    (140.0, 200.0, 4_160, 15_000),
    (200.0, 280.0, 12_470, 25_000),
    (280.0, 400.0, 24_940, 34_500),
    (400.0, 700.0, 34_500, 69_000),
)


# ---------------------------------------------------------------------------
# Phase spacing (NESC Rule 235 / common utility construction standards)
# ---------------------------------------------------------------------------

#: Typical horizontal phase-to-phase spacing in metres for each class. Real
#: construction varies with span length and terrain, so these are wide.
PHASE_SPACING_M: dict[VoltageClass, tuple[float, float]] = {
    VoltageClass.SECONDARY: (0.0, 0.35),
    VoltageClass.DISTRIBUTION: (0.3, 1.6),
    VoltageClass.SUBTRANSMISSION: (1.2, 3.5),
    VoltageClass.TRANSMISSION: (2.5, 9.0),
    VoltageClass.EHV: (7.0, 16.0),
}


# ---------------------------------------------------------------------------
# Conductors
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Conductor:
    """A published overhead conductor size."""

    codeword: str
    material: str  # ACSR, AAC, AAAC, ACSS, Cu
    size: str  # AWG or kcmil
    diameter_mm: float
    #: Steady-state thermal rating at 75 C conductor / 25 C ambient / 0.6 m/s
    #: wind, from the Aluminum Electrical Conductor Handbook.
    ampacity_75c_a: int
    #: Emergency / 100 C rating where published.
    ampacity_100c_a: int | None = None
    typical_classes: tuple[VoltageClass, ...] = ()

    @property
    def diameter_in(self) -> float:
        return self.diameter_mm / 25.4


CONDUCTOR_CATALOGUE: tuple[Conductor, ...] = (
    Conductor("Turkey", "ACSR", "6 AWG", 5.03, 105, 130, (VoltageClass.SECONDARY,)),
    Conductor("Swan", "ACSR", "4 AWG", 6.35, 140, 170, (VoltageClass.SECONDARY, VoltageClass.DISTRIBUTION)),
    Conductor("Sparrow", "ACSR", "2 AWG", 8.03, 184, 220, (VoltageClass.DISTRIBUTION,)),
    Conductor("Raven", "ACSR", "1/0 AWG", 10.11, 242, 290, (VoltageClass.DISTRIBUTION,)),
    Conductor("Quail", "ACSR", "2/0 AWG", 11.35, 276, 330, (VoltageClass.DISTRIBUTION,)),
    Conductor("Pigeon", "ACSR", "3/0 AWG", 12.75, 315, 380, (VoltageClass.DISTRIBUTION,)),
    Conductor("Penguin", "ACSR", "4/0 AWG", 14.30, 357, 430, (VoltageClass.DISTRIBUTION,)),
    Conductor("Partridge", "ACSR", "266.8 kcmil", 16.31, 457, 550, (VoltageClass.DISTRIBUTION, VoltageClass.SUBTRANSMISSION)),
    Conductor("Linnet", "ACSR", "336.4 kcmil", 18.31, 530, 640, (VoltageClass.DISTRIBUTION, VoltageClass.SUBTRANSMISSION)),
    Conductor("Hawk", "ACSR", "477 kcmil", 21.80, 670, 810, (VoltageClass.SUBTRANSMISSION, VoltageClass.TRANSMISSION)),
    Conductor("Dove", "ACSR", "556.5 kcmil", 23.55, 730, 880, (VoltageClass.SUBTRANSMISSION, VoltageClass.TRANSMISSION)),
    Conductor("Drake", "ACSR", "795 kcmil", 28.14, 907, 1_100, (VoltageClass.TRANSMISSION,)),
    Conductor("Cardinal", "ACSR", "954 kcmil", 30.38, 1_010, 1_220, (VoltageClass.TRANSMISSION,)),
    Conductor("Bittern", "ACSR", "1272 kcmil", 34.16, 1_200, 1_450, (VoltageClass.TRANSMISSION, VoltageClass.EHV)),
    Conductor("Bluebird", "ACSR", "2156 kcmil", 44.75, 1_700, 2_050, (VoltageClass.EHV,)),
)


def conductors_near_diameter(diameter_mm: float, tolerance_mm: float = 2.5) -> list[Conductor]:
    """Conductors whose published diameter is within ``tolerance_mm``."""
    matches = [c for c in CONDUCTOR_CATALOGUE if abs(c.diameter_mm - diameter_mm) <= tolerance_mm]
    return sorted(matches, key=lambda c: abs(c.diameter_mm - diameter_mm))


def typical_conductors_for_class(cls: VoltageClass) -> list[Conductor]:
    return [c for c in CONDUCTOR_CATALOGUE if cls in c.typical_classes]


#: Fraction of thermal rating a healthy circuit typically carries. Utilities
#: plan distribution feeders around a 40-60% peak loading and transmission
#: around N-1 contingency headroom, so normal flow sits well below the limit.
#: These multipliers turn a thermal rating into an *operating range*, never a
#: measurement.
TYPICAL_LOADING_FRACTION: dict[VoltageClass, tuple[float, float]] = {
    VoltageClass.SECONDARY: (0.05, 0.60),
    VoltageClass.DISTRIBUTION: (0.10, 0.55),
    VoltageClass.SUBTRANSMISSION: (0.15, 0.60),
    VoltageClass.TRANSMISSION: (0.20, 0.70),
    VoltageClass.EHV: (0.25, 0.75),
    VoltageClass.UNKNOWN: (0.10, 0.60),
}


# ---------------------------------------------------------------------------
# Structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StructureProfile:
    """What a given structure type tells us about the circuit it carries."""

    key: str
    label: str
    plausible_classes: tuple[VoltageClass, ...]
    note: str


STRUCTURE_PROFILES: dict[str, StructureProfile] = {
    "wood_distribution_pole": StructureProfile(
        "wood_distribution_pole",
        "Wood distribution pole",
        (VoltageClass.SECONDARY, VoltageClass.DISTRIBUTION, VoltageClass.SUBTRANSMISSION),
        "Wood poles dominate 4-35 kV primary; 46-69 kV on wood is common in "
        "rural subtransmission but rare above 69 kV.",
    ),
    "concrete_pole": StructureProfile(
        "concrete_pole",
        "Spun concrete pole",
        (VoltageClass.DISTRIBUTION, VoltageClass.SUBTRANSMISSION, VoltageClass.TRANSMISSION),
        "Concrete poles appear in coastal/fire-hardening programs across both "
        "distribution and subtransmission.",
    ),
    "steel_pole": StructureProfile(
        "steel_pole",
        "Tubular steel pole",
        (VoltageClass.DISTRIBUTION, VoltageClass.SUBTRANSMISSION, VoltageClass.TRANSMISSION),
        "Tubular steel monopoles are used for hardened distribution and for "
        "115-230 kV single-circuit transmission.",
    ),
    "lattice_tower": StructureProfile(
        "lattice_tower",
        "Steel lattice tower",
        (VoltageClass.TRANSMISSION, VoltageClass.EHV, VoltageClass.SUBTRANSMISSION),
        "Lattice towers are effectively never used below 69 kV.",
    ),
    "h_frame": StructureProfile(
        "h_frame",
        "H-frame structure",
        (VoltageClass.SUBTRANSMISSION, VoltageClass.TRANSMISSION),
        "H-frames carry 69-345 kV single circuits on long rural spans.",
    ),
    "unknown": StructureProfile(
        "unknown", "Unclassified structure", tuple(VoltageClass), "No structure evidence."
    ),
}


#: Hardware that pins a circuit to a specific class regardless of anything else.
HARDWARE_VOLTAGE_CONSTRAINTS: dict[str, tuple[VoltageClass, ...]] = {
    # Pole-mounted distribution transformers step primary down to secondary and
    # are only manufactured up to 34.5 kV primary.
    "transformer": (VoltageClass.DISTRIBUTION,),
    "recloser": (VoltageClass.DISTRIBUTION, VoltageClass.SUBTRANSMISSION),
    "capacitor_bank": (VoltageClass.DISTRIBUTION, VoltageClass.SUBTRANSMISSION),
    "cutout_fuse": (VoltageClass.DISTRIBUTION,),
    "spacer_cable": (VoltageClass.DISTRIBUTION,),
    "covered_conductor": (VoltageClass.DISTRIBUTION, VoltageClass.SUBTRANSMISSION),
    "secondary_rack": (VoltageClass.SECONDARY,),
    "streetlight": (VoltageClass.SECONDARY,),
    "shield_wire": (VoltageClass.SUBTRANSMISSION, VoltageClass.TRANSMISSION, VoltageClass.EHV),
    "corona_ring": (VoltageClass.TRANSMISSION, VoltageClass.EHV),
    "bundled_conductors": (VoltageClass.TRANSMISSION, VoltageClass.EHV),
}


# ---------------------------------------------------------------------------
# Utility construction standards (regional priors)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UtilityStandard:
    """A published/observed construction standard for one operator."""

    operator: str
    aliases: tuple[str, ...]
    region: str
    primary_distribution_v: tuple[int, ...]
    subtransmission_v: tuple[int, ...] = ()
    transmission_v: tuple[int, ...] = ()
    notes: str = ""


UTILITY_STANDARDS: tuple[UtilityStandard, ...] = (
    UtilityStandard(
        "Pacific Gas and Electric Company",
        ("pg&e", "pge", "pacific gas"),
        "Northern California",
        (12_000, 12_470, 17_200, 21_000),
        (60_000, 70_000, 115_000),
        (115_000, 230_000, 500_000),
        "PG&E uses a 12 kV and 21 kV primary standard and an unusual 60 kV "
        "subtransmission class.",
    ),
    UtilityStandard(
        "Southern California Edison",
        ("sce", "southern california edison", "edison"),
        "Southern California",
        (4_160, 12_000, 16_000, 33_000),
        (66_000, 115_000),
        (115_000, 220_000, 500_000),
        "SCE standardises on 12 kV and 16 kV primary with 66 kV subtransmission.",
    ),
    UtilityStandard(
        "San Diego Gas & Electric",
        ("sdg&e", "sdge", "san diego gas"),
        "Southern California",
        (4_160, 12_000),
        (69_000, 138_000),
        (138_000, 230_000, 500_000),
    ),
    UtilityStandard(
        "Consolidated Edison",
        ("con edison", "coned", "consolidated edison"),
        "New York",
        (4_160, 13_800, 27_000),
        (69_000,),
        (138_000, 345_000),
        "Con Edison runs an extensive 27 kV and 13.8 kV network with heavy "
        "underground penetration in Manhattan.",
    ),
    UtilityStandard(
        "Commonwealth Edison",
        ("comed", "commonwealth edison"),
        "Northern Illinois",
        (4_160, 12_000, 34_500),
        (69_000, 138_000),
        (138_000, 345_000),
    ),
    UtilityStandard(
        "Georgia Power",
        ("georgia power", "southern company"),
        "Georgia",
        (12_470, 25_000),
        (46_000, 115_000),
        (115_000, 230_000, 500_000),
    ),
    UtilityStandard(
        "Florida Power & Light",
        ("fpl", "florida power"),
        "Florida",
        (13_200, 22_900),
        (69_000, 138_000),
        (138_000, 230_000, 500_000),
        "FPL has aggressively converted to concrete distribution poles after "
        "the 2004-2005 hurricane seasons.",
    ),
    UtilityStandard(
        "Oncor Electric Delivery",
        ("oncor",),
        "Texas",
        (12_470, 25_000),
        (69_000, 138_000),
        (138_000, 345_000),
    ),
    UtilityStandard(
        "Xcel Energy",
        ("xcel", "public service company of colorado", "northern states power"),
        "Colorado / Minnesota",
        (13_200, 13_800),
        (69_000, 115_000),
        (115_000, 230_000, 345_000),
    ),
    UtilityStandard(
        "Duke Energy",
        ("duke energy", "duke"),
        "Carolinas / Midwest / Florida",
        (12_470, 24_940),
        (44_000, 69_000, 100_000),
        (115_000, 230_000, 500_000),
        "Duke retains a legacy 44 kV and 100 kV subtransmission network in the "
        "Carolinas.",
    ),
    UtilityStandard(
        "National Grid",
        ("national grid",),
        "New York / New England",
        (4_160, 13_200, 34_500),
        (69_000, 115_000),
        (115_000, 230_000, 345_000),
    ),
    UtilityStandard(
        "Eversource Energy",
        ("eversource", "nstar"),
        "New England",
        (4_160, 13_800, 23_000),
        (69_000, 115_000),
        (115_000, 345_000),
        "Eversource has widely deployed spacer cable on 13.8 kV and 23 kV "
        "circuits in tree-dense corridors.",
    ),
    UtilityStandard(
        "Arizona Public Service",
        ("aps", "arizona public service"),
        "Arizona",
        (12_470, 21_000),
        (69_000,),
        (230_000, 500_000),
    ),
    UtilityStandard(
        "Portland General Electric",
        ("pge portland", "portland general"),
        "Oregon",
        (12_470, 19_900),
        (57_000, 115_000),
        (115_000, 230_000, 500_000),
    ),
    UtilityStandard(
        "Seattle City Light",
        ("seattle city light",),
        "Washington",
        (13_800, 26_400),
        (26_400, 34_500),
        (115_000, 230_000),
    ),
)


def find_utility_standard(name: str | None) -> UtilityStandard | None:
    """Resolve a free-text operator name to a known construction standard."""
    if not name:
        return None
    needle = name.strip().lower()
    if not needle:
        return None
    for std in UTILITY_STANDARDS:
        if needle == std.operator.lower():
            return std
        for alias in std.aliases:
            if alias in needle or needle in alias:
                return std
    return None


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------

#: OSHA 1910.269 Table R-6 minimum approach distance for qualified line workers
#: (phase to ground, altitude <= 900 m), in metres. Used only to generate
#: warnings; a drone operator's clearance requirement is set by their own
#: authorisation, not by this table.
MINIMUM_APPROACH_DISTANCE_M: tuple[tuple[int, float], ...] = (
    (750, 0.0),
    (15_000, 0.66),
    (36_000, 0.77),
    (46_000, 0.84),
    (72_500, 1.00),
    (121_000, 1.02),
    (145_000, 1.12),
    (169_000, 1.22),
    (242_000, 1.60),
    (362_000, 2.60),
    (550_000, 3.80),
    (800_000, 5.20),
)


def minimum_approach_distance_m(volts: float) -> float:
    for ceiling, distance in MINIMUM_APPROACH_DISTANCE_M:
        if volts <= ceiling:
            return distance
    return MINIMUM_APPROACH_DISTANCE_M[-1][1]


@dataclass
class ClassScore:
    """Accumulated evidence for one voltage class."""

    voltage_class: VoltageClass
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)

    def add(self, weight: float, reason: str) -> None:
        self.score += weight
        self.reasons.append(reason)
