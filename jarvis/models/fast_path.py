# =============================================================================
# jarvis/models/fast_path.py — S06 Fast Path Ensemble
#
# Authority: FAS v6.0.1, S06 (Lines 2767-2903)
#
# Real-time prediction (< 50ms) via lightweight ensemble:
#   1. Member 0 (Kalman):     StateEstimator wrapper
#   2. Member 1 (RF-like):    Deterministic decision tree on features
#   3. Member 2 (Rule-based): classify() signal mapping
#
# Entry point: FastPathEnsemble.predict()
# Aggregation: aggregate_fast()
#
# CLASSIFICATION: Tier 6 — ANALYSIS AND STRATEGY RESEARCH TOOL.
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects (beyond instance state for get_uncertainty).
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
#   internal: jarvis.core.state_estimator (StateEstimator)
#             jarvis.core.state_layer (LatentState)
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from jarvis.core.state_estimator import StateEstimator
from jarvis.core.state_layer import LatentState

__all__ = [
    "ENSEMBLE_WEIGHTS",
    "UNCERTAINTY_TRIGGER_DEEP_PATH",
    "RF_N_ESTIMATORS",
    "RF_MAX_DEPTH",
    "RF_MIN_SAMPLES_SPLIT",
    "RF_MIN_SAMPLES_LEAF",
    "Prediction",
    "FastResult",
    "FastPathEnsemble",
    "aggregate_fast",
    "classify",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals, not parametrisable)
# =============================================================================

ENSEMBLE_WEIGHTS: Tuple[float, ...] = (1.0, 1.5, 0.8)
"""Ensemble member weights: Kalman, RF-like, Rule-based."""

UNCERTAINTY_TRIGGER_DEEP_PATH: float = 0.15
"""Sigma threshold above which the deep path is triggered."""

RF_N_ESTIMATORS: int = 50
"""Number of estimators for the RF-like member (informational)."""

RF_MAX_DEPTH: int = 8
"""Maximum depth for the RF-like member (informational)."""

RF_MIN_SAMPLES_SPLIT: int = 20
"""Minimum samples to split for the RF-like member (informational)."""

RF_MIN_SAMPLES_LEAF: int = 10
"""Minimum samples per leaf for the RF-like member (informational)."""

#: Epsilon floor for sigma values.
_SIGMA_FLOOR: float = 1e-6

#: Confidence floor and ceiling.
_CONFIDENCE_FLOOR: float = 1e-6
_CONFIDENCE_CEILING: float = 1.0 - 1e-6

#: Epsilon for safe division.
_EPS: float = 1e-10


# =============================================================================
# SECTION 2 -- DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class Prediction:
    """
    Single ensemble member prediction.

    Fields:
        mu:         Direction prediction, clipped to [-1.0, 1.0].
        sigma:      Uncertainty >= 0, epsilon-floored at 1e-6.
        confidence: Clipped to [1e-6, 1-1e-6].
    """
    mu: float
    sigma: float
    confidence: float

    def __post_init__(self) -> None:
        # NaN/Inf guard on all fields
        for name, val in [("mu", self.mu), ("sigma", self.sigma),
                          ("confidence", self.confidence)]:
            if not math.isfinite(val):
                raise ValueError(
                    f"Prediction.{name} must be finite, got {val!r}"
                )
        # Clip mu to [-1.0, 1.0]
        clamped_mu = max(-1.0, min(1.0, self.mu))
        object.__setattr__(self, "mu", clamped_mu)
        # Floor sigma at epsilon
        floored_sigma = max(_SIGMA_FLOOR, self.sigma)
        object.__setattr__(self, "sigma", floored_sigma)
        # Clip confidence to [1e-6, 1-1e-6]
        clipped_conf = max(_CONFIDENCE_FLOOR, min(_CONFIDENCE_CEILING, self.confidence))
        object.__setattr__(self, "confidence", clipped_conf)


@dataclass(frozen=True)
class FastResult:
    """
    Aggregated ensemble prediction result.

    Fields:
        mu:              Aggregated prediction direction.
        sigma:           Total uncertainty (sqrt(epistemic^2 + aleatoric^2)).
        deep_triggered:  True if sigma > UNCERTAINTY_TRIGGER_DEEP_PATH.
        latency_ms:      Execution time (caller-supplied for DET compliance).
        ensemble_seeds:  Seeds for reproducibility (tuple, not list -- frozen).
    """
    mu: float
    sigma: float
    deep_triggered: bool
    latency_ms: float
    ensemble_seeds: Tuple[int, ...]

    def __post_init__(self) -> None:
        # NaN/Inf guard on numeric fields
        for name, val in [("mu", self.mu), ("sigma", self.sigma),
                          ("latency_ms", self.latency_ms)]:
            if not math.isfinite(val):
                raise ValueError(
                    f"FastResult.{name} must be finite, got {val!r}"
                )
        if not isinstance(self.ensemble_seeds, tuple):
            raise TypeError(
                f"ensemble_seeds must be a tuple, "
                f"got {type(self.ensemble_seeds).__name__}"
            )


# =============================================================================
# SECTION 3 -- CLASSIFY (rule-based classifier)
# =============================================================================

def classify(features: dict) -> str:
    """
    Rule-based classifier.

    Returns 'HIGH_UNCERTAINTY', 'AVOID', or 'NORMAL' based on feature values.

    Args:
        features: Dictionary of feature name -> float value.

    Returns:
        Signal string: 'HIGH_UNCERTAINTY', 'AVOID', or 'NORMAL'.
    """
    volatility = features.get("volatility", 0.0)
    trend_strength = features.get("trend_strength", 0.0)

    # Guard against non-finite values -- treat as high uncertainty
    if not math.isfinite(volatility) or not math.isfinite(trend_strength):
        return "HIGH_UNCERTAINTY"

    if volatility > 0.3:
        return "HIGH_UNCERTAINTY"
    if trend_strength < -0.5:
        return "AVOID"
    return "NORMAL"


# =============================================================================
# SECTION 4 -- AGGREGATE FAST
# =============================================================================

def aggregate_fast(
    predictions: tuple,
    weights: tuple = ENSEMBLE_WEIGHTS,
) -> tuple:
    """
    Aggregate ensemble predictions.

    Returns (mu, sigma_total, deep_triggered) tuple.

    mu = weighted_mean(predictions.mu, weights)
    sigma_epistemic = sqrt(weighted_variance_of_means)
    sigma_aleatoric = weighted_mean(predictions.sigma, weights)
    sigma_total = sqrt(sigma_epistemic^2 + sigma_aleatoric^2)
    deep_triggered = sigma_total > UNCERTAINTY_TRIGGER_DEEP_PATH

    Args:
        predictions: Tuple of Prediction objects.
        weights:     Tuple of float weights (default: ENSEMBLE_WEIGHTS).

    Returns:
        Tuple of (mu, sigma_total, deep_triggered).
    """
    if len(predictions) == 0:
        return (0.0, 1.0, True)

    total_weight = sum(weights[:len(predictions)])
    if total_weight < _EPS:
        total_weight = _EPS

    # Weighted mean of mu
    mu = sum(
        p.mu * w for p, w in zip(predictions, weights)
    ) / total_weight

    # Epistemic uncertainty = sqrt(weighted variance of means)
    sigma_epistemic_sq = sum(
        w * (p.mu - mu) ** 2 for p, w in zip(predictions, weights)
    ) / total_weight
    sigma_epistemic = math.sqrt(max(0.0, sigma_epistemic_sq))

    # Aleatoric uncertainty = weighted mean of individual sigmas
    sigma_aleatoric = sum(
        p.sigma * w for p, w in zip(predictions, weights)
    ) / total_weight

    # Total uncertainty
    sigma_total = math.sqrt(sigma_epistemic ** 2 + sigma_aleatoric ** 2)

    # NaN/Inf guard
    if not math.isfinite(sigma_total):
        sigma_total = 1.0  # Maximum uncertainty as safe fallback
    if not math.isfinite(mu):
        mu = 0.0

    deep_triggered = sigma_total > UNCERTAINTY_TRIGGER_DEEP_PATH

    return (mu, sigma_total, deep_triggered)


# =============================================================================
# SECTION 5 -- MEMBER IMPLEMENTATIONS (private helpers)
# =============================================================================

def _safe_feature(features: dict, key: str, default: float = 0.0) -> float:
    """Extract a feature value, returning default if missing or non-finite."""
    val = features.get(key, default)
    if not isinstance(val, (int, float)):
        return default
    if not math.isfinite(val):
        return default
    return float(val)


def _member0_kalman(
    features: dict,
    state: Optional[LatentState],
    estimator: StateEstimator,
) -> Prediction:
    """
    Member 0: Kalman wrapper.

    If state is provided, extract mu from state fields and sigma from
    state uncertainty. Otherwise, use features for a simple prediction.
    """
    if state is not None:
        # Extract prediction from state fields
        mu_raw = state.trend_strength * 0.5 + state.momentum * 0.3
        sigma_raw = state.prediction_uncertainty
        confidence_raw = state.regime_confidence

        # Use estimator predict to update internal covariance
        estimator.predict(state)

        # Get covariance trace as additional uncertainty measure
        cov = estimator.get_covariance()
        cov_trace = sum(cov[i][i] for i in range(len(cov)))
        # Normalise trace to a small additive uncertainty
        sigma_cov = math.sqrt(max(0.0, cov_trace)) / len(cov)

        mu = max(-1.0, min(1.0, mu_raw))
        sigma = max(_SIGMA_FLOOR, sigma_raw + sigma_cov * 0.1)
        confidence = max(_CONFIDENCE_FLOOR, min(_CONFIDENCE_CEILING, confidence_raw))
    else:
        # Fallback: use features directly
        momentum = _safe_feature(features, "momentum", 0.0)
        trend = _safe_feature(features, "trend_strength", 0.0)
        vol = _safe_feature(features, "volatility", 0.1)

        mu = max(-1.0, min(1.0, momentum * 0.4 + trend * 0.3))
        sigma = max(_SIGMA_FLOOR, vol * 0.5 + 0.05)
        confidence = max(
            _CONFIDENCE_FLOOR,
            min(_CONFIDENCE_CEILING, 1.0 - vol)
        )

    return Prediction(mu=mu, sigma=sigma, confidence=confidence)


def _member1_tree(features: dict) -> Prediction:
    """
    Member 1: Deterministic decision tree on features.

    Uses fixed decision boundaries on features (no training, no sklearn).
    Multiple feature checks create a tree-like structure.
    Deterministic given same features.
    """
    momentum = _safe_feature(features, "momentum", 0.0)
    trend = _safe_feature(features, "trend_strength", 0.0)
    vol = _safe_feature(features, "volatility", 0.1)
    stress = _safe_feature(features, "stress", 0.0)
    mean_rev = _safe_feature(features, "mean_reversion", 0.0)

    # Decision tree with fixed boundaries
    if vol > 0.4:
        # High volatility regime
        if stress > 0.5:
            mu = -0.3
            sigma = 0.4
            confidence = 0.3
        else:
            mu = 0.0
            sigma = 0.3
            confidence = 0.4
    elif momentum > 0.5:
        # Strong positive momentum
        if trend > 0.3:
            mu = 0.4
            sigma = 0.1
            confidence = 0.7
        else:
            mu = 0.2
            sigma = 0.15
            confidence = 0.55
    elif momentum < -0.5:
        # Strong negative momentum
        if trend < -0.3:
            mu = -0.4
            sigma = 0.1
            confidence = 0.7
        else:
            mu = -0.2
            sigma = 0.15
            confidence = 0.55
    elif mean_rev > 0.3:
        # Mean reversion signal
        mu = -momentum * 0.3
        sigma = 0.2
        confidence = 0.5
    elif mean_rev < -0.3:
        mu = -momentum * 0.3
        sigma = 0.2
        confidence = 0.5
    else:
        # Neutral / low signal regime
        mu = momentum * 0.1 + trend * 0.1
        sigma = 0.2
        confidence = 0.45

    # Clamp mu
    mu = max(-1.0, min(1.0, mu))

    return Prediction(mu=mu, sigma=sigma, confidence=confidence)


def _member2_rules(features: dict) -> Prediction:
    """
    Member 2: Rule-based classifier mapped to Prediction.

    Calls classify(features) and maps the signal to a Prediction:
      NORMAL           -> mu=0.0,  sigma=0.1, confidence=0.6
      HIGH_UNCERTAINTY -> mu=0.0,  sigma=0.5, confidence=0.3
      AVOID            -> mu=-0.3, sigma=0.3, confidence=0.5
    """
    signal = classify(features)

    if signal == "NORMAL":
        return Prediction(mu=0.0, sigma=0.1, confidence=0.6)
    elif signal == "HIGH_UNCERTAINTY":
        return Prediction(mu=0.0, sigma=0.5, confidence=0.3)
    else:  # AVOID
        return Prediction(mu=-0.3, sigma=0.3, confidence=0.5)


# =============================================================================
# SECTION 6 -- FAST PATH ENSEMBLE
# =============================================================================

class FastPathEnsemble:
    """
    S06 Fast Path Ensemble for real-time prediction.

    Three ensemble members:
      0. Kalman wrapper (StateEstimator)
      1. Deterministic decision tree (RF-like, no sklearn)
      2. Rule-based classifier

    Aggregation uses weighted mean with epistemic/aleatoric decomposition.
    Deep path is triggered when total sigma > UNCERTAINTY_TRIGGER_DEEP_PATH.

    Usage:
        ensemble = FastPathEnsemble(base_seed=42)
        result = ensemble.predict(features, state=latent_state)
        uncertainty = ensemble.get_uncertainty()
    """

    def __init__(self, base_seed: int = 42) -> None:
        """
        Initialise ensemble with deterministic seeds.

        Creates 3 seeds: [base_seed, base_seed+1000, base_seed+2000].
        Creates a fresh StateEstimator for member 0 (Kalman).

        Args:
            base_seed: Base seed for reproducibility. Must be an integer.
        """
        if not isinstance(base_seed, int):
            raise TypeError(
                f"base_seed must be an int, got {type(base_seed).__name__}"
            )
        self._n_members: int = 3
        self._seeds: Tuple[int, ...] = tuple(
            base_seed + i * 1000 for i in range(self._n_members)
        )
        # Fresh StateEstimator per instance (DET-02: no global state)
        self._estimator: StateEstimator = StateEstimator()
        # Last computed sigma for get_uncertainty() (instance state, not global)
        self._last_sigma: float = 0.0

    def predict(
        self,
        features: dict,
        state: Optional[LatentState] = None,
        latency_ms: float = 0.0,
    ) -> FastResult:
        """
        Run ensemble prediction.

        1. Member 0 (Kalman): StateEstimator wrapper
        2. Member 1 (RF-like): Deterministic decision tree
        3. Member 2 (Rule-based): classify() signal mapping
        4. Aggregate with ENSEMBLE_WEIGHTS

        Args:
            features:   Dict of feature name -> float value.
            state:      Optional LatentState for Kalman member.
            latency_ms: Caller-supplied latency (DET compliance: no time.time()).

        Returns:
            FastResult with aggregated prediction.
        """
        if not isinstance(features, dict):
            raise TypeError(
                f"features must be a dict, got {type(features).__name__}"
            )
        if not math.isfinite(latency_ms):
            raise ValueError(
                f"latency_ms must be finite, got {latency_ms!r}"
            )

        # Run all three members
        pred0 = _member0_kalman(features, state, self._estimator)
        pred1 = _member1_tree(features)
        pred2 = _member2_rules(features)

        predictions = (pred0, pred1, pred2)

        # Aggregate
        mu, sigma_total, deep_triggered = aggregate_fast(
            predictions, ENSEMBLE_WEIGHTS
        )

        # Store last sigma for get_uncertainty()
        self._last_sigma = sigma_total

        return FastResult(
            mu=mu,
            sigma=sigma_total,
            deep_triggered=deep_triggered,
            latency_ms=latency_ms,
            ensemble_seeds=self._seeds,
        )

    def get_uncertainty(self) -> float:
        """
        Return the last computed sigma_total.

        Returns 0.0 if no prediction has been made yet.
        Always >= 0.
        """
        return self._last_sigma
