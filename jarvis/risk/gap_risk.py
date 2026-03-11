# =============================================================================
# jarvis/risk/gap_risk.py -- Gap Risk Model (Phase MA-5)
#
# Estimates gap risk for session-based markets (indices, commodities, rates).
# 24/7 markets (crypto) and near-24h markets (forex) return zero gap risk.
#
# Gap = (Open - PrevClose) / PrevClose, computed from price series.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   gap_risk.py -> jarvis.core.regime (AssetClass)
#   gap_risk.py -> jarvis.core.data_layer (GAP_THRESHOLDS)
#   gap_risk.py -> (stdlib + math only)
#
# DETERMINISM GUARANTEES: DET-01 through DET-07 enforced.
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly.
#   DET-03  No side effects.
#   DET-05  Same inputs -> same outputs.
#   DET-06  Fixed literals not parameterizable.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01: No numpy, no scipy. Pure stdlib math.
#   PROHIBITED-02: No file I/O.
#   PROHIBITED-03: No logging/print.
#   PROHIBITED-05: No global mutable state.
#   PROHIBITED-08: No new Enum definitions.
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from jarvis.core.regime import AssetClass
from jarvis.core.data_layer import GAP_THRESHOLDS


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

# Asset classes with session-based trading (gaps possible)
GAP_ENABLED_CLASSES: frozenset = frozenset({
    AssetClass.INDICES,
    AssetClass.COMMODITIES,
    AssetClass.RATES,
})

# Worst-case gap multiplier (3-sigma)
WORST_CASE_GAP_SIGMA: float = 3.0

# Portfolio gap risk recommendation threshold (5% of total notional)
GAP_RISK_RECOMMENDATION_THRESHOLD: float = 0.05


# =============================================================================
# SECTION 2 -- RESULT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class AssetGapRiskResult:
    """Gap risk result for a single asset.

    Attributes:
        symbol: Asset symbol.
        asset_class: Asset class.
        gap_enabled: Whether gap detection is enabled for this asset class.
        num_gaps: Number of gaps detected in the price series.
        mean_gap: Mean absolute gap size (fraction).
        std_gap: Standard deviation of gaps (fraction).
        expected_gap_risk: Expected gap risk in currency units (1-sigma).
        worst_case_gap_risk: Worst-case gap risk (3-sigma).
        notional: Position notional value.
    """
    symbol: str
    asset_class: AssetClass
    gap_enabled: bool
    num_gaps: int
    mean_gap: float
    std_gap: float
    expected_gap_risk: float
    worst_case_gap_risk: float
    notional: float


@dataclass(frozen=True)
class PortfolioGapRiskResult:
    """Portfolio-level gap risk result.

    Attributes:
        total_expected_gap_risk: Sum of expected gap risks across assets.
        total_worst_case_gap_risk: Sum of worst-case gap risks.
        total_notional: Total portfolio notional.
        gap_risk_ratio: total_expected / total_notional.
        recommendation: Human-readable recommendation.
        asset_results: Per-asset gap risk results.
        num_gap_exposed_assets: Number of assets with gap risk enabled.
        result_hash: SHA-256[:16] for determinism verification.
    """
    total_expected_gap_risk: float
    total_worst_case_gap_risk: float
    total_notional: float
    gap_risk_ratio: float
    recommendation: str
    asset_results: Tuple[AssetGapRiskResult, ...]
    num_gap_exposed_assets: int
    result_hash: str


# =============================================================================
# SECTION 3 -- PURE MATH HELPERS (stdlib only, DET-01)
# =============================================================================

def _compute_gaps(prices: List[float]) -> List[float]:
    """Compute overnight gaps from a price series.

    Gap = (Open_t - Close_{t-1}) / Close_{t-1}
    For daily prices, this is simply (price[i] - price[i-1]) / price[i-1].

    Args:
        prices: Daily price series (at least 2 elements).

    Returns:
        List of gap fractions (can be positive or negative).
    """
    if len(prices) < 2:
        return []

    gaps = []
    for i in range(1, len(prices)):
        if prices[i - 1] > 0.0:
            gap = (prices[i] - prices[i - 1]) / prices[i - 1]
            gaps.append(gap)
    return gaps


def _filter_significant_gaps(
    gaps: List[float],
    threshold: float,
) -> List[float]:
    """Filter gaps exceeding the asset-specific threshold.

    Args:
        gaps: All computed gaps.
        threshold: Minimum absolute gap size to be considered significant.

    Returns:
        List of significant gaps (absolute value >= threshold).
    """
    return [g for g in gaps if abs(g) >= threshold]


def _gap_statistics(gaps: List[float]) -> Tuple[float, float]:
    """Compute mean absolute gap and standard deviation.

    Args:
        gaps: List of significant gaps.

    Returns:
        (mean_abs_gap, std_gap). Both 0.0 if no gaps.
    """
    if not gaps:
        return 0.0, 0.0

    abs_gaps = [abs(g) for g in gaps]
    n = len(abs_gaps)
    mean_gap = sum(abs_gaps) / n

    if n < 2:
        return mean_gap, 0.0

    var_sum = sum((g - mean_gap) ** 2 for g in abs_gaps) / (n - 1)
    std_gap = math.sqrt(max(var_sum, 0.0))

    return mean_gap, std_gap


# =============================================================================
# SECTION 4 -- GAP RISK MODEL
# =============================================================================

class GapRiskModel:
    """Portfolio-level gap risk estimation for session-based markets.

    Gap risk is only relevant for markets with trading sessions (indices,
    commodities, rates). 24/7 markets (crypto) and near-24h markets (forex)
    have negligible gap risk and return zero.

    Deterministic: no sampling (DET-01, PROHIBITED-01).
    All inputs are explicit parameters (DET-02).
    No internal state retained between calls (DET-03, PROHIBITED-05).
    """

    def estimate(
        self,
        *,
        positions: Dict[str, Tuple[AssetClass, float, float]],
        price_histories: Dict[str, List[float]],
    ) -> PortfolioGapRiskResult:
        """Estimate gap risk for portfolio.

        Args:
            positions: Dict mapping symbol -> (asset_class, price, size).
            price_histories: Dict mapping symbol -> daily price series.

        Returns:
            PortfolioGapRiskResult with per-asset and portfolio gap risk.
        """
        asset_results = []
        total_notional = 0.0

        for symbol, (asset_class, price, size) in positions.items():
            notional = abs(price * size)
            total_notional += notional

            prices = price_histories.get(symbol, [])
            result = self._estimate_asset_gap_risk(
                symbol=symbol,
                asset_class=asset_class,
                notional=notional,
                prices=prices,
            )
            asset_results.append(result)

        total_expected = sum(r.expected_gap_risk for r in asset_results)
        total_worst = sum(r.worst_case_gap_risk for r in asset_results)
        num_exposed = sum(1 for r in asset_results if r.gap_enabled)

        gap_ratio = total_expected / total_notional if total_notional > 0.0 else 0.0

        if gap_ratio > GAP_RISK_RECOMMENDATION_THRESHOLD:
            recommendation = "REDUCE_GAP_EXPOSURE"
        elif gap_ratio > GAP_RISK_RECOMMENDATION_THRESHOLD * 0.5:
            recommendation = "MONITOR_GAP_RISK"
        else:
            recommendation = "GAP_RISK_ACCEPTABLE"

        # Sort for deterministic ordering
        asset_results_sorted = tuple(sorted(asset_results, key=lambda r: r.symbol))

        payload = {
            "total_expected": round(total_expected, 8),
            "total_worst": round(total_worst, 8),
            "total_notional": round(total_notional, 8),
            "gap_ratio": round(gap_ratio, 8),
            "num_exposed": num_exposed,
        }
        result_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]

        return PortfolioGapRiskResult(
            total_expected_gap_risk=total_expected,
            total_worst_case_gap_risk=total_worst,
            total_notional=total_notional,
            gap_risk_ratio=gap_ratio,
            recommendation=recommendation,
            asset_results=asset_results_sorted,
            num_gap_exposed_assets=num_exposed,
            result_hash=result_hash,
        )

    def _estimate_asset_gap_risk(
        self,
        *,
        symbol: str,
        asset_class: AssetClass,
        notional: float,
        prices: List[float],
    ) -> AssetGapRiskResult:
        """Estimate gap risk for a single asset.

        Args:
            symbol: Asset symbol.
            asset_class: Asset class enum.
            notional: Position notional value.
            prices: Daily price series.

        Returns:
            AssetGapRiskResult.
        """
        gap_enabled = asset_class in GAP_ENABLED_CLASSES

        if not gap_enabled:
            return AssetGapRiskResult(
                symbol=symbol,
                asset_class=asset_class,
                gap_enabled=False,
                num_gaps=0,
                mean_gap=0.0,
                std_gap=0.0,
                expected_gap_risk=0.0,
                worst_case_gap_risk=0.0,
                notional=notional,
            )

        # Compute gaps from price series
        all_gaps = _compute_gaps(prices)

        # Filter by asset-specific threshold
        threshold = GAP_THRESHOLDS.get(asset_class.value, 0.02)
        significant_gaps = _filter_significant_gaps(all_gaps, threshold)

        # Gap statistics
        mean_gap, std_gap = _gap_statistics(significant_gaps)

        # Risk in currency units
        # Expected = notional * std_gap (1-sigma move)
        # If no significant gaps found, use mean_gap as fallback
        risk_factor = std_gap if std_gap > 0.0 else mean_gap
        expected_gap_risk = notional * risk_factor
        worst_case_gap_risk = notional * risk_factor * WORST_CASE_GAP_SIGMA

        return AssetGapRiskResult(
            symbol=symbol,
            asset_class=asset_class,
            gap_enabled=True,
            num_gaps=len(significant_gaps),
            mean_gap=mean_gap,
            std_gap=std_gap,
            expected_gap_risk=expected_gap_risk,
            worst_case_gap_risk=worst_case_gap_risk,
            notional=notional,
        )
