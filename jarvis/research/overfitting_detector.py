# =============================================================================
# jarvis/research/overfitting_detector.py
# Authority: FAS v6.0.1 -- S10592-10607, Overfitting Detection
# =============================================================================
#
# SCOPE
# -----
# Overfitting detection via IS/OOS Sharpe ratio comparison and parameter
# sensitivity scoring.  Generates OverfittingReport consumed by
# StrategyRegistry for registration gate checks.
#
# Public symbols:
#   PERFORMANCE_SPIKE_THRESHOLD   IS/OOS Sharpe ratio flag (3.0)
#   PARAM_SENSITIVITY_THRESHOLD   Sensitivity score flag (0.5)
#   OverfittingReport             Frozen dataclass for detection result
#   OverfittingDetector           Detector class
#
# GOVERNANCE
# ----------
# Registration BLOCKED if overfitting_flag = True.
# Sandbox results CANNOT override this verdict.
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
# DET-06  Fixed literals not parametrisable.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "PERFORMANCE_SPIKE_THRESHOLD",
    "PARAM_SENSITIVITY_THRESHOLD",
    "OverfittingReport",
    "OverfittingDetector",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

PERFORMANCE_SPIKE_THRESHOLD: float = 3.0
"""IS/OOS Sharpe ratio above this flags overfitting."""

PARAM_SENSITIVITY_THRESHOLD: float = 0.5
"""Parameter sensitivity above this flags overfitting."""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class OverfittingReport:
    """
    Overfitting detection report.

    Fields:
        strategy_id:       Strategy identifier.
        performance_spike: True if IS/OOS Sharpe > PERFORMANCE_SPIKE_THRESHOLD.
        param_sensitivity: True if sensitivity_score > PARAM_SENSITIVITY_THRESHOLD.
        overfitting_flag:  True if either check triggers.
        is_to_oos_ratio:   |IS Sharpe| / |OOS Sharpe| ratio.
        sensitivity_score: Parameter sensitivity score [0, 1].
    """
    strategy_id: str
    performance_spike: bool
    param_sensitivity: bool
    overfitting_flag: bool
    is_to_oos_ratio: float
    sensitivity_score: float


# =============================================================================
# SECTION 3 -- DETECTOR
# =============================================================================

class OverfittingDetector:
    """
    Overfitting detection engine.

    Checks two independent signals:
    1. Performance spike: IS/OOS Sharpe ratio > 3.0
    2. Parameter sensitivity: sensitivity_score > 0.5

    Either signal triggers overfitting_flag = True → blocks registration.

    Stateless: all inputs passed explicitly.
    """

    def detect(
        self,
        strategy_id: str,
        is_sharpe: float,
        oos_sharpe: float,
        param_sensitivity_score: float,
    ) -> OverfittingReport:
        """
        Detect overfitting for a strategy.

        Args:
            strategy_id:            Strategy identifier.
            is_sharpe:              In-sample Sharpe ratio.
            oos_sharpe:             Out-of-sample Sharpe ratio.
            param_sensitivity_score: Parameter sensitivity [0, 1].

        Returns:
            OverfittingReport.

        Raises:
            TypeError: If arguments have wrong types.
        """
        if not isinstance(strategy_id, str):
            raise TypeError(
                f"strategy_id must be a string, "
                f"got {type(strategy_id).__name__}"
            )
        if not isinstance(is_sharpe, (int, float)):
            raise TypeError(
                f"is_sharpe must be numeric, "
                f"got {type(is_sharpe).__name__}"
            )
        if not isinstance(oos_sharpe, (int, float)):
            raise TypeError(
                f"oos_sharpe must be numeric, "
                f"got {type(oos_sharpe).__name__}"
            )
        if not isinstance(param_sensitivity_score, (int, float)):
            raise TypeError(
                f"param_sensitivity_score must be numeric, "
                f"got {type(param_sensitivity_score).__name__}"
            )

        # Compute IS/OOS ratio with division-by-zero guard
        oos_safe = oos_sharpe if abs(oos_sharpe) > 1e-6 else 1e-6
        is_to_oos = abs(is_sharpe) / abs(oos_safe)

        # Check 1: Performance spike
        performance_spike = is_to_oos > PERFORMANCE_SPIKE_THRESHOLD

        # Check 2: Parameter sensitivity
        clipped_sensitivity = float(np.clip(param_sensitivity_score, 0.0, 1.0))
        param_sensitive = clipped_sensitivity > PARAM_SENSITIVITY_THRESHOLD

        return OverfittingReport(
            strategy_id=strategy_id,
            performance_spike=performance_spike,
            param_sensitivity=param_sensitive,
            overfitting_flag=performance_spike or param_sensitive,
            is_to_oos_ratio=float(is_to_oos),
            sensitivity_score=clipped_sensitivity,
        )

    def detect_from_segments(
        self,
        strategy_id: str,
        is_sharpes: np.ndarray,
        oos_sharpes: np.ndarray,
        param_sensitivity_score: float,
    ) -> OverfittingReport:
        """
        Detect overfitting from multiple WFV segments.

        Uses mean IS Sharpe and mean OOS Sharpe across segments.

        Args:
            strategy_id:            Strategy identifier.
            is_sharpes:             Array of per-segment IS Sharpe ratios.
            oos_sharpes:            Array of per-segment OOS Sharpe ratios.
            param_sensitivity_score: Parameter sensitivity [0, 1].

        Returns:
            OverfittingReport.

        Raises:
            TypeError: If arguments have wrong types.
            ValueError: If arrays are empty.
        """
        if not isinstance(is_sharpes, np.ndarray):
            raise TypeError(
                f"is_sharpes must be numpy ndarray, "
                f"got {type(is_sharpes).__name__}"
            )
        if not isinstance(oos_sharpes, np.ndarray):
            raise TypeError(
                f"oos_sharpes must be numpy ndarray, "
                f"got {type(oos_sharpes).__name__}"
            )
        if len(is_sharpes) == 0 or len(oos_sharpes) == 0:
            raise ValueError("Sharpe arrays must not be empty")

        mean_is = float(np.mean(is_sharpes))
        mean_oos = float(np.mean(oos_sharpes))

        return self.detect(
            strategy_id=strategy_id,
            is_sharpe=mean_is,
            oos_sharpe=mean_oos,
            param_sensitivity_score=param_sensitivity_score,
        )
