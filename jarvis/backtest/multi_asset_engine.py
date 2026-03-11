# =============================================================================
# jarvis/backtest/multi_asset_engine.py
# Version: 1.0.0
# =============================================================================
#
# SCOPE
# -----
# Portfolio-level multi-asset backtesting with cross-asset correlation,
# walk-forward splits, and aggregated performance metrics.
#
# Delegates ALL risk assessment to RiskEngine.assess() and ALL allocation
# logic to route_exposure_to_positions(). No risk or allocation formulas
# are reimplemented here. Correlation is computed via _pearson() from
# jarvis.risk.correlation (canonical owner). Metrics are delegated to
# jarvis.metrics.engine (canonical owner).
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  No I/O, no logging, no datetime.now().
# DET-05  All branching is deterministic.
# DET-06  Fixed literals are not parametrised.
# DET-07  Same inputs -> bit-identical outputs.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   PROHIBITED-01: No random / secrets / uuid / numpy.random.
#   PROHIBITED-02: No file I/O.
#   PROHIBITED-03: No logging / print.
#   PROHIBITED-04: No os.environ / os.getenv.
#   PROHIBITED-05: No global mutable state.
#   PROHIBITED-06: Delegates to canonical owners (no reimplementation).
#   PROHIBITED-09: No string-based regime branching.
#
# IMPORT RULES (DAG)
# ------------------
#   backtest/ -> core/, orchestrator/
#   Correlation from risk/ is accessed via its pure function _pearson.
#   Metrics from metrics/ via compute_metrics, sharpe_ratio, max_drawdown.
#
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from jarvis.core.regime import GlobalRegimeState
from jarvis.governance.backtest_governance import (
    BacktestGovernanceEngine,
    OverfittingReport,
)
from jarvis.metrics.engine import compute_metrics, sharpe_ratio, max_drawdown
from jarvis.orchestrator import run_full_pipeline
from jarvis.risk.correlation import _pearson
from jarvis.simulation.strategy_lab import SlippageModel, StrategyLab
from jarvis.walkforward.engine import generate_windows, WalkForwardWindow


# =============================================================================
# CONSTANTS (DET-06: fixed literals, not parametrizable)
# =============================================================================

# Minimum lookback window for RiskEngine
MIN_WINDOW: int = 20

# Correlation lookback (number of periods for cross-asset correlation)
CORRELATION_LOOKBACK: int = 60

# Equity floor to prevent zero/negative capital (FAS contract)
EQUITY_FLOOR: float = 1e-10


# =============================================================================
# RESULT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class AssetBacktestResult:
    """Per-asset backtest result.

    Attributes:
        symbol:       Asset identifier.
        equity_curve: Equity values per timestep.
        returns:      Per-period returns derived from equity curve.
        metrics:      Performance metrics from compute_metrics().
    """
    symbol:       str
    equity_curve: Tuple[float, ...]
    returns:      Tuple[float, ...]
    metrics:      Dict[str, float]


@dataclass(frozen=True)
class CorrelationSnapshot:
    """Cross-asset correlation at a point in time.

    Attributes:
        symbols:     Ordered symbols.
        matrix:      NxN correlation matrix (tuple of tuples).
        avg_off_diag: Mean absolute off-diagonal correlation.
    """
    symbols:      Tuple[str, ...]
    matrix:       Tuple[Tuple[float, ...], ...]
    avg_off_diag: float


@dataclass(frozen=True)
class MultiAssetBacktestResult:
    """Complete multi-asset backtest output.

    Attributes:
        asset_results:       Per-asset results keyed by symbol.
        portfolio_equity:    Combined portfolio equity curve.
        portfolio_metrics:   Aggregated portfolio metrics.
        correlation_final:   Final correlation snapshot.
        n_assets:            Number of assets.
        n_periods:           Number of backtest periods.
    """
    asset_results:     Dict[str, AssetBacktestResult]
    portfolio_equity:  Tuple[float, ...]
    portfolio_metrics: Dict[str, float]
    correlation_final: Optional[CorrelationSnapshot]
    n_assets:          int
    n_periods:         int


@dataclass(frozen=True)
class WalkForwardFoldResult:
    """Result of a single walk-forward fold.

    Attributes:
        fold:               Fold index.
        window:             WalkForwardWindow descriptor.
        train_metrics:      Portfolio metrics on training period.
        test_metrics:       Portfolio metrics on test (OOS) period.
        oos_sharpe:         Out-of-sample Sharpe ratio.
        overfitting_report: Overfitting detection report for this fold.
    """
    fold:               int
    window:             WalkForwardWindow
    train_metrics:      Dict[str, float]
    test_metrics:       Dict[str, float]
    oos_sharpe:         float
    overfitting_report: Optional[OverfittingReport] = None


@dataclass(frozen=True)
class MultiAssetWalkForwardResult:
    """Complete walk-forward validation over multi-asset portfolio.

    Attributes:
        folds:            Per-fold results.
        mean_oos_sharpe:  Mean OOS Sharpe across folds.
        std_oos_sharpe:   Std of OOS Sharpe across folds.
        n_folds:          Number of folds.
        full_backtest:    Full-period backtest result (no split).
        any_overfitting:  True if any fold was flagged for overfitting.
    """
    folds:           Tuple[WalkForwardFoldResult, ...]
    mean_oos_sharpe: float
    std_oos_sharpe:  float
    n_folds:         int
    full_backtest:   MultiAssetBacktestResult
    any_overfitting: bool = False


# =============================================================================
# HELPERS (pure, stateless, deterministic)
# =============================================================================

def _mean(values: Sequence[float]) -> float:
    """Arithmetic mean. Returns 0.0 for empty input."""
    n = len(values)
    if n == 0:
        return 0.0
    return sum(values) / n


def _std_pop(values: Sequence[float]) -> float:
    """Population standard deviation. Returns 0.0 for <2 elements."""
    n = len(values)
    if n < 2:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / n
    return math.sqrt(max(variance, 0.0))


def _compute_correlation_snapshot(
    asset_returns: Dict[str, List[float]],
    symbols: List[str],
    lookback: int,
) -> Optional[CorrelationSnapshot]:
    """Compute cross-asset correlation matrix from recent returns.

    Delegates pairwise correlation to _pearson from jarvis.risk.correlation.
    Returns None if fewer than 2 assets.
    """
    n = len(symbols)
    if n < 2:
        return None

    # Truncate to lookback window
    series: Dict[str, List[float]] = {}
    for s in symbols:
        raw = asset_returns.get(s, [])
        series[s] = raw[-lookback:] if len(raw) > lookback else list(raw)

    # Build NxN correlation matrix
    matrix: List[List[float]] = [[0.0] * n for _ in range(n)]
    off_diag_sum = 0.0
    off_diag_count = 0

    for i in range(n):
        matrix[i][i] = 1.0
        for j in range(i + 1, n):
            r = _pearson(series[symbols[i]], series[symbols[j]])
            matrix[i][j] = r
            matrix[j][i] = r
            off_diag_sum += abs(r)
            off_diag_count += 1

    avg_off = off_diag_sum / max(off_diag_count, 1)

    return CorrelationSnapshot(
        symbols=tuple(symbols),
        matrix=tuple(tuple(row) for row in matrix),
        avg_off_diag=avg_off,
    )


# =============================================================================
# CORE: MULTI-ASSET BACKTEST
# =============================================================================

def run_multi_asset_backtest(
    asset_returns: Dict[str, List[float]],
    asset_prices: Dict[str, List[float]],
    window: int,
    initial_capital: float,
    regime: GlobalRegimeState,
    meta_uncertainty: float,
    slippage_model: Optional[SlippageModel] = None,
) -> MultiAssetBacktestResult:
    """
    Deterministic rolling-window backtest across multiple assets.

    At each timestep t >= window:
      1. Builds lookback returns per asset from asset_returns.
      2. Constructs current prices dict from asset_prices.
      3. Delegates to run_full_pipeline() for position sizing.
      4. Updates per-asset and portfolio equity.

    All risk assessment and allocation is delegated to run_full_pipeline().
    Cross-asset correlation is computed at the end from realised returns.

    Parameters
    ----------
    asset_returns : Dict[str, List[float]]
        Per-asset return series. All series must have equal length.
        Keys are symbol names. At least one asset required.
    asset_prices : Dict[str, List[float]]
        Per-asset price series. Same keys and lengths as asset_returns.
        All prices must be positive.
    window : int
        Lookback window size. Must be >= 20.
    initial_capital : float
        Starting portfolio equity. Must be > 0.
    regime : GlobalRegimeState
        Regime held constant across all timesteps.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].
    slippage_model : Optional[SlippageModel]
        When provided, slippage is computed via StrategyLab.compute_slippage()
        and subtracted from each per-asset equity update:
        equity * (1.0 + return * position_size - slippage).
        When None (default), no slippage is applied (backward compatible).

    Returns
    -------
    MultiAssetBacktestResult
        Frozen result with per-asset and portfolio-level metrics.

    Raises
    ------
    ValueError
        If window < 20, initial_capital <= 0, series lengths differ,
        asset_returns is empty, or keys don't match between dicts.
    """
    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------
    if not asset_returns:
        raise ValueError("asset_returns must contain at least one asset.")

    if set(asset_returns.keys()) != set(asset_prices.keys()):
        raise ValueError(
            "asset_returns and asset_prices must have the same keys. "
            f"returns keys: {sorted(asset_returns.keys())}, "
            f"prices keys: {sorted(asset_prices.keys())}"
        )

    if window < MIN_WINDOW:
        raise ValueError(
            f"window must be >= {MIN_WINDOW}. Received: {window}"
        )

    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be > 0. Received: {initial_capital}"
        )

    symbols: List[str] = sorted(asset_returns.keys())
    n_assets = len(symbols)

    # Validate equal lengths
    lengths = [len(asset_returns[s]) for s in symbols]
    if len(set(lengths)) != 1:
        raise ValueError(
            f"All asset return series must have equal length. "
            f"Got: {dict(zip(symbols, lengths))}"
        )
    for s in symbols:
        if len(asset_prices[s]) != lengths[0]:
            raise ValueError(
                f"asset_prices[{s!r}] length {len(asset_prices[s])} != "
                f"asset_returns length {lengths[0]}"
            )

    n_total: int = lengths[0]
    if n_total <= window:
        # Not enough data for even one step
        return MultiAssetBacktestResult(
            asset_results={s: AssetBacktestResult(
                symbol=s, equity_curve=(), returns=(), metrics={},
            ) for s in symbols},
            portfolio_equity=(),
            portfolio_metrics={},
            correlation_final=None,
            n_assets=n_assets,
            n_periods=0,
        )

    # ------------------------------------------------------------------
    # Rolling-window backtest loop
    # ------------------------------------------------------------------
    # Equal-weight capital allocation across assets
    per_asset_equity: Dict[str, float] = {
        s: initial_capital / n_assets for s in symbols
    }
    asset_equity_curves: Dict[str, List[float]] = {s: [] for s in symbols}
    portfolio_equity_curve: List[float] = []
    realised_returns: Dict[str, List[float]] = {s: [] for s in symbols}

    # Pre-create StrategyLab instance if slippage is active (one per call, DET-02)
    lab: Optional[StrategyLab] = StrategyLab() if slippage_model is not None else None

    for t in range(window, n_total):
        # Build combined lookback returns (average across assets for pipeline)
        combined_returns: List[float] = []
        for i in range(t - window, t):
            period_return = _mean([asset_returns[s][i] for s in symbols])
            combined_returns.append(period_return)

        # Current prices
        current_prices: Dict[str, float] = {
            s: asset_prices[s][t] for s in symbols
        }

        # Total portfolio equity
        total_equity = sum(per_asset_equity[s] for s in symbols)
        total_equity = max(total_equity, EQUITY_FLOOR)

        # Delegate to pipeline for position sizing
        positions: Dict[str, float] = run_full_pipeline(
            returns_history=combined_returns,
            current_regime=regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=total_equity,
            asset_prices=current_prices,
        )

        # Compute window volatility once for slippage (if active)
        if lab is not None and slippage_model is not None:
            current_vol = _std_pop(combined_returns) * math.sqrt(252)
        else:
            current_vol = 0.0

        # Update per-asset equity
        for s in symbols:
            position_size = positions.get(s, 0.0)
            ret = asset_returns[s][t]
            old_eq = per_asset_equity[s]

            if lab is not None and slippage_model is not None:
                slippage = lab.compute_slippage(
                    slippage_model, abs(position_size), current_vol,
                )
            else:
                slippage = 0.0

            new_eq = old_eq * (1.0 + ret * position_size - slippage)
            per_asset_equity[s] = max(EQUITY_FLOOR, new_eq)
            asset_equity_curves[s].append(per_asset_equity[s])
            realised_returns[s].append(ret * position_size)

        # Portfolio equity
        portfolio_eq = sum(per_asset_equity[s] for s in symbols)
        portfolio_equity_curve.append(portfolio_eq)

    # ------------------------------------------------------------------
    # Compute per-asset metrics
    # ------------------------------------------------------------------
    asset_results: Dict[str, AssetBacktestResult] = {}
    for s in symbols:
        curve = asset_equity_curves[s]
        if len(curve) >= 2:
            # Prepend initial equity for compute_metrics
            full_curve = [initial_capital / n_assets] + curve
            metrics = compute_metrics(full_curve)
        else:
            metrics = {}
        asset_results[s] = AssetBacktestResult(
            symbol=s,
            equity_curve=tuple(curve),
            returns=tuple(realised_returns[s]),
            metrics=metrics,
        )

    # ------------------------------------------------------------------
    # Compute portfolio metrics
    # ------------------------------------------------------------------
    if len(portfolio_equity_curve) >= 2:
        full_portfolio = [initial_capital] + portfolio_equity_curve
        portfolio_metrics = compute_metrics(full_portfolio)
    else:
        portfolio_metrics = {}

    # ------------------------------------------------------------------
    # Final correlation snapshot
    # ------------------------------------------------------------------
    correlation_final = _compute_correlation_snapshot(
        realised_returns, symbols, CORRELATION_LOOKBACK,
    )

    return MultiAssetBacktestResult(
        asset_results=asset_results,
        portfolio_equity=tuple(portfolio_equity_curve),
        portfolio_metrics=portfolio_metrics,
        correlation_final=correlation_final,
        n_assets=n_assets,
        n_periods=len(portfolio_equity_curve),
    )


# =============================================================================
# WALK-FORWARD MULTI-ASSET BACKTEST
# =============================================================================

def run_multi_asset_walkforward(
    asset_returns: Dict[str, List[float]],
    asset_prices: Dict[str, List[float]],
    window: int,
    train_size: int,
    test_size: int,
    step: int,
    initial_capital: float,
    regime: GlobalRegimeState,
    meta_uncertainty: float,
) -> MultiAssetWalkForwardResult:
    """
    Walk-forward validation of multi-asset portfolio backtest.

    Generates train/test splits via generate_windows(), runs
    run_multi_asset_backtest() on each split, and aggregates OOS metrics.

    Parameters
    ----------
    asset_returns : Dict[str, List[float]]
        Per-asset return series (equal length, at least one asset).
    asset_prices : Dict[str, List[float]]
        Per-asset price series (same keys/lengths as asset_returns).
    window : int
        Lookback window for risk engine (>= 20).
    train_size : int
        Number of periods in each training window. Must be >= window + 1.
    test_size : int
        Number of periods in each test window. Must be >= 1.
    step : int
        Number of periods to advance per fold. Must be >= 1.
    initial_capital : float
        Starting capital per fold. Must be > 0.
    regime : GlobalRegimeState
        Regime held constant.
    meta_uncertainty : float
        Meta-uncertainty in [0.0, 1.0].

    Returns
    -------
    MultiAssetWalkForwardResult
        Contains per-fold results and aggregated OOS statistics.

    Raises
    ------
    ValueError
        If train_size < window + 1, or other validation failures
        propagated from run_multi_asset_backtest().
    """
    if train_size < window + 1:
        raise ValueError(
            f"train_size must be >= window + 1 ({window + 1}). "
            f"Received: {train_size}"
        )
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1. Received: {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1. Received: {step}")

    # Use any symbol to determine total length
    symbols = sorted(asset_returns.keys())
    n_total = len(asset_returns[symbols[0]])

    # Generate walk-forward windows
    windows = generate_windows(n_total, train_size, test_size, step)

    folds: List[WalkForwardFoldResult] = []

    for wf_window in windows:
        # Slice asset data for training period
        train_returns = {
            s: asset_returns[s][wf_window.train_start:wf_window.train_end]
            for s in symbols
        }
        train_prices = {
            s: asset_prices[s][wf_window.train_start:wf_window.train_end]
            for s in symbols
        }

        # Slice asset data for test period
        test_returns = {
            s: asset_returns[s][wf_window.test_start:wf_window.test_end]
            for s in symbols
        }
        test_prices = {
            s: asset_prices[s][wf_window.test_start:wf_window.test_end]
            for s in symbols
        }

        # Run backtest on training period
        train_result = run_multi_asset_backtest(
            asset_returns=train_returns,
            asset_prices=train_prices,
            window=window,
            initial_capital=initial_capital,
            regime=regime,
            meta_uncertainty=meta_uncertainty,
        )

        # Run backtest on test period
        test_result = run_multi_asset_backtest(
            asset_returns=test_returns,
            asset_prices=test_prices,
            window=window,
            initial_capital=initial_capital,
            regime=regime,
            meta_uncertainty=meta_uncertainty,
        )

        # Extract IS and OOS Sharpe
        is_sharpe = train_result.portfolio_metrics.get("sharpe", 0.0)
        oos_sharpe = test_result.portfolio_metrics.get("sharpe", 0.0)

        # Overfitting detection via governance engine
        governance = BacktestGovernanceEngine()
        overfitting_report = governance.detect_overfitting(
            strategy_id=f"walkforward_fold_{wf_window.fold}",
            is_sharpe=is_sharpe,
            oos_sharpe=oos_sharpe,
            sensitivity_score=0.0,
        )

        folds.append(WalkForwardFoldResult(
            fold=wf_window.fold,
            window=wf_window,
            train_metrics=train_result.portfolio_metrics,
            test_metrics=test_result.portfolio_metrics,
            oos_sharpe=oos_sharpe,
            overfitting_report=overfitting_report,
        ))

    # ------------------------------------------------------------------
    # Aggregate OOS statistics
    # ------------------------------------------------------------------
    oos_sharpes = [f.oos_sharpe for f in folds]
    mean_oos = _mean(oos_sharpes)
    std_oos = _std_pop(oos_sharpes)

    # ------------------------------------------------------------------
    # Full-period backtest (no splits)
    # ------------------------------------------------------------------
    full_backtest = run_multi_asset_backtest(
        asset_returns=asset_returns,
        asset_prices=asset_prices,
        window=window,
        initial_capital=initial_capital,
        regime=regime,
        meta_uncertainty=meta_uncertainty,
    )

    # Aggregate overfitting flag across all folds
    any_overfitting = any(
        f.overfitting_report is not None and f.overfitting_report.overfitting_flag
        for f in folds
    )

    return MultiAssetWalkForwardResult(
        folds=tuple(folds),
        mean_oos_sharpe=mean_oos,
        std_oos_sharpe=std_oos,
        n_folds=len(folds),
        full_backtest=full_backtest,
        any_overfitting=any_overfitting,
    )


__all__ = [
    "AssetBacktestResult",
    "CorrelationSnapshot",
    "MultiAssetBacktestResult",
    "WalkForwardFoldResult",
    "MultiAssetWalkForwardResult",
    "run_multi_asset_backtest",
    "run_multi_asset_walkforward",
    "MIN_WINDOW",
    "CORRELATION_LOOKBACK",
    "EQUITY_FLOOR",
]
