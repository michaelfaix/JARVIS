# =============================================================================
# jarvis/risk/tail_risk.py -- Multivariate Tail Risk Model (Phase MA-5)
#
# Estimates joint tail risk across a multi-asset portfolio using
# correlation-adjusted parametric VaR/CVaR with asset-specific tail parameters.
#
# FAS: Copula-based approach. Implementation uses deterministic parametric
# approximation (no Monte Carlo sampling per PROHIBITED-01/DET-01).
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   tail_risk.py -> jarvis.core.regime (AssetClass)
#   tail_risk.py -> jarvis.risk.asset_risk (AssetRiskResult, TAIL_PARAMS)
#   tail_risk.py -> jarvis.risk.correlation (CorrelationMatrixResult)
#   tail_risk.py -> (stdlib + math only)
#
# DETERMINISM GUARANTEES: DET-01 through DET-07 enforced.
#   DET-01  No stochastic operations. No Monte Carlo. No sampling.
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
from jarvis.risk.asset_risk import AssetRiskResult, TAIL_PARAMS


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

# VaR confidence z-scores
VAR_95_Z: float = 1.645
VAR_99_Z: float = 2.326

# Tail dependence boost for correlated tails (Student-t copula approximation)
# Higher correlation -> stronger tail dependence
TAIL_DEPENDENCE_BASE: float = 0.1
TAIL_DEPENDENCE_CORR_FACTOR: float = 0.3

# Worst-case multiplier for extreme scenario
WORST_CASE_MULTIPLIER: float = 3.0


# =============================================================================
# SECTION 2 -- RESULT DATACLASS
# =============================================================================

@dataclass(frozen=True)
class MultivariateTailRiskResult:
    """Portfolio-level multivariate tail risk result.

    Attributes:
        var_95: Portfolio VaR at 95% confidence (positive = loss magnitude).
        cvar_95: Portfolio CVaR (Expected Shortfall) at 95%.
        var_99: Portfolio VaR at 99% confidence.
        cvar_99: Portfolio CVaR at 99%.
        worst_case: Worst-case loss estimate.
        diversification_adjusted: Whether correlation adjustment was applied.
        tail_dependence: Estimated tail dependence coefficient.
        num_assets: Number of assets in portfolio.
        result_hash: SHA-256[:16] for determinism verification.
    """
    var_95: float
    cvar_95: float
    var_99: float
    cvar_99: float
    worst_case: float
    diversification_adjusted: bool
    tail_dependence: float
    num_assets: int
    result_hash: str


# =============================================================================
# SECTION 3 -- PURE MATH HELPERS (stdlib only, DET-01)
# =============================================================================

def _portfolio_var_parametric(
    asset_vars: List[float],
    correlation_matrix: Tuple[Tuple[float, ...], ...],
) -> float:
    """Compute portfolio VaR from individual asset VaRs and correlations.

    Uses the variance-covariance approach:
        portfolio_var^2 = sum_i sum_j VaR_i * VaR_j * corr(i,j)

    Args:
        asset_vars: Individual asset VaR values.
        correlation_matrix: NxN correlation matrix.

    Returns:
        Portfolio VaR (positive = loss).
    """
    n = len(asset_vars)
    if n == 0:
        return 0.0
    if n == 1:
        return asset_vars[0]

    portfolio_var_sq = 0.0
    for i in range(n):
        for j in range(n):
            corr = correlation_matrix[i][j] if i < len(correlation_matrix) and j < len(correlation_matrix[i]) else (1.0 if i == j else 0.0)
            portfolio_var_sq += asset_vars[i] * asset_vars[j] * corr

    return math.sqrt(max(portfolio_var_sq, 0.0))


def _estimate_tail_dependence(
    avg_correlation: float,
    min_tail_decay: float,
) -> float:
    """Estimate tail dependence from average correlation and tail parameters.

    Approximation of Student-t copula tail dependence:
    - Higher correlation -> more tail dependence
    - Fatter tails (lower tail_decay) -> more tail dependence

    Returns:
        Tail dependence coefficient [0, 1].
    """
    corr_component = max(0.0, avg_correlation) * TAIL_DEPENDENCE_CORR_FACTOR

    if min_tail_decay > 2.0:
        tail_component = TAIL_DEPENDENCE_BASE * (5.0 / min_tail_decay)
    else:
        tail_component = TAIL_DEPENDENCE_BASE * 2.5

    return max(0.0, min(1.0, corr_component + tail_component))


def _cvar_from_var(var_value: float, tail_dependence: float) -> float:
    """Estimate CVaR from VaR using tail dependence adjustment.

    CVaR >= VaR always. Higher tail dependence -> larger CVaR/VaR ratio.

    Args:
        var_value: VaR (positive = loss).
        tail_dependence: Tail dependence coefficient [0, 1].

    Returns:
        CVaR estimate (positive = loss).
    """
    # CVaR/VaR ratio: 1.0 to 1.5 depending on tail dependence
    ratio = 1.0 + 0.5 * tail_dependence
    return var_value * ratio


# =============================================================================
# SECTION 4 -- MULTIVARIATE TAIL MODEL
# =============================================================================

class MultivariateTailModel:
    """Portfolio-level multivariate tail risk estimation.

    Estimates joint tail risk using:
    1. Per-asset parametric VaR (from AssetRiskResult).
    2. Correlation-adjusted portfolio VaR (variance-covariance).
    3. Tail dependence adjustment (Student-t copula approximation).
    4. CVaR estimation from VaR + tail dependence.

    Deterministic: no Monte Carlo sampling (DET-01, PROHIBITED-01).
    All inputs are explicit parameters (DET-02).
    No internal state retained between calls (DET-03, PROHIBITED-05).
    """

    def estimate(
        self,
        *,
        asset_risks: Dict[str, AssetRiskResult],
        correlation_matrix: Tuple[Tuple[float, ...], ...],
        symbols: Tuple[str, ...],
    ) -> MultivariateTailRiskResult:
        """Estimate multivariate tail risk for portfolio.

        Args:
            asset_risks: Dict mapping symbol -> AssetRiskResult.
            correlation_matrix: NxN correlation matrix (tuple of tuples).
            symbols: Ordered symbol list matching matrix rows/cols.

        Returns:
            MultivariateTailRiskResult with portfolio VaR/CVaR.
        """
        n = len(symbols)

        if n == 0:
            return self._empty_result()

        # 1. Extract individual VaRs
        vars_95 = [asset_risks[s].daily_var_95 for s in symbols]
        vars_99 = [asset_risks[s].daily_var_99 for s in symbols]

        # 2. Portfolio VaR via variance-covariance
        portfolio_var_95 = _portfolio_var_parametric(vars_95, correlation_matrix)
        portfolio_var_99 = _portfolio_var_parametric(vars_99, correlation_matrix)

        # 3. Tail dependence
        avg_corr = self._average_off_diagonal(correlation_matrix, n)
        min_decay = min(
            (asset_risks[s].tail_risk.tail_decay for s in symbols),
            default=5.0,
        )
        tail_dep = _estimate_tail_dependence(avg_corr, min_decay)

        # 4. CVaR from VaR + tail dependence
        portfolio_cvar_95 = _cvar_from_var(portfolio_var_95, tail_dep)
        portfolio_cvar_99 = _cvar_from_var(portfolio_var_99, tail_dep)

        # 5. Worst case
        worst_case = portfolio_var_99 * WORST_CASE_MULTIPLIER

        diversification_adjusted = n > 1

        # Hash
        payload = {
            "var_95": round(portfolio_var_95, 8),
            "cvar_95": round(portfolio_cvar_95, 8),
            "var_99": round(portfolio_var_99, 8),
            "cvar_99": round(portfolio_cvar_99, 8),
            "worst_case": round(worst_case, 8),
            "n": n,
            "tail_dep": round(tail_dep, 8),
        }
        result_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]

        return MultivariateTailRiskResult(
            var_95=portfolio_var_95,
            cvar_95=portfolio_cvar_95,
            var_99=portfolio_var_99,
            cvar_99=portfolio_cvar_99,
            worst_case=worst_case,
            diversification_adjusted=diversification_adjusted,
            tail_dependence=tail_dep,
            num_assets=n,
            result_hash=result_hash,
        )

    def _average_off_diagonal(
        self,
        matrix: Tuple[Tuple[float, ...], ...],
        n: int,
    ) -> float:
        """Mean off-diagonal correlation."""
        if n < 2:
            return 0.0
        total = 0.0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                if i < len(matrix) and j < len(matrix[i]):
                    total += matrix[i][j]
                count += 1
        return total / count if count > 0 else 0.0

    def _empty_result(self) -> MultivariateTailRiskResult:
        payload = {"var_95": 0.0, "cvar_95": 0.0, "var_99": 0.0,
                   "cvar_99": 0.0, "worst_case": 0.0, "n": 0, "tail_dep": 0.0}
        h = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        return MultivariateTailRiskResult(
            var_95=0.0, cvar_95=0.0, var_99=0.0, cvar_99=0.0,
            worst_case=0.0, diversification_adjusted=False,
            tail_dependence=0.0, num_assets=0, result_hash=h,
        )
