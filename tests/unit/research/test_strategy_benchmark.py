# =============================================================================
# tests/unit/research/test_strategy_benchmark.py
# =============================================================================

from __future__ import annotations

import dataclasses
import math

import pytest

from jarvis.research.strategy_benchmark import (
    BenchmarkResult,
    StrategyBenchmarkEngine,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def engine() -> StrategyBenchmarkEngine:
    return StrategyBenchmarkEngine()


# =============================================================================
# 1. BenchmarkResult is frozen dataclass
# =============================================================================

class TestBenchmarkResult:
    def test_is_frozen_dataclass(self):
        assert dataclasses.is_dataclass(BenchmarkResult)
        result = BenchmarkResult(
            strategy_id="S1",
            benchmark_name="buy_and_hold",
            sharpe_ratio=1.0,
            benchmark_sharpe=0.5,
            sharpe_delta=0.5,
            max_drawdown=-0.1,
            benchmark_drawdown=-0.15,
            win_rate=0.55,
            calmar_ratio=2.0,
            outperformance_pct=10.0,
            notes="test",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.sharpe_ratio = 999.0

    def test_has_11_fields(self):
        fields = dataclasses.fields(BenchmarkResult)
        assert len(fields) == 11


# =============================================================================
# 2-4. compute_sharpe
# =============================================================================

class TestComputeSharpe:
    def test_known_values(self, engine):
        # Constant positive returns should yield positive Sharpe
        returns = [0.01] * 100
        # With constant returns, excess = 0.01 each, std ≈ 0
        # Actually with perfectly constant, std = 0 → sharpe = 0.0
        # Use slightly varying returns instead
        returns = [0.01, 0.02, 0.015, 0.005, 0.01] * 20
        sharpe = engine.compute_sharpe(returns)
        assert sharpe > 0.0
        assert isinstance(sharpe, float)

    def test_known_exact_sharpe(self, engine):
        # Manual computation: mean=0.01, std should be nonzero
        returns = [0.02, 0.00]  # mean=0.01, std=0.01
        sharpe = engine.compute_sharpe(returns, risk_free=0.0)
        # excess = [0.02, 0.00], mean=0.01, std=0.01
        # sharpe = 0.01/0.01 * sqrt(252) = sqrt(252) ≈ 15.8745
        expected = math.sqrt(252.0)
        assert abs(sharpe - expected) < 0.01

    def test_returns_zero_for_fewer_than_2(self, engine):
        assert engine.compute_sharpe([]) == 0.0
        assert engine.compute_sharpe([0.01]) == 0.0

    def test_returns_zero_for_constant_returns(self, engine):
        # All identical → std = 0 → sharpe = 0
        returns = [0.01] * 50
        assert engine.compute_sharpe(returns) == 0.0

    def test_nan_rejection(self, engine):
        with pytest.raises(ValueError, match="NaN or Inf"):
            engine.compute_sharpe([0.01, float("nan"), 0.02])

    def test_inf_rejection(self, engine):
        with pytest.raises(ValueError, match="NaN or Inf"):
            engine.compute_sharpe([0.01, float("inf"), 0.02])


# =============================================================================
# 5. compute_max_drawdown
# =============================================================================

class TestComputeMaxDrawdown:
    def test_known_values(self, engine):
        # Start at 1.0, go to 1.1, drop to 0.88 → dd = (0.88-1.1)/1.1
        returns = [0.10, -0.20]
        dd = engine.compute_max_drawdown(returns)
        # cumul: [1.10, 0.88], running_max: [1.10, 1.10]
        # dd at 0: (1.10-1.10)/1.10 = 0, dd at 1: (0.88-1.10)/1.10 = -0.2
        assert abs(dd - (-0.2)) < 1e-10

    def test_no_drawdown(self, engine):
        # Monotonically increasing
        returns = [0.01, 0.02, 0.03]
        dd = engine.compute_max_drawdown(returns)
        assert dd == 0.0

    def test_empty_returns(self, engine):
        assert engine.compute_max_drawdown([]) == 0.0

    def test_nan_rejection(self, engine):
        with pytest.raises(ValueError, match="NaN or Inf"):
            engine.compute_max_drawdown([0.01, float("nan")])


# =============================================================================
# 6-7. benchmark_vs_buy_and_hold
# =============================================================================

class TestBenchmarkVsBuyAndHold:
    def test_produces_correct_result(self, engine):
        strat = [0.01, 0.02, -0.005, 0.015, 0.01] * 10
        market = [0.005, 0.01, 0.002, 0.008, 0.006] * 10
        result = engine.benchmark_vs_buy_and_hold(strat, market, "MY_STRAT")

        assert isinstance(result, BenchmarkResult)
        assert result.strategy_id == "MY_STRAT"
        assert result.benchmark_name == "buy_and_hold"
        assert isinstance(result.sharpe_ratio, float)
        assert isinstance(result.benchmark_sharpe, float)
        assert abs(result.sharpe_delta - (result.sharpe_ratio - result.benchmark_sharpe)) < 1e-10
        assert result.max_drawdown <= 0.0
        assert result.benchmark_drawdown <= 0.0
        assert 0.0 <= result.win_rate <= 1.0
        assert result.calmar_ratio >= 0.0

    def test_nan_rejection(self, engine):
        with pytest.raises(ValueError, match="NaN or Inf"):
            engine.benchmark_vs_buy_and_hold(
                [0.01, float("nan")],
                [0.01, 0.02],
            )

    def test_inf_rejection(self, engine):
        with pytest.raises(ValueError, match="NaN or Inf"):
            engine.benchmark_vs_buy_and_hold(
                [0.01, 0.02],
                [float("inf"), 0.02],
            )

    def test_length_mismatch(self, engine):
        with pytest.raises(ValueError, match="length"):
            engine.benchmark_vs_buy_and_hold([0.01], [0.01, 0.02])


# =============================================================================
# 8-9. benchmark_vs_ma_crossover
# =============================================================================

class TestBenchmarkVsMaCrossover:
    def test_known_prices(self, engine):
        # Create a simple uptrend price series (60 bars)
        prices = [100.0 + i * 0.5 for i in range(60)]
        strat_returns = [0.005] * 10  # only 10 returns
        result = engine.benchmark_vs_ma_crossover(
            strat_returns, prices, fast_period=10, slow_period=50,
            strategy_id="TREND_STRAT",
        )
        assert isinstance(result, BenchmarkResult)
        assert result.benchmark_name == "ma_crossover"
        assert result.strategy_id == "TREND_STRAT"

    def test_raises_on_too_few_prices(self, engine):
        with pytest.raises(ValueError, match="slow_period"):
            engine.benchmark_vs_ma_crossover(
                [0.01] * 10,
                [100.0] * 5,  # < slow_period=50
                slow_period=50,
            )

    def test_raises_on_nan_in_prices(self, engine):
        prices = [100.0] * 49 + [float("nan")]
        with pytest.raises(ValueError, match="NaN or Inf"):
            engine.benchmark_vs_ma_crossover(
                [0.01] * 10, prices, slow_period=50,
            )


# =============================================================================
# 10. BASELINES list
# =============================================================================

class TestBaselines:
    def test_has_4_entries(self):
        assert len(StrategyBenchmarkEngine.BASELINES) == 4

    def test_contains_expected(self):
        expected = {"buy_and_hold", "ma_crossover", "random_entry", "vol_filter"}
        assert set(StrategyBenchmarkEngine.BASELINES) == expected


# =============================================================================
# 11. Determinism
# =============================================================================

class TestDeterminism:
    def test_same_inputs_same_outputs(self, engine):
        strat = [0.01, -0.005, 0.02, 0.003, -0.01] * 10
        market = [0.005, 0.002, 0.01, 0.001, -0.005] * 10

        r1 = engine.benchmark_vs_buy_and_hold(strat, market, "DET")
        r2 = engine.benchmark_vs_buy_and_hold(strat, market, "DET")

        assert r1 == r2

    def test_sharpe_deterministic(self, engine):
        returns = [0.01, -0.005, 0.02, 0.003] * 20
        s1 = engine.compute_sharpe(returns)
        s2 = engine.compute_sharpe(returns)
        assert s1 == s2

    def test_max_drawdown_deterministic(self, engine):
        returns = [0.01, -0.05, 0.02, -0.03] * 10
        d1 = engine.compute_max_drawdown(returns)
        d2 = engine.compute_max_drawdown(returns)
        assert d1 == d2


# =============================================================================
# 12. Import contract
# =============================================================================

class TestImportContract:
    def test_import_from_module(self):
        from jarvis.research.strategy_benchmark import BenchmarkResult as BR
        from jarvis.research.strategy_benchmark import StrategyBenchmarkEngine as SBE
        assert BR is BenchmarkResult
        assert SBE is StrategyBenchmarkEngine

    def test_all_exports(self):
        import jarvis.research.strategy_benchmark as mod
        assert "BenchmarkResult" in mod.__all__
        assert "StrategyBenchmarkEngine" in mod.__all__
