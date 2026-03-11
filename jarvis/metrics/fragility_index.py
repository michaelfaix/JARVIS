# =============================================================================
# jarvis/metrics/fragility_index.py
# Authority: FAS v6.0.1 -- Structural Fragility Index
# =============================================================================
#
# SCOPE
# -----
# Structural fragility index for system-level health assessment.
# Measures systemic risk from four dimensions: component coupling,
# failure propagation, recovery capacity, and cascade potential.
# Produces FragilityAssessment objects — pure analytical data.
#
# DISTINCT FROM jarvis/strategy/signal_fragility_analyzer.py which
# measures signal-level perturbation sensitivity.  This module operates
# at the system/portfolio structural level.
#
# Public symbols:
#   FRAGILITY_LOW_THRESHOLD        Classification boundary (0.3)
#   FRAGILITY_MEDIUM_THRESHOLD     Classification boundary (0.6)
#   FRAGILITY_HIGH_THRESHOLD       Classification boundary (0.8)
#   FRAGILITY_WEIGHT_COUPLING      Component weight (0.3)
#   FRAGILITY_WEIGHT_PROPAGATION   Component weight (0.3)
#   FRAGILITY_WEIGHT_RECOVERY      Component weight (0.2)
#   FRAGILITY_WEIGHT_CASCADE       Component weight (0.2)
#   FragilityAssessment            Frozen dataclass for assessment output
#   StructuralFragilityIndex       Engine class
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, typing
#   external:  NONE
#   internal:  NONE
#   PROHIBITED: logging, random, file IO, network IO, datetime.now(), numpy
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-06  Fixed literals not parametrisable.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List

__all__ = [
    "FRAGILITY_LOW_THRESHOLD",
    "FRAGILITY_MEDIUM_THRESHOLD",
    "FRAGILITY_HIGH_THRESHOLD",
    "FRAGILITY_WEIGHT_COUPLING",
    "FRAGILITY_WEIGHT_PROPAGATION",
    "FRAGILITY_WEIGHT_RECOVERY",
    "FRAGILITY_WEIGHT_CASCADE",
    "FragilityAssessment",
    "StructuralFragilityIndex",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

FRAGILITY_LOW_THRESHOLD: float = 0.3
"""System robust: fragility below this."""

FRAGILITY_MEDIUM_THRESHOLD: float = 0.6
"""System stressed: fragility between LOW and this."""

FRAGILITY_HIGH_THRESHOLD: float = 0.8
"""System fragile: fragility above this."""

FRAGILITY_WEIGHT_COUPLING: float = 0.3
"""Weight for component coupling score."""

FRAGILITY_WEIGHT_PROPAGATION: float = 0.3
"""Weight for failure propagation score."""

FRAGILITY_WEIGHT_RECOVERY: float = 0.2
"""Weight for recovery capacity score."""

FRAGILITY_WEIGHT_CASCADE: float = 0.2
"""Weight for cascade potential score."""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class FragilityAssessment:
    """
    Structural fragility assessment result.

    Fields:
        coupling_score:       Component coupling [0, 1]. High = tightly coupled.
        propagation_score:    Failure propagation [0, 1]. High = failures spread.
        recovery_score:       Recovery difficulty [0, 1]. High = slow recovery.
        cascade_score:        Cascade potential [0, 1]. High = cascade likely.
        fragility_index:      Composite index [0, 1].
        classification:       "LOW", "MEDIUM", "HIGH", or "CRITICAL".
    """
    coupling_score: float
    propagation_score: float
    recovery_score: float
    cascade_score: float
    fragility_index: float
    classification: str


# =============================================================================
# SECTION 3 -- HELPERS
# =============================================================================

def _clip01(value: float) -> float:
    """Clip value to [0.0, 1.0]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _classify(index: float) -> str:
    """Classify fragility index into LOW/MEDIUM/HIGH/CRITICAL."""
    if index < FRAGILITY_LOW_THRESHOLD:
        return "LOW"
    if index < FRAGILITY_MEDIUM_THRESHOLD:
        return "MEDIUM"
    if index < FRAGILITY_HIGH_THRESHOLD:
        return "HIGH"
    return "CRITICAL"


# =============================================================================
# SECTION 4 -- ENGINE
# =============================================================================

class StructuralFragilityIndex:
    """
    Structural fragility index engine.

    Computes system-level fragility from four dimensions:
    coupling, propagation, recovery, and cascade.

    Stateless: all inputs passed explicitly.
    """

    def compute(
        self,
        coupling_score: float,
        propagation_score: float,
        recovery_score: float,
        cascade_score: float,
    ) -> FragilityAssessment:
        """
        Compute structural fragility index from four dimension scores.

        Args:
            coupling_score:     Component coupling intensity [0, 1].
            propagation_score:  Failure propagation reach [0, 1].
            recovery_score:     Recovery difficulty [0, 1].
            cascade_score:      Cascade potential [0, 1].

        Returns:
            FragilityAssessment.

        Raises:
            TypeError: If any score is not numeric.
        """
        for name, val in [
            ("coupling_score", coupling_score),
            ("propagation_score", propagation_score),
            ("recovery_score", recovery_score),
            ("cascade_score", cascade_score),
        ]:
            if not isinstance(val, (int, float)):
                raise TypeError(
                    f"{name} must be numeric, "
                    f"got {type(val).__name__}"
                )

        c = _clip01(coupling_score)
        p = _clip01(propagation_score)
        r = _clip01(recovery_score)
        k = _clip01(cascade_score)

        index = _clip01(
            FRAGILITY_WEIGHT_COUPLING * c
            + FRAGILITY_WEIGHT_PROPAGATION * p
            + FRAGILITY_WEIGHT_RECOVERY * r
            + FRAGILITY_WEIGHT_CASCADE * k
        )

        return FragilityAssessment(
            coupling_score=c,
            propagation_score=p,
            recovery_score=r,
            cascade_score=k,
            fragility_index=index,
            classification=_classify(index),
        )

    def compute_from_correlations(
        self,
        pairwise_correlations: List[float],
        failure_count: int,
        total_components: int,
        recovery_time_bars: int,
        max_recovery_bars: int,
    ) -> FragilityAssessment:
        """
        Compute fragility from raw system observables.

        Derives the four dimension scores from concrete measurements:
        - coupling:     mean of absolute pairwise correlations
        - propagation:  failure_count / total_components
        - recovery:     recovery_time_bars / max_recovery_bars
        - cascade:      coupling * propagation (interaction term)

        Args:
            pairwise_correlations: List of pairwise correlation values.
            failure_count:         Number of components in failure state.
            total_components:      Total number of components (>= 1).
            recovery_time_bars:    Observed recovery time in bars.
            max_recovery_bars:     Maximum expected recovery time (>= 1).

        Returns:
            FragilityAssessment.

        Raises:
            TypeError:  If arguments have wrong types.
            ValueError: If total_components < 1 or max_recovery_bars < 1.
        """
        if not isinstance(pairwise_correlations, list):
            raise TypeError(
                f"pairwise_correlations must be a list, "
                f"got {type(pairwise_correlations).__name__}"
            )
        if not isinstance(failure_count, int):
            raise TypeError(
                f"failure_count must be int, "
                f"got {type(failure_count).__name__}"
            )
        if not isinstance(total_components, int):
            raise TypeError(
                f"total_components must be int, "
                f"got {type(total_components).__name__}"
            )
        if not isinstance(recovery_time_bars, int):
            raise TypeError(
                f"recovery_time_bars must be int, "
                f"got {type(recovery_time_bars).__name__}"
            )
        if not isinstance(max_recovery_bars, int):
            raise TypeError(
                f"max_recovery_bars must be int, "
                f"got {type(max_recovery_bars).__name__}"
            )
        if total_components < 1:
            raise ValueError(
                f"total_components must be >= 1, got {total_components}"
            )
        if max_recovery_bars < 1:
            raise ValueError(
                f"max_recovery_bars must be >= 1, got {max_recovery_bars}"
            )

        # Coupling: mean of absolute correlations
        if len(pairwise_correlations) == 0:
            coupling = 0.0
        else:
            coupling = sum(
                abs(c) for c in pairwise_correlations
            ) / len(pairwise_correlations)

        # Propagation: fraction of failed components
        propagation = failure_count / total_components

        # Recovery: normalized recovery time
        recovery = recovery_time_bars / max_recovery_bars

        # Cascade: interaction of coupling and propagation
        cascade = coupling * propagation

        return self.compute(coupling, propagation, recovery, cascade)
