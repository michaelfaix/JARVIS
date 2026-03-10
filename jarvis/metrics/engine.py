# =============================================================================
# JARVIS v6.1.0 -- METRICS ENGINE
# File:   jarvis/metrics/engine.py
# Version: 1.2.0
# =============================================================================
#
# SCOPE
# -----
# Pure deterministic performance metrics. All functions are stateless,
# side-effect-free, and take no external dependencies beyond stdlib math.
#
# PUBLIC FUNCTIONS
# ----------------
#   sharpe_ratio(returns, periods_per_year, risk_free_rate) -> float
#   max_drawdown(returns) -> float
#   calmar_ratio(returns, periods_per_year) -> float
#   regime_conditional_returns(returns, regime_labels) -> dict
#   compute_metrics(equity_curve, periods_per_year) -> dict
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  No I/O, no logging, no datetime.now().
# DET-05  All branching is deterministic.
# DET-06  Fixed literals are not parametrised.
# DET-07  Same inputs = bit-identical outputs.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No numpy / scipy
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
# =============================================================================

from __future__ import annotations

import math
from typing import List, Sequence, Dict


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _mean(values: Sequence[float]) -> float:
    n = len(values)
    if n == 0:
        return 0.0
    return sum(values) / n


def _std(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(variance, 0.0))


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def sharpe_ratio(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def max_drawdown(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def calmar_ratio(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def regime_conditional_returns(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# COMPUTE METRICS (aggregate entry point)
# ---------------------------------------------------------------------------

def compute_metrics(
    equity_curve:     List[float],
    periods_per_year: int = 252,
) -> Dict[str, float]:
    """
    Compute a standard set of performance metrics from an equity curve.

    Converts the equity curve (absolute equity values) to period-over-period
    returns, then delegates to the individual metric functions defined in
    this module.  No metric formula is inlined -- all computation is
    delegated to sharpe_ratio(), max_drawdown(), _std(), and _mean().

    Pipeline (fixed order):
        1. Validate inputs (length, positivity, finiteness, periods).
        2. Convert equity_curve to returns: r[i] = curve[i]/curve[i-1] - 1.
        3. total_return  = curve[-1] / curve[0] - 1.
        4. cagr          = (curve[-1] / curve[0]) ^ (periods / n) - 1.
        5. volatility    = std(returns, ddof=1) * sqrt(periods).
        6. sharpe        = sharpe_ratio(returns, periods, risk_free_rate=0).
        7. max_drawdown  = max_drawdown(returns).

    Args:
        equity_curve:     Sequence of portfolio equity values.
                          Must contain >= 2 values. All must be finite and > 0.
        periods_per_year: Annualisation factor. Must be >= 1. Default 252.

    Returns:
        dict with keys:
            "total_return"  -- cumulative return: (final / initial) - 1.
            "cagr"          -- compound annual growth rate.
            "volatility"    -- annualised volatility (std * sqrt(periods)).
            "sharpe"        -- annualised Sharpe ratio (rf=0).
            "max_drawdown"  -- maximum peak-to-trough drawdown.

    Raises:
        ValueError if equity_curve has fewer than 2 elements.
        ValueError if any equity value is not finite or <= 0.
        ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(
            f"periods_per_year must be >= 1; got {periods_per_year}"
        )
    if len(equity_curve) < 2:
        raise ValueError(
            f"equity_curve must contain at least 2 values; "
            f"got {len(equity_curve)}"
        )
    for i, v in enumerate(equity_curve):
        if not math.isfinite(v) or v <= 0.0:
            raise ValueError(
                f"equity_curve[{i}] must be finite and > 0; got {v!r}"
            )

    # Step 2: equity curve -> period returns
    returns: List[float] = [
        equity_curve[i] / equity_curve[i - 1] - 1.0
        for i in range(1, len(equity_curve))
    ]

    # Step 3: total return
    total_ret: float = equity_curve[-1] / equity_curve[0] - 1.0

    # Step 4: CAGR
    n: int = len(returns)
    growth: float = equity_curve[-1] / equity_curve[0]
    cagr_val: float = growth ** (periods_per_year / n) - 1.0

    # Step 5: annualised volatility
    vol: float = _std(returns, ddof=1) * math.sqrt(periods_per_year)

    # Step 6: Sharpe (delegated)
    sharpe_val: float = sharpe_ratio(
        returns, periods_per_year, risk_free_rate=0.0
    )

    # Step 7: max drawdown (delegated)
    mdd: float = max_drawdown(returns)

    return {
        "total_return": total_ret,
        "cagr": cagr_val,
        "volatility": vol,
        "sharpe": sharpe_val,
        "max_drawdown": mdd,
    }


__all__ = [
    "sharpe_ratio",
    "max_drawdown",
    "calmar_ratio",
    "regime_conditional_returns",
    "compute_metrics",
]
