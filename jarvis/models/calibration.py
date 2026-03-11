# =============================================================================
# jarvis/models/calibration.py — Probability Calibration Layer
#
# Authority: FAS v6.0.1, S09 (Lines 1522-1620, 3477-3620)
#
# Three calibration methods:
#   1. Platt Scaling     — logistic regression on logits
#   2. Isotonic Regression — PAV (Pool Adjacent Violators) algorithm
#   3. Beta Calibration  — 3-parameter beta transform
#
# Entry point: evaluate_calibration()
# Consumes: compute_ece() from jarvis.metrics.ece_calculator
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
#   No numpy / scipy
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
#
# DEPENDENCIES
# ------------
#   stdlib:   dataclasses, math
#   internal: jarvis.metrics.ece_calculator (compute_ece, ECEResult)
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from jarvis.metrics.ece_calculator import compute_ece, ECEResult
from jarvis.utils.exceptions import CalibrationGateViolation

__all__ = [
    "CONFIDENCE_FLOOR",
    "CONFIDENCE_CEILING",
    "ECE_HARD_GATE",
    "ECE_REGIME_DRIFT_GATE",
    "PLATT_MAX_ITER",
    "PLATT_LR",
    "ISOTONIC_MIN_SAMPLES",
    "BETA_MAX_ITER",
    "BETA_LR",
    "ONLINE_WINDOW_SIZE",
    "ONLINE_UPDATE_FREQUENCY",
    "TEMPERATURE_SCALING_T",
    "CalibrationMetrics",
    "CalibrationResult",
    "platt_scaling",
    "isotonic_regression",
    "beta_calibration",
    "evaluate_calibration",
    "temperature_scaling",
    "CalibrationHardGate",
    "CalibrationLayer",
    "OnlineCalibrator",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals, not parametrisable)
# =============================================================================

CONFIDENCE_FLOOR: float = 1e-6
"""Minimum calibrated confidence value."""

CONFIDENCE_CEILING: float = 1.0 - 1e-6
"""Maximum calibrated confidence value."""

ECE_HARD_GATE: float = 0.05
"""ECE threshold — deployment blocked if ECE >= this."""

ECE_REGIME_DRIFT_GATE: float = 0.02
"""Maximum allowed ECE drift between regimes."""

PLATT_MAX_ITER: int = 100
"""Maximum iterations for Platt scaling gradient descent."""

PLATT_LR: float = 0.01
"""Learning rate for Platt scaling gradient descent."""

ISOTONIC_MIN_SAMPLES: int = 2
"""Minimum samples for isotonic regression."""

BETA_MAX_ITER: int = 100
"""Maximum iterations for beta calibration gradient descent."""

BETA_LR: float = 0.01
"""Learning rate for beta calibration gradient descent."""


# =============================================================================
# SECTION 2 -- DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class CalibrationMetrics:
    """
    Metrics from a calibration evaluation.

    Fields:
        ece:            Expected Calibration Error in [0, 1].
        mce:            Maximum Calibration Error (max per-bin error).
        brier:          Brier score (mean squared error of probabilities).
        nll:            Negative log-likelihood.
        is_calibrated:  True if ece < ECE_HARD_GATE (0.05).
        n_samples:      Number of samples evaluated.
        ece_result:     Full ECEResult from compute_ece().
    """
    ece: float
    mce: float
    brier: float
    nll: float
    is_calibrated: bool
    n_samples: int
    ece_result: ECEResult


@dataclass(frozen=True)
class CalibrationResult:
    """
    Result of a calibration method.

    Fields:
        method:                   Calibration method name.
        calibrated_confidences:   Calibrated probabilities in
                                  [CONFIDENCE_FLOOR, CONFIDENCE_CEILING].
        metrics:                  CalibrationMetrics for calibrated output.
        parameters:               Fitted parameters (method-specific).
    """
    method: str
    calibrated_confidences: Tuple[float, ...]
    metrics: CalibrationMetrics
    parameters: Dict[str, float]


# =============================================================================
# SECTION 3 -- HELPERS (pure, stateless, deterministic)
# =============================================================================

def _clamp(value: float) -> float:
    """Clamp to [CONFIDENCE_FLOOR, CONFIDENCE_CEILING]."""
    if value < CONFIDENCE_FLOOR:
        return CONFIDENCE_FLOOR
    if value > CONFIDENCE_CEILING:
        return CONFIDENCE_CEILING
    return value


def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _logit(p: float) -> float:
    """Logit transform: log(p / (1-p)). Input clamped to avoid inf."""
    p = _clamp(p)
    return math.log(p / (1.0 - p))


def _brier_score(
    confidences: Sequence[float],
    outcomes: Sequence[float],
) -> float:
    """Brier score: mean squared error between confidences and outcomes."""
    n = len(confidences)
    return sum((c - o) ** 2 for c, o in zip(confidences, outcomes)) / n


def _nll(
    confidences: Sequence[float],
    outcomes: Sequence[float],
) -> float:
    """Negative log-likelihood (binary cross-entropy)."""
    n = len(confidences)
    total = 0.0
    for c, o in zip(confidences, outcomes):
        p = _clamp(c)
        total -= o * math.log(p) + (1.0 - o) * math.log(1.0 - p)
    return total / n


def _compute_metrics(
    calibrated: Sequence[float],
    outcomes: Sequence[float],
) -> CalibrationMetrics:
    """Compute CalibrationMetrics from calibrated confidences and outcomes."""
    ece_result = compute_ece(list(calibrated), list(outcomes))
    brier = _brier_score(calibrated, outcomes)
    nll = _nll(calibrated, outcomes)
    return CalibrationMetrics(
        ece=ece_result.ece,
        mce=ece_result.max_bin_error,
        brier=brier,
        nll=nll,
        is_calibrated=ece_result.is_calibrated,
        n_samples=len(calibrated),
        ece_result=ece_result,
    )


def _validate_inputs(
    confidences: Sequence[float],
    outcomes: Sequence[float],
) -> None:
    """
    Validate calibration inputs.

    Raises:
        TypeError:  If inputs are not list/tuple or contain non-numeric.
        ValueError: If empty, lengths differ, or values out of [0,1] / non-finite.
    """
    if not isinstance(confidences, (list, tuple)):
        raise TypeError(
            f"confidences must be a list or tuple, "
            f"got {type(confidences).__name__}"
        )
    if not isinstance(outcomes, (list, tuple)):
        raise TypeError(
            f"outcomes must be a list or tuple, "
            f"got {type(outcomes).__name__}"
        )
    if len(confidences) == 0:
        raise ValueError("confidences must not be empty")
    if len(confidences) != len(outcomes):
        raise ValueError(
            f"confidences and outcomes must have equal length. "
            f"Got {len(confidences)} vs {len(outcomes)}"
        )
    for i, c in enumerate(confidences):
        if not isinstance(c, (int, float)):
            raise TypeError(
                f"confidences[{i}] must be numeric, "
                f"got {type(c).__name__}"
            )
        if not math.isfinite(c):
            raise ValueError(f"confidences[{i}] must be finite, got {c}")
        if c < 0.0 or c > 1.0:
            raise ValueError(
                f"confidences[{i}] must be in [0, 1], got {c}"
            )
    for i, o in enumerate(outcomes):
        if not isinstance(o, (int, float)):
            raise TypeError(
                f"outcomes[{i}] must be numeric, "
                f"got {type(o).__name__}"
            )
        if not math.isfinite(o):
            raise ValueError(f"outcomes[{i}] must be finite, got {o}")
        if o < 0.0 or o > 1.0:
            raise ValueError(
                f"outcomes[{i}] must be in [0, 1], got {o}"
            )


# =============================================================================
# SECTION 4 -- PLATT SCALING
# =============================================================================

def platt_scaling(
    confidences: Sequence[float],
    outcomes: Sequence[float],
) -> CalibrationResult:
    """
    Platt Scaling: fit q = sigmoid(a * logit(p) + b) via gradient descent.

    Minimises binary cross-entropy (NLL) over the training set.
    Parameters a (scale) and b (shift) are fitted.

    Args:
        confidences: Raw predicted probabilities in [0, 1].
        outcomes:    Binary outcomes in [0, 1].

    Returns:
        CalibrationResult with method="platt".

    Raises:
        TypeError:  If inputs are not list/tuple or contain non-numeric.
        ValueError: If inputs are empty, lengths differ, or values invalid.
    """
    _validate_inputs(confidences, outcomes)

    n = len(confidences)
    logits = [_logit(c) for c in confidences]

    # Gradient descent for parameters a, b
    a = 1.0
    b = 0.0

    for _ in range(PLATT_MAX_ITER):
        grad_a = 0.0
        grad_b = 0.0
        for j in range(n):
            q = _sigmoid(a * logits[j] + b)
            diff = q - outcomes[j]
            grad_a += diff * logits[j]
            grad_b += diff
        grad_a /= n
        grad_b /= n
        a -= PLATT_LR * grad_a
        b -= PLATT_LR * grad_b

    # Apply calibration
    calibrated = [_clamp(_sigmoid(a * logits[j] + b)) for j in range(n)]

    metrics = _compute_metrics(calibrated, outcomes)
    return CalibrationResult(
        method="platt",
        calibrated_confidences=tuple(calibrated),
        metrics=metrics,
        parameters={"a": a, "b": b},
    )


# =============================================================================
# SECTION 5 -- ISOTONIC REGRESSION (PAV)
# =============================================================================

def isotonic_regression(
    confidences: Sequence[float],
    outcomes: Sequence[float],
) -> CalibrationResult:
    """
    Isotonic Regression via Pool Adjacent Violators (PAV) algorithm.

    Fits a monotonically non-decreasing step function mapping
    raw confidences to calibrated probabilities.

    Args:
        confidences: Raw predicted probabilities in [0, 1].
        outcomes:    Binary outcomes in [0, 1].

    Returns:
        CalibrationResult with method="isotonic".

    Raises:
        TypeError:  If inputs are not list/tuple or contain non-numeric.
        ValueError: If inputs are empty, lengths differ, or values invalid.
    """
    _validate_inputs(confidences, outcomes)

    n = len(confidences)

    # Sort by confidence (ties broken by index for determinism)
    indices = sorted(range(n), key=lambda i: (confidences[i], i))
    sorted_outcomes = [float(outcomes[i]) for i in indices]

    # PAV algorithm: merge adjacent blocks that violate monotonicity
    # Each block is [start, end, value, weight]
    blocks: List[List] = []
    for j in range(n):
        blocks.append([j, j, sorted_outcomes[j], 1.0])
        # Merge while last two blocks violate non-decreasing order
        while len(blocks) > 1 and blocks[-2][2] > blocks[-1][2]:
            prev = blocks[-2]
            curr = blocks.pop()
            total_w = prev[3] + curr[3]
            merged_val = (prev[2] * prev[3] + curr[2] * curr[3]) / total_w
            prev[1] = curr[1]
            prev[2] = merged_val
            prev[3] = total_w

    # Map PAV output back to original order
    pav_values = [0.0] * n
    for block in blocks:
        for j in range(block[0], block[1] + 1):
            pav_values[j] = block[2]

    # Reorder to original indices
    calibrated_sorted = pav_values
    calibrated = [0.0] * n
    for sorted_pos, orig_idx in enumerate(indices):
        calibrated[orig_idx] = _clamp(calibrated_sorted[sorted_pos])

    # Compute number of unique step levels for parameters
    unique_levels = sorted(set(
        block[2] for block in blocks
    ))

    metrics = _compute_metrics(calibrated, outcomes)
    return CalibrationResult(
        method="isotonic",
        calibrated_confidences=tuple(calibrated),
        metrics=metrics,
        parameters={
            "n_blocks": float(len(blocks)),
            "n_levels": float(len(unique_levels)),
        },
    )


# =============================================================================
# SECTION 6 -- BETA CALIBRATION
# =============================================================================

def beta_calibration(
    confidences: Sequence[float],
    outcomes: Sequence[float],
) -> CalibrationResult:
    """
    Beta Calibration: fit q = sigmoid(a*log(p) + b*log(1-p) + c).

    Three-parameter model that generalises Platt scaling by operating
    on log(p) and log(1-p) independently.

    Args:
        confidences: Raw predicted probabilities in [0, 1].
        outcomes:    Binary outcomes in [0, 1].

    Returns:
        CalibrationResult with method="beta".

    Raises:
        TypeError:  If inputs are not list/tuple or contain non-numeric.
        ValueError: If inputs are empty, lengths differ, or values invalid.
    """
    _validate_inputs(confidences, outcomes)

    n = len(confidences)
    clamped = [_clamp(c) for c in confidences]
    log_p = [math.log(c) for c in clamped]
    log_1mp = [math.log(1.0 - c) for c in clamped]

    # Gradient descent for parameters a, b, c
    a = 1.0
    b = -1.0
    c = 0.0

    for _ in range(BETA_MAX_ITER):
        grad_a = 0.0
        grad_b = 0.0
        grad_c = 0.0
        for j in range(n):
            z = a * log_p[j] + b * log_1mp[j] + c
            q = _sigmoid(z)
            diff = q - outcomes[j]
            grad_a += diff * log_p[j]
            grad_b += diff * log_1mp[j]
            grad_c += diff
        grad_a /= n
        grad_b /= n
        grad_c /= n
        a -= BETA_LR * grad_a
        b -= BETA_LR * grad_b
        c -= BETA_LR * grad_c

    # Apply calibration
    calibrated = []
    for j in range(n):
        z = a * log_p[j] + b * log_1mp[j] + c
        calibrated.append(_clamp(_sigmoid(z)))

    metrics = _compute_metrics(calibrated, outcomes)
    return CalibrationResult(
        method="beta",
        calibrated_confidences=tuple(calibrated),
        metrics=metrics,
        parameters={"a": a, "b": b, "c": c},
    )


# =============================================================================
# SECTION 7 -- ENTRY POINT
# =============================================================================

_VALID_METHODS = ("platt", "isotonic", "beta")

def evaluate_calibration(
    confidences: Sequence[float],
    outcomes: Sequence[float],
    method: str = "platt",
) -> CalibrationResult:
    """
    Evaluate and calibrate predicted probabilities.

    Entry-point function that dispatches to the requested calibration
    method and returns calibrated confidences with full metrics.

    Consumes compute_ece() from jarvis.metrics.ece_calculator for
    ECE computation on the calibrated output.

    Args:
        confidences: Raw predicted probabilities in [0, 1].
        outcomes:    Binary outcomes in [0, 1].
        method:      Calibration method: "platt", "isotonic", or "beta".

    Returns:
        CalibrationResult with calibrated confidences, metrics, and
        fitted parameters.

    Raises:
        TypeError:  If inputs are not list/tuple or contain non-numeric.
        ValueError: If inputs are empty, lengths differ, values invalid,
                    or method is not one of the valid methods.
    """
    if not isinstance(method, str):
        raise TypeError(
            f"method must be a string, got {type(method).__name__}"
        )
    if method not in _VALID_METHODS:
        raise ValueError(
            f"method must be one of {_VALID_METHODS}, got {method!r}"
        )

    if method == "platt":
        return platt_scaling(confidences, outcomes)
    elif method == "isotonic":
        return isotonic_regression(confidences, outcomes)
    else:
        return beta_calibration(confidences, outcomes)


# =============================================================================
# SECTION 8 -- S09 EXTENSION CONSTANTS (DET-06: fixed literals)
# =============================================================================

ONLINE_WINDOW_SIZE: int = 500
"""Maximum number of samples retained in the online calibrator sliding window."""

ONLINE_UPDATE_FREQUENCY: int = 100
"""Number of new samples required before triggering a recalibration."""

TEMPERATURE_SCALING_T: float = 2.5
"""Temperature parameter for CRISIS regime temperature scaling."""


# =============================================================================
# SECTION 9 -- TEMPERATURE SCALING
# =============================================================================

def temperature_scaling(
    confidences: Sequence[float],
    outcomes: Sequence[float],
    T: float = TEMPERATURE_SCALING_T,
) -> CalibrationResult:
    """
    Temperature scaling: soften logits by dividing by T before sigmoid.

    calibrated_i = sigmoid(logit(conf_i) / T)

    Higher T pushes calibrated values closer to 0.5 (more conservative).
    T = 1.0 is the identity transform (no change).

    Args:
        confidences: Raw predicted probabilities in [0, 1].
        outcomes:    Binary outcomes in [0, 1].
        T:           Temperature parameter (> 0). Default TEMPERATURE_SCALING_T.

    Returns:
        CalibrationResult with method="temperature".

    Raises:
        TypeError:  If inputs are not list/tuple or contain non-numeric.
        ValueError: If inputs are empty, lengths differ, values invalid,
                    or T is not positive / not finite.
    """
    _validate_inputs(confidences, outcomes)

    if not isinstance(T, (int, float)):
        raise TypeError(f"T must be numeric, got {type(T).__name__}")
    if not math.isfinite(T):
        raise ValueError(f"T must be finite, got {T!r}")
    if T <= 0.0:
        raise ValueError(f"T must be positive, got {T!r}")

    n = len(confidences)
    logits = [_logit(c) for c in confidences]

    calibrated = []
    for j in range(n):
        scaled_logit = logits[j] / T
        val = _sigmoid(scaled_logit)
        val = _clamp(val)
        # NaN/Inf guard
        if not math.isfinite(val):
            val = 0.5
        calibrated.append(val)

    metrics = _compute_metrics(calibrated, outcomes)
    return CalibrationResult(
        method="temperature",
        calibrated_confidences=tuple(calibrated),
        metrics=metrics,
        parameters={"T": T},
    )


# =============================================================================
# SECTION 10 -- CALIBRATION HARD GATE
# =============================================================================

class CalibrationHardGate:
    """
    Enforces hard calibration gates.

    Raises CalibrationGateViolation if ECE >= ECE_HARD_GATE or
    drift > ECE_REGIME_DRIFT_GATE.
    """

    def enforce(self, metrics: CalibrationMetrics) -> bool:
        """
        Check metrics against the ECE hard gate.

        Args:
            metrics: CalibrationMetrics to check.

        Returns:
            True if calibration passes the gate (ECE < ECE_HARD_GATE).

        Raises:
            CalibrationGateViolation: If ECE >= ECE_HARD_GATE.
        """
        if not isinstance(metrics, CalibrationMetrics):
            raise TypeError(
                f"metrics must be a CalibrationMetrics instance, "
                f"got {type(metrics).__name__}"
            )
        ece = metrics.ece
        # NaN/Inf guard: treat non-finite as violation
        if not math.isfinite(ece):
            raise CalibrationGateViolation(
                f"ECE is non-finite ({ece!r}); hard gate blocks deployment."
            )
        if ece >= ECE_HARD_GATE:
            raise CalibrationGateViolation(
                f"ECE {ece:.6f} >= hard gate {ECE_HARD_GATE}; "
                f"deployment blocked."
            )
        return True

    def check_drift(
        self, current_ece: float, previous_ece: float
    ) -> bool:
        """
        Check if ECE drift between regimes exceeds the gate.

        Args:
            current_ece:  Current ECE value.
            previous_ece: Previous ECE value.

        Returns:
            True if drift is within limits.

        Raises:
            CalibrationGateViolation: If |current - previous| > ECE_REGIME_DRIFT_GATE.
        """
        for name, val in [("current_ece", current_ece),
                          ("previous_ece", previous_ece)]:
            if not isinstance(val, (int, float)):
                raise TypeError(f"{name} must be numeric, got {type(val).__name__}")
            if not math.isfinite(val):
                raise CalibrationGateViolation(
                    f"{name} is non-finite ({val!r}); drift check fails."
                )
        drift = abs(current_ece - previous_ece)
        if drift > ECE_REGIME_DRIFT_GATE:
            raise CalibrationGateViolation(
                f"ECE drift {drift:.6f} > drift gate {ECE_REGIME_DRIFT_GATE}; "
                f"recalibration required."
            )
        return True


# =============================================================================
# SECTION 11 -- CALIBRATION LAYER (regime-specific dispatch)
# =============================================================================

# Regime -> calibration method mapping (deterministic, no global mutable state)
_REGIME_METHOD_MAP: Dict[str, str] = {
    "RISK_ON": "platt",
    "RISK_OFF": "isotonic",
    "TRANSITION": "beta",
    "CRISIS": "temperature",
    "UNKNOWN": "platt",
}


class CalibrationLayer:
    """
    Dispatches to the appropriate calibration method based on regime.

    Regime -> Method mapping:
      RISK_ON     -> platt_scaling (stable, well-calibrated)
      RISK_OFF    -> isotonic_regression (more flexible for stressed markets)
      TRANSITION  -> beta_calibration (handles distribution shifts)
      CRISIS      -> temperature_scaling with T=2.5 (conservative widening)
      UNKNOWN     -> platt_scaling (safe default)
    """

    def calibrate(
        self,
        confidences: tuple,
        outcomes: tuple,
        regime: str = "RISK_ON",
    ) -> CalibrationResult:
        """
        Dispatch to regime-appropriate calibration method.

        Args:
            confidences: Raw predicted probabilities in [0, 1] (tuple or list).
            outcomes:    Binary outcomes in [0, 1] (tuple or list).
            regime:      Regime string. Default "RISK_ON".

        Returns:
            CalibrationResult from the selected method.

        Raises:
            ValueError: If regime is not recognised.
            TypeError:  If inputs are invalid.
        """
        method_name = self.get_method_for_regime(regime)

        if method_name == "platt":
            return platt_scaling(confidences, outcomes)
        elif method_name == "isotonic":
            return isotonic_regression(confidences, outcomes)
        elif method_name == "beta":
            return beta_calibration(confidences, outcomes)
        elif method_name == "temperature":
            return temperature_scaling(
                confidences, outcomes, T=TEMPERATURE_SCALING_T
            )
        else:
            # Defensive fallback (should not be reachable)
            return platt_scaling(confidences, outcomes)

    def get_method_for_regime(self, regime: str) -> str:
        """
        Return method name for the given regime string.

        Args:
            regime: Regime string.

        Returns:
            Method name string.

        Raises:
            ValueError: If regime is not in the known mapping.
        """
        if not isinstance(regime, str):
            raise TypeError(
                f"regime must be a string, got {type(regime).__name__}"
            )
        if regime not in _REGIME_METHOD_MAP:
            raise ValueError(
                f"Unknown regime {regime!r}. "
                f"Must be one of {tuple(_REGIME_METHOD_MAP.keys())}"
            )
        return _REGIME_METHOD_MAP[regime]


# =============================================================================
# SECTION 12 -- ONLINE CALIBRATOR
# =============================================================================

class OnlineCalibrator:
    """
    Online calibration with a sliding window.

    Maintains the last ONLINE_WINDOW_SIZE samples. Triggers recalibration
    every ONLINE_UPDATE_FREQUENCY new samples.

    Instance state is per-object (no global mutable state). A fresh
    OnlineCalibrator should be created per session (DET-02).
    """

    def __init__(self) -> None:
        self._confidences: List[float] = []
        self._outcomes: List[float] = []
        self._sample_count: int = 0
        self._last_calibration_count: int = 0

    def add_sample(self, confidence: float, outcome: float) -> None:
        """
        Add a single (confidence, outcome) sample.

        Values are clamped to [0, 1]. Non-finite values are silently
        replaced with 0.5 (confidence) or 0.0 (outcome).

        Trims the window to ONLINE_WINDOW_SIZE after insertion.

        Args:
            confidence: Predicted probability.
            outcome:    Observed outcome.
        """
        # NaN/Inf guard
        if not isinstance(confidence, (int, float)) or not math.isfinite(confidence):
            confidence = 0.5
        if not isinstance(outcome, (int, float)) or not math.isfinite(outcome):
            outcome = 0.0

        # Clamp to [0, 1]
        confidence = max(0.0, min(1.0, float(confidence)))
        outcome = max(0.0, min(1.0, float(outcome)))

        self._confidences.append(confidence)
        self._outcomes.append(outcome)
        self._sample_count += 1

        # Trim to window size
        if len(self._confidences) > ONLINE_WINDOW_SIZE:
            excess = len(self._confidences) - ONLINE_WINDOW_SIZE
            self._confidences = self._confidences[excess:]
            self._outcomes = self._outcomes[excess:]

    def should_recalibrate(self) -> bool:
        """
        Check whether enough new samples have arrived since last calibration.

        Returns:
            True if ONLINE_UPDATE_FREQUENCY new samples have been added
            since the last recalibration call.
        """
        return (
            self._sample_count - self._last_calibration_count
            >= ONLINE_UPDATE_FREQUENCY
        )

    def recalibrate(self, regime: str = "RISK_ON") -> CalibrationResult:
        """
        Run calibration on the current window using CalibrationLayer.

        Updates the internal counter so should_recalibrate() resets.

        Args:
            regime: Regime string for CalibrationLayer dispatch.

        Returns:
            CalibrationResult from CalibrationLayer.calibrate().

        Raises:
            ValueError: If the window is empty.
        """
        if len(self._confidences) == 0:
            raise ValueError(
                "Cannot recalibrate: no samples in window."
            )
        self._last_calibration_count = self._sample_count

        layer = CalibrationLayer()
        return layer.calibrate(
            tuple(self._confidences),
            tuple(self._outcomes),
            regime=regime,
        )

    def get_current_ece(self) -> float:
        """
        Compute ECE on the current window.

        Returns 0.0 if the window has fewer than 2 samples (not enough
        for meaningful ECE computation).

        Returns:
            ECE value as float in [0, 1].
        """
        if len(self._confidences) < 2:
            return 0.0
        ece_result = compute_ece(
            list(self._confidences), list(self._outcomes)
        )
        ece = ece_result.ece
        # NaN/Inf guard
        if not math.isfinite(ece):
            return 0.0
        return ece
