# =============================================================================
# jarvis/risk/failure_mode_handler.py
# Authority: FAS v6.0.1 -- S17.5 (FM-01..FM-06 detection + simultaneous rules)
# =============================================================================
#
# SCOPE
# -----
# Detection of 6 canonical failure modes (FM-01..FM-06) from raw numeric
# inputs.  Produces a FailureModeStatus with active modes, severity, and
# recommended action based on SIMULTANEOUS_FM_RULES.
#
# Public symbols:
#   FailureMode              Enum (FM_01..FM_06)
#   FailureModeStatus        Frozen dataclass — detection output
#   detect_failure_modes     Pure function — detect active failure modes
#   SIMULTANEOUS_FM_RULES    Count → recommended action mapping
#   FM01_KALMAN_THRESHOLD    1e6
#   FM02_VOL_SPIKE_FACTOR    3.0
#   FM03_REGIME_CHANGE_LIMIT 3
#   FM04_CORRELATION_THRESHOLD 0.85
#   FM06_ECE_THRESHOLD       0.05
#
# GOVERNANCE
# ----------
# This module does NOT modify risk engine state.  Output is advisory.
# The caller (e.g. confidence layer) decides how to apply the result.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, enum, typing
#   external:  NONE
#   internal:  NONE
#   PROHIBITED: logging, random, file IO, network IO, datetime.now(), numpy
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
from enum import Enum
from typing import Dict, Tuple

__all__ = [
    "FailureMode",
    "FailureModeStatus",
    "detect_failure_modes",
    "SIMULTANEOUS_FM_RULES",
    "FM01_KALMAN_THRESHOLD",
    "FM02_VOL_SPIKE_FACTOR",
    "FM03_REGIME_CHANGE_LIMIT",
    "FM04_CORRELATION_THRESHOLD",
    "FM06_ECE_THRESHOLD",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

FM01_KALMAN_THRESHOLD: float = 1e6
"""Kalman condition number above this triggers FM-01 (Kalman divergence)."""

FM02_VOL_SPIKE_FACTOR: float = 3.0
"""Volatility above baseline * this factor triggers FM-02 (vol spike)."""

FM03_REGIME_CHANGE_LIMIT: int = 3
"""More than this many regime changes in window triggers FM-03 (oscillation)."""

FM04_CORRELATION_THRESHOLD: float = 0.85
"""Average correlation above this triggers FM-04 (correlation breakdown)."""

FM06_ECE_THRESHOLD: float = 0.05
"""ECE above this triggers FM-06 (calibration violation)."""

SIMULTANEOUS_FM_RULES: Dict[int, str] = {
    0: "NORMAL",
    1: "REDUCE_EXPOSURE",
    2: "DEFENSIVE",
}
"""Map of simultaneous failure mode count to recommended action.

Counts >= 3 map to "HALT" (handled by lookup logic).
"""


# =============================================================================
# SECTION 2 -- ENUMS
# =============================================================================

class FailureMode(Enum):
    """Canonical failure modes FM-01 through FM-06."""
    FM_01 = "FM-01"  # Kalman divergence (cond(P) > 1e6)
    FM_02 = "FM-02"  # Volatility spike (vol > 3x baseline)
    FM_03 = "FM-03"  # Regime oscillation (> 3 changes in window)
    FM_04 = "FM-04"  # Correlation breakdown (avg corr > 0.85)
    FM_05 = "FM-05"  # OOD detection triggered
    FM_06 = "FM-06"  # ECE calibration violation (ECE > 0.05)


# =============================================================================
# SECTION 3 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class FailureModeStatus:
    """
    Result of failure mode detection.

    Fields:
        active_modes:       Tuple of active FailureMode enums.
        severity:           Maximum severity across active modes [0, 1].
        simultaneous_count: Number of concurrently active failure modes.
        recommended_action: Action from SIMULTANEOUS_FM_RULES.
    """
    active_modes: Tuple[FailureMode, ...]
    severity: float
    simultaneous_count: int
    recommended_action: str


# =============================================================================
# SECTION 4 -- DETECTION LOGIC
# =============================================================================

def _clip(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clip value to [lo, hi] without numpy."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _resolve_action(count: int) -> str:
    """Resolve recommended action from simultaneous failure mode count."""
    if count >= 3:
        return "HALT"
    return SIMULTANEOUS_FM_RULES.get(count, "NORMAL")


def detect_failure_modes(
    kalman_condition_number: float,
    current_volatility: float,
    baseline_volatility: float,
    regime_changes_in_window: int,
    avg_correlation: float,
    ood_score: float,
    ood_threshold: float,
    current_ece: float,
) -> FailureModeStatus:
    """
    Detect active failure modes from raw numeric inputs.

    Each failure mode has a binary trigger condition and a severity score
    in [0, 1].  The overall severity is the maximum of individual
    severities.  The recommended action is determined by the number of
    simultaneously active failure modes via SIMULTANEOUS_FM_RULES.

    Args:
        kalman_condition_number: Condition number of Kalman P matrix (>= 0).
        current_volatility:     Current annualised volatility (>= 0).
        baseline_volatility:    Normal/baseline annualised volatility (> 0).
        regime_changes_in_window: Number of regime changes in lookback window (>= 0).
        avg_correlation:        Average pairwise correlation [0, 1].
        ood_score:              Out-of-distribution score (>= 0).
        ood_threshold:          Threshold for OOD detection (> 0).
        current_ece:            Expected Calibration Error (>= 0).

    Returns:
        FailureModeStatus (frozen).

    Raises:
        TypeError:  If arguments are not numeric.
        ValueError: If baseline_volatility <= 0 or ood_threshold <= 0.
    """
    # -- Validation --
    for name, val in [
        ("kalman_condition_number", kalman_condition_number),
        ("current_volatility", current_volatility),
        ("baseline_volatility", baseline_volatility),
        ("avg_correlation", avg_correlation),
        ("ood_score", ood_score),
        ("ood_threshold", ood_threshold),
        ("current_ece", current_ece),
    ]:
        if not isinstance(val, (int, float)):
            raise TypeError(
                f"{name} must be numeric, got {type(val).__name__}"
            )

    if not isinstance(regime_changes_in_window, int):
        raise TypeError(
            f"regime_changes_in_window must be int, "
            f"got {type(regime_changes_in_window).__name__}"
        )

    if baseline_volatility <= 0:
        raise ValueError(
            f"baseline_volatility must be > 0, got {baseline_volatility}"
        )
    if ood_threshold <= 0:
        raise ValueError(
            f"ood_threshold must be > 0, got {ood_threshold}"
        )

    active: list = []
    severities: list = []

    # -- FM-01: Kalman divergence --
    if kalman_condition_number > FM01_KALMAN_THRESHOLD:
        active.append(FailureMode.FM_01)
        # Severity: linear ramp from threshold to 10x threshold, capped at 1.0
        sev = _clip(
            (kalman_condition_number - FM01_KALMAN_THRESHOLD)
            / (9.0 * FM01_KALMAN_THRESHOLD)
        )
        severities.append(sev)

    # -- FM-02: Volatility spike --
    vol_ratio = current_volatility / baseline_volatility
    if vol_ratio > FM02_VOL_SPIKE_FACTOR:
        active.append(FailureMode.FM_02)
        # Severity: linear ramp from factor to 2x factor
        sev = _clip(
            (vol_ratio - FM02_VOL_SPIKE_FACTOR) / FM02_VOL_SPIKE_FACTOR
        )
        severities.append(sev)

    # -- FM-03: Regime oscillation --
    if regime_changes_in_window > FM03_REGIME_CHANGE_LIMIT:
        active.append(FailureMode.FM_03)
        # Severity: linear ramp from limit to 2x limit
        sev = _clip(
            (regime_changes_in_window - FM03_REGIME_CHANGE_LIMIT)
            / FM03_REGIME_CHANGE_LIMIT
        )
        severities.append(sev)

    # -- FM-04: Correlation breakdown --
    if avg_correlation > FM04_CORRELATION_THRESHOLD:
        active.append(FailureMode.FM_04)
        # Severity: linear ramp from threshold to 1.0
        sev = _clip(
            (avg_correlation - FM04_CORRELATION_THRESHOLD)
            / (1.0 - FM04_CORRELATION_THRESHOLD)
        )
        severities.append(sev)

    # -- FM-05: OOD detection --
    if ood_score > ood_threshold:
        active.append(FailureMode.FM_05)
        # Severity: linear ramp from threshold to 2x threshold
        sev = _clip(
            (ood_score - ood_threshold) / ood_threshold
        )
        severities.append(sev)

    # -- FM-06: ECE calibration violation --
    if current_ece > FM06_ECE_THRESHOLD:
        active.append(FailureMode.FM_06)
        # Severity: linear ramp from threshold to 5x threshold
        sev = _clip(
            (current_ece - FM06_ECE_THRESHOLD)
            / (4.0 * FM06_ECE_THRESHOLD)
        )
        severities.append(sev)

    count = len(active)
    max_severity = max(severities) if severities else 0.0

    return FailureModeStatus(
        active_modes=tuple(active),
        severity=max_severity,
        simultaneous_count=count,
        recommended_action=_resolve_action(count),
    )
