# =============================================================================
# jarvis/systems/degradation_ctrl.py — S13 Degradation Controller
#
# Authority: FAS v6.0.1, S13 (Lines ~4100-4400)
#
# Evaluates system health and determines operating mode (SystemModus).
# Maps SystemZustand inputs to a DegradationResult with mode, configuration,
# the input state (audit trail), and a human-readable reason string.
#
# Entry points:
#   DegradationsController.evaluate()         -> DegradationResult
#   DegradationsController.get_configuration() -> ModusKonfiguration
#   DegradationsController.is_predictions_safe() -> bool
#
# CLASSIFICATION: Tier 6 — ANALYSIS AND STRATEGY RESEARCH TOOL.
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  Deterministic arithmetic only.
# DET-05  All branching is deterministic.
# DET-06  Fixed literals are not parametrised.
# DET-07  Same inputs = bit-identical outputs.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No numpy / scipy / sklearn / torch
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
#
# DEPENDENCIES
# ------------
#   stdlib:   dataclasses, enum, math
#   internal: NONE
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum, unique

__all__ = [
    # Enums
    "SystemModus",
    # Dataclasses
    "SystemZustand",
    "ModusKonfiguration",
    "DegradationResult",
    # Constants
    "MODUS_KONFIGURATIONEN",
    "ECE_KONSERVATIV_THRESHOLD",
    "ECE_KRISE_THRESHOLD",
    "OOD_ERHOEHTE_THRESHOLD",
    "OOD_KRISE_THRESHOLD",
    "OOD_NOTFALL_THRESHOLD",
    "META_U_KONSERVATIV",
    "META_U_KRISE",
    "META_U_KOLLAPS",
    "DATENVERLUST_MINIMAL_THRESHOLD",
    "DATENVERLUST_NOTFALL_THRESHOLD",
    "KALTSTART_ENTSCHEIDUNGS_MINIMUM",
    # Class
    "DegradationsController",
]


# =============================================================================
# SECTION 1 -- ENUMS
# =============================================================================

@unique
class SystemModus(Enum):
    """9 system operating modes, ordered by severity."""
    NORMAL = "NORMAL"
    KONSERVATIV = "KONSERVATIV"
    ERHOEHTE_WACHSAMKEIT = "ERHOEHTE_WACHSAMKEIT"
    KRISE = "KRISE"
    MINIMAL = "MINIMAL"
    NOTFALL = "NOTFALL"
    REKALIBRIERUNG = "REKALIBRIERUNG"
    KALTSTART = "KALTSTART"
    KONFIDENZ_KOLLAPS = "KONFIDENZ_KOLLAPS"


# =============================================================================
# SECTION 2 -- DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class SystemZustand:
    """Current system health state -- all inputs for mode determination."""
    ece: float                      # Current ECE [0, 1]
    ood_score: float                # Current OOD score [0, 1]
    datenverlust_ratio: float       # Data loss ratio [0, 1]
    entscheidungs_count: int        # Total decisions made
    aktive_rekalibrierung: bool     # Is recalibration in progress?
    meta_unsicherheit_u: float      # Meta-uncertainty U [0, 1]

    def __post_init__(self) -> None:
        for name, val in [
            ("ece", self.ece),
            ("ood_score", self.ood_score),
            ("datenverlust_ratio", self.datenverlust_ratio),
            ("meta_unsicherheit_u", self.meta_unsicherheit_u),
        ]:
            if not isinstance(val, (int, float)):
                raise TypeError(
                    f"SystemZustand.{name} must be numeric, "
                    f"got {type(val).__name__}"
                )
            if not math.isfinite(val):
                raise ValueError(
                    f"SystemZustand.{name} must be finite, got {val!r}"
                )
        if not isinstance(self.entscheidungs_count, int):
            raise TypeError(
                f"SystemZustand.entscheidungs_count must be int, "
                f"got {type(self.entscheidungs_count).__name__}"
            )
        if not isinstance(self.aktive_rekalibrierung, bool):
            raise TypeError(
                f"SystemZustand.aktive_rekalibrierung must be bool, "
                f"got {type(self.aktive_rekalibrierung).__name__}"
            )


@dataclass(frozen=True)
class ModusKonfiguration:
    """Configuration for a specific system mode."""
    vorhersagen_aktiv: bool         # Are predictions enabled?
    konfidenz_multiplikator: float  # Confidence multiplier [0, 1]
    deep_path_erzwungen: bool       # Force deep path?
    warnungen_prominent: bool       # Show prominent warnings?
    rekalibrierung_ausloesen: bool  # Trigger recalibration?


@dataclass(frozen=True)
class DegradationResult:
    """Result of system health evaluation."""
    modus: SystemModus              # Determined mode
    konfiguration: ModusKonfiguration  # Mode configuration
    zustand: SystemZustand          # Input state (for audit)
    grund: str                      # Reason for mode selection


# =============================================================================
# SECTION 3 -- CONSTANTS (DET-06: fixed literals, not parametrisable)
# =============================================================================

MODUS_KONFIGURATIONEN: dict = {
    SystemModus.NORMAL: ModusKonfiguration(
        vorhersagen_aktiv=True, konfidenz_multiplikator=1.0,
        deep_path_erzwungen=False, warnungen_prominent=False,
        rekalibrierung_ausloesen=False),
    SystemModus.KONSERVATIV: ModusKonfiguration(
        vorhersagen_aktiv=True, konfidenz_multiplikator=0.8,
        deep_path_erzwungen=False, warnungen_prominent=False,
        rekalibrierung_ausloesen=False),
    SystemModus.ERHOEHTE_WACHSAMKEIT: ModusKonfiguration(
        vorhersagen_aktiv=True, konfidenz_multiplikator=0.6,
        deep_path_erzwungen=True, warnungen_prominent=True,
        rekalibrierung_ausloesen=False),
    SystemModus.KRISE: ModusKonfiguration(
        vorhersagen_aktiv=True, konfidenz_multiplikator=0.4,
        deep_path_erzwungen=True, warnungen_prominent=True,
        rekalibrierung_ausloesen=True),
    SystemModus.MINIMAL: ModusKonfiguration(
        vorhersagen_aktiv=True, konfidenz_multiplikator=0.2,
        deep_path_erzwungen=True, warnungen_prominent=True,
        rekalibrierung_ausloesen=True),
    SystemModus.NOTFALL: ModusKonfiguration(
        vorhersagen_aktiv=False, konfidenz_multiplikator=0.0,
        deep_path_erzwungen=True, warnungen_prominent=True,
        rekalibrierung_ausloesen=True),
    SystemModus.REKALIBRIERUNG: ModusKonfiguration(
        vorhersagen_aktiv=True, konfidenz_multiplikator=0.5,
        deep_path_erzwungen=False, warnungen_prominent=True,
        rekalibrierung_ausloesen=True),
    SystemModus.KALTSTART: ModusKonfiguration(
        vorhersagen_aktiv=False, konfidenz_multiplikator=0.0,
        deep_path_erzwungen=False, warnungen_prominent=True,
        rekalibrierung_ausloesen=False),
    SystemModus.KONFIDENZ_KOLLAPS: ModusKonfiguration(
        vorhersagen_aktiv=False, konfidenz_multiplikator=0.0,
        deep_path_erzwungen=True, warnungen_prominent=True,
        rekalibrierung_ausloesen=True),
}

# Thresholds for mode transitions
ECE_KONSERVATIV_THRESHOLD: float = 0.03
ECE_KRISE_THRESHOLD: float = 0.05
OOD_ERHOEHTE_THRESHOLD: float = 0.4
OOD_KRISE_THRESHOLD: float = 0.6
OOD_NOTFALL_THRESHOLD: float = 0.8
META_U_KONSERVATIV: float = 0.3
META_U_KRISE: float = 0.5
META_U_KOLLAPS: float = 0.7
DATENVERLUST_MINIMAL_THRESHOLD: float = 0.3
DATENVERLUST_NOTFALL_THRESHOLD: float = 0.5
KALTSTART_ENTSCHEIDUNGS_MINIMUM: int = 50


# =============================================================================
# SECTION 4 -- DEGRADATION CONTROLLER
# =============================================================================

class DegradationsController:
    """
    Evaluates system health and determines operating mode.

    Stateless -- all inputs passed explicitly (DET-02).
    No side effects (DET-03).
    Same inputs = same outputs (DET-07).

    Usage:
        ctrl = DegradationsController()
        result = ctrl.evaluate(zustand)
        config = ctrl.get_configuration(SystemModus.NORMAL)
        safe = ctrl.is_predictions_safe(zustand)
    """

    def evaluate(self, zustand: SystemZustand) -> DegradationResult:
        """
        Determine system mode from current state.

        Priority order (highest severity wins):
        1. KONFIDENZ_KOLLAPS: meta_unsicherheit_u > META_U_KOLLAPS (0.7)
        2. NOTFALL: ood_score > OOD_NOTFALL_THRESHOLD (0.8) OR
                    datenverlust_ratio > DATENVERLUST_NOTFALL_THRESHOLD (0.5)
        3. KALTSTART: entscheidungs_count < KALTSTART_ENTSCHEIDUNGS_MINIMUM (50)
        4. REKALIBRIERUNG: aktive_rekalibrierung == True
        5. KRISE: ece > ECE_KRISE_THRESHOLD (0.05) OR
                  ood_score > OOD_KRISE_THRESHOLD (0.6) OR
                  meta_unsicherheit_u > META_U_KRISE (0.5)
        6. MINIMAL: datenverlust_ratio > DATENVERLUST_MINIMAL_THRESHOLD (0.3)
        7. ERHOEHTE_WACHSAMKEIT: ood_score > OOD_ERHOEHTE_THRESHOLD (0.4)
        8. KONSERVATIV: ece > ECE_KONSERVATIV_THRESHOLD (0.03) OR
                        meta_unsicherheit_u > META_U_KONSERVATIV (0.3)
        9. NORMAL: default

        Args:
            zustand: Current system health state.

        Returns:
            DegradationResult with mode, config, state, and reason string.
        """
        if not isinstance(zustand, SystemZustand):
            raise TypeError(
                f"zustand must be SystemZustand, got {type(zustand).__name__}"
            )

        modus, grund = self._determine_mode(zustand)
        konfiguration = MODUS_KONFIGURATIONEN[modus]

        return DegradationResult(
            modus=modus,
            konfiguration=konfiguration,
            zustand=zustand,
            grund=grund,
        )

    def get_configuration(self, modus: SystemModus) -> ModusKonfiguration:
        """Return ModusKonfiguration for a given mode."""
        if not isinstance(modus, SystemModus):
            raise TypeError(
                f"modus must be SystemModus, got {type(modus).__name__}"
            )
        return MODUS_KONFIGURATIONEN[modus]

    def is_predictions_safe(self, zustand: SystemZustand) -> bool:
        """Quick check: are predictions allowed in current state?"""
        result = self.evaluate(zustand)
        return result.konfiguration.vorhersagen_aktiv

    @staticmethod
    def _determine_mode(
        zustand: SystemZustand,
    ) -> tuple:
        """
        Apply priority cascade to determine mode and reason.

        Returns:
            Tuple of (SystemModus, reason_string).
        """
        # Priority 1: KONFIDENZ_KOLLAPS
        if zustand.meta_unsicherheit_u > META_U_KOLLAPS:
            return (
                SystemModus.KONFIDENZ_KOLLAPS,
                f"meta_unsicherheit_u ({zustand.meta_unsicherheit_u}) "
                f"> META_U_KOLLAPS ({META_U_KOLLAPS})",
            )

        # Priority 2: NOTFALL
        if zustand.ood_score > OOD_NOTFALL_THRESHOLD:
            return (
                SystemModus.NOTFALL,
                f"ood_score ({zustand.ood_score}) "
                f"> OOD_NOTFALL_THRESHOLD ({OOD_NOTFALL_THRESHOLD})",
            )
        if zustand.datenverlust_ratio > DATENVERLUST_NOTFALL_THRESHOLD:
            return (
                SystemModus.NOTFALL,
                f"datenverlust_ratio ({zustand.datenverlust_ratio}) "
                f"> DATENVERLUST_NOTFALL_THRESHOLD ({DATENVERLUST_NOTFALL_THRESHOLD})",
            )

        # Priority 3: KALTSTART
        if zustand.entscheidungs_count < KALTSTART_ENTSCHEIDUNGS_MINIMUM:
            return (
                SystemModus.KALTSTART,
                f"entscheidungs_count ({zustand.entscheidungs_count}) "
                f"< KALTSTART_ENTSCHEIDUNGS_MINIMUM ({KALTSTART_ENTSCHEIDUNGS_MINIMUM})",
            )

        # Priority 4: REKALIBRIERUNG
        if zustand.aktive_rekalibrierung:
            return (
                SystemModus.REKALIBRIERUNG,
                "aktive_rekalibrierung is True",
            )

        # Priority 5: KRISE
        if zustand.ece > ECE_KRISE_THRESHOLD:
            return (
                SystemModus.KRISE,
                f"ece ({zustand.ece}) "
                f"> ECE_KRISE_THRESHOLD ({ECE_KRISE_THRESHOLD})",
            )
        if zustand.ood_score > OOD_KRISE_THRESHOLD:
            return (
                SystemModus.KRISE,
                f"ood_score ({zustand.ood_score}) "
                f"> OOD_KRISE_THRESHOLD ({OOD_KRISE_THRESHOLD})",
            )
        if zustand.meta_unsicherheit_u > META_U_KRISE:
            return (
                SystemModus.KRISE,
                f"meta_unsicherheit_u ({zustand.meta_unsicherheit_u}) "
                f"> META_U_KRISE ({META_U_KRISE})",
            )

        # Priority 6: MINIMAL
        if zustand.datenverlust_ratio > DATENVERLUST_MINIMAL_THRESHOLD:
            return (
                SystemModus.MINIMAL,
                f"datenverlust_ratio ({zustand.datenverlust_ratio}) "
                f"> DATENVERLUST_MINIMAL_THRESHOLD ({DATENVERLUST_MINIMAL_THRESHOLD})",
            )

        # Priority 7: ERHOEHTE_WACHSAMKEIT
        if zustand.ood_score > OOD_ERHOEHTE_THRESHOLD:
            return (
                SystemModus.ERHOEHTE_WACHSAMKEIT,
                f"ood_score ({zustand.ood_score}) "
                f"> OOD_ERHOEHTE_THRESHOLD ({OOD_ERHOEHTE_THRESHOLD})",
            )

        # Priority 8: KONSERVATIV
        if zustand.ece > ECE_KONSERVATIV_THRESHOLD:
            return (
                SystemModus.KONSERVATIV,
                f"ece ({zustand.ece}) "
                f"> ECE_KONSERVATIV_THRESHOLD ({ECE_KONSERVATIV_THRESHOLD})",
            )
        if zustand.meta_unsicherheit_u > META_U_KONSERVATIV:
            return (
                SystemModus.KONSERVATIV,
                f"meta_unsicherheit_u ({zustand.meta_unsicherheit_u}) "
                f"> META_U_KONSERVATIV ({META_U_KONSERVATIV})",
            )

        # Priority 9: NORMAL (default)
        return (
            SystemModus.NORMAL,
            "All inputs within normal thresholds",
        )
