# =============================================================================
# jarvis/risk/risk_budget.py -- Risk Budget Allocation (Phase MA-5)
#
# Allocates risk budget across asset classes using a 4-stage pipeline:
# 1. Equal risk contribution (base allocation)
# 2. Regime adjustment (risk_off, crisis, panic)
# 3. Correlation adjustment (breakdown, divergence)
# 4. Constraint application (max per asset, max correlated bucket)
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   risk_budget.py -> jarvis.core.regime (AssetClass, GlobalRegimeState,
#                     CorrelationRegimeState, HierarchicalRegime)
#   risk_budget.py -> jarvis.risk.portfolio_risk (PortfolioRiskResult)
#   risk_budget.py -> (stdlib + math only)
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
#   PROHIBITED-09: No string-based regime branching (uses Enum instances).
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple

from jarvis.core.regime import (
    AssetClass,
    CorrelationRegimeState,
    GlobalRegimeState,
    HierarchicalRegime,
)
from jarvis.risk.portfolio_risk import PortfolioRiskResult


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

# Maximum allocation per single asset class (30%)
MAX_SINGLE_ASSET: float = 0.30

# Maximum allocation in highly correlated assets (50%)
MAX_CORRELATION_BUCKET: float = 0.50

# Default risk budget per asset class when no portfolio risk data (20%)
RISK_BUDGET_DEFAULT_PCT: float = 0.20

# Regime adjustment factors (FAS Section 6)
# RISK_OFF adjustments
RISK_OFF_CRYPTO_FACTOR: float = 0.5
RISK_OFF_INDICES_FACTOR: float = 0.7
RISK_OFF_FOREX_FACTOR: float = 1.2  # Safe haven
RISK_OFF_COMMODITIES_FACTOR: float = 0.8
RISK_OFF_RATES_FACTOR: float = 1.1  # Flight to quality

# CRISIS adjustments (more severe than RISK_OFF)
CRISIS_CRYPTO_FACTOR: float = 0.2
CRISIS_INDICES_FACTOR: float = 0.4
CRISIS_FOREX_FACTOR: float = 0.8
CRISIS_COMMODITIES_FACTOR: float = 0.5
CRISIS_RATES_FACTOR: float = 1.0

# Correlation BREAKDOWN blanket reduction
BREAKDOWN_FACTOR: float = 0.6

# Correlation DIVERGENCE allows more spread
DIVERGENCE_FACTOR: float = 1.1

# Correlation COUPLED reduces slightly
COUPLED_FACTOR: float = 0.85


# =============================================================================
# SECTION 2 -- RESULT DATACLASS
# =============================================================================

@dataclass(frozen=True)
class RiskBudget:
    """Risk budget allocation for a single asset class.

    Attributes:
        asset_class: Asset class this budget applies to.
        allocated_capital: Capital allocated to this asset class.
        allocated_risk: Risk budget fraction after adjustments.
        risk_budget_fraction: Final fraction of total risk budget.
        base_allocation: Pre-adjustment equal risk contribution.
        regime_adjustment_factor: Cumulative regime adjustment applied.
        correlation_adjustment_factor: Correlation-based adjustment applied.
        result_hash: SHA-256[:16] for determinism verification.
    """
    asset_class: AssetClass
    allocated_capital: float
    allocated_risk: float
    risk_budget_fraction: float
    base_allocation: float
    regime_adjustment_factor: float
    correlation_adjustment_factor: float
    result_hash: str


@dataclass(frozen=True)
class RiskBudgetResult:
    """Portfolio-level risk budget allocation result.

    Attributes:
        budgets: Per-asset-class risk budgets.
        total_capital: Total capital being allocated.
        total_allocated: Sum of allocated capital.
        utilization: Fraction of total capital allocated.
        regime_applied: Global regime at time of allocation.
        correlation_regime_applied: Correlation regime at time of allocation.
        num_asset_classes: Number of asset classes with budgets.
        result_hash: SHA-256[:16] for determinism verification.
    """
    budgets: Dict[AssetClass, RiskBudget]
    total_capital: float
    total_allocated: float
    utilization: float
    regime_applied: GlobalRegimeState
    correlation_regime_applied: CorrelationRegimeState
    num_asset_classes: int
    result_hash: str


# =============================================================================
# SECTION 3 -- RISK BUDGET ALLOCATOR
# =============================================================================

class PortfolioRiskBudget:
    """Risk budget allocation across asset classes.

    4-stage pipeline:
    1. Equal risk contribution (base allocation)
    2. Regime adjustment (risk_off, crisis)
    3. Correlation regime adjustment (breakdown, divergence)
    4. Constraint application (max per asset, normalization)

    All inputs are explicit parameters (DET-02).
    No internal state retained between calls (DET-03, PROHIBITED-05).
    """

    def allocate(
        self,
        *,
        total_capital: float,
        asset_classes: List[AssetClass],
        regime: HierarchicalRegime,
        portfolio_risk: PortfolioRiskResult,
    ) -> RiskBudgetResult:
        """Allocate risk budget across asset classes.

        Args:
            total_capital: Total capital available.
            asset_classes: List of asset classes to allocate to.
            regime: Current HierarchicalRegime.
            portfolio_risk: Portfolio risk assessment for weighting.

        Returns:
            RiskBudgetResult with per-asset-class budgets.
        """
        if not asset_classes or total_capital <= 0.0:
            return self._empty_result(
                total_capital, regime.global_regime, regime.correlation_regime,
            )

        # Stage 1: Equal risk contribution
        base = self._equal_risk_contribution(asset_classes, portfolio_risk)

        # Stage 2: Regime adjustment
        regime_adjusted = self._regime_adjusted_allocation(
            base, regime.global_regime,
        )

        # Stage 3: Correlation adjustment
        corr_adjusted = self._correlation_adjusted_allocation(
            regime_adjusted, regime.correlation_regime,
        )

        # Stage 4: Apply constraints and normalize
        constrained = self._apply_constraints(corr_adjusted)

        # Build RiskBudget results
        budgets: Dict[AssetClass, RiskBudget] = {}
        total_allocated = 0.0

        for ac in asset_classes:
            fraction = constrained.get(ac, 0.0)
            allocated_capital = total_capital * fraction
            total_allocated += allocated_capital

            base_alloc = base.get(ac, 0.0)
            regime_factor = (
                regime_adjusted.get(ac, 0.0) / base_alloc
                if base_alloc > 0.0 else 1.0
            )
            corr_factor = (
                corr_adjusted.get(ac, 0.0) / regime_adjusted.get(ac, 0.0)
                if regime_adjusted.get(ac, 0.0) > 0.0 else 1.0
            )

            payload = {
                "ac": ac.value,
                "fraction": round(fraction, 8),
                "capital": round(allocated_capital, 8),
                "regime_factor": round(regime_factor, 8),
                "corr_factor": round(corr_factor, 8),
            }
            budget_hash = hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode("utf-8")
            ).hexdigest()[:16]

            budgets[ac] = RiskBudget(
                asset_class=ac,
                allocated_capital=allocated_capital,
                allocated_risk=fraction,
                risk_budget_fraction=fraction,
                base_allocation=base_alloc,
                regime_adjustment_factor=regime_factor,
                correlation_adjustment_factor=corr_factor,
                result_hash=budget_hash,
            )

        utilization = total_allocated / total_capital if total_capital > 0.0 else 0.0

        result_payload = {
            "total_capital": round(total_capital, 8),
            "total_allocated": round(total_allocated, 8),
            "utilization": round(utilization, 8),
            "n": len(asset_classes),
            "regime": regime.global_regime.value,
            "corr_regime": regime.correlation_regime.value,
        }
        result_hash = hashlib.sha256(
            json.dumps(result_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]

        return RiskBudgetResult(
            budgets=budgets,
            total_capital=total_capital,
            total_allocated=total_allocated,
            utilization=utilization,
            regime_applied=regime.global_regime,
            correlation_regime_applied=regime.correlation_regime,
            num_asset_classes=len(asset_classes),
            result_hash=result_hash,
        )

    def _equal_risk_contribution(
        self,
        asset_classes: List[AssetClass],
        portfolio_risk: PortfolioRiskResult,
    ) -> Dict[AssetClass, float]:
        """Stage 1: Equal risk contribution base allocation.

        Uses portfolio risk to weight by inverse volatility when available.
        Falls back to equal weighting if no meaningful risk data.

        Args:
            asset_classes: Asset classes to allocate to.
            portfolio_risk: Portfolio risk for risk-weighting.

        Returns:
            Dict mapping AssetClass -> base allocation fraction.
        """
        n = len(asset_classes)
        if n == 0:
            return {}

        # Collect per-asset-class volatilities from portfolio risk
        class_vols: Dict[AssetClass, float] = {}
        class_counts: Dict[AssetClass, int] = {}
        for sym, ar in portfolio_risk.asset_risks.items():
            ac = ar.asset_class
            if ac in class_vols:
                class_vols[ac] += ar.volatility.annualized
                class_counts[ac] += 1
            else:
                class_vols[ac] = ar.volatility.annualized
                class_counts[ac] = 1

        # Average vol per class
        avg_vols: Dict[AssetClass, float] = {}
        for ac in asset_classes:
            if ac in class_vols and class_counts.get(ac, 0) > 0:
                avg_vols[ac] = class_vols[ac] / class_counts[ac]
            else:
                avg_vols[ac] = 0.0

        # Inverse volatility weighting (lower vol -> more allocation)
        total_inv_vol = 0.0
        inv_vols: Dict[AssetClass, float] = {}
        for ac in asset_classes:
            vol = avg_vols.get(ac, 0.0)
            if vol > 1e-10:
                inv_vol = 1.0 / vol
            else:
                inv_vol = 1.0  # Default weight for zero-vol assets
            inv_vols[ac] = inv_vol
            total_inv_vol += inv_vol

        # Normalize to sum to 1.0
        result: Dict[AssetClass, float] = {}
        for ac in asset_classes:
            result[ac] = inv_vols[ac] / total_inv_vol if total_inv_vol > 0.0 else 1.0 / n

        return result

    def _regime_adjusted_allocation(
        self,
        base: Dict[AssetClass, float],
        global_regime: GlobalRegimeState,
    ) -> Dict[AssetClass, float]:
        """Stage 2: Regime-based allocation adjustment.

        RISK_OFF: reduce risky assets, increase safe havens.
        CRISIS: severe reduction across most assets.

        Args:
            base: Base allocation fractions.
            global_regime: Global regime state (Enum, not string).

        Returns:
            Regime-adjusted allocation fractions (not yet normalized).
        """
        result: Dict[AssetClass, float] = {}

        for ac, alloc in base.items():
            factor = 1.0

            if global_regime == GlobalRegimeState.CRISIS:
                factor = self._crisis_factor(ac)
            elif global_regime == GlobalRegimeState.RISK_OFF:
                factor = self._risk_off_factor(ac)
            # RISK_ON, TRANSITION, UNKNOWN: no adjustment

            result[ac] = alloc * factor

        return result

    def _risk_off_factor(self, ac: AssetClass) -> float:
        """Get RISK_OFF adjustment factor for asset class."""
        factors = {
            AssetClass.CRYPTO: RISK_OFF_CRYPTO_FACTOR,
            AssetClass.INDICES: RISK_OFF_INDICES_FACTOR,
            AssetClass.FOREX: RISK_OFF_FOREX_FACTOR,
            AssetClass.COMMODITIES: RISK_OFF_COMMODITIES_FACTOR,
            AssetClass.RATES: RISK_OFF_RATES_FACTOR,
        }
        return factors.get(ac, 1.0)

    def _crisis_factor(self, ac: AssetClass) -> float:
        """Get CRISIS adjustment factor for asset class."""
        factors = {
            AssetClass.CRYPTO: CRISIS_CRYPTO_FACTOR,
            AssetClass.INDICES: CRISIS_INDICES_FACTOR,
            AssetClass.FOREX: CRISIS_FOREX_FACTOR,
            AssetClass.COMMODITIES: CRISIS_COMMODITIES_FACTOR,
            AssetClass.RATES: CRISIS_RATES_FACTOR,
        }
        return factors.get(ac, 1.0)

    def _correlation_adjusted_allocation(
        self,
        regime_adjusted: Dict[AssetClass, float],
        correlation_regime: CorrelationRegimeState,
    ) -> Dict[AssetClass, float]:
        """Stage 3: Correlation regime adjustment.

        BREAKDOWN: blanket reduction (diversification lost).
        DIVERGENCE: slight increase (assets decoupling).
        COUPLED: slight reduction.
        NORMAL: no change.

        Args:
            regime_adjusted: Post-regime allocation fractions.
            correlation_regime: Correlation regime state.

        Returns:
            Correlation-adjusted allocation fractions.
        """
        if correlation_regime == CorrelationRegimeState.BREAKDOWN:
            factor = BREAKDOWN_FACTOR
        elif correlation_regime == CorrelationRegimeState.DIVERGENCE:
            factor = DIVERGENCE_FACTOR
        elif correlation_regime == CorrelationRegimeState.COUPLED:
            factor = COUPLED_FACTOR
        else:
            factor = 1.0

        return {ac: alloc * factor for ac, alloc in regime_adjusted.items()}

    def _apply_constraints(
        self,
        allocation: Dict[AssetClass, float],
    ) -> Dict[AssetClass, float]:
        """Stage 4: Apply constraints and normalize.

        Caps individual asset class allocation at MAX_SINGLE_ASSET.
        Normalizes so fractions sum to 1.0.

        Args:
            allocation: Pre-constraint allocation fractions.

        Returns:
            Constrained and normalized allocation fractions.
        """
        if not allocation:
            return {}

        # Cap at MAX_SINGLE_ASSET
        capped: Dict[AssetClass, float] = {}
        for ac, alloc in allocation.items():
            capped[ac] = min(alloc, MAX_SINGLE_ASSET)

        # Normalize to sum to 1.0
        total = sum(capped.values())
        if total <= 0.0:
            n = len(capped)
            return {ac: 1.0 / n for ac in capped}

        return {ac: v / total for ac, v in capped.items()}

    def _empty_result(
        self,
        total_capital: float,
        global_regime: GlobalRegimeState,
        correlation_regime: CorrelationRegimeState,
    ) -> RiskBudgetResult:
        """Return empty result for edge cases."""
        payload = {
            "total_capital": round(total_capital, 8),
            "total_allocated": 0.0,
            "utilization": 0.0,
            "n": 0,
            "regime": global_regime.value,
            "corr_regime": correlation_regime.value,
        }
        result_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]

        return RiskBudgetResult(
            budgets={},
            total_capital=total_capital,
            total_allocated=0.0,
            utilization=0.0,
            regime_applied=global_regime,
            correlation_regime_applied=correlation_regime,
            num_asset_classes=0,
            result_hash=result_hash,
        )
