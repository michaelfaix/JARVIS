# =============================================================================
# jarvis/research/strategy_benchmark.py
# Authority: FAS v6.0.1 -- lines 10207-10337
# =============================================================================
#
# SCOPE
# -----
# Strategy benchmarking engine.  Compares strategy returns against
# standard baselines (buy-and-hold, MA crossover, etc.).  Produces
# BenchmarkResult objects -- pure analytical data, no state mutation.
#
# Public symbols:
#   BenchmarkResult              Frozen dataclass for benchmark output
#   StrategyBenchmarkEngine      Engine class
#
# ISOLATION RULES
# ---------------
# R1: Reads ONLY immutable snapshots -- no live state references.
# R2: NEVER mutates external state.
# R3: Returns BenchmarkResult only -- no Order/broker references.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, typing, math
#   external:  NONE
#   internal:  NONE
#   PROHIBITED: logging, random, file IO, network IO, datetime.now(), numpy
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

import math
from dataclasses import dataclass
from typing import List

__all__ = [
    "BenchmarkResult",
    "StrategyBenchmarkEngine",
]


# =============================================================================
# SECTION 1 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class BenchmarkResult:
    """
    Benchmark comparison result -- pure analytical data.

    Fields:
        strategy_id:         Strategy identifier.
        benchmark_name:      Name of baseline used.
        sharpe_ratio:        Strategy annualized Sharpe ratio.
        benchmark_sharpe:    Benchmark annualized Sharpe ratio.
        sharpe_delta:        sharpe_ratio - benchmark_sharpe.
        max_drawdown:        Strategy max drawdown (negative).
        benchmark_drawdown:  Benchmark max drawdown (negative).
        win_rate:            Fraction of periods strategy > benchmark.
        calmar_ratio:        Strategy Calmar ratio.
        outperformance_pct:  Percentage outperformance over benchmark.
        notes:               Analytical explanation.
    """
    strategy_id: str
    benchmark_name: str
    sharpe_ratio: float
    benchmark_sharpe: float
    sharpe_delta: float
    max_drawdown: float
    benchmark_drawdown: float
    win_rate: float
    calmar_ratio: float
    outperformance_pct: float
    notes: str


# =============================================================================
# SECTION 2 -- HELPERS
# =============================================================================

def _validate_returns(returns: List[float], name: str) -> None:
    """Validate that returns contain no NaN or Inf values."""
    for i, r in enumerate(returns):
        if not isinstance(r, (int, float)):
            raise ValueError(
                f"{name}[{i}] is not numeric: {type(r).__name__}"
            )
        if math.isnan(r) or math.isinf(r):
            raise ValueError(
                f"{name}[{i}] contains NaN or Inf: {r}"
            )


def _mean(values: List[float]) -> float:
    """Arithmetic mean of a list."""
    return sum(values) / len(values)


def _std(values: List[float]) -> float:
    """Population standard deviation of a list."""
    m = _mean(values)
    variance = sum((x - m) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def _cumulative_returns(returns: List[float]) -> List[float]:
    """Compute cumulative wealth curve from returns (1+r_0, (1+r_0)(1+r_1), ...)."""
    cumul = []
    wealth = 1.0
    for r in returns:
        wealth *= (1.0 + r)
        cumul.append(wealth)
    return cumul


# =============================================================================
# SECTION 3 -- ENGINE
# =============================================================================

class StrategyBenchmarkEngine:
    """
    Strategy benchmarking engine.

    Compares strategy return series against standard baselines.
    Stateless: all inputs passed explicitly.
    """

    BASELINES: List[str] = [
        "buy_and_hold",
        "ma_crossover",
        "random_entry",
        "vol_filter",
    ]

    def compute_sharpe(
        self,
        returns: List[float],
        risk_free: float = 0.0,
    ) -> float:
        """
        Compute annualized Sharpe ratio.

        Formula: mean(excess) / std(excess) * sqrt(252)
        where excess = returns - risk_free/252.

        Args:
            returns:   List of period returns.
            risk_free: Annualized risk-free rate.

        Returns:
            Annualized Sharpe ratio, or 0.0 for degenerate inputs.

        Raises:
            ValueError: If returns contain NaN or Inf.
        """
        _validate_returns(returns, "returns")
        if len(returns) < 2:
            return 0.0

        daily_rf = risk_free / 252.0
        excess = [r - daily_rf for r in returns]

        std = _std(excess)
        if std < 1e-10:
            return 0.0

        return _mean(excess) / std * math.sqrt(252.0)

    def compute_max_drawdown(
        self,
        returns: List[float],
    ) -> float:
        """
        Compute maximum drawdown from a return series.

        Formula: min((cumulative - running_max) / max(running_max, 1e-10))

        Args:
            returns: List of period returns.

        Returns:
            Maximum drawdown (negative or zero value).

        Raises:
            ValueError: If returns contain NaN or Inf.
        """
        _validate_returns(returns, "returns")
        if len(returns) == 0:
            return 0.0

        cumul = _cumulative_returns(returns)
        running_max = cumul[0]
        max_dd = 0.0

        for c in cumul:
            if c > running_max:
                running_max = c
            dd = (c - running_max) / max(running_max, 1e-10)
            if dd < max_dd:
                max_dd = dd

        return max_dd

    def benchmark_vs_buy_and_hold(
        self,
        strategy_returns: List[float],
        market_returns: List[float],
        strategy_id: str = "STRATEGY",
    ) -> BenchmarkResult:
        """
        Benchmark strategy against buy-and-hold market returns.

        Args:
            strategy_returns: Strategy period returns.
            market_returns:   Market period returns (buy-and-hold).
            strategy_id:      Strategy identifier.

        Returns:
            BenchmarkResult.

        Raises:
            ValueError: If inputs contain NaN/Inf or lengths differ.
        """
        _validate_returns(strategy_returns, "strategy_returns")
        _validate_returns(market_returns, "market_returns")

        if len(strategy_returns) != len(market_returns):
            raise ValueError(
                f"strategy_returns length ({len(strategy_returns)}) "
                f"!= market_returns length ({len(market_returns)})"
            )

        sharpe = self.compute_sharpe(strategy_returns)
        bench_sharpe = self.compute_sharpe(market_returns)
        max_dd = self.compute_max_drawdown(strategy_returns)
        bench_dd = self.compute_max_drawdown(market_returns)

        # Win rate: fraction of periods where strategy > benchmark
        n = len(strategy_returns)
        if n > 0:
            wins = sum(
                1 for s, b in zip(strategy_returns, market_returns) if s > b
            )
            win_rate = wins / n
        else:
            win_rate = 0.0

        # Calmar ratio
        abs_dd = abs(max_dd)
        if abs_dd < 1e-6:
            calmar = 0.0
        else:
            ann_return = _mean(strategy_returns) * 252.0 if n > 0 else 0.0
            calmar = abs(ann_return) / abs_dd

        # Outperformance percentage
        if n > 0:
            strat_total = 1.0
            bench_total = 1.0
            for s, b in zip(strategy_returns, market_returns):
                strat_total *= (1.0 + s)
                bench_total *= (1.0 + b)
            outperf = (strat_total - bench_total) / max(abs(bench_total), 1e-10) * 100.0
        else:
            outperf = 0.0

        return BenchmarkResult(
            strategy_id=strategy_id,
            benchmark_name="buy_and_hold",
            sharpe_ratio=sharpe,
            benchmark_sharpe=bench_sharpe,
            sharpe_delta=sharpe - bench_sharpe,
            max_drawdown=max_dd,
            benchmark_drawdown=bench_dd,
            win_rate=win_rate,
            calmar_ratio=calmar,
            outperformance_pct=outperf,
            notes=(
                f"Strategy {strategy_id} vs buy_and_hold. "
                f"Sharpe delta: {sharpe - bench_sharpe:.4f}. "
                f"Win rate: {win_rate:.2%}"
            ),
        )

    def benchmark_vs_ma_crossover(
        self,
        strategy_returns: List[float],
        prices: List[float],
        fast_period: int = 10,
        slow_period: int = 50,
        strategy_id: str = "STRATEGY",
    ) -> BenchmarkResult:
        """
        Benchmark strategy against a moving-average crossover baseline.

        The MA crossover baseline is long when fast MA > slow MA, else flat.

        Args:
            strategy_returns: Strategy period returns.
            prices:           Price series (used to generate MA signals).
            fast_period:      Fast MA period.
            slow_period:      Slow MA period.
            strategy_id:      Strategy identifier.

        Returns:
            BenchmarkResult.

        Raises:
            ValueError: If prices < slow_period or inputs contain NaN/Inf.
        """
        _validate_returns(strategy_returns, "strategy_returns")
        _validate_returns(prices, "prices")

        if len(prices) < slow_period:
            raise ValueError(
                f"prices length ({len(prices)}) must be >= "
                f"slow_period ({slow_period})"
            )

        # Compute MA crossover returns from prices
        # Price returns start from index 1
        price_returns = [
            (prices[i] - prices[i - 1]) / max(abs(prices[i - 1]), 1e-10)
            for i in range(1, len(prices))
        ]

        # Compute MA signals: for each bar, compute fast and slow MA
        # Signal at bar i uses prices[0..i] (inclusive)
        ma_returns: List[float] = []
        for i in range(slow_period - 1, len(prices) - 1):
            # Fast MA: average of last fast_period prices up to index i
            fast_start = i - fast_period + 1
            fast_ma = sum(prices[fast_start:i + 1]) / fast_period

            # Slow MA: average of last slow_period prices up to index i
            slow_start = i - slow_period + 1
            slow_ma = sum(prices[slow_start:i + 1]) / slow_period

            # Next period return
            ret_idx = i  # index into price_returns (offset by 1 from prices)
            if ret_idx < len(price_returns):
                if fast_ma > slow_ma:
                    ma_returns.append(price_returns[ret_idx])
                else:
                    ma_returns.append(0.0)  # flat (no position)

        # Align strategy returns to ma_returns length
        n = min(len(strategy_returns), len(ma_returns))
        aligned_strat = strategy_returns[:n]
        aligned_ma = ma_returns[:n]

        sharpe = self.compute_sharpe(aligned_strat)
        bench_sharpe = self.compute_sharpe(aligned_ma)
        max_dd = self.compute_max_drawdown(aligned_strat)
        bench_dd = self.compute_max_drawdown(aligned_ma)

        # Win rate
        if n > 0:
            wins = sum(
                1 for s, b in zip(aligned_strat, aligned_ma) if s > b
            )
            win_rate = wins / n
        else:
            win_rate = 0.0

        # Calmar ratio
        abs_dd = abs(max_dd)
        if abs_dd < 1e-6:
            calmar = 0.0
        else:
            ann_return = _mean(aligned_strat) * 252.0 if n > 0 else 0.0
            calmar = abs(ann_return) / abs_dd

        # Outperformance percentage
        if n > 0:
            strat_total = 1.0
            bench_total = 1.0
            for s, b in zip(aligned_strat, aligned_ma):
                strat_total *= (1.0 + s)
                bench_total *= (1.0 + b)
            outperf = (strat_total - bench_total) / max(abs(bench_total), 1e-10) * 100.0
        else:
            outperf = 0.0

        return BenchmarkResult(
            strategy_id=strategy_id,
            benchmark_name="ma_crossover",
            sharpe_ratio=sharpe,
            benchmark_sharpe=bench_sharpe,
            sharpe_delta=sharpe - bench_sharpe,
            max_drawdown=max_dd,
            benchmark_drawdown=bench_dd,
            win_rate=win_rate,
            calmar_ratio=calmar,
            outperformance_pct=outperf,
            notes=(
                f"Strategy {strategy_id} vs ma_crossover "
                f"(fast={fast_period}, slow={slow_period}). "
                f"Sharpe delta: {sharpe - bench_sharpe:.4f}. "
                f"Win rate: {win_rate:.2%}"
            ),
        )
