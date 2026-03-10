# =============================================================================
# test_strategy_engine.py -- Unit tests for jarvis/strategy/engine.py
#
# Covers all 4 public functions:
#   momentum_signal, mean_reversion_signal, combine_signals, run_strategy
#
# Mutation-killing strategy:
#   - Boundary values tested (lookback=0, 1, exact length)
#   - Hand-computed expected values for arithmetic
#   - Clip boundaries tested at -1.0 and +1.0
#   - Determinism and immutability verified
#   - All error paths exercised
# =============================================================================

from __future__ import annotations

import math

import pytest

from jarvis.core.regime import GlobalRegimeState
from jarvis.strategy.engine import (
    _clip,
    combine_signals,
    mean_reversion_signal,
    momentum_signal,
    run_strategy,
)


# =============================================================================
# SECTION 1 -- _clip helper
# =============================================================================

class TestClip:
    def test_within_range(self):
        assert _clip(0.5, -1.0, 1.0) == 0.5

    def test_below_lo(self):
        assert _clip(-2.0, -1.0, 1.0) == -1.0

    def test_above_hi(self):
        assert _clip(2.0, -1.0, 1.0) == 1.0

    def test_at_lo(self):
        assert _clip(-1.0, -1.0, 1.0) == -1.0

    def test_at_hi(self):
        assert _clip(1.0, -1.0, 1.0) == 1.0

    def test_zero(self):
        assert _clip(0.0, -1.0, 1.0) == 0.0


# =============================================================================
# SECTION 2 -- momentum_signal
# =============================================================================

class TestMomentumSignal:
    def test_lookback_zero_returns_zero(self):
        assert momentum_signal([0.01, 0.02], 0) == 0.0

    def test_lookback_negative_returns_zero(self):
        assert momentum_signal([0.01, 0.02], -1) == 0.0

    def test_insufficient_data_returns_zero(self):
        assert momentum_signal([0.01], 2) == 0.0

    def test_empty_returns_zero(self):
        assert momentum_signal([], 1) == 0.0

    def test_lookback_equals_length(self):
        rets = [0.01, 0.02, 0.03]
        result = momentum_signal(rets, 3)
        assert result != 0.0  # should compute

    def test_lookback_one(self):
        # lookback=1: window=[0.05], mu=0.05, var=0/(max(0,1))=0, sd=sqrt(1e-15)
        # signal = 0.05/sqrt(1e-15) -> very large -> clipped to 1.0
        result = momentum_signal([0.05], 1)
        assert result == 1.0

    def test_lookback_one_negative(self):
        result = momentum_signal([-0.05], 1)
        assert result == -1.0

    def test_positive_trend(self):
        rets = [0.01, 0.02, 0.03, 0.04, 0.05]
        result = momentum_signal(rets, 5)
        assert result > 0.0
        assert result <= 1.0

    def test_negative_trend(self):
        rets = [-0.01, -0.02, -0.03, -0.04, -0.05]
        result = momentum_signal(rets, 5)
        assert result < 0.0
        assert result >= -1.0

    def test_uses_last_n_values(self):
        # First 3 values are noise; lookback=2 uses only last 2
        rets = [100.0, -100.0, 50.0, 0.01, 0.02]
        result_lb2 = momentum_signal(rets, 2)
        # should be based on [0.01, 0.02] only
        assert result_lb2 > 0.0

    def test_hand_computed(self):
        window = [0.01, -0.01]
        mu = 0.0
        # signal = 0/sd = 0
        result = momentum_signal(window, 2)
        assert result == 0.0

    def test_hand_computed_nonzero(self):
        window = [0.02, 0.04]
        mu = 0.03
        var = ((0.02 - 0.03) ** 2 + (0.04 - 0.03) ** 2) / 1  # ddof=1
        sd = math.sqrt(var)
        expected = _clip(mu / sd, -1.0, 1.0)
        result = momentum_signal(window, 2)
        assert result == pytest.approx(expected)

    def test_output_range(self):
        # Large positive returns -> should clip to 1.0
        rets = [1.0, 1.0, 1.0]
        result = momentum_signal(rets, 3)
        assert -1.0 <= result <= 1.0

    def test_determinism(self):
        rets = [0.01, -0.02, 0.015, 0.005, -0.01]
        r1 = momentum_signal(rets, 3)
        r2 = momentum_signal(rets, 3)
        assert r1 == r2

    def test_input_not_mutated(self):
        rets = [0.01, 0.02, 0.03]
        original = rets.copy()
        momentum_signal(rets, 2)
        assert rets == original


# =============================================================================
# SECTION 3 -- mean_reversion_signal
# =============================================================================

class TestMeanReversionSignal:
    def test_negates_momentum(self):
        rets = [0.01, 0.02, 0.03]
        mom = momentum_signal(rets, 3)
        mr = mean_reversion_signal(rets, 3)
        assert mr == pytest.approx(-mom)

    def test_zero_when_insufficient(self):
        assert mean_reversion_signal([0.01], 2) == 0.0

    def test_zero_when_lookback_zero(self):
        assert mean_reversion_signal([0.01], 0) == 0.0

    def test_range(self):
        rets = [0.05, 0.10, 0.15]
        result = mean_reversion_signal(rets, 3)
        assert -1.0 <= result <= 1.0

    def test_determinism(self):
        rets = [0.01, -0.02, 0.03]
        r1 = mean_reversion_signal(rets, 2)
        r2 = mean_reversion_signal(rets, 2)
        assert r1 == r2


# =============================================================================
# SECTION 4 -- combine_signals
# =============================================================================

class TestCombineSignals:
    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="equal length"):
            combine_signals([0.5], [1.0, 2.0])

    def test_empty_returns_zero(self):
        assert combine_signals([], []) == 0.0

    def test_zero_weights_returns_zero(self):
        assert combine_signals([0.5, -0.3], [0.0, 0.0]) == 0.0

    def test_single_signal(self):
        assert combine_signals([0.7], [1.0]) == pytest.approx(0.7)

    def test_equal_weights(self):
        result = combine_signals([0.4, 0.6], [1.0, 1.0])
        assert result == pytest.approx(0.5)

    def test_unequal_weights(self):
        # (0.4*2 + 0.6*1) / (2+1) = 1.4/3
        result = combine_signals([0.4, 0.6], [2.0, 1.0])
        assert result == pytest.approx(1.4 / 3.0)

    def test_clips_to_positive_one(self):
        result = combine_signals([1.0, 1.0], [1.0, 1.0])
        assert result == 1.0

    def test_clips_to_negative_one(self):
        result = combine_signals([-1.0, -1.0], [1.0, 1.0])
        assert result == -1.0

    def test_near_zero_weight(self):
        result = combine_signals([0.5], [1e-16])
        assert result == 0.0

    def test_determinism(self):
        s = [0.3, -0.5, 0.1]
        w = [1.0, 2.0, 0.5]
        r1 = combine_signals(s, w)
        r2 = combine_signals(s, w)
        assert r1 == r2

    def test_input_not_mutated(self):
        s = [0.3, 0.5]
        w = [1.0, 1.0]
        s_orig, w_orig = s.copy(), w.copy()
        combine_signals(s, w)
        assert s == s_orig
        assert w == w_orig


# =============================================================================
# SECTION 5 -- run_strategy
# =============================================================================

def _make_series(n: int = 50):
    """Generate deterministic test returns and prices."""
    returns = [0.005 * ((-1) ** i) for i in range(n)]
    prices = [100.0 + i * 0.1 for i in range(n)]
    return returns, prices


class TestRunStrategyValidation:
    def test_window_too_small_raises(self):
        rets, prices = _make_series(50)
        with pytest.raises(ValueError, match="window must be >= 20"):
            run_strategy(rets, prices, window=19, step=1,
                         initial_capital=100_000.0,
                         regime=GlobalRegimeState.RISK_ON,
                         meta_uncertainty=0.2)

    def test_step_zero_raises(self):
        rets, prices = _make_series(50)
        with pytest.raises(ValueError, match="step must be >= 1"):
            run_strategy(rets, prices, window=20, step=0,
                         initial_capital=100_000.0,
                         regime=GlobalRegimeState.RISK_ON,
                         meta_uncertainty=0.2)

    def test_negative_capital_raises(self):
        rets, prices = _make_series(50)
        with pytest.raises(ValueError, match="initial_capital must be > 0"):
            run_strategy(rets, prices, window=20, step=1,
                         initial_capital=-1.0,
                         regime=GlobalRegimeState.RISK_ON,
                         meta_uncertainty=0.2)

    def test_zero_capital_raises(self):
        rets, prices = _make_series(50)
        with pytest.raises(ValueError, match="initial_capital must be > 0"):
            run_strategy(rets, prices, window=20, step=1,
                         initial_capital=0.0,
                         regime=GlobalRegimeState.RISK_ON,
                         meta_uncertainty=0.2)

    def test_length_mismatch_raises(self):
        rets, prices = _make_series(50)
        with pytest.raises(ValueError, match="equal length"):
            run_strategy(rets, prices[:40], window=20, step=1,
                         initial_capital=100_000.0,
                         regime=GlobalRegimeState.RISK_ON,
                         meta_uncertainty=0.2)

    def test_series_too_short_raises(self):
        rets, prices = _make_series(25)
        with pytest.raises(ValueError, match="series length"):
            run_strategy(rets, prices, window=20, step=10,
                         initial_capital=100_000.0,
                         regime=GlobalRegimeState.RISK_ON,
                         meta_uncertainty=0.2)


class TestRunStrategyOutputStructure:
    @pytest.fixture()
    def result(self):
        rets, prices = _make_series(50)
        return run_strategy(
            returns_series=rets,
            asset_price_series=prices,
            window=20, step=5,
            initial_capital=100_000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )

    def test_top_level_keys(self, result):
        assert set(result.keys()) == {"segments", "segment_metrics", "aggregate"}

    def test_segments_is_list(self, result):
        assert isinstance(result["segments"], list)
        assert len(result["segments"]) > 0

    def test_segment_metrics_matches_segments(self, result):
        assert len(result["segment_metrics"]) == len(result["segments"])

    def test_segment_has_required_keys(self, result):
        for seg in result["segments"]:
            assert "start" in seg
            assert "end" in seg
            assert "equity_curve" in seg

    def test_segment_equity_curve_not_empty(self, result):
        for seg in result["segments"]:
            assert len(seg["equity_curve"]) > 0

    def test_segment_start_end_ordering(self, result):
        for seg in result["segments"]:
            assert seg["start"] < seg["end"]

    def test_segments_cover_full_range(self, result):
        first_start = result["segments"][0]["start"]
        last_end = result["segments"][-1]["end"]
        assert first_start == 20  # window
        assert last_end == 50  # series length

    def test_aggregate_has_metric_keys(self, result):
        expected = {"total_return", "cagr", "volatility", "sharpe", "max_drawdown"}
        assert set(result["aggregate"].keys()) == expected

    def test_aggregate_values_finite(self, result):
        for k, v in result["aggregate"].items():
            assert math.isfinite(v), f"aggregate[{k}] is not finite: {v}"

    def test_segment_equity_values_positive(self, result):
        for seg in result["segments"]:
            for eq in seg["equity_curve"]:
                assert eq > 0.0


class TestRunStrategyBehavior:
    def test_step_one_produces_most_segments(self):
        rets, prices = _make_series(30)
        r1 = run_strategy(rets, prices, window=20, step=1,
                          initial_capital=100_000.0,
                          regime=GlobalRegimeState.RISK_ON,
                          meta_uncertainty=0.2)
        r5 = run_strategy(rets, prices, window=20, step=5,
                          initial_capital=100_000.0,
                          regime=GlobalRegimeState.RISK_ON,
                          meta_uncertainty=0.2)
        assert len(r1["segments"]) >= len(r5["segments"])

    def test_different_regimes_may_differ(self):
        rets, prices = _make_series(50)
        kwargs = dict(window=20, step=5, initial_capital=100_000.0,
                      meta_uncertainty=0.2)
        r_on = run_strategy(rets, prices, regime=GlobalRegimeState.RISK_ON, **kwargs)
        r_crisis = run_strategy(rets, prices, regime=GlobalRegimeState.CRISIS, **kwargs)
        # At least one metric should differ (CRISIS dampening)
        on_agg = r_on["aggregate"]
        cr_agg = r_crisis["aggregate"]
        differs = any(on_agg[k] != cr_agg[k] for k in on_agg)
        assert differs

    def test_all_regimes_succeed(self):
        rets, prices = _make_series(50)
        for regime in GlobalRegimeState:
            result = run_strategy(
                rets, prices, window=20, step=5,
                initial_capital=100_000.0,
                regime=regime, meta_uncertainty=0.2,
            )
            assert "aggregate" in result

    def test_custom_periods_per_year(self):
        rets, prices = _make_series(50)
        kwargs = dict(window=20, step=5, initial_capital=100_000.0,
                      regime=GlobalRegimeState.RISK_ON, meta_uncertainty=0.2)
        r252 = run_strategy(rets, prices, periods_per_year=252, **kwargs)
        r12 = run_strategy(rets, prices, periods_per_year=12, **kwargs)
        # Annualisation affects cagr and volatility
        assert r252["aggregate"]["cagr"] != r12["aggregate"]["cagr"]


class TestRunStrategyDeterminism:
    def test_identical_calls_produce_identical_output(self):
        rets, prices = _make_series(50)
        kwargs = dict(
            returns_series=rets, asset_price_series=prices,
            window=20, step=5, initial_capital=100_000.0,
            regime=GlobalRegimeState.RISK_ON, meta_uncertainty=0.2,
        )
        r1 = run_strategy(**kwargs)
        r2 = run_strategy(**kwargs)
        # Compare aggregate metrics
        for k in r1["aggregate"]:
            assert r1["aggregate"][k] == r2["aggregate"][k]
        # Compare segment count
        assert len(r1["segments"]) == len(r2["segments"])

    def test_inputs_not_mutated(self):
        rets, prices = _make_series(50)
        rets_orig = rets.copy()
        prices_orig = prices.copy()
        run_strategy(
            returns_series=rets, asset_price_series=prices,
            window=20, step=5, initial_capital=100_000.0,
            regime=GlobalRegimeState.RISK_ON, meta_uncertainty=0.2,
        )
        assert rets == rets_orig
        assert prices == prices_orig


# =============================================================================
# SECTION 6 -- MODULE __all__
# =============================================================================

class TestModuleAll:
    def test_all_contains_momentum(self):
        from jarvis.strategy.engine import __all__
        assert "momentum_signal" in __all__

    def test_all_contains_mean_reversion(self):
        from jarvis.strategy.engine import __all__
        assert "mean_reversion_signal" in __all__

    def test_all_contains_combine(self):
        from jarvis.strategy.engine import __all__
        assert "combine_signals" in __all__

    def test_all_contains_run_strategy(self):
        from jarvis.strategy.engine import __all__
        assert "run_strategy" in __all__

    def test_all_length(self):
        from jarvis.strategy.engine import __all__
        assert len(__all__) == 4
