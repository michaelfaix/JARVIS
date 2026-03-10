# =============================================================================
# JARVIS v6.1.0 -- STRATEGY ENGINE
# File:   jarvis/strategy/engine.py
# Version: 1.2.0
# =============================================================================
#
# SCOPE
# -----
# Deterministic strategy engine. Generates directional signals from a returns
# series based on configurable momentum and mean-reversion lookbacks, and
# executes a rolling-window strategy backtest via run_full_pipeline().
#
# PUBLIC FUNCTIONS
# ----------------
#   momentum_signal(returns, lookback) -> float  in [-1.0, 1.0]
#   mean_reversion_signal(returns, lookback) -> float  in [-1.0, 1.0]
#   combine_signals(signals, weights) -> float  in [-1.0, 1.0]
#   run_strategy(returns_series, asset_price_series, window, step,
#                initial_capital, regime, meta_uncertainty,
#                periods_per_year) -> dict
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
from typing import Dict, List, Sequence

from jarvis.core.regime import GlobalRegimeState
from jarvis.metrics.engine import compute_metrics
from jarvis.orchestrator.pipeline import run_full_pipeline


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


_SYNTHETIC_SYMBOL: str = "ASSET"


# ---------------------------------------------------------------------------
# MOMENTUM SIGNAL
# ---------------------------------------------------------------------------

def momentum_signal(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


# ---------------------------------------------------------------------------
# MEAN-REVERSION SIGNAL
# ---------------------------------------------------------------------------

def mean_reversion_signal(returns: List[float], lookback: int) -> float:
    """
    Mean-reversion signal: negative of momentum signal.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    return -momentum_signal(returns, lookback)


# ---------------------------------------------------------------------------
# COMBINE SIGNALS
# ---------------------------------------------------------------------------

def combine_signals(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


# ---------------------------------------------------------------------------
# RUN STRATEGY
# ---------------------------------------------------------------------------

def run_strategy(
    returns_series:     list[float],
    asset_price_series: list[float],
    window:             int,
    step:               int,
    initial_capital:    float,
    regime:             GlobalRegimeState,
    meta_uncertainty:   float,
    periods_per_year:   int = 252,
) -> dict:
    """
    Execute a rolling-window strategy backtest over a single-asset series.

    For each segment starting at offset t (stepping by ``step``):
      1. Slice returns_series[t - window : t] as the lookback window.
      2. Delegate risk assessment and allocation to run_full_pipeline().
      3. Update equity via: equity *= (1 + return_t * position_size).
      4. Record per-segment equity snapshots.

    After all segments are processed, compute per-segment and aggregate
    performance metrics via jarvis.metrics.compute_metrics().

    All risk, allocation, and metric logic is delegated -- nothing is
    reimplemented here (PROHIBITED-06).

    Parameters
    ----------
    returns_series : list[float]
        Per-period returns. Length must be >= window + step.
    asset_price_series : list[float]
        Per-period asset prices. Same length as returns_series.
    window : int
        Lookback window size. Must be >= 20 (RiskEngine minimum).
    step : int
        Step size for rolling window. Must be >= 1.
    initial_capital : float
        Starting equity. Must be > 0.
    regime : GlobalRegimeState
        Canonical regime enum instance.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
    periods_per_year : int
        Annualisation factor for metrics. Default 252.

    Returns
    -------
    dict with keys:
        "segments"        -- list of per-segment dicts, each containing:
                             "start", "end", "equity_curve".
        "segment_metrics" -- list of per-segment metric dicts (from
                             compute_metrics), or empty dict if segment
                             has fewer than 2 equity points.
        "aggregate"       -- dict with aggregate metrics computed from the
                             full equity curve, or empty dict if fewer
                             than 2 equity points total.

    Raises
    ------
    ValueError
        If window < 20, step < 1, initial_capital <= 0,
        series lengths differ, or series too short for one full window+step.
    """
    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------
    if window < 20:
        raise ValueError(
            f"window must be >= 20 (RiskEngine minimum); got {window}"
        )
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")
    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be > 0; got {initial_capital}"
        )
    if len(asset_price_series) != len(returns_series):
        raise ValueError(
            f"returns_series and asset_price_series must have equal length; "
            f"got {len(returns_series)} vs {len(asset_price_series)}"
        )
    n: int = len(returns_series)
    if n < window + step:
        raise ValueError(
            f"series length ({n}) must be >= window + step "
            f"({window} + {step} = {window + step})"
        )

    # ------------------------------------------------------------------
    # Rolling-window strategy execution
    # ------------------------------------------------------------------
    segments: list[dict] = []
    full_equity_curve: list[float] = [initial_capital]
    equity: float = initial_capital

    t: int = window
    while t < n:
        seg_end: int = min(t + step, n)
        seg_equity: list[float] = []

        for i in range(t, seg_end):
            window_returns: list[float] = returns_series[i - window : i]

            asset_prices: dict[str, float] = {
                _SYNTHETIC_SYMBOL: asset_price_series[i]
            }

            positions: dict[str, float] = run_full_pipeline(
                returns_history=window_returns,
                current_regime=regime,
                meta_uncertainty=meta_uncertainty,
                total_capital=equity,
                asset_prices=asset_prices,
            )

            position_size: float = positions[_SYNTHETIC_SYMBOL]
            updated: float = equity * (1.0 + returns_series[i] * position_size)
            equity = max(1e-10, updated)

            seg_equity.append(equity)
            full_equity_curve.append(equity)

        segments.append({
            "start": t,
            "end": seg_end,
            "equity_curve": seg_equity,
        })

        t = seg_end

    # ------------------------------------------------------------------
    # Per-segment metrics
    # ------------------------------------------------------------------
    segment_metrics: list[dict] = []
    for seg in segments:
        curve = seg["equity_curve"]
        if len(curve) >= 2:
            segment_metrics.append(
                compute_metrics(curve, periods_per_year)
            )
        else:
            segment_metrics.append({})

    # ------------------------------------------------------------------
    # Aggregate metrics over the full equity curve
    # ------------------------------------------------------------------
    if len(full_equity_curve) >= 2:
        aggregate: dict = compute_metrics(full_equity_curve, periods_per_year)
    else:
        aggregate = {}

    return {
        "segments": segments,
        "segment_metrics": segment_metrics,
        "aggregate": aggregate,
    }


__all__ = [
    "momentum_signal",
    "mean_reversion_signal",
    "combine_signals",
    "run_strategy",
]
