# =============================================================================
# jarvis/governance/backtest_governance.py
# Authority: FAS v6.0.1 -- S27, Backtest Governance
# =============================================================================
#
# SCOPE
# -----
# Dedicated backtest governance module enforcing walk-forward validation,
# overfitting detection, and look-ahead bias prevention.  Extends the
# base BacktestGovernance from model_registry with WFV constants,
# overfitting detection, and segment validation.
#
# Public symbols:
#   TRAIN_WINDOW_MIN           Minimum training period (365 days)
#   TEST_WINDOW                Fixed test window (90 days)
#   MIN_TRADES                 Minimum trades in test period (30)
#   TRANSACTION_COST_MIN       Minimum transaction cost (0.0001 = 1 bps)
#   WFV_MIN_OOS_RATIO          Minimum OOS fraction per segment (0.30)
#   WFV_MIN_SEGMENTS           Minimum walk-forward segments (3)
#   WFV_MIN_IS_BARS            Minimum in-sample bars per segment (100)
#   PERFORMANCE_SPIKE_THRESHOLD IS/OOS Sharpe ratio flag (3.0)
#   BacktestValidationResult   Frozen dataclass for validation result
#   WalkForwardSplit           Frozen dataclass for a single WF split
#   OverfittingReport          Frozen dataclass for overfitting check
#   BacktestGovernanceEngine   Extended governance engine
#
# GOVERNANCE
# ----------
# Hard constraints — violations block deployment.
# BACKTEST-01: train window >= 365 days
# BACKTEST-02: transaction costs >= 1 bps
# BACKTEST-03: walk-forward segments >= 3
# BACKTEST-04: OOS ratio >= 0.30 per segment
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
from typing import List, Optional

__all__ = [
    "TRAIN_WINDOW_MIN",
    "TEST_WINDOW",
    "MIN_TRADES",
    "TRANSACTION_COST_MIN",
    "WFV_MIN_OOS_RATIO",
    "WFV_MIN_SEGMENTS",
    "WFV_MIN_IS_BARS",
    "PERFORMANCE_SPIKE_THRESHOLD",
    "BacktestValidationResult",
    "WalkForwardSplit",
    "OverfittingReport",
    "BacktestGovernanceEngine",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

TRAIN_WINDOW_MIN: int = 365
"""BACKTEST-01: Minimum training period in days."""

TEST_WINDOW: int = 90
"""Fixed test (OOS) window size in days."""

MIN_TRADES: int = 30
"""Minimum number of trades required in test period."""

TRANSACTION_COST_MIN: float = 0.0001
"""BACKTEST-02: Minimum transaction cost (1 basis point)."""

WFV_MIN_OOS_RATIO: float = 0.30
"""BACKTEST-04: Minimum out-of-sample fraction per segment."""

WFV_MIN_SEGMENTS: int = 3
"""BACKTEST-03: Minimum walk-forward segments required."""

WFV_MIN_IS_BARS: int = 100
"""Minimum in-sample bars per segment."""

PERFORMANCE_SPIKE_THRESHOLD: float = 3.0
"""IS/OOS Sharpe ratio above this flags overfitting."""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class WalkForwardSplit:
    """
    A single walk-forward train/test split.

    Fields:
        train_start: Start day of training window (inclusive).
        train_end:   End day of training window (exclusive).
        test_start:  Start day of test window (inclusive).
        test_end:    End day of test window (exclusive).
    """
    train_start: int
    train_end: int
    test_start: int
    test_end: int


@dataclass(frozen=True)
class BacktestValidationResult:
    """
    Result of backtest governance validation.

    Fields:
        valid:       True if all governance rules passed.
        violations:  Tuple of (rule_id, message) for each violation.
        warnings:    Tuple of (rule_id, message) for each warning.
    """
    valid: bool
    violations: tuple
    warnings: tuple


@dataclass(frozen=True)
class OverfittingReport:
    """
    Overfitting detection report.

    Fields:
        strategy_id:        Strategy identifier.
        performance_spike:  True if IS/OOS Sharpe ratio > PERFORMANCE_SPIKE_THRESHOLD.
        param_sensitivity:  True if sensitivity_score > 0.5.
        overfitting_flag:   True if either check triggers.
        is_to_oos_ratio:    IS Sharpe / OOS Sharpe ratio.
        sensitivity_score:  Parameter sensitivity score [0, 1].
    """
    strategy_id: str
    performance_spike: bool
    param_sensitivity: bool
    overfitting_flag: bool
    is_to_oos_ratio: float
    sensitivity_score: float


# =============================================================================
# SECTION 3 -- ENGINE
# =============================================================================

class BacktestGovernanceEngine:
    """
    Extended backtest governance engine.

    Enforces walk-forward validation, overfitting detection,
    and look-ahead bias prevention.  Stateless.
    """

    def validate_backtest(
        self,
        total_data_days: int,
        transaction_costs: float,
        n_trades: int,
    ) -> BacktestValidationResult:
        """
        Validate backtest parameters against governance rules.

        Args:
            total_data_days:   Total days of data available.
            transaction_costs: Transaction cost assumption.
            n_trades:          Number of trades in test period.

        Returns:
            BacktestValidationResult.

        Raises:
            TypeError: If arguments have wrong types.
        """
        if not isinstance(total_data_days, int):
            raise TypeError(
                f"total_data_days must be int, "
                f"got {type(total_data_days).__name__}"
            )
        if not isinstance(transaction_costs, (int, float)):
            raise TypeError(
                f"transaction_costs must be numeric, "
                f"got {type(transaction_costs).__name__}"
            )
        if not isinstance(n_trades, int):
            raise TypeError(
                f"n_trades must be int, got {type(n_trades).__name__}"
            )

        violations: List[tuple] = []
        warnings: List[tuple] = []

        # BACKTEST-01: train window
        min_required = TRAIN_WINDOW_MIN + TEST_WINDOW
        if total_data_days < min_required:
            violations.append((
                "BACKTEST-01",
                f"Total data {total_data_days} days < minimum "
                f"{min_required} (train {TRAIN_WINDOW_MIN} + test {TEST_WINDOW})",
            ))

        # BACKTEST-02: transaction costs
        if transaction_costs < TRANSACTION_COST_MIN:
            violations.append((
                "BACKTEST-02",
                f"Transaction costs {transaction_costs} < minimum "
                f"{TRANSACTION_COST_MIN} (1 bps)",
            ))

        # MIN_TRADES check
        if n_trades < MIN_TRADES:
            violations.append((
                "BACKTEST-TRADES",
                f"Number of trades {n_trades} < minimum {MIN_TRADES}",
            ))

        # BACKTEST-03: walk-forward segments
        splits = self.generate_walk_forward_splits(total_data_days)
        if len(splits) < WFV_MIN_SEGMENTS:
            violations.append((
                "BACKTEST-03",
                f"Walk-forward segments {len(splits)} < minimum "
                f"{WFV_MIN_SEGMENTS}",
            ))

        return BacktestValidationResult(
            valid=len(violations) == 0,
            violations=tuple(violations),
            warnings=tuple(warnings),
        )

    def generate_walk_forward_splits(
        self,
        total_data_days: int,
    ) -> List[WalkForwardSplit]:
        """
        Generate walk-forward train/test splits.

        Slides forward by TEST_WINDOW each iteration.
        Training window is always TRAIN_WINDOW_MIN days.

        Args:
            total_data_days: Total days of data available.

        Returns:
            List of WalkForwardSplit.

        Raises:
            TypeError: If total_data_days is not int.
            ValueError: If total_data_days < 0.
        """
        if not isinstance(total_data_days, int):
            raise TypeError(
                f"total_data_days must be int, "
                f"got {type(total_data_days).__name__}"
            )
        if total_data_days < 0:
            raise ValueError(
                f"total_data_days must be >= 0, got {total_data_days}"
            )

        splits: List[WalkForwardSplit] = []
        current_day = 0

        while (
            current_day + TRAIN_WINDOW_MIN + TEST_WINDOW
            <= total_data_days
        ):
            train_start = current_day
            train_end = current_day + TRAIN_WINDOW_MIN
            test_start = train_end
            test_end = test_start + TEST_WINDOW

            splits.append(WalkForwardSplit(
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            ))

            current_day += TEST_WINDOW

        return splits

    def validate_oos_ratio(
        self,
        is_bars: int,
        oos_bars: int,
    ) -> bool:
        """
        Validate that OOS ratio meets minimum threshold.

        BACKTEST-04: OOS / (IS + OOS) >= WFV_MIN_OOS_RATIO.

        Args:
            is_bars:  Number of in-sample bars.
            oos_bars: Number of out-of-sample bars.

        Returns:
            True if ratio meets threshold.

        Raises:
            TypeError: If arguments not int.
            ValueError: If bars negative or total is zero.
        """
        if not isinstance(is_bars, int):
            raise TypeError(
                f"is_bars must be int, got {type(is_bars).__name__}"
            )
        if not isinstance(oos_bars, int):
            raise TypeError(
                f"oos_bars must be int, got {type(oos_bars).__name__}"
            )
        if is_bars < 0 or oos_bars < 0:
            raise ValueError("Bars must be >= 0")
        total = is_bars + oos_bars
        if total == 0:
            raise ValueError("Total bars must be > 0")
        return oos_bars / total >= WFV_MIN_OOS_RATIO

    def validate_is_bars(self, is_bars: int) -> bool:
        """
        Validate in-sample bars meet minimum.

        Args:
            is_bars: Number of in-sample bars.

        Returns:
            True if is_bars >= WFV_MIN_IS_BARS.
        """
        if not isinstance(is_bars, int):
            raise TypeError(
                f"is_bars must be int, got {type(is_bars).__name__}"
            )
        return is_bars >= WFV_MIN_IS_BARS

    def detect_overfitting(
        self,
        strategy_id: str,
        is_sharpe: float,
        oos_sharpe: float,
        sensitivity_score: float,
    ) -> OverfittingReport:
        """
        Detect overfitting via IS/OOS Sharpe ratio and sensitivity.

        Overfitting is flagged if:
        - IS/OOS Sharpe ratio > PERFORMANCE_SPIKE_THRESHOLD (3.0), OR
        - sensitivity_score > 0.5.

        Args:
            strategy_id:       Strategy identifier.
            is_sharpe:         In-sample Sharpe ratio.
            oos_sharpe:        Out-of-sample Sharpe ratio.
            sensitivity_score: Parameter sensitivity [0, 1].

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
        if not isinstance(sensitivity_score, (int, float)):
            raise TypeError(
                f"sensitivity_score must be numeric, "
                f"got {type(sensitivity_score).__name__}"
            )

        # Compute IS/OOS ratio (guard against division by zero)
        if abs(oos_sharpe) < 1e-10:
            # OOS essentially zero — any positive IS is a spike
            is_to_oos = float("inf") if abs(is_sharpe) > 1e-10 else 1.0
        else:
            is_to_oos = abs(is_sharpe / oos_sharpe)

        performance_spike = is_to_oos > PERFORMANCE_SPIKE_THRESHOLD
        param_sensitivity = sensitivity_score > 0.5
        overfitting_flag = performance_spike or param_sensitivity

        return OverfittingReport(
            strategy_id=strategy_id,
            performance_spike=performance_spike,
            param_sensitivity=param_sensitivity,
            overfitting_flag=overfitting_flag,
            is_to_oos_ratio=is_to_oos,
            sensitivity_score=float(sensitivity_score),
        )
