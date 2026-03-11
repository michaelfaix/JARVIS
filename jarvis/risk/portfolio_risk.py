# =============================================================================
# jarvis/risk/portfolio_risk.py -- Portfolio Risk Aggregator (Phase MA-5)
#
# Aggregates individual asset risks, dynamic correlations, multivariate tail
# risk, and gap risk into a single portfolio-level risk assessment.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   portfolio_risk.py -> jarvis.core.regime (AssetClass, AssetRegimeState,
#                        CorrelationRegimeState, GlobalRegimeState,
#                        HierarchicalRegime)
#   portfolio_risk.py -> jarvis.risk.asset_risk (AssetRiskCalculator,
#                        AssetRiskResult)
#   portfolio_risk.py -> jarvis.risk.correlation (DynamicCorrelationModel,
#                        CorrelationMatrixResult)
#   portfolio_risk.py -> jarvis.risk.tail_risk (MultivariateTailModel,
#                        MultivariateTailRiskResult)
#   portfolio_risk.py -> jarvis.risk.gap_risk (GapRiskModel,
#                        PortfolioGapRiskResult)
#   portfolio_risk.py -> (stdlib + math only)
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
#   PROHIBITED-06: No reimplementation -- delegates to canonical owners.
#   PROHIBITED-08: No new Enum definitions.
#   PROHIBITED-09: No string-based regime branching.
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from jarvis.core.regime import (
    AssetClass,
    AssetRegimeState,
    CorrelationRegimeState,
    GlobalRegimeState,
    HierarchicalRegime,
)
from jarvis.risk.asset_risk import AssetRiskCalculator, AssetRiskResult
from jarvis.risk.correlation import DynamicCorrelationModel, CorrelationMatrixResult
from jarvis.risk.tail_risk import MultivariateTailModel, MultivariateTailRiskResult
from jarvis.risk.gap_risk import GapRiskModel, PortfolioGapRiskResult


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

VAR_95_Z: float = 1.645
VAR_99_Z: float = 2.326


# =============================================================================
# SECTION 2 -- RESULT DATACLASS
# =============================================================================

@dataclass(frozen=True)
class PortfolioRiskResult:
    """Portfolio-level risk assessment aggregating all risk components.

    Attributes:
        asset_risks: Per-asset risk results.
        correlation_result: Dynamic correlation matrix result.
        tail_risk: Multivariate tail risk result.
        gap_risk: Gap risk result for session-based assets.
        portfolio_var_95: Portfolio 95% VaR (positive = loss).
        portfolio_var_99: Portfolio 99% VaR.
        portfolio_volatility: Portfolio-level volatility (daily).
        total_notional: Sum of absolute notional values.
        diversification_benefit: [0, 1] benefit from diversification.
        num_assets: Number of assets.
        regime: HierarchicalRegime at time of calculation.
        result_hash: SHA-256[:16] for determinism verification.
    """
    asset_risks: Dict[str, AssetRiskResult]
    correlation_result: CorrelationMatrixResult
    tail_risk: MultivariateTailRiskResult
    gap_risk: PortfolioGapRiskResult
    portfolio_var_95: float
    portfolio_var_99: float
    portfolio_volatility: float
    total_notional: float
    diversification_benefit: float
    num_assets: int
    regime: HierarchicalRegime
    result_hash: str


# =============================================================================
# SECTION 3 -- PORTFOLIO RISK ENGINE
# =============================================================================

class PortfolioRiskEngine:
    """Aggregates all risk components into portfolio-level risk assessment.

    Delegates to canonical owners:
    - AssetRiskCalculator for per-asset risk
    - DynamicCorrelationModel for regime-adjusted correlations
    - MultivariateTailModel for tail risk
    - GapRiskModel for gap risk

    All inputs are explicit parameters (DET-02).
    No internal state retained between calls (DET-03, PROHIBITED-05).
    """

    def calculate_portfolio_risk(
        self,
        *,
        positions: Dict[str, Tuple[AssetClass, float, float]],
        returns: Dict[str, List[float]],
        regime: HierarchicalRegime,
        price_histories: Dict[str, List[float]],
    ) -> PortfolioRiskResult:
        """Calculate complete portfolio risk.

        Args:
            positions: Dict mapping symbol -> (asset_class, price, size).
            returns: Dict mapping symbol -> return series.
            regime: Current HierarchicalRegime.
            price_histories: Dict mapping symbol -> daily price series
                (for gap risk estimation).

        Returns:
            PortfolioRiskResult with all risk components.
        """
        symbols = sorted(positions.keys())
        n = len(symbols)

        # 1. Individual asset risks (delegate to AssetRiskCalculator)
        asset_calculator = AssetRiskCalculator()
        asset_risks: Dict[str, AssetRiskResult] = {}
        for sym in symbols:
            asset_class, price, size = positions[sym]
            asset_regime_state = regime.asset_regimes.get(
                asset_class, AssetRegimeState.UNKNOWN,
            )
            sym_returns = returns.get(sym, [])
            liquidity = 0.8  # Default liquidity score
            asset_risks[sym] = asset_calculator.calculate_risk(
                symbol=sym,
                asset_class=asset_class,
                returns=sym_returns,
                current_price=price,
                position_size=size,
                regime_state=asset_regime_state,
                liquidity_score=liquidity,
            )

        # 2. Correlation matrix (delegate to DynamicCorrelationModel)
        corr_model = DynamicCorrelationModel()
        if n >= 2:
            correlation_result = corr_model.estimate(
                returns=returns,
                symbols=symbols,
                regime=regime,
            )
        else:
            correlation_result = corr_model.estimate(
                returns=returns,
                symbols=symbols,
                regime=regime,
            )

        # 3. Portfolio volatility and VaR
        portfolio_vol = self._calculate_portfolio_volatility(
            asset_risks=asset_risks,
            correlation_matrix=correlation_result.matrix,
            symbols=tuple(symbols),
        )
        portfolio_var_95 = portfolio_vol * VAR_95_Z
        portfolio_var_99 = portfolio_vol * VAR_99_Z

        # 4. Multivariate tail risk (delegate to MultivariateTailModel)
        tail_model = MultivariateTailModel()
        tail_risk = tail_model.estimate(
            asset_risks=asset_risks,
            correlation_matrix=correlation_result.matrix,
            symbols=tuple(symbols),
        )

        # 5. Gap risk (delegate to GapRiskModel)
        gap_model = GapRiskModel()
        gap_risk = gap_model.estimate(
            positions=positions,
            price_histories=price_histories,
        )

        # 6. Total notional
        total_notional = sum(ar.notional for ar in asset_risks.values())

        # 7. Diversification benefit
        diversification = self._calculate_diversification_benefit(
            asset_risks=asset_risks,
            portfolio_var_95=portfolio_var_95,
        )

        # Hash
        payload = {
            "portfolio_var_95": round(portfolio_var_95, 8),
            "portfolio_var_99": round(portfolio_var_99, 8),
            "portfolio_vol": round(portfolio_vol, 8),
            "total_notional": round(total_notional, 8),
            "diversification": round(diversification, 8),
            "n": n,
            "tail_hash": tail_risk.result_hash,
            "gap_hash": gap_risk.result_hash,
            "corr_hash": correlation_result.result_hash,
        }
        result_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]

        return PortfolioRiskResult(
            asset_risks=asset_risks,
            correlation_result=correlation_result,
            tail_risk=tail_risk,
            gap_risk=gap_risk,
            portfolio_var_95=portfolio_var_95,
            portfolio_var_99=portfolio_var_99,
            portfolio_volatility=portfolio_vol,
            total_notional=total_notional,
            diversification_benefit=diversification,
            num_assets=n,
            regime=regime,
            result_hash=result_hash,
        )

    def _calculate_portfolio_volatility(
        self,
        *,
        asset_risks: Dict[str, AssetRiskResult],
        correlation_matrix: Tuple[Tuple[float, ...], ...],
        symbols: Tuple[str, ...],
    ) -> float:
        """Calculate portfolio volatility using variance-covariance approach.

        portfolio_var = sum_i sum_j notional_i * vol_i * notional_j * vol_j * corr_ij
        portfolio_vol = sqrt(portfolio_var)

        Args:
            asset_risks: Per-asset risk results.
            correlation_matrix: NxN correlation matrix.
            symbols: Ordered symbol list.

        Returns:
            Portfolio-level daily volatility (in currency units).
        """
        n = len(symbols)
        if n == 0:
            return 0.0

        # Position volatilities: notional * daily_vol
        pos_vols = []
        for sym in symbols:
            ar = asset_risks[sym]
            pos_vols.append(ar.notional * ar.volatility.daily)

        if n == 1:
            return pos_vols[0]

        portfolio_var = 0.0
        for i in range(n):
            for j in range(n):
                corr = (
                    correlation_matrix[i][j]
                    if i < len(correlation_matrix) and j < len(correlation_matrix[i])
                    else (1.0 if i == j else 0.0)
                )
                portfolio_var += pos_vols[i] * pos_vols[j] * corr

        return math.sqrt(max(portfolio_var, 0.0))

    def _calculate_diversification_benefit(
        self,
        *,
        asset_risks: Dict[str, AssetRiskResult],
        portfolio_var_95: float,
    ) -> float:
        """Calculate diversification benefit.

        benefit = (sum_individual_var95 - portfolio_var95) / sum_individual_var95
        Result clamped to [0, 1].

        Args:
            asset_risks: Per-asset risk results.
            portfolio_var_95: Portfolio-level 95% VaR.

        Returns:
            Diversification benefit in [0, 1].
        """
        sum_individual = sum(ar.daily_var_95 for ar in asset_risks.values())
        if sum_individual <= 0.0:
            return 0.0

        benefit = (sum_individual - portfolio_var_95) / sum_individual
        return max(0.0, min(1.0, benefit))
