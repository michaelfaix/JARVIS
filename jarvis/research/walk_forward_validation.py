# =============================================================================
# jarvis/research/walk_forward_validation.py
# Authority: FAS v6.0.1 -- S10340-10537, Walk-Forward Validation
# =============================================================================
#
# SCOPE
# -----
# Walk-forward validation engine.  Splits historical returns into
# IS/OOS segments, computes per-segment Sharpe ratios, derives a
# stability score, and evaluates cross-asset robustness.
#
# Public symbols:
#   WFV_MIN_OOS_RATIO             Minimum OOS fraction per segment (0.30)
#   WFV_MIN_SEGMENTS              Minimum walk-forward segments (3)
#   WFV_MIN_IS_BARS               Minimum in-sample bars per segment (100)
#   CROSS_ASSET_MIN_POSITIVE      Min asset classes with positive OOS Sharpe (2)
#   ROBUSTNESS_PENALTY            Weight posterior penalty on failure (0.5)
#   WalkForwardSegment            Frozen dataclass per segment
#   WalkForwardResult             Frozen dataclass for full WFV result
#   CrossAssetRobustnessScore     Frozen dataclass for cross-asset check
#   WalkForwardValidationEngine   Engine class
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, typing, math
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
from typing import Dict, List, Optional

import numpy as np

__all__ = [
    "WFV_MIN_OOS_RATIO",
    "WFV_MIN_SEGMENTS",
    "WFV_MIN_IS_BARS",
    "CROSS_ASSET_MIN_POSITIVE",
    "ROBUSTNESS_PENALTY",
    "WalkForwardSegment",
    "WalkForwardResult",
    "CrossAssetRobustnessScore",
    "WalkForwardValidationEngine",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

WFV_MIN_OOS_RATIO: float = 0.30
"""Minimum out-of-sample fraction per segment."""

WFV_MIN_SEGMENTS: int = 3
"""Minimum walk-forward segments required."""

WFV_MIN_IS_BARS: int = 100
"""Minimum in-sample bars per segment."""

CROSS_ASSET_MIN_POSITIVE: int = 2
"""Minimum asset classes with positive OOS Sharpe."""

ROBUSTNESS_PENALTY: float = 0.5
"""Weight posterior penalty when robustness check fails."""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class WalkForwardSegment:
    """
    A single walk-forward IS/OOS segment.

    Fields:
        segment_id: Zero-based segment index.
        is_start:   In-sample bar index start (inclusive).
        is_end:     In-sample bar index end (exclusive).
        oos_start:  Out-of-sample bar index start (inclusive).
        oos_end:    Out-of-sample bar index end (exclusive).
        is_sharpe:  In-sample Sharpe ratio (annualized).
        oos_sharpe: Out-of-sample Sharpe ratio (annualized).
        oos_ratio:  OOS bars / total bars for this segment.
    """
    segment_id: int
    is_start: int
    is_end: int
    oos_start: int
    oos_end: int
    is_sharpe: float
    oos_sharpe: float
    oos_ratio: float


@dataclass(frozen=True)
class WalkForwardResult:
    """
    Full walk-forward validation result.

    Fields:
        strategy_id:     Strategy identifier.
        n_segments:      Number of segments generated.
        segments:        Tuple of WalkForwardSegment.
        mean_oos_sharpe: Mean OOS Sharpe across segments.
        std_oos_sharpe:  Std dev of OOS Sharpes.
        stability_score: 1 - (std/max(|mean|, 0.01)), clipped to [0, 1].
        wfv_passed:      False = hard failure, blocks registration.
        failure_reason:  Non-None if wfv_passed is False.
    """
    strategy_id: str
    n_segments: int
    segments: tuple
    mean_oos_sharpe: float
    std_oos_sharpe: float
    stability_score: float
    wfv_passed: bool
    failure_reason: Optional[str]


@dataclass(frozen=True)
class CrossAssetRobustnessScore:
    """
    Cross-asset robustness evaluation.

    Fields:
        strategy_id:         Strategy identifier.
        asset_classes_tested: Tuple of asset class names tested.
        oos_sharpe_by_class:  Tuple of (class_name, sharpe) pairs.
        classes_positive:     Count of classes with OOS Sharpe > 0.
        robustness_passed:    True if classes_positive >= CROSS_ASSET_MIN_POSITIVE.
        penalty_multiplier:   1.0 if passed, ROBUSTNESS_PENALTY if failed.
    """
    strategy_id: str
    asset_classes_tested: tuple
    oos_sharpe_by_class: tuple
    classes_positive: int
    robustness_passed: bool
    penalty_multiplier: float


# =============================================================================
# SECTION 3 -- ENGINE
# =============================================================================

class WalkForwardValidationEngine:
    """
    Walk-forward validation engine.

    Splits returns into IS/OOS segments, computes Sharpe ratios,
    derives stability scores, and evaluates cross-asset robustness.

    Stateless: all inputs passed explicitly.
    """

    def validate(
        self,
        strategy_id: str,
        returns: np.ndarray,
        n_segments: int = 5,
    ) -> WalkForwardResult:
        """
        Run walk-forward validation on a return series.

        Args:
            strategy_id: Strategy identifier.
            returns:     Full historical return series (1-D numpy array).
            n_segments:  Number of segments (default 5, minimum WFV_MIN_SEGMENTS).

        Returns:
            WalkForwardResult.

        Raises:
            TypeError:  If arguments have wrong types.
            ValueError: If n_segments < WFV_MIN_SEGMENTS or insufficient data.
        """
        if not isinstance(strategy_id, str):
            raise TypeError(
                f"strategy_id must be a string, "
                f"got {type(strategy_id).__name__}"
            )
        if not isinstance(returns, np.ndarray):
            raise TypeError(
                f"returns must be a numpy ndarray, "
                f"got {type(returns).__name__}"
            )
        if not isinstance(n_segments, int):
            raise TypeError(
                f"n_segments must be int, "
                f"got {type(n_segments).__name__}"
            )
        if n_segments < WFV_MIN_SEGMENTS:
            raise ValueError(
                f"n_segments {n_segments} < minimum {WFV_MIN_SEGMENTS}"
            )

        n = len(returns)
        min_required = n_segments * WFV_MIN_IS_BARS * 2
        if n < min_required:
            raise ValueError(
                f"Insufficient data: {n} bars < minimum "
                f"{min_required} for {n_segments} segments"
            )

        seg_size = n // n_segments
        oos_size = max(1, int(seg_size * WFV_MIN_OOS_RATIO))
        is_size = seg_size - oos_size

        segments: List[WalkForwardSegment] = []
        failure_reasons: List[str] = []

        for k in range(n_segments):
            start = k * seg_size
            is_start = start
            is_end = start + is_size
            oos_start = is_end
            oos_end = min(start + seg_size, n)

            is_ret = returns[is_start:is_end]
            oos_ret = returns[oos_start:oos_end]

            is_sharpe = self._sharpe(is_ret)
            oos_sharpe = self._sharpe(oos_ret)

            total_bars = len(is_ret) + len(oos_ret)
            oos_ratio = len(oos_ret) / max(total_bars, 1)

            if oos_ratio < WFV_MIN_OOS_RATIO:
                failure_reasons.append(
                    f"Segment {k}: oos_ratio {oos_ratio:.3f} "
                    f"< {WFV_MIN_OOS_RATIO}"
                )

            if len(is_ret) < WFV_MIN_IS_BARS:
                failure_reasons.append(
                    f"Segment {k}: is_bars {len(is_ret)} "
                    f"< {WFV_MIN_IS_BARS}"
                )

            segments.append(WalkForwardSegment(
                segment_id=k,
                is_start=is_start,
                is_end=is_end,
                oos_start=oos_start,
                oos_end=oos_end,
                is_sharpe=is_sharpe,
                oos_sharpe=oos_sharpe,
                oos_ratio=oos_ratio,
            ))

        oos_sharpes = np.array([s.oos_sharpe for s in segments])
        mean_oos = float(np.mean(oos_sharpes))
        std_oos = float(np.std(oos_sharpes))

        # Stability score: 1 - (std / max(|mean|, 0.01)), clipped [0, 1]
        stability = max(0.0, 1.0 - (std_oos / max(abs(mean_oos), 0.01)))
        stability = float(np.clip(stability, 0.0, 1.0))

        wfv_passed = len(failure_reasons) == 0
        failure_reason = "; ".join(failure_reasons) if failure_reasons else None

        return WalkForwardResult(
            strategy_id=strategy_id,
            n_segments=n_segments,
            segments=tuple(segments),
            mean_oos_sharpe=mean_oos,
            std_oos_sharpe=std_oos,
            stability_score=stability,
            wfv_passed=wfv_passed,
            failure_reason=failure_reason,
        )

    def cross_asset_robustness(
        self,
        strategy_id: str,
        returns_by_class: Dict[str, np.ndarray],
    ) -> CrossAssetRobustnessScore:
        """
        Evaluate cross-asset robustness.

        Strategy must show positive Sharpe in >= CROSS_ASSET_MIN_POSITIVE
        asset classes.  Otherwise penalty_multiplier = ROBUSTNESS_PENALTY.

        Args:
            strategy_id:      Strategy identifier.
            returns_by_class: Dict mapping asset class name to return array.

        Returns:
            CrossAssetRobustnessScore.

        Raises:
            TypeError: If arguments have wrong types.
        """
        if not isinstance(strategy_id, str):
            raise TypeError(
                f"strategy_id must be a string, "
                f"got {type(strategy_id).__name__}"
            )
        if not isinstance(returns_by_class, dict):
            raise TypeError(
                f"returns_by_class must be a dict, "
                f"got {type(returns_by_class).__name__}"
            )

        sharpe_by_class: List[tuple] = []
        classes_positive = 0

        for class_name in sorted(returns_by_class.keys()):
            ret = returns_by_class[class_name]
            if not isinstance(ret, np.ndarray):
                raise TypeError(
                    f"returns for '{class_name}' must be numpy ndarray, "
                    f"got {type(ret).__name__}"
                )
            s = self._sharpe(ret)
            sharpe_by_class.append((class_name, s))
            if s > 0.0:
                classes_positive += 1

        robustness_passed = classes_positive >= CROSS_ASSET_MIN_POSITIVE
        penalty = 1.0 if robustness_passed else ROBUSTNESS_PENALTY

        return CrossAssetRobustnessScore(
            strategy_id=strategy_id,
            asset_classes_tested=tuple(sorted(returns_by_class.keys())),
            oos_sharpe_by_class=tuple(sharpe_by_class),
            classes_positive=classes_positive,
            robustness_passed=robustness_passed,
            penalty_multiplier=penalty,
        )

    def _sharpe(
        self,
        returns: np.ndarray,
        risk_free: float = 0.0,
    ) -> float:
        """
        Compute annualized Sharpe ratio.

        Args:
            returns:   Return series.
            risk_free: Annual risk-free rate (default 0.0).

        Returns:
            Annualized Sharpe ratio.  0.0 if insufficient data or zero std.
        """
        if len(returns) < 2:
            return 0.0
        excess = returns - risk_free / 252.0
        std = float(np.std(excess))
        if std < 1e-10:
            return 0.0
        return float(np.mean(excess) / std * np.sqrt(252.0))
