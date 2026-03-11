# jarvis/portfolio/multi_asset_allocator.py
# Version: 1.0.0
# Multi-asset capital allocation with diversification benefits.
# Complements jarvis/portfolio/portfolio_allocator.py (single-exposure equal-weight).
#
# DETERMINISM GUARANTEE:
#   No stochastic operations. No random number generation. No sampling.
#   No external state reads. No side effects. No file I/O. No logging.
#   No environment variable access. No global mutable state.
#   Output is a pure function of inputs.
#
# Standard import pattern:
#   from jarvis.portfolio.multi_asset_allocator import (
#       MultiAssetCapitalAllocator, AllocationResult,
#   )

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math

from jarvis.core.regime import GlobalRegimeState


__all__ = [
    "AllocationResult",
    "MultiAssetCapitalAllocator",
]


# ---------------------------------------------------------------------------
# FIXED LITERALS (DET-06: not parameterizable)
# ---------------------------------------------------------------------------

# Regime weight multipliers applied to total allocation.
_REGIME_WEIGHT_MULTIPLIER: Dict[GlobalRegimeState, float] = {
    GlobalRegimeState.RISK_ON:    1.0,
    GlobalRegimeState.RISK_OFF:   0.7,
    GlobalRegimeState.TRANSITION: 0.85,
    GlobalRegimeState.CRISIS:     0.5,
    GlobalRegimeState.UNKNOWN:    0.6,
}

# Correlation threshold above which assets are considered highly correlated.
_HIGH_CORRELATION_THRESHOLD: float = 0.7

# Penalty multiplier applied to the smaller allocation in a highly correlated pair.
_CORRELATION_PENALTY: float = 0.7

# Volatility scaling factors for cross-asset normalization.
# Crypto is baseline (1.0). Lower values = less volatile asset class.
# Canonical source: jarvis/core/data_structures.py VOLATILITY_SCALING
_VOLATILITY_SCALING: Dict[str, float] = {
    "crypto":      1.0,
    "forex":       0.3,
    "indices":     0.6,
    "commodities": 0.8,
    "rates":       0.25,
}

# Diversification benefit threshold for leverage bonus (FAS LAYER 9).
_DIVERSIFICATION_LEVERAGE_THRESHOLD: float = 0.2

# Leverage multiplier scale factor applied when diversification benefit exceeds threshold.
_DIVERSIFICATION_LEVERAGE_SCALE: float = 0.5


# ---------------------------------------------------------------------------
# RESULT DATACLASS
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AllocationResult:
    """
    Immutable result of multi-asset capital allocation.

    Attributes
    ----------
    allocations : dict[str, float]
        Mapping of asset name to allocated capital amount.
    diversification_benefit : float
        Fraction of risk reduction from diversification, in [0.0, 1.0].
        1.0 = perfectly uncorrelated (maximum benefit).
        0.0 = perfectly correlated (no benefit).
    total_exposure : float
        Sum of final asset weights after all adjustments, in [0.0, 1.0].
    asset_weights : dict[str, float]
        Mapping of asset name to final portfolio weight (fraction of capital).
    regime_adjustments : dict[str, float]
        Mapping of asset name to the regime adjustment factor applied.
    """
    allocations: Dict[str, float]
    diversification_benefit: float
    total_exposure: float
    asset_weights: Dict[str, float]
    regime_adjustments: Dict[str, float]


# ---------------------------------------------------------------------------
# ALLOCATOR
# ---------------------------------------------------------------------------

class MultiAssetCapitalAllocator:
    """
    Multi-asset capital allocator with diversification benefits.

    Provides correlation-weighted allocation, regime-based adjustment,
    per-asset-class volatility normalization, and diversification benefit
    calculation per FAS LAYER 9 specification.

    DETERMINISM: All methods are pure functions of their inputs.
    No internal mutable state is retained between calls.

    Usage
    -----
    >>> allocator = MultiAssetCapitalAllocator()
    >>> result = allocator.allocate(
    ...     total_capital=100_000.0,
    ...     asset_exposures={"BTC": 0.4, "SPY": 0.3, "EUR_USD": 0.3},
    ...     asset_classes={"BTC": "crypto", "SPY": "indices", "EUR_USD": "forex"},
    ...     correlation_matrix={"BTC": {"BTC": 1.0, "SPY": 0.3, "EUR_USD": 0.1}, ...},
    ...     current_regime=GlobalRegimeState.RISK_ON,
    ... )
    """

    def allocate(
        self,
        total_capital: float,
        asset_exposures: Dict[str, float],
        asset_classes: Dict[str, str],
        correlation_matrix: Dict[str, Dict[str, float]],
        current_regime: GlobalRegimeState,
    ) -> AllocationResult:
        """
        Compute multi-asset capital allocation with diversification benefits.

        Parameters
        ----------
        total_capital : float
            Total portfolio capital. Must be >= 0.0.
        asset_exposures : dict[str, float]
            Mapping of asset name to desired exposure weight in [0.0, 1.0].
            May be empty (returns zero allocation).
        asset_classes : dict[str, str]
            Mapping of asset name to asset class string.
            Must contain all keys from asset_exposures.
            Valid classes: "crypto", "forex", "indices", "commodities", "rates".
        correlation_matrix : dict[str, dict[str, float]]
            Pairwise correlation matrix as nested dict.
            Must be symmetric and contain all asset pairs.
            Diagonal entries must be 1.0. Off-diagonal in [-1.0, 1.0].
        current_regime : GlobalRegimeState
            Current macro regime state. Must be a GlobalRegimeState enum.

        Returns
        -------
        AllocationResult
            Frozen dataclass with allocation details.

        Raises
        ------
        ValueError
            If total_capital < 0.
            If current_regime is not a GlobalRegimeState instance.
            If any exposure is outside [0.0, 1.0].
            If any asset class is invalid.
            If correlation matrix is inconsistent with assets.
        """
        # ---------------------------------------------------------------
        # 1. Input validation
        # ---------------------------------------------------------------
        self._validate_inputs(
            total_capital, asset_exposures, asset_classes,
            correlation_matrix, current_regime,
        )

        # ---------------------------------------------------------------
        # 2. Handle empty / zero-capital edge cases
        # ---------------------------------------------------------------
        if not asset_exposures or total_capital == 0.0:
            return AllocationResult(
                allocations={},
                diversification_benefit=0.0,
                total_exposure=0.0,
                asset_weights={},
                regime_adjustments={},
            )

        assets = sorted(asset_exposures.keys())

        # ---------------------------------------------------------------
        # 3. Volatility normalization
        # ---------------------------------------------------------------
        vol_normalized_exposures = self._normalize_by_volatility(
            asset_exposures, asset_classes,
        )

        # ---------------------------------------------------------------
        # 4. Correlation-weighted adjustment
        # ---------------------------------------------------------------
        corr_adjusted_exposures = self._adjust_for_correlation(
            vol_normalized_exposures, correlation_matrix,
        )

        # ---------------------------------------------------------------
        # 5. Regime-based weight adjustment
        # ---------------------------------------------------------------
        regime_multiplier = _REGIME_WEIGHT_MULTIPLIER[current_regime]
        regime_adjusted: Dict[str, float] = {
            asset: exposure * regime_multiplier
            for asset, exposure in corr_adjusted_exposures.items()
        }
        regime_adjustments: Dict[str, float] = {
            asset: regime_multiplier for asset in assets
        }

        # ---------------------------------------------------------------
        # 6. Diversification benefit calculation
        # ---------------------------------------------------------------
        diversification_benefit = self._calculate_diversification_benefit(
            regime_adjusted, correlation_matrix,
        )

        # ---------------------------------------------------------------
        # 7. Apply diversification leverage bonus (FAS LAYER 9)
        # ---------------------------------------------------------------
        if diversification_benefit > _DIVERSIFICATION_LEVERAGE_THRESHOLD:
            leverage_multiplier = 1.0 + (
                diversification_benefit * _DIVERSIFICATION_LEVERAGE_SCALE
            )
            final_exposures = {
                asset: exposure * leverage_multiplier
                for asset, exposure in regime_adjusted.items()
            }
        else:
            final_exposures = dict(regime_adjusted)

        # ---------------------------------------------------------------
        # 8. Enforce total exposure <= 1.0
        # ---------------------------------------------------------------
        total_weight = sum(final_exposures.values())
        if total_weight > 1.0:
            scale = 1.0 / total_weight
            final_exposures = {
                asset: w * scale for asset, w in final_exposures.items()
            }
            total_weight = sum(final_exposures.values())

        # ---------------------------------------------------------------
        # 9. Compute capital allocations
        # ---------------------------------------------------------------
        allocations: Dict[str, float] = {
            asset: total_capital * weight
            for asset, weight in final_exposures.items()
        }

        return AllocationResult(
            allocations=allocations,
            diversification_benefit=diversification_benefit,
            total_exposure=total_weight,
            asset_weights=final_exposures,
            regime_adjustments=regime_adjustments,
        )

    # -------------------------------------------------------------------
    # PRIVATE METHODS
    # -------------------------------------------------------------------

    @staticmethod
    def _validate_inputs(
        total_capital: float,
        asset_exposures: Dict[str, float],
        asset_classes: Dict[str, str],
        correlation_matrix: Dict[str, Dict[str, float]],
        current_regime: GlobalRegimeState,
    ) -> None:
        """Validate all inputs. Raises ValueError on violation."""
        if not isinstance(current_regime, GlobalRegimeState):
            raise ValueError(
                f"current_regime must be a GlobalRegimeState instance. "
                f"Received: {type(current_regime).__name__}"
            )

        if total_capital < 0.0:
            raise ValueError(
                f"total_capital must be >= 0.0. Received: {total_capital}"
            )

        for asset, exposure in asset_exposures.items():
            if exposure < 0.0 or exposure > 1.0:
                raise ValueError(
                    f"Exposure for '{asset}' must be in [0.0, 1.0]. "
                    f"Received: {exposure}"
                )

        for asset in asset_exposures:
            if asset not in asset_classes:
                raise ValueError(
                    f"Asset '{asset}' is in asset_exposures but missing "
                    f"from asset_classes."
                )
            ac = asset_classes[asset]
            if ac not in _VOLATILITY_SCALING:
                raise ValueError(
                    f"Asset class '{ac}' for asset '{asset}' is not valid. "
                    f"Valid classes: {sorted(_VOLATILITY_SCALING.keys())}"
                )

        # Validate correlation matrix structure
        for asset in asset_exposures:
            if asset not in correlation_matrix:
                raise ValueError(
                    f"Asset '{asset}' missing from correlation_matrix."
                )
            for other_asset in asset_exposures:
                if other_asset not in correlation_matrix[asset]:
                    raise ValueError(
                        f"Correlation between '{asset}' and '{other_asset}' "
                        f"missing from correlation_matrix."
                    )

    @staticmethod
    def _normalize_by_volatility(
        asset_exposures: Dict[str, float],
        asset_classes: Dict[str, str],
    ) -> Dict[str, float]:
        """
        Normalize exposures by asset-class volatility scaling.

        Higher-volatility asset classes get proportionally smaller exposures
        to equalize risk contribution. Lower-volatility classes get larger.

        The normalization uses inverse volatility scaling:
            adjusted_i = exposure_i * (1 / vol_scale_i)
        Then re-normalized so total matches original total exposure.
        """
        if not asset_exposures:
            return {}

        original_total = sum(asset_exposures.values())
        if original_total == 0.0:
            return {asset: 0.0 for asset in asset_exposures}

        # Inverse-volatility weighting
        inv_vol_exposures: Dict[str, float] = {}
        for asset, exposure in asset_exposures.items():
            vol_scale = _VOLATILITY_SCALING[asset_classes[asset]]
            # Inverse vol: lower vol assets get higher weight
            inv_vol = 1.0 / vol_scale if vol_scale > 0.0 else 1.0
            inv_vol_exposures[asset] = exposure * inv_vol

        # Re-normalize to preserve original total exposure
        adjusted_total = sum(inv_vol_exposures.values())
        if adjusted_total == 0.0:
            return {asset: 0.0 for asset in asset_exposures}

        scale = original_total / adjusted_total
        return {
            asset: val * scale for asset, val in inv_vol_exposures.items()
        }

    @staticmethod
    def _adjust_for_correlation(
        exposures: Dict[str, float],
        correlation_matrix: Dict[str, Dict[str, float]],
    ) -> Dict[str, float]:
        """
        Reduce allocation to highly correlated asset pairs.

        For each pair with |correlation| > _HIGH_CORRELATION_THRESHOLD,
        the asset with the smaller exposure is penalized by
        _CORRELATION_PENALTY (FAS LAYER 9: cross-asset rebalancing).
        """
        adjusted = dict(exposures)
        assets = sorted(exposures.keys())

        # Find and penalize highly correlated pairs
        processed_pairs: set = set()
        for i, asset_a in enumerate(assets):
            for j, asset_b in enumerate(assets):
                if i >= j:
                    continue
                pair_key = (asset_a, asset_b)
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                corr = correlation_matrix[asset_a][asset_b]
                if abs(corr) > _HIGH_CORRELATION_THRESHOLD:
                    # Penalize the smaller allocation
                    if adjusted[asset_a] <= adjusted[asset_b]:
                        adjusted[asset_a] *= _CORRELATION_PENALTY
                    else:
                        adjusted[asset_b] *= _CORRELATION_PENALTY

        return adjusted

    @staticmethod
    def _calculate_diversification_benefit(
        exposures: Dict[str, float],
        correlation_matrix: Dict[str, Dict[str, float]],
    ) -> float:
        """
        Calculate diversification benefit as fraction of risk reduction.

        benefit = (sum_individual_risk - portfolio_risk) / sum_individual_risk

        Where:
        - sum_individual_risk = sum of individual asset risks (sqrt of variance)
        - portfolio_risk = sqrt of portfolio variance (with correlations)

        Returns value in [0.0, 1.0].
        0.0 = perfectly correlated, no diversification benefit.
        1.0 = perfectly uncorrelated, maximum diversification benefit.
        """
        if not exposures:
            return 0.0

        assets = sorted(exposures.keys())
        n = len(assets)

        if n <= 1:
            return 0.0

        # Sum of individual risks (each asset's standalone risk contribution)
        sum_individual = sum(abs(exposures[a]) for a in assets)
        if sum_individual == 0.0:
            return 0.0

        # Portfolio variance = sum_i sum_j w_i * w_j * corr_ij
        # (using exposures as risk proxies)
        portfolio_var = 0.0
        for a in assets:
            for b in assets:
                corr = correlation_matrix[a][b]
                portfolio_var += exposures[a] * exposures[b] * corr

        # Guard against floating-point issues producing tiny negative values
        portfolio_var = max(portfolio_var, 0.0)
        portfolio_risk = math.sqrt(portfolio_var)

        # Diversification benefit
        benefit = (sum_individual - portfolio_risk) / sum_individual
        return max(0.0, min(1.0, benefit))
