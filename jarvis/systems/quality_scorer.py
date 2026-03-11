# =============================================================================
# jarvis/systems/quality_scorer.py — S11 Quality Scorer
#
# Authority: FAS v6.0.1, S11 (Lines 4224-4386)
#
# Computes mu (information quality) from system contract D(t).
# mu is the formal quality metric of the system contract.
#
# Formula (System Contract, Whitepaper 2.2):
#   mu = w_cal * (1 - ECE) +
#        w_conf * confidence +
#        w_stab * stability +
#        w_data * data_quality +
#        w_regime * regime_confidence
#
#   where: sum(w_i) = 1.0 (enforced)
#          mu in [0, 1]
#
# Entry points:
#   QualityScorer.compute_quality() -> QualityScore
#   QualityScorer.get_weights()     -> dict
#   calibration_score()             -> float
#   confidence_score()              -> float
#   stability_score()               -> float
#   data_quality_score()            -> float
#   regime_score()                  -> float
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
#   stdlib:   dataclasses, math
#   internal: NONE
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    # Constants
    "QUALITY_WEIGHTS",
    "STABILITY_WINDOW",
    "QUALITY_FLOOR",
    "QUALITY_CEILING",
    # Dataclasses
    "QualityScore",
    # Component functions
    "calibration_score",
    "confidence_score",
    "stability_score",
    "data_quality_score",
    "regime_score",
    # Class
    "QualityScorer",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals, not parametrisable)
# =============================================================================

QUALITY_WEIGHTS: dict = {
    "calibration": 0.35,
    "confidence": 0.25,
    "stability": 0.20,
    "data_quality": 0.10,
    "regime": 0.10,
}
"""Component weights for quality score. Must sum to 1.0."""

STABILITY_WINDOW: int = 20
"""Number of recent predictions for stability computation."""

QUALITY_FLOOR: float = 0.0
"""Minimum quality score."""

QUALITY_CEILING: float = 1.0
"""Maximum quality score."""


# =============================================================================
# SECTION 2 -- DATACLASS
# =============================================================================

@dataclass(frozen=True)
class QualityScore:
    """
    Multi-component quality assessment.
    All fields in [0, 1], NaN/Inf guarded.

    Fields:
        total:                  Weighted sum of components, in [0, 1].
        calibration_component:  1 - ECE.
        confidence_component:   1 / (1 + sigma).
        stability_component:    1 / (1 + variance_of_recent_mus).
        data_quality_component: (completeness + freshness + reliability) / 3.
        regime_component:       Regime confidence score.
    """
    total: float
    calibration_component: float
    confidence_component: float
    stability_component: float
    data_quality_component: float
    regime_component: float

    def __post_init__(self) -> None:
        for name, val in [
            ("total", self.total),
            ("calibration_component", self.calibration_component),
            ("confidence_component", self.confidence_component),
            ("stability_component", self.stability_component),
            ("data_quality_component", self.data_quality_component),
            ("regime_component", self.regime_component),
        ]:
            if not isinstance(val, (int, float)):
                raise TypeError(
                    f"QualityScore.{name} must be numeric, "
                    f"got {type(val).__name__}"
                )
            if not math.isfinite(val):
                raise ValueError(
                    f"QualityScore.{name} must be finite, got {val!r}"
                )
            if val < 0.0 or val > 1.0:
                raise ValueError(
                    f"QualityScore.{name} must be in [0, 1], got {val!r}"
                )


# =============================================================================
# SECTION 3 -- HELPER
# =============================================================================

def _clamp_01(value: float) -> float:
    """Clamp a value to [0.0, 1.0]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


# =============================================================================
# SECTION 4 -- COMPONENT FUNCTIONS (pure, stateless, deterministic)
# =============================================================================

def calibration_score(ece: float) -> float:
    """
    Score from Expected Calibration Error. Higher is better.

    Returns max(1 - ece, 0). Clips result to [0, 1].
    Non-finite input returns 0.0.

    Args:
        ece: Expected Calibration Error value.

    Returns:
        Calibration score in [0, 1].
    """
    if not isinstance(ece, (int, float)) or not math.isfinite(ece):
        return 0.0
    result = 1.0 - ece
    return _clamp_01(result)


def confidence_score(sigma: float) -> float:
    """
    Score from uncertainty sigma. Lower sigma = higher score.

    Returns 1 / (1 + max(sigma, 0)).
    Non-finite input returns 0.0.

    Args:
        sigma: Prediction uncertainty.

    Returns:
        Confidence score in [0, 1].
    """
    if not isinstance(sigma, (int, float)) or not math.isfinite(sigma):
        return 0.0
    safe_sigma = max(sigma, 0.0)
    result = 1.0 / (1.0 + safe_sigma)
    if not math.isfinite(result):
        return 0.0
    return _clamp_01(result)


def stability_score(recent_mus: tuple) -> float:
    """
    Score from prediction stability.

    Computes variance of the last STABILITY_WINDOW predictions.
    Returns 1 / (1 + variance). Lower variance = higher score.
    Returns 1.0 for empty or single-element input.

    Non-finite values in recent_mus are skipped.

    Args:
        recent_mus: Tuple of recent prediction mu values.

    Returns:
        Stability score in [0, 1].
    """
    if not isinstance(recent_mus, tuple):
        return 1.0

    # Filter to last STABILITY_WINDOW and only finite values
    window = recent_mus[-STABILITY_WINDOW:]
    finite_vals = tuple(v for v in window if isinstance(v, (int, float)) and math.isfinite(v))

    if len(finite_vals) < 2:
        return 1.0

    n = len(finite_vals)
    mean = sum(finite_vals) / n
    variance = sum((v - mean) ** 2 for v in finite_vals) / n

    if not math.isfinite(variance):
        return 0.0

    variance = max(variance, 0.0)
    result = 1.0 / (1.0 + variance)

    if not math.isfinite(result):
        return 0.0
    return _clamp_01(result)


def data_quality_score(
    feature_completeness: float,
    data_freshness: float,
    source_reliability: float,
) -> float:
    """
    Score from data quality metrics.

    All inputs clipped to [0, 1].
    Returns (completeness + freshness + reliability) / 3.
    Non-finite inputs treated as 0.0.

    Args:
        feature_completeness: Fraction of features available.
        data_freshness:       Data freshness score.
        source_reliability:   Source reliability score.

    Returns:
        Data quality score in [0, 1].
    """
    vals = []
    for val in (feature_completeness, data_freshness, source_reliability):
        if not isinstance(val, (int, float)) or not math.isfinite(val):
            vals.append(0.0)
        else:
            vals.append(_clamp_01(val))

    result = sum(vals) / 3.0

    if not math.isfinite(result):
        return 0.0
    return _clamp_01(result)


def regime_score(regime_confidence: float) -> float:
    """
    Score from regime detection confidence.

    Clips input to [0, 1].
    Non-finite input returns 0.0.

    Args:
        regime_confidence: Regime confidence value.

    Returns:
        Regime score in [0, 1].
    """
    if not isinstance(regime_confidence, (int, float)) or not math.isfinite(regime_confidence):
        return 0.0
    return _clamp_01(regime_confidence)


# =============================================================================
# SECTION 5 -- QUALITY SCORER CLASS
# =============================================================================

class QualityScorer:
    """
    Computes weighted quality scores. < 5ms per call.
    Stateless -- all inputs passed explicitly (DET-02).

    Usage:
        scorer = QualityScorer()
        score = scorer.compute_quality(ece=0.02, sigma=0.1)
        weights = scorer.get_weights()
    """

    def __init__(self) -> None:
        # Weight consistency check (DET-06: fixed literals)
        total_w = sum(QUALITY_WEIGHTS.values())
        if abs(total_w - 1.0) > 1e-9:
            raise ValueError(
                f"QUALITY_WEIGHTS must sum to 1.0, got {total_w}"
            )

    def compute_quality(
        self,
        ece: float = 0.0,
        sigma: float = 0.0,
        recent_mus: tuple = (),
        feature_completeness: float = 1.0,
        data_freshness: float = 1.0,
        source_reliability: float = 1.0,
        regime_confidence: float = 1.0,
    ) -> QualityScore:
        """
        Compute quality score from all components.

        1. Compute each component score.
        2. Weighted sum: total = sum(weight * component for each).
        3. Clip total to [QUALITY_FLOOR, QUALITY_CEILING].
        4. Return QualityScore with all components.

        Args:
            ece:                  Expected Calibration Error (default 0.0).
            sigma:                Prediction uncertainty (default 0.0).
            recent_mus:           Tuple of recent prediction values.
            feature_completeness: Feature completeness in [0, 1].
            data_freshness:       Data freshness in [0, 1].
            source_reliability:   Source reliability in [0, 1].
            regime_confidence:    Regime confidence in [0, 1].

        Returns:
            QualityScore with all components and weighted total.
        """
        cal = calibration_score(ece)
        conf = confidence_score(sigma)
        stab = stability_score(recent_mus)
        dq = data_quality_score(feature_completeness, data_freshness, source_reliability)
        reg = regime_score(regime_confidence)

        # Weighted sum
        total = (
            QUALITY_WEIGHTS["calibration"] * cal
            + QUALITY_WEIGHTS["confidence"] * conf
            + QUALITY_WEIGHTS["stability"] * stab
            + QUALITY_WEIGHTS["data_quality"] * dq
            + QUALITY_WEIGHTS["regime"] * reg
        )

        # NaN/Inf guard
        if not math.isfinite(total):
            total = QUALITY_FLOOR

        # Clip to [QUALITY_FLOOR, QUALITY_CEILING]
        total = max(QUALITY_FLOOR, min(QUALITY_CEILING, total))

        return QualityScore(
            total=total,
            calibration_component=cal,
            confidence_component=conf,
            stability_component=stab,
            data_quality_component=dq,
            regime_component=reg,
        )

    def get_weights(self) -> dict:
        """Return a copy of QUALITY_WEIGHTS."""
        return dict(QUALITY_WEIGHTS)
