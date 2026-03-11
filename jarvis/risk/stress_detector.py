# =============================================================================
# jarvis/risk/stress_detector.py
# Authority: FAS v6.0.1 -- S17.5, lines 6326-6430
# =============================================================================
#
# SCOPE
# -----
# 4-dimension explicit stress detection.  Operates on raw numeric inputs
# (volatility ratio, volume ratio, correlation score, liquidity score).
# Independent of OOD detector — both run in parallel.
#
# Public symbols:
#   STRESS_THRESHOLD           Aggregate threshold for is_stressed (0.70)
#   VOL_SPIKE_FACTOR           Volatility spike multiplier (3.0)
#   VOLUME_SPIKE_FACTOR        Volume spike multiplier (5.0)
#   CORRELATION_FLOOR          Correlation stress threshold (0.20)
#   LIQUIDITY_FLOOR            Liquidity stress threshold (0.20)
#   StressIndicators           Frozen dataclass — stress detection output
#   ExplicitStressDetector     Detector class
#
# GOVERNANCE
# ----------
# Output is advisory.  is_stressed feeds RiskEngine for risk-level
# escalation (NORMAL → HIGH) but does NOT directly alter positions.
# Separate from OOD detector — not a replacement.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses
#   external:  numpy
#   internal:  NONE
#   PROHIBITED: logging, random, file IO, network IO, datetime.now()
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-06  Fixed literals (thresholds) not parametrisable.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "STRESS_THRESHOLD",
    "VOL_SPIKE_FACTOR",
    "VOLUME_SPIKE_FACTOR",
    "CORRELATION_FLOOR",
    "LIQUIDITY_FLOOR",
    "StressIndicators",
    "ExplicitStressDetector",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

STRESS_THRESHOLD: float = 0.70
"""Aggregate stress >= this value triggers is_stressed = True."""

VOL_SPIKE_FACTOR: float = 3.0
"""Volatility ratio above this produces maximum stress score."""

VOLUME_SPIKE_FACTOR: float = 5.0
"""Volume ratio above this produces maximum stress score."""

CORRELATION_FLOOR: float = 0.20
"""Correlation below this produces maximum stress score."""

LIQUIDITY_FLOOR: float = 0.20
"""Liquidity score below this produces maximum stress score."""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class StressIndicators:
    """
    4-dimension stress detection output.

    Fields:
        volatility_stress:   Volatility spike stress [0, 1].
        volume_stress:       Volume anomaly stress [0, 1].
        correlation_stress:  Correlation breakdown stress [0, 1].
        liquidity_stress:    Liquidity crunch stress [0, 1].
        aggregate_stress:    max(all 4 dimensions) [0, 1].
        is_stressed:         True if aggregate_stress >= STRESS_THRESHOLD.
    """
    volatility_stress: float
    volume_stress: float
    correlation_stress: float
    liquidity_stress: float
    aggregate_stress: float
    is_stressed: bool


# =============================================================================
# SECTION 3 -- DETECTOR
# =============================================================================

class ExplicitStressDetector:
    """
    4-dimension explicit stress detector.

    Evaluates volatility, volume, correlation, and liquidity dimensions
    independently.  Aggregate = max(all 4) — worst-case, not average.

    Stateless: all inputs passed explicitly to detect().
    """

    def detect(
        self,
        volatility_ratio: float,
        volume_ratio: float,
        correlation_score: float,
        liquidity_score: float,
    ) -> StressIndicators:
        """
        Detect stress across 4 dimensions.

        Each dimension produces a score in [0, 1].  The aggregate is the
        maximum of all 4 (worst-case principle).

        Args:
            volatility_ratio:  Current vol / normal vol.  1.0 = normal.
                               Higher = more volatile.  Must be >= 0.
            volume_ratio:      Current volume / normal volume.  1.0 = normal.
                               Higher = more volume.  Must be >= 0.
            correlation_score: Pairwise correlation score in [0, 1].
                               Lower = more stress (breakdown).
            liquidity_score:   Liquidity quality in [0, 1].
                               Lower = more stress (crunch).

        Returns:
            StressIndicators (frozen).

        Raises:
            TypeError:  If arguments are not numeric.
            ValueError: If arguments are out of valid range.
        """
        # -- Validation --
        if not isinstance(volatility_ratio, (int, float)):
            raise TypeError(
                f"volatility_ratio must be numeric, "
                f"got {type(volatility_ratio).__name__}"
            )
        if not isinstance(volume_ratio, (int, float)):
            raise TypeError(
                f"volume_ratio must be numeric, "
                f"got {type(volume_ratio).__name__}"
            )
        if not isinstance(correlation_score, (int, float)):
            raise TypeError(
                f"correlation_score must be numeric, "
                f"got {type(correlation_score).__name__}"
            )
        if not isinstance(liquidity_score, (int, float)):
            raise TypeError(
                f"liquidity_score must be numeric, "
                f"got {type(liquidity_score).__name__}"
            )

        if volatility_ratio < 0:
            raise ValueError(
                f"volatility_ratio must be >= 0, got {volatility_ratio}"
            )
        if volume_ratio < 0:
            raise ValueError(
                f"volume_ratio must be >= 0, got {volume_ratio}"
            )
        if not (0.0 <= correlation_score <= 1.0):
            raise ValueError(
                f"correlation_score must be in [0, 1], "
                f"got {correlation_score}"
            )
        if not (0.0 <= liquidity_score <= 1.0):
            raise ValueError(
                f"liquidity_score must be in [0, 1], "
                f"got {liquidity_score}"
            )

        # -- Dimension 1: Volatility spike --
        # Linear ramp from 0 at ratio=1.0 to 1.0 at ratio=VOL_SPIKE_FACTOR
        if volatility_ratio <= 1.0:
            vol_stress = 0.0
        else:
            vol_stress = float(np.clip(
                (volatility_ratio - 1.0) / (VOL_SPIKE_FACTOR - 1.0),
                0.0, 1.0,
            ))

        # -- Dimension 2: Volume anomaly --
        # Linear ramp from 0 at ratio=1.0 to 1.0 at ratio=VOLUME_SPIKE_FACTOR
        if volume_ratio <= 1.0:
            vol_a_stress = 0.0
        else:
            vol_a_stress = float(np.clip(
                (volume_ratio - 1.0) / (VOLUME_SPIKE_FACTOR - 1.0),
                0.0, 1.0,
            ))

        # -- Dimension 3: Correlation breakdown --
        # Stress increases as correlation drops below CORRELATION_FLOOR
        if correlation_score >= CORRELATION_FLOOR:
            corr_stress = 0.0
        else:
            corr_stress = float(np.clip(
                1.0 - (correlation_score / CORRELATION_FLOOR),
                0.0, 1.0,
            ))

        # -- Dimension 4: Liquidity crunch --
        # Stress increases as liquidity drops below LIQUIDITY_FLOOR
        if liquidity_score >= LIQUIDITY_FLOOR:
            liq_stress = 0.0
        else:
            liq_stress = float(np.clip(
                1.0 - (liquidity_score / LIQUIDITY_FLOOR),
                0.0, 1.0,
            ))

        # -- Aggregate: worst-case (max) --
        aggregate = max(vol_stress, vol_a_stress, corr_stress, liq_stress)

        return StressIndicators(
            volatility_stress=vol_stress,
            volume_stress=vol_a_stress,
            correlation_stress=corr_stress,
            liquidity_stress=liq_stress,
            aggregate_stress=aggregate,
            is_stressed=(aggregate >= STRESS_THRESHOLD),
        )
