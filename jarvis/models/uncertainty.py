# =============================================================================
# jarvis/models/uncertainty.py — S08 Uncertainty Layer
#
# Authority: FAS v6.0.1, S08 (Lines 3067-3250, 20340-20408)
#
# Uncertainty decomposition and interval computation:
#   1. UncertaintyBreakdown:          Full uncertainty decomposition
#   2. Intervals:                     Confidence intervals (50%, 90%, 95%)
#   3. MetaUncertaintyState:          Meta-uncertainty state tracking
#   4. UncertaintyLayer:              Main orchestrator
#   5. MetaUncertaintyEstimator:      Meta-U computation
#   6. InformationQualityEstimator:   Feature quality scoring
#
# Entry points:
#   UncertaintyLayer.decompose()      → UncertaintyBreakdown
#   UncertaintyLayer.compute_intervals() → Intervals
#   MetaUncertaintyEstimator.estimate() → MetaUncertaintyState
#   InformationQualityEstimator.compute_quality() → float
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
#   internal: jarvis.models.fast_path (Prediction)
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Tuple

from jarvis.models.fast_path import Prediction

__all__ = [
    # Constants
    "META_U_RECALIBRATION",
    "META_U_CONSERVATIVE",
    "META_U_COLLAPSE",
    "CI_Z_50",
    "CI_Z_90",
    "CI_Z_95",
    "UNCERTAINTY_MAX",
    # Dataclasses
    "UncertaintyBreakdown",
    "Intervals",
    "MetaUncertaintyState",
    # Classes
    "UncertaintyLayer",
    "MetaUncertaintyEstimator",
    "InformationQualityEstimator",
    # Helper functions
    "compute_aleatoric",
    "compute_epistemic",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals, not parametrisable)
# =============================================================================

META_U_RECALIBRATION: float = 0.3
"""U > this triggers recalibration."""

META_U_CONSERVATIVE: float = 0.5
"""U > this triggers conservative mode."""

META_U_COLLAPSE: float = 0.7
"""U > this triggers confidence collapse."""

CI_Z_50: float = 0.6745
"""z-score for 50% confidence interval."""

CI_Z_90: float = 1.6449
"""z-score for 90% confidence interval."""

CI_Z_95: float = 1.9600
"""z-score for 95% confidence interval."""

UNCERTAINTY_MAX: float = 0.95
"""Hard cap on total uncertainty."""

#: Epsilon floor for safe operations.
_EPS: float = 1e-10


# =============================================================================
# SECTION 2 -- DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class UncertaintyBreakdown:
    """
    Full uncertainty decomposition.

    Fields:
        aleatoric:        Irreducible noise [0, 1].
        epistemic_model:  Model disagreement [0, 1].
        epistemic_data:   Data/feature drift [0, 1].
        distributional:   Distribution shift [0, 1].
        meta:             Meta-uncertainty U [0, 1].
        total:            Total uncertainty [0, UNCERTAINTY_MAX].
    """
    aleatoric: float
    epistemic_model: float
    epistemic_data: float
    distributional: float
    meta: float
    total: float

    def __post_init__(self) -> None:
        for name, val in [
            ("aleatoric", self.aleatoric),
            ("epistemic_model", self.epistemic_model),
            ("epistemic_data", self.epistemic_data),
            ("distributional", self.distributional),
            ("meta", self.meta),
            ("total", self.total),
        ]:
            if not isinstance(val, (int, float)):
                raise TypeError(
                    f"UncertaintyBreakdown.{name} must be numeric, "
                    f"got {type(val).__name__}"
                )
            if not math.isfinite(val):
                raise ValueError(
                    f"UncertaintyBreakdown.{name} must be finite, got {val!r}"
                )
            if val < 0.0:
                raise ValueError(
                    f"UncertaintyBreakdown.{name} must be non-negative, "
                    f"got {val!r}"
                )
        # total must be capped at UNCERTAINTY_MAX
        if self.total > UNCERTAINTY_MAX:
            raise ValueError(
                f"UncertaintyBreakdown.total must be <= {UNCERTAINTY_MAX}, "
                f"got {self.total!r}"
            )


@dataclass(frozen=True)
class Intervals:
    """
    Confidence intervals at 50%, 90%, 95%.

    Fields:
        ci_50: (lower, upper) for 50% confidence interval.
        ci_90: (lower, upper) for 90% confidence interval.
        ci_95: (lower, upper) for 95% confidence interval.
    """
    ci_50: Tuple[float, float]
    ci_90: Tuple[float, float]
    ci_95: Tuple[float, float]

    def __post_init__(self) -> None:
        for name, ci in [
            ("ci_50", self.ci_50),
            ("ci_90", self.ci_90),
            ("ci_95", self.ci_95),
        ]:
            if not isinstance(ci, tuple) or len(ci) != 2:
                raise TypeError(
                    f"Intervals.{name} must be a 2-tuple, got {ci!r}"
                )
            for i, v in enumerate(ci):
                if not isinstance(v, (int, float)):
                    raise TypeError(
                        f"Intervals.{name}[{i}] must be numeric, "
                        f"got {type(v).__name__}"
                    )
                if not math.isfinite(v):
                    raise ValueError(
                        f"Intervals.{name}[{i}] must be finite, got {v!r}"
                    )
            if ci[0] > ci[1]:
                raise ValueError(
                    f"Intervals.{name} lower must be <= upper, "
                    f"got ({ci[0]}, {ci[1]})"
                )


@dataclass(frozen=True)
class MetaUncertaintyState:
    """
    Meta-uncertainty state with threshold tracking.

    Fields:
        U:                    Meta-uncertainty value [0, 1].
        state:                "NORMAL", "RECALIBRATION", "CONSERVATIVE", "COLLAPSE".
        triggered_threshold:  Which threshold was crossed (0.0 if NORMAL).
    """
    U: float
    state: str
    triggered_threshold: float

    def __post_init__(self) -> None:
        if not isinstance(self.U, (int, float)):
            raise TypeError(
                f"MetaUncertaintyState.U must be numeric, "
                f"got {type(self.U).__name__}"
            )
        if not math.isfinite(self.U):
            raise ValueError(
                f"MetaUncertaintyState.U must be finite, got {self.U!r}"
            )
        if self.U < 0.0 or self.U > 1.0:
            raise ValueError(
                f"MetaUncertaintyState.U must be in [0, 1], got {self.U!r}"
            )
        _VALID_STATES = ("NORMAL", "RECALIBRATION", "CONSERVATIVE", "COLLAPSE")
        if self.state not in _VALID_STATES:
            raise ValueError(
                f"MetaUncertaintyState.state must be one of {_VALID_STATES}, "
                f"got {self.state!r}"
            )
        if not isinstance(self.triggered_threshold, (int, float)):
            raise TypeError(
                f"MetaUncertaintyState.triggered_threshold must be numeric, "
                f"got {type(self.triggered_threshold).__name__}"
            )
        if not math.isfinite(self.triggered_threshold):
            raise ValueError(
                f"MetaUncertaintyState.triggered_threshold must be finite, "
                f"got {self.triggered_threshold!r}"
            )


# =============================================================================
# SECTION 3 -- HELPER FUNCTIONS (pure, stateless, deterministic)
# =============================================================================

def compute_aleatoric(predictions: tuple) -> float:
    """
    Mean of prediction sigmas. Returns 0.0 for empty input.

    Args:
        predictions: Tuple of Prediction objects.

    Returns:
        Mean sigma value, always >= 0.
    """
    if not predictions:
        return 0.0
    n = len(predictions)
    total = 0.0
    for p in predictions:
        total += p.sigma
    result = total / n
    if not math.isfinite(result):
        return 0.0
    return max(0.0, result)


def compute_epistemic(predictions: tuple) -> float:
    """
    Population standard deviation of prediction mus. Returns 0.0 for
    empty or single input.

    Args:
        predictions: Tuple of Prediction objects.

    Returns:
        Population std of mu values, always >= 0.
    """
    if not predictions or len(predictions) < 2:
        return 0.0
    n = len(predictions)
    mean_mu = sum(p.mu for p in predictions) / n
    variance = sum((p.mu - mean_mu) ** 2 for p in predictions) / n
    result = math.sqrt(max(0.0, variance))
    if not math.isfinite(result):
        return 0.0
    return result


def _clamp_01(value: float) -> float:
    """Clamp a value to [0.0, 1.0]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


# =============================================================================
# SECTION 4 -- UNCERTAINTY LAYER
# =============================================================================

class UncertaintyLayer:
    """
    Main orchestrator for uncertainty decomposition and interval computation.

    S08 entry point. Consumes Prediction objects from S06 (fast_path) and
    computes full uncertainty decomposition plus confidence intervals.

    Usage:
        layer = UncertaintyLayer()
        breakdown = layer.decompose(predictions, data_drift=0.1)
        intervals = layer.compute_intervals(mu=0.5, sigma=0.2)
    """

    def decompose(
        self,
        predictions: tuple,
        data_drift: float = 0.0,
        distributional_shift: float = 0.0,
    ) -> UncertaintyBreakdown:
        """
        Decompose uncertainty from ensemble predictions.

        aleatoric = mean(p.sigma for p in predictions)
        epistemic_model = population_std(p.mu for p in predictions)
        epistemic_data = data_drift
        distributional = distributional_shift
        meta = 0.0 (set externally by MetaUncertaintyEstimator)
        total = min(sqrt(sum of squares), UNCERTAINTY_MAX)

        Args:
            predictions:          Tuple of Prediction objects.
            data_drift:           Feature drift score [0, 1].
            distributional_shift: Distribution shift score [0, 1].

        Returns:
            UncertaintyBreakdown with all components.

        Raises:
            ValueError: If data_drift or distributional_shift are non-finite
                        or negative.
        """
        if not isinstance(predictions, tuple):
            raise TypeError(
                f"predictions must be a tuple, "
                f"got {type(predictions).__name__}"
            )
        if not math.isfinite(data_drift):
            raise ValueError(
                f"data_drift must be finite, got {data_drift!r}"
            )
        if not math.isfinite(distributional_shift):
            raise ValueError(
                f"distributional_shift must be finite, "
                f"got {distributional_shift!r}"
            )

        # Clamp inputs to [0, 1]
        data_drift = _clamp_01(data_drift)
        distributional_shift = _clamp_01(distributional_shift)

        aleatoric = compute_aleatoric(predictions)
        epistemic_model = compute_epistemic(predictions)
        epistemic_data = data_drift
        distributional = distributional_shift
        meta = 0.0  # Set externally by MetaUncertaintyEstimator

        # Clamp individual components to [0, 1]
        aleatoric = _clamp_01(aleatoric)
        epistemic_model = _clamp_01(epistemic_model)

        # Total = sqrt(sum of squares), capped at UNCERTAINTY_MAX
        sum_sq = (
            aleatoric ** 2
            + epistemic_model ** 2
            + epistemic_data ** 2
            + distributional ** 2
            + meta ** 2
        )
        total = math.sqrt(sum_sq)
        total = min(total, UNCERTAINTY_MAX)

        # NaN/Inf guard
        if not math.isfinite(total):
            total = UNCERTAINTY_MAX

        return UncertaintyBreakdown(
            aleatoric=aleatoric,
            epistemic_model=epistemic_model,
            epistemic_data=epistemic_data,
            distributional=distributional,
            meta=meta,
            total=total,
        )

    def compute_intervals(self, mu: float, sigma: float) -> Intervals:
        """
        Compute confidence intervals from prediction mean and uncertainty.

        ci_X = (mu - z_X * sigma, mu + z_X * sigma)

        Args:
            mu:    Prediction mean.
            sigma: Prediction uncertainty (>= 0).

        Returns:
            Intervals with ci_50, ci_90, ci_95.

        Raises:
            ValueError: If mu or sigma is non-finite, or sigma < 0.
        """
        if not math.isfinite(mu):
            raise ValueError(f"mu must be finite, got {mu!r}")
        if not math.isfinite(sigma):
            raise ValueError(f"sigma must be finite, got {sigma!r}")
        if sigma < 0.0:
            raise ValueError(f"sigma must be non-negative, got {sigma!r}")

        ci_50 = (mu - CI_Z_50 * sigma, mu + CI_Z_50 * sigma)
        ci_90 = (mu - CI_Z_90 * sigma, mu + CI_Z_90 * sigma)
        ci_95 = (mu - CI_Z_95 * sigma, mu + CI_Z_95 * sigma)

        return Intervals(ci_50=ci_50, ci_90=ci_90, ci_95=ci_95)


# =============================================================================
# SECTION 5 -- META-UNCERTAINTY ESTIMATOR
# =============================================================================

class MetaUncertaintyEstimator:
    """
    Computes meta-uncertainty U from calibration error and stability.

    U = sqrt(calibration_error^2 + (1 - stability)^2)

    State transitions:
      U <= META_U_RECALIBRATION                        -> NORMAL
      META_U_RECALIBRATION < U <= META_U_CONSERVATIVE  -> RECALIBRATION
      META_U_CONSERVATIVE  < U <= META_U_COLLAPSE      -> CONSERVATIVE
      U > META_U_COLLAPSE                              -> COLLAPSE

    Usage:
        estimator = MetaUncertaintyEstimator()
        state = estimator.estimate(calibration_error=0.05, stability=0.9)
    """

    def estimate(
        self,
        calibration_error: float,
        stability: float,
    ) -> MetaUncertaintyState:
        """
        Compute meta-uncertainty state.

        Args:
            calibration_error: Calibration error (ECE or similar) in [0, 1].
            stability:         System stability in [0, 1].

        Returns:
            MetaUncertaintyState with U, state name, and triggered threshold.

        Raises:
            ValueError: If inputs are non-finite.
        """
        if not math.isfinite(calibration_error):
            raise ValueError(
                f"calibration_error must be finite, "
                f"got {calibration_error!r}"
            )
        if not math.isfinite(stability):
            raise ValueError(
                f"stability must be finite, got {stability!r}"
            )

        # Clamp inputs to [0, 1]
        calibration_error = _clamp_01(calibration_error)
        stability = _clamp_01(stability)

        # U = sqrt(calibration_error^2 + (1 - stability)^2)
        instability = 1.0 - stability
        U = math.sqrt(calibration_error ** 2 + instability ** 2)

        # Clamp U to [0, 1]
        U = _clamp_01(U)

        # Determine state
        if U > META_U_COLLAPSE:
            state = "COLLAPSE"
            triggered_threshold = META_U_COLLAPSE
        elif U > META_U_CONSERVATIVE:
            state = "CONSERVATIVE"
            triggered_threshold = META_U_CONSERVATIVE
        elif U > META_U_RECALIBRATION:
            state = "RECALIBRATION"
            triggered_threshold = META_U_RECALIBRATION
        else:
            state = "NORMAL"
            triggered_threshold = 0.0

        return MetaUncertaintyState(
            U=U,
            state=state,
            triggered_threshold=triggered_threshold,
        )


# =============================================================================
# SECTION 6 -- INFORMATION QUALITY ESTIMATOR
# =============================================================================

class InformationQualityEstimator:
    """
    Estimates information quality of features for prediction.
    Pure Python implementation (no sklearn).
    Uses simple weighted scoring based on feature completeness and freshness.

    Usage:
        estimator = InformationQualityEstimator()
        quality = estimator.compute_quality(0.9, 0.8, 0.95)
        weights = estimator.compute_feature_weights(
            {"momentum": 0.3, "vol": 0.7}, regime="CRISIS"
        )
    """

    def compute_quality(
        self,
        feature_completeness: float,
        data_freshness: float,
        source_reliability: float,
    ) -> float:
        """
        Returns information quality score in [0, 1].

        quality = (feature_completeness + data_freshness + source_reliability) / 3.0
        All inputs clipped to [0, 1].

        Args:
            feature_completeness: Fraction of features available [0, 1].
            data_freshness:       Data freshness score [0, 1].
            source_reliability:   Source reliability score [0, 1].

        Returns:
            Quality score in [0, 1].

        Raises:
            ValueError: If any input is non-finite.
        """
        for name, val in [
            ("feature_completeness", feature_completeness),
            ("data_freshness", data_freshness),
            ("source_reliability", source_reliability),
        ]:
            if not math.isfinite(val):
                raise ValueError(f"{name} must be finite, got {val!r}")

        fc = _clamp_01(feature_completeness)
        df = _clamp_01(data_freshness)
        sr = _clamp_01(source_reliability)

        quality = (fc + df + sr) / 3.0

        # NaN/Inf guard (should not happen with clamped inputs, but safety)
        if not math.isfinite(quality):
            return 0.0

        return quality

    def compute_feature_weights(
        self,
        feature_importances: dict,
        regime: str = "NORMAL",
    ) -> dict:
        """
        Weight features by importance, adjusted for regime.

        Returns dict of feature_name -> weight.
        Weights normalized to sum to 1.0.

        In CRISIS regime, all weights are equalised (uniform).
        In other regimes, weights are proportional to importances.

        Args:
            feature_importances: Dict of feature_name -> importance (float >= 0).
            regime:              Regime string: "NORMAL", "CRISIS", etc.

        Returns:
            Dict of feature_name -> normalised weight.

        Raises:
            TypeError: If feature_importances is not a dict.
        """
        if not isinstance(feature_importances, dict):
            raise TypeError(
                f"feature_importances must be a dict, "
                f"got {type(feature_importances).__name__}"
            )

        if not feature_importances:
            return {}

        n = len(feature_importances)

        if regime == "CRISIS":
            # Equalise weights in crisis
            uniform = 1.0 / n
            return {k: uniform for k in feature_importances}

        # Clamp importances to non-negative, finite values
        clamped: Dict[str, float] = {}
        for k, v in feature_importances.items():
            if not isinstance(v, (int, float)) or not math.isfinite(v):
                clamped[k] = 0.0
            else:
                clamped[k] = max(0.0, float(v))

        total = sum(clamped.values())
        if total < _EPS:
            # All zero importances: uniform
            uniform = 1.0 / n
            return {k: uniform for k in clamped}

        return {k: v / total for k, v in clamped.items()}
