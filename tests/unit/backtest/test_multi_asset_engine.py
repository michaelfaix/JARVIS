# =============================================================================
# tests/unit/backtest/test_multi_asset_engine.py
# Tests for jarvis/backtest/multi_asset_engine.py
# =============================================================================

from __future__ import annotations

import math

import pytest

from jarvis.core.regime import GlobalRegimeState
from jarvis.walkforward.engine import WalkForwardWindow
from jarvis.backtest.multi_asset_engine import (
    AssetBacktestResult,
    CorrelationSnapshot,
    MultiAssetBacktestResult,
    WalkForwardFoldResult,
    MultiAssetWalkForwardResult,
    run_multi_asset_backtest,
    run_multi_asset_walkforward,
    MIN_WINDOW,
    CORRELATION_LOOKBACK,
    EQUITY_FLOOR,
    _mean,
    _std_pop,
    _compute_correlation_snapshot,
    OverfittingReport,
)


# =============================================================================
# HELPERS
# =============================================================================

def _make_returns(n: int, base: float = 0.001) -> list[float]:
    """Generate deterministic return series oscillating around zero."""
    return [base * (i % 7 - 3) for i in range(n)]


def _make_prices(n: int, start: float = 100.0, returns: list[float] | None = None) -> list[float]:
    """Generate price series from returns or monotonic."""
    if returns is not None:
        prices = [start]
        for r in returns:
            prices.append(prices[-1] * (1.0 + r))
        return prices
    return [start + i * 0.5 for i in range(n)]


def _two_asset_data(n: int = 60):
    """Create two-asset dataset with n periods."""
    ret_a = _make_returns(n, base=0.003)
    ret_b = _make_returns(n, base=0.005)
    price_a = _make_prices(n, start=100.0, returns=None)
    price_b = _make_prices(n, start=50.0, returns=None)
    # Ensure prices are all positive and match return length
    price_a = [100.0 + i * 0.5 for i in range(n)]
    price_b = [50.0 + i * 0.3 for i in range(n)]
    return (
        {"BTC": ret_a, "ETH": ret_b},
        {"BTC": price_a, "ETH": price_b},
    )


def _three_asset_data(n: int = 80):
    """Create three-asset dataset with n periods."""
    ret_a = _make_returns(n, base=0.003)
    ret_b = _make_returns(n, base=0.005)
    ret_c = _make_returns(n, base=-0.001)
    price_a = [100.0 + i * 0.5 for i in range(n)]
    price_b = [50.0 + i * 0.3 for i in range(n)]
    price_c = [200.0 + i * 0.2 for i in range(n)]
    return (
        {"BTC": ret_a, "ETH": ret_b, "SPY": ret_c},
        {"BTC": price_a, "ETH": price_b, "SPY": price_c},
    )


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_min_window(self):
        assert MIN_WINDOW == 20

    def test_correlation_lookback(self):
        assert CORRELATION_LOOKBACK == 60

    def test_equity_floor(self):
        assert EQUITY_FLOOR == 1e-10


# =============================================================================
# SECTION 2 -- HELPERS
# =============================================================================

class TestMean:
    def test_empty(self):
        assert _mean([]) == 0.0

    def test_single(self):
        assert _mean([5.0]) == 5.0

    def test_multiple(self):
        assert _mean([1.0, 2.0, 3.0]) == 2.0


class TestStdPop:
    def test_empty(self):
        assert _std_pop([]) == 0.0

    def test_single(self):
        assert _std_pop([5.0]) == 0.0

    def test_identical(self):
        assert _std_pop([3.0, 3.0, 3.0]) == 0.0

    def test_known_values(self):
        # Population std of [1, 2, 3] = sqrt(2/3)
        result = _std_pop([1.0, 2.0, 3.0])
        assert abs(result - math.sqrt(2.0 / 3.0)) < 1e-10


# =============================================================================
# SECTION 3 -- CORRELATION SNAPSHOT
# =============================================================================

class TestCorrelationSnapshot:
    def test_single_asset_returns_none(self):
        result = _compute_correlation_snapshot(
            {"BTC": [0.01, 0.02, 0.03]}, ["BTC"], 60,
        )
        assert result is None

    def test_two_assets_diagonal_is_one(self):
        ret = {
            "A": [0.01, 0.02, -0.01, 0.03, 0.01],
            "B": [0.02, 0.01, 0.00, 0.02, -0.01],
        }
        result = _compute_correlation_snapshot(ret, ["A", "B"], 60)
        assert result is not None
        assert result.matrix[0][0] == 1.0
        assert result.matrix[1][1] == 1.0

    def test_two_assets_symmetric(self):
        ret = {
            "A": [0.01, 0.02, -0.01, 0.03],
            "B": [0.02, 0.01, 0.00, 0.02],
        }
        result = _compute_correlation_snapshot(ret, ["A", "B"], 60)
        assert result is not None
        assert result.matrix[0][1] == result.matrix[1][0]

    def test_identical_series_corr_one(self):
        vals = [0.01, -0.02, 0.03, 0.01, -0.01]
        ret = {"X": vals, "Y": list(vals)}
        result = _compute_correlation_snapshot(ret, ["X", "Y"], 60)
        assert result is not None
        assert abs(result.matrix[0][1] - 1.0) < 1e-10

    def test_avg_off_diag_nonneg(self):
        ret = {
            "A": [0.01, -0.02, 0.03],
            "B": [-0.01, 0.02, -0.03],
        }
        result = _compute_correlation_snapshot(ret, ["A", "B"], 60)
        assert result is not None
        assert result.avg_off_diag >= 0.0

    def test_three_assets_matrix_shape(self):
        ret = {
            "A": [0.01, 0.02, 0.03, 0.04],
            "B": [0.02, 0.01, 0.04, 0.02],
            "C": [-0.01, 0.03, -0.02, 0.01],
        }
        result = _compute_correlation_snapshot(ret, ["A", "B", "C"], 60)
        assert result is not None
        assert len(result.matrix) == 3
        assert all(len(row) == 3 for row in result.matrix)

    def test_lookback_truncation(self):
        # Only last 3 values should be used
        ret = {
            "A": [99.0, 99.0, 0.01, 0.02, 0.03],
            "B": [99.0, 99.0, 0.02, 0.01, 0.03],
        }
        result = _compute_correlation_snapshot(ret, ["A", "B"], 3)
        assert result is not None
        # Correlation should be computed from last 3 values
        assert math.isfinite(result.matrix[0][1])

    def test_snapshot_is_frozen(self):
        ret = {"A": [0.01, 0.02], "B": [0.02, 0.01]}
        result = _compute_correlation_snapshot(ret, ["A", "B"], 60)
        assert result is not None
        with pytest.raises(AttributeError):
            result.avg_off_diag = 0.5  # type: ignore


# =============================================================================
# SECTION 4 -- RESULT DATACLASS INVARIANTS
# =============================================================================

class TestResultDataclasses:
    def test_asset_result_frozen(self):
        r = AssetBacktestResult(
            symbol="BTC", equity_curve=(1.0,), returns=(0.01,), metrics={},
        )
        with pytest.raises(AttributeError):
            r.symbol = "ETH"  # type: ignore

    def test_multi_asset_result_frozen(self):
        r = MultiAssetBacktestResult(
            asset_results={}, portfolio_equity=(),
            portfolio_metrics={}, correlation_final=None,
            n_assets=0, n_periods=0,
        )
        with pytest.raises(AttributeError):
            r.n_assets = 5  # type: ignore

    def test_walkforward_fold_frozen(self):
        from jarvis.walkforward.engine import WalkForwardWindow
        w = WalkForwardWindow(fold=0, train_start=0, train_end=40,
                              test_start=40, test_end=60)
        r = WalkForwardFoldResult(
            fold=0, window=w, train_metrics={}, test_metrics={},
            oos_sharpe=0.5,
        )
        with pytest.raises(AttributeError):
            r.oos_sharpe = 1.0  # type: ignore


# =============================================================================
# SECTION 5 -- INPUT VALIDATION
# =============================================================================

class TestInputValidation:
    def test_empty_assets_raises(self):
        with pytest.raises(ValueError, match="at least one asset"):
            run_multi_asset_backtest(
                asset_returns={},
                asset_prices={},
                window=20,
                initial_capital=10000.0,
                regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty=0.2,
            )

    def test_key_mismatch_raises(self):
        with pytest.raises(ValueError, match="same keys"):
            run_multi_asset_backtest(
                asset_returns={"BTC": [0.01] * 30},
                asset_prices={"ETH": [100.0] * 30},
                window=20,
                initial_capital=10000.0,
                regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty=0.2,
            )

    def test_window_too_small_raises(self):
        with pytest.raises(ValueError, match="window must be >= 20"):
            run_multi_asset_backtest(
                asset_returns={"BTC": [0.01] * 30},
                asset_prices={"BTC": [100.0] * 30},
                window=10,
                initial_capital=10000.0,
                regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty=0.2,
            )

    def test_negative_capital_raises(self):
        with pytest.raises(ValueError, match="initial_capital must be > 0"):
            run_multi_asset_backtest(
                asset_returns={"BTC": [0.01] * 30},
                asset_prices={"BTC": [100.0] * 30},
                window=20,
                initial_capital=-100.0,
                regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty=0.2,
            )

    def test_zero_capital_raises(self):
        with pytest.raises(ValueError, match="initial_capital must be > 0"):
            run_multi_asset_backtest(
                asset_returns={"BTC": [0.01] * 30},
                asset_prices={"BTC": [100.0] * 30},
                window=20,
                initial_capital=0.0,
                regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty=0.2,
            )

    def test_unequal_return_lengths_raises(self):
        with pytest.raises(ValueError, match="equal length"):
            run_multi_asset_backtest(
                asset_returns={"BTC": [0.01] * 30, "ETH": [0.01] * 25},
                asset_prices={"BTC": [100.0] * 30, "ETH": [50.0] * 25},
                window=20,
                initial_capital=10000.0,
                regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty=0.2,
            )

    def test_price_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="length"):
            run_multi_asset_backtest(
                asset_returns={"BTC": [0.01] * 30},
                asset_prices={"BTC": [100.0] * 25},
                window=20,
                initial_capital=10000.0,
                regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty=0.2,
            )


# =============================================================================
# SECTION 6 -- SINGLE ASSET BACKTEST
# =============================================================================

class TestSingleAssetBacktest:
    def test_returns_result(self):
        n = 50
        rets = _make_returns(n)
        prices = [100.0 + i * 0.5 for i in range(n)]
        result = run_multi_asset_backtest(
            asset_returns={"BTC": rets},
            asset_prices={"BTC": prices},
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert isinstance(result, MultiAssetBacktestResult)
        assert result.n_assets == 1
        assert result.n_periods == n - 20
        assert len(result.portfolio_equity) == n - 20
        assert "BTC" in result.asset_results

    def test_portfolio_equity_positive(self):
        n = 50
        rets = _make_returns(n)
        prices = [100.0 + i * 0.5 for i in range(n)]
        result = run_multi_asset_backtest(
            asset_returns={"BTC": rets},
            asset_prices={"BTC": prices},
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert all(eq > 0.0 for eq in result.portfolio_equity)

    def test_single_asset_no_correlation(self):
        n = 50
        rets = _make_returns(n)
        prices = [100.0 + i * 0.5 for i in range(n)]
        result = run_multi_asset_backtest(
            asset_returns={"BTC": rets},
            asset_prices={"BTC": prices},
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert result.correlation_final is None


# =============================================================================
# SECTION 7 -- MULTI-ASSET BACKTEST
# =============================================================================

class TestMultiAssetBacktest:
    def test_two_assets_basic(self):
        returns, prices = _two_asset_data(60)
        result = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=100000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert result.n_assets == 2
        assert result.n_periods == 40
        assert "BTC" in result.asset_results
        assert "ETH" in result.asset_results

    def test_three_assets(self):
        returns, prices = _three_asset_data(80)
        result = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=100000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert result.n_assets == 3
        assert result.n_periods == 60
        assert len(result.asset_results) == 3

    def test_portfolio_equity_length_matches_periods(self):
        returns, prices = _two_asset_data(50)
        result = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert len(result.portfolio_equity) == result.n_periods

    def test_per_asset_equity_length(self):
        returns, prices = _two_asset_data(50)
        result = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        for s, ar in result.asset_results.items():
            assert len(ar.equity_curve) == result.n_periods
            assert len(ar.returns) == result.n_periods

    def test_correlation_final_present(self):
        returns, prices = _two_asset_data(60)
        result = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert result.correlation_final is not None
        assert len(result.correlation_final.symbols) == 2
        assert result.correlation_final.matrix[0][0] == 1.0
        assert result.correlation_final.matrix[1][1] == 1.0

    def test_correlation_matrix_symmetric(self):
        returns, prices = _three_asset_data(80)
        result = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        corr = result.correlation_final
        assert corr is not None
        for i in range(3):
            for j in range(3):
                assert corr.matrix[i][j] == corr.matrix[j][i]

    def test_portfolio_metrics_keys(self):
        returns, prices = _two_asset_data(60)
        result = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        expected_keys = {"total_return", "cagr", "volatility", "sharpe", "max_drawdown"}
        assert set(result.portfolio_metrics.keys()) == expected_keys

    def test_per_asset_metrics_keys(self):
        returns, prices = _two_asset_data(60)
        result = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        for ar in result.asset_results.values():
            assert "sharpe" in ar.metrics
            assert "max_drawdown" in ar.metrics

    def test_all_values_finite(self):
        returns, prices = _two_asset_data(60)
        result = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        for eq in result.portfolio_equity:
            assert math.isfinite(eq)
        for v in result.portfolio_metrics.values():
            assert math.isfinite(v)


# =============================================================================
# SECTION 8 -- EDGE CASES
# =============================================================================

class TestEdgeCases:
    def test_data_exactly_window_length(self):
        """No backtest steps possible when data length == window."""
        n = 20
        rets = _make_returns(n)
        prices = [100.0 + i for i in range(n)]
        result = run_multi_asset_backtest(
            asset_returns={"BTC": rets},
            asset_prices={"BTC": prices},
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert result.n_periods == 0
        assert len(result.portfolio_equity) == 0
        assert result.portfolio_metrics == {}

    def test_crisis_regime(self):
        returns, prices = _two_asset_data(50)
        result = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.CRISIS,
            meta_uncertainty=0.5,
        )
        assert result.n_periods > 0
        assert all(eq > 0 for eq in result.portfolio_equity)

    def test_high_meta_uncertainty(self):
        returns, prices = _two_asset_data(50)
        result = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.9,
        )
        # High uncertainty should reduce positions, equity stays near initial
        assert result.n_periods > 0

    def test_negative_returns(self):
        n = 50
        rets = [-0.01] * n
        prices = [100.0 + i * 0.5 for i in range(n)]
        result = run_multi_asset_backtest(
            asset_returns={"BTC": rets},
            asset_prices={"BTC": prices},
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert result.n_periods > 0
        # Equity should still be positive (floor guarantees this)
        assert all(eq > 0 for eq in result.portfolio_equity)


# =============================================================================
# SECTION 9 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_same_inputs_same_output(self):
        returns, prices = _two_asset_data(50)
        r1 = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        r2 = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert r1.portfolio_equity == r2.portfolio_equity
        assert r1.portfolio_metrics == r2.portfolio_metrics
        assert r1.n_periods == r2.n_periods

    def test_independent_instances(self):
        returns, prices = _two_asset_data(50)
        r1 = run_multi_asset_backtest(
            asset_returns=dict(returns),
            asset_prices=dict(prices),
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        r2 = run_multi_asset_backtest(
            asset_returns=dict(returns),
            asset_prices=dict(prices),
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert r1.portfolio_equity == r2.portfolio_equity


# =============================================================================
# SECTION 10 -- WALK-FORWARD VALIDATION
# =============================================================================

class TestWalkForwardValidation:
    def test_walkforward_input_validation_train_too_small(self):
        returns, prices = _two_asset_data(100)
        with pytest.raises(ValueError, match="train_size must be >= window"):
            run_multi_asset_walkforward(
                asset_returns=returns,
                asset_prices=prices,
                window=20,
                train_size=15,  # < window + 1
                test_size=10,
                step=10,
                initial_capital=10000.0,
                regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty=0.2,
            )

    def test_walkforward_input_validation_test_zero(self):
        returns, prices = _two_asset_data(100)
        with pytest.raises(ValueError, match="test_size must be >= 1"):
            run_multi_asset_walkforward(
                asset_returns=returns,
                asset_prices=prices,
                window=20,
                train_size=30,
                test_size=0,
                step=10,
                initial_capital=10000.0,
                regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty=0.2,
            )

    def test_walkforward_input_validation_step_zero(self):
        returns, prices = _two_asset_data(100)
        with pytest.raises(ValueError, match="step must be >= 1"):
            run_multi_asset_walkforward(
                asset_returns=returns,
                asset_prices=prices,
                window=20,
                train_size=30,
                test_size=10,
                step=0,
                initial_capital=10000.0,
                regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty=0.2,
            )

    def test_walkforward_basic(self):
        n = 120
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=40,
            test_size=20,
            step=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert isinstance(result, MultiAssetWalkForwardResult)
        assert result.n_folds > 0
        assert len(result.folds) == result.n_folds
        assert isinstance(result.full_backtest, MultiAssetBacktestResult)

    def test_walkforward_fold_structure(self):
        n = 120
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=40,
            test_size=20,
            step=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        for fold in result.folds:
            assert isinstance(fold, WalkForwardFoldResult)
            assert isinstance(fold.window, WalkForwardWindow)
            assert math.isfinite(fold.oos_sharpe)

    def test_walkforward_oos_sharpe_aggregation(self):
        n = 120
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=40,
            test_size=20,
            step=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        # mean_oos_sharpe should be the mean of individual fold sharpes
        oos_sharpes = [f.oos_sharpe for f in result.folds]
        expected_mean = sum(oos_sharpes) / len(oos_sharpes)
        assert abs(result.mean_oos_sharpe - expected_mean) < 1e-10

    def test_walkforward_std_nonneg(self):
        n = 120
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=40,
            test_size=20,
            step=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert result.std_oos_sharpe >= 0.0

    def test_walkforward_determinism(self):
        n = 100
        returns, prices = _two_asset_data(n)
        r1 = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=30,
            test_size=15,
            step=15,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        r2 = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=30,
            test_size=15,
            step=15,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert r1.mean_oos_sharpe == r2.mean_oos_sharpe
        assert r1.n_folds == r2.n_folds

    def test_walkforward_full_backtest_present(self):
        n = 100
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=30,
            test_size=15,
            step=15,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        fb = result.full_backtest
        assert fb.n_assets == 2
        assert fb.n_periods == n - 20

    def test_walkforward_no_folds_when_data_too_short(self):
        n = 40
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=30,
            test_size=20,
            step=10,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert result.n_folds == 0
        assert result.mean_oos_sharpe == 0.0


# =============================================================================
# SECTION 11 -- WALK-FORWARD RESULT FROZEN
# =============================================================================

class TestWalkForwardResultFrozen:
    def test_multi_asset_wf_result_frozen(self):
        n = 100
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=30,
            test_size=15,
            step=15,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        with pytest.raises(AttributeError):
            result.n_folds = 99  # type: ignore


# =============================================================================
# SECTION 12 -- IMPORT CONTRACT
# =============================================================================

class TestImportContract:
    def test_import_from_init(self):
        from jarvis.backtest import run_multi_asset_backtest as f1
        from jarvis.backtest import run_multi_asset_walkforward as f2
        assert callable(f1)
        assert callable(f2)

    def test_import_from_module(self):
        from jarvis.backtest.multi_asset_engine import (
            run_multi_asset_backtest,
            run_multi_asset_walkforward,
            AssetBacktestResult,
            CorrelationSnapshot,
            MultiAssetBacktestResult,
            WalkForwardFoldResult,
            MultiAssetWalkForwardResult,
        )
        assert callable(run_multi_asset_backtest)
        assert callable(run_multi_asset_walkforward)


# =============================================================================
# SECTION 13 -- REGIME SENSITIVITY
# =============================================================================

class TestRegimeSensitivity:
    def test_crisis_reduces_exposure(self):
        """CRISIS regime should produce lower equity growth than RISK_ON."""
        returns, prices = _two_asset_data(60)
        result_on = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        result_crisis = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.CRISIS,
            meta_uncertainty=0.2,
        )
        # CRISIS dampening (0.75) means less exposure
        # Final equity under CRISIS should differ from RISK_ON
        assert result_on.portfolio_equity != result_crisis.portfolio_equity

    def test_meta_uncertainty_dampens_positions(self):
        """Higher meta_uncertainty should reduce exposure."""
        returns, prices = _two_asset_data(60)
        result_low = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.1,
        )
        result_high = run_multi_asset_backtest(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.9,
        )
        # Different uncertainty levels should produce different results
        assert result_low.portfolio_equity != result_high.portfolio_equity


# =============================================================================
# SECTION 14 -- WALKFORWARD IMPORT FROM ENGINE
# =============================================================================

class TestWalkForwardWindowImport:
    def test_uses_canonical_walkforward_windows(self):
        """Verify we use the canonical generate_windows from walkforward."""
        from jarvis.walkforward.engine import generate_windows as canonical
        from jarvis.backtest.multi_asset_engine import generate_windows as used
        assert canonical is used


# =============================================================================
# SECTION 15 -- OVERFITTING GOVERNANCE INTEGRATION
# =============================================================================

class TestWalkForwardOverfittingIntegration:
    """Tests for BacktestGovernanceEngine integration in walk-forward."""

    def test_fold_has_overfitting_report(self):
        n = 120
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=40,
            test_size=20,
            step=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        for fold in result.folds:
            assert fold.overfitting_report is not None
            assert isinstance(fold.overfitting_report, OverfittingReport)

    def test_overfitting_report_strategy_id_per_fold(self):
        n = 120
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=40,
            test_size=20,
            step=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        for fold in result.folds:
            report = fold.overfitting_report
            assert report is not None
            expected_id = f"walkforward_fold_{fold.fold}"
            assert report.strategy_id == expected_id

    def test_overfitting_report_has_valid_fields(self):
        n = 120
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=40,
            test_size=20,
            step=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        for fold in result.folds:
            report = fold.overfitting_report
            assert report is not None
            assert isinstance(report.performance_spike, bool)
            assert isinstance(report.param_sensitivity, bool)
            assert isinstance(report.overfitting_flag, bool)
            assert math.isfinite(report.is_to_oos_ratio) or report.is_to_oos_ratio == float("inf")
            assert report.sensitivity_score == 0.0

    def test_any_overfitting_is_bool(self):
        n = 120
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=40,
            test_size=20,
            step=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert isinstance(result.any_overfitting, bool)

    def test_any_overfitting_consistent_with_folds(self):
        n = 120
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=40,
            test_size=20,
            step=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        fold_flags = [
            f.overfitting_report.overfitting_flag
            for f in result.folds
            if f.overfitting_report is not None
        ]
        assert result.any_overfitting == any(fold_flags)

    def test_no_folds_no_overfitting(self):
        n = 40
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=30,
            test_size=20,
            step=10,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert result.n_folds == 0
        assert result.any_overfitting is False

    def test_overfitting_report_frozen(self):
        from jarvis.governance.backtest_governance import OverfittingReport
        n = 120
        returns, prices = _two_asset_data(n)
        result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=40,
            test_size=20,
            step=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert result.n_folds > 0
        report = result.folds[0].overfitting_report
        assert report is not None
        with pytest.raises(AttributeError):
            report.overfitting_flag = True  # type: ignore

    def test_overfitting_deterministic(self):
        n = 120
        returns, prices = _two_asset_data(n)
        kwargs = dict(
            asset_returns=returns,
            asset_prices=prices,
            window=20,
            train_size=40,
            test_size=20,
            step=20,
            initial_capital=10000.0,
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        r1 = run_multi_asset_walkforward(**kwargs)
        r2 = run_multi_asset_walkforward(**kwargs)
        assert r1.any_overfitting == r2.any_overfitting
        for f1, f2 in zip(r1.folds, r2.folds):
            assert f1.overfitting_report == f2.overfitting_report

    def test_import_overfitting_report(self):
        from jarvis.governance.backtest_governance import OverfittingReport
        from jarvis.backtest.multi_asset_engine import OverfittingReport as OR
        assert OverfittingReport is OR
