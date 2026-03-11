# =============================================================================
# jarvis/risk/asset_risk.py -- Individual Asset Risk Calculator (Phase MA-5)
#
# Calculates per-asset risk metrics: volatility estimation (regime-dependent),
# tail risk, VaR, CVaR, and execution cost.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   asset_risk.py -> jarvis.core.regime (AssetClass, AssetRegimeState)
#   asset_risk.py -> jarvis.core.data_structures (VOLATILITY_SCALING)
#   asset_risk.py -> (stdlib + math only)
#
# DETERMINISM GUARANTEES: DET-01 through DET-07 enforced.
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly.
#   DET-03  No side effects.
#   DET-05  Same inputs -> same outputs.
#   DET-06  Fixed literals not parameterizable.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01: No numpy. Pure stdlib math.
#   PROHIBITED-02: No file I/O.
#   PROHIBITED-03: No logging/print.
#   PROHIBITED-05: No global mutable state.
#   PROHIBITED-08: No new Enum definitions.
#   PROHIBITED-09: No string-based regime branching (uses Enum instances).
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from jarvis.core.regime import AssetClass, AssetRegimeState


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

# Annualization factors
CRYPTO_ANNUALIZATION: float = 365.0     # 24/7 trading
FOREX_ANNUALIZATION: float = 252.0      # Trading days
INDICES_ANNUALIZATION: float = 252.0
COMMODITIES_ANNUALIZATION: float = 252.0
RATES_ANNUALIZATION: float = 252.0

ANNUALIZATION_FACTORS: Dict[AssetClass, float] = {
    AssetClass.CRYPTO: CRYPTO_ANNUALIZATION,
    AssetClass.FOREX: FOREX_ANNUALIZATION,
    AssetClass.INDICES: INDICES_ANNUALIZATION,
    AssetClass.COMMODITIES: COMMODITIES_ANNUALIZATION,
    AssetClass.RATES: RATES_ANNUALIZATION,
}

# EWMA decay factor for realized volatility
EWMA_DECAY: float = 0.94

# VaR confidence z-scores
VAR_95_Z: float = 1.645
VAR_99_Z: float = 2.326

# Regime-dependent volatility multipliers per asset class (FAS Section 1)
# Maps (AssetClass, AssetRegimeState) -> vol multiplier
CRYPTO_VOL_MULTIPLIERS: Dict[AssetRegimeState, float] = {
    AssetRegimeState.TRENDING_UP:   1.0,
    AssetRegimeState.TRENDING_DOWN: 1.2,
    AssetRegimeState.RANGING_TIGHT: 0.7,
    AssetRegimeState.RANGING_WIDE:  1.1,
    AssetRegimeState.HIGH_VOLATILITY: 1.5,
    AssetRegimeState.SHOCK:         2.0,
    AssetRegimeState.RECOVERY:      1.3,
    AssetRegimeState.UNKNOWN:       1.0,
}

FOREX_VOL_MULTIPLIERS: Dict[AssetRegimeState, float] = {
    AssetRegimeState.TRENDING_UP:   1.0,
    AssetRegimeState.TRENDING_DOWN: 1.0,
    AssetRegimeState.RANGING_TIGHT: 0.7,
    AssetRegimeState.RANGING_WIDE:  1.0,
    AssetRegimeState.HIGH_VOLATILITY: 1.5,
    AssetRegimeState.SHOCK:         1.8,
    AssetRegimeState.RECOVERY:      1.2,
    AssetRegimeState.UNKNOWN:       1.0,
}

INDICES_VOL_MULTIPLIERS: Dict[AssetRegimeState, float] = {
    AssetRegimeState.TRENDING_UP:   0.9,
    AssetRegimeState.TRENDING_DOWN: 1.2,
    AssetRegimeState.RANGING_TIGHT: 0.7,
    AssetRegimeState.RANGING_WIDE:  1.1,
    AssetRegimeState.HIGH_VOLATILITY: 1.5,
    AssetRegimeState.SHOCK:         2.0,
    AssetRegimeState.RECOVERY:      1.2,
    AssetRegimeState.UNKNOWN:       1.0,
}

COMMODITIES_VOL_MULTIPLIERS: Dict[AssetRegimeState, float] = {
    AssetRegimeState.TRENDING_UP:   1.0,
    AssetRegimeState.TRENDING_DOWN: 1.1,
    AssetRegimeState.RANGING_TIGHT: 0.8,
    AssetRegimeState.RANGING_WIDE:  1.1,
    AssetRegimeState.HIGH_VOLATILITY: 1.5,
    AssetRegimeState.SHOCK:         1.8,
    AssetRegimeState.RECOVERY:      1.2,
    AssetRegimeState.UNKNOWN:       1.0,
}

RATES_VOL_MULTIPLIERS: Dict[AssetRegimeState, float] = {
    AssetRegimeState.TRENDING_UP:   0.9,
    AssetRegimeState.TRENDING_DOWN: 1.0,
    AssetRegimeState.RANGING_TIGHT: 0.7,
    AssetRegimeState.RANGING_WIDE:  0.9,
    AssetRegimeState.HIGH_VOLATILITY: 1.3,
    AssetRegimeState.SHOCK:         1.8,
    AssetRegimeState.RECOVERY:      1.1,
    AssetRegimeState.UNKNOWN:       1.0,
}

VOL_MULTIPLIERS: Dict[AssetClass, Dict[AssetRegimeState, float]] = {
    AssetClass.CRYPTO: CRYPTO_VOL_MULTIPLIERS,
    AssetClass.FOREX: FOREX_VOL_MULTIPLIERS,
    AssetClass.INDICES: INDICES_VOL_MULTIPLIERS,
    AssetClass.COMMODITIES: COMMODITIES_VOL_MULTIPLIERS,
    AssetClass.RATES: RATES_VOL_MULTIPLIERS,
}

# Tail distribution parameters per asset class
# (tail_decay_factor: higher = thinner tails)
TAIL_PARAMS: Dict[AssetClass, float] = {
    AssetClass.CRYPTO: 3.0,        # Fat tails (low df ~ Student-t)
    AssetClass.FOREX: 8.0,         # Thinner tails (higher df)
    AssetClass.INDICES: 5.0,       # Medium tails
    AssetClass.COMMODITIES: 4.0,   # Moderate fat tails
    AssetClass.RATES: 10.0,        # Thinnest tails
}

# Execution cost basis points per asset class
EXECUTION_COST_BPS: Dict[AssetClass, float] = {
    AssetClass.CRYPTO: 10.0,
    AssetClass.FOREX: 2.0,
    AssetClass.INDICES: 3.0,
    AssetClass.COMMODITIES: 5.0,
    AssetClass.RATES: 1.5,
}


# =============================================================================
# SECTION 2 -- RESULT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class VolatilityEstimate:
    """Regime-adjusted volatility estimate.

    Attributes:
        daily: Daily volatility (annualized / sqrt(annualization_factor)).
        annualized: Annualized volatility.
        regime_multiplier: Applied regime multiplier.
        asset_class: Asset class this estimate applies to.
    """
    daily: float
    annualized: float
    regime_multiplier: float
    asset_class: AssetClass


@dataclass(frozen=True)
class TailRiskEstimate:
    """Tail risk parameters for an individual asset.

    Attributes:
        var_95: Value-at-Risk at 95% confidence (loss as positive fraction).
        var_99: Value-at-Risk at 99% confidence.
        cvar_99: Conditional VaR (Expected Shortfall) at 99%.
        tail_decay: Tail decay parameter (higher = thinner tails).
        asset_class: Asset class.
    """
    var_95: float
    var_99: float
    cvar_99: float
    tail_decay: float
    asset_class: AssetClass


@dataclass(frozen=True)
class AssetRiskResult:
    """Complete risk assessment for a single asset.

    Attributes:
        symbol: Asset symbol.
        asset_class: Asset class.
        notional: Position notional value.
        volatility: Regime-adjusted volatility estimate.
        daily_var_95: 95% daily VaR in currency units.
        daily_var_99: 99% daily VaR in currency units.
        tail_cvar_99: 99% CVaR in currency units.
        tail_risk: Tail risk parameters.
        execution_cost_bps: Estimated execution cost in basis points.
        liquidity_score: Liquidity quality [0, 1].
        result_hash: SHA-256[:16] for determinism verification.
    """
    symbol: str
    asset_class: AssetClass
    notional: float
    volatility: VolatilityEstimate
    daily_var_95: float
    daily_var_99: float
    tail_cvar_99: float
    tail_risk: TailRiskEstimate
    execution_cost_bps: float
    liquidity_score: float
    result_hash: str


# =============================================================================
# SECTION 3 -- PURE MATH HELPERS (stdlib only, DET-01)
# =============================================================================

def _ewma_volatility(returns: List[float], decay: float = EWMA_DECAY) -> float:
    """EWMA volatility estimation. Pure stdlib.

    Args:
        returns: Return series.
        decay: Decay factor (lambda). Default 0.94.

    Returns:
        EWMA standard deviation of returns. 0.0 if fewer than 2 returns.
    """
    n = len(returns)
    if n < 2:
        return 0.0

    mean_r = sum(returns) / n
    var = 0.0
    weight_sum = 0.0

    for i in range(n):
        w = (1.0 - decay) * (decay ** (n - 1 - i))
        var += w * (returns[i] - mean_r) ** 2
        weight_sum += w

    if weight_sum < 1e-15:
        return 0.0

    return math.sqrt(var / weight_sum)


def _compute_tail_var(
    returns: List[float],
    confidence: float,
    tail_decay: float,
) -> float:
    """Compute parametric VaR using tail-adjusted estimate.

    Uses empirical std adjusted by tail decay factor to approximate
    heavy-tailed distributions without scipy.

    Lower tail_decay = fatter tails = higher VaR multiplier.

    Args:
        returns: Return series.
        confidence: Confidence level z-score (e.g., 1.645 for 95%).
        tail_decay: Tail decay parameter.

    Returns:
        VaR as a positive fraction (loss magnitude).
    """
    if len(returns) < 2:
        return 0.0

    n = len(returns)
    mean_r = sum(returns) / n
    var_sum = sum((r - mean_r) ** 2 for r in returns) / (n - 1)
    std = math.sqrt(max(var_sum, 0.0))

    # Tail adjustment: lower tail_decay -> fatter tails -> higher VaR
    # Approximation: multiply z-score by sqrt(tail_decay / (tail_decay - 2))
    # for Student-t-like behavior (df = tail_decay)
    if tail_decay > 2.0:
        tail_factor = math.sqrt(tail_decay / (tail_decay - 2.0))
    else:
        tail_factor = 3.0  # Very fat tails

    return abs(confidence * std * tail_factor)


def _compute_cvar(returns: List[float], var_threshold: float) -> float:
    """Compute CVaR (Expected Shortfall) from empirical returns.

    CVaR = average of returns worse than -var_threshold.

    Args:
        returns: Return series.
        var_threshold: VaR threshold (positive, representing loss magnitude).

    Returns:
        CVaR as positive fraction. Returns var_threshold if no tail returns.
    """
    tail_returns = [r for r in returns if r < -var_threshold]
    if not tail_returns:
        return var_threshold
    return abs(sum(tail_returns) / len(tail_returns))


# =============================================================================
# SECTION 4 -- ASSET RISK CALCULATOR
# =============================================================================

class AssetRiskCalculator:
    """Calculates risk for individual positions across asset classes.

    Regime-dependent volatility estimation with asset-specific:
    - Annualization factors (365 for crypto, 252 for traditional)
    - Tail distribution parameters
    - Execution cost estimates
    - Regime-based vol multipliers

    All inputs are explicit parameters (DET-02).
    No internal state retained between calls (DET-03, PROHIBITED-05).
    """

    def calculate_risk(
        self,
        *,
        symbol: str,
        asset_class: AssetClass,
        returns: List[float],
        current_price: float,
        position_size: float,
        regime_state: AssetRegimeState,
        liquidity_score: float,
    ) -> AssetRiskResult:
        """Calculate complete risk for a single asset position.

        Args:
            symbol: Asset symbol (e.g., "BTC", "EURUSD").
            asset_class: Asset class enum.
            returns: Historical return series (at least 20 elements).
            current_price: Current asset price.
            position_size: Position size in units.
            regime_state: Current asset regime state.
            liquidity_score: Liquidity quality [0, 1].

        Returns:
            AssetRiskResult with all risk metrics.
        """
        notional = abs(position_size * current_price)

        # 1. Volatility estimation (regime-adjusted)
        volatility = self._estimate_volatility(
            returns, asset_class, regime_state
        )

        # 2. Tail risk estimation
        tail_risk = self._estimate_tail_risk(returns, asset_class)

        # 3. Position-level VaR
        daily_var_95 = notional * volatility.daily * VAR_95_Z
        daily_var_99 = notional * volatility.daily * VAR_99_Z

        # 4. Tail CVaR
        tail_cvar_99 = notional * tail_risk.cvar_99

        # 5. Execution cost
        exec_cost = EXECUTION_COST_BPS.get(asset_class, 5.0)

        # Deterministic hash
        payload = {
            "symbol": symbol,
            "asset_class": asset_class.value,
            "notional": round(notional, 8),
            "daily_vol": round(volatility.daily, 8),
            "var_95": round(daily_var_95, 8),
            "var_99": round(daily_var_99, 8),
            "cvar_99": round(tail_cvar_99, 8),
        }
        result_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]

        return AssetRiskResult(
            symbol=symbol,
            asset_class=asset_class,
            notional=notional,
            volatility=volatility,
            daily_var_95=daily_var_95,
            daily_var_99=daily_var_99,
            tail_cvar_99=tail_cvar_99,
            tail_risk=tail_risk,
            execution_cost_bps=exec_cost,
            liquidity_score=max(0.0, min(1.0, liquidity_score)),
            result_hash=result_hash,
        )

    def _estimate_volatility(
        self,
        returns: List[float],
        asset_class: AssetClass,
        regime_state: AssetRegimeState,
    ) -> VolatilityEstimate:
        """Estimate regime-adjusted volatility."""
        # Base EWMA volatility
        realized_vol = _ewma_volatility(returns)

        # Annualize
        ann_factor = ANNUALIZATION_FACTORS.get(asset_class, 252.0)
        annualized_vol = realized_vol * math.sqrt(ann_factor)

        # Regime multiplier
        multipliers = VOL_MULTIPLIERS.get(asset_class, {})
        regime_mult = multipliers.get(regime_state, 1.0)

        adjusted_ann = annualized_vol * regime_mult
        daily_vol = adjusted_ann / math.sqrt(ann_factor)

        return VolatilityEstimate(
            daily=daily_vol,
            annualized=adjusted_ann,
            regime_multiplier=regime_mult,
            asset_class=asset_class,
        )

    def _estimate_tail_risk(
        self,
        returns: List[float],
        asset_class: AssetClass,
    ) -> TailRiskEstimate:
        """Estimate tail risk with asset-specific parameters."""
        tail_decay = TAIL_PARAMS.get(asset_class, 5.0)

        var_95 = _compute_tail_var(returns, VAR_95_Z, tail_decay)
        var_99 = _compute_tail_var(returns, VAR_99_Z, tail_decay)
        cvar_99 = _compute_cvar(returns, var_99)

        return TailRiskEstimate(
            var_95=var_95,
            var_99=var_99,
            cvar_99=cvar_99,
            tail_decay=tail_decay,
            asset_class=asset_class,
        )
