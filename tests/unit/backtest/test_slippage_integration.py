# =============================================================================
# tests/unit/backtest/test_slippage_integration.py
# =============================================================================
#
# Tests for slippage_model integration in run_backtest() and
# run_multi_asset_backtest(). Verifies backward compatibility (None default),
# slippage reducing equity, determinism, and delegation to
# StrategyLab.compute_slippage().
#
# =============================================================================

import math

import pytest

from jarvis.backtest.engine import run_backtest
from jarvis.backtest.multi_asset_engine import run_multi_asset_backtest
from jarvis.core.regime import GlobalRegimeState
from jarvis.simulation.strategy_lab import SlippageModel, StrategyLab


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def stable_returns():
    """30 periods of tiny positive returns for a stable backtest."""
    return [0.0005] * 30


@pytest.fixture
def stable_prices():
    """30 periods of monotonically increasing prices."""
    prices = [100.0]
    for i in range(29):
        prices.append(prices[-1] * 1.0005)
    return prices


@pytest.fixture
def default_params():
    """Default backtest parameters."""
    return {
        "window": 20,
        "initial_capital": 10_000.0,
        "regime": GlobalRegimeState.RISK_ON,
        "meta_uncertainty": 0.2,
    }


@pytest.fixture
def slippage_model_small():
    """Small slippage model for testing."""
    return SlippageModel(
        base_slippage_pct=0.0001,
        vol_multiplier=0.01,
        size_impact=0.001,
    )


@pytest.fixture
def slippage_model_large():
    """Large slippage model to amplify the effect."""
    return SlippageModel(
        base_slippage_pct=0.01,
        vol_multiplier=0.1,
        size_impact=0.05,
    )


@pytest.fixture
def multi_asset_returns():
    """Two-asset returns for multi-asset backtest (30 periods)."""
    return {
        "A": [0.0005] * 30,
        "B": [0.0003] * 30,
    }


@pytest.fixture
def multi_asset_prices():
    """Two-asset price series (30 periods)."""
    prices_a = [100.0]
    prices_b = [50.0]
    for i in range(29):
        prices_a.append(prices_a[-1] * 1.0005)
        prices_b.append(prices_b[-1] * 1.0003)
    return {"A": prices_a, "B": prices_b}


# =============================================================================
# SECTION 1 -- BACKWARD COMPATIBILITY (run_backtest)
# =============================================================================

class TestBacktestBackwardCompatibility:
    """Verify that run_backtest without slippage_model produces identical results."""

    def test_default_none(self, stable_returns, stable_prices, default_params):
        """Calling without slippage_model works (backward compatible)."""
        curve = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            **default_params,
        )
        assert len(curve) == 10  # 30 - 20
        assert all(isinstance(v, float) for v in curve)

    def test_explicit_none_matches_default(self, stable_returns, stable_prices, default_params):
        """Explicit slippage_model=None produces identical results to omitting it."""
        curve_default = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            **default_params,
        )
        curve_none = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            slippage_model=None,
            **default_params,
        )
        assert curve_default == curve_none

    def test_no_slippage_equity_grows(self, stable_returns, stable_prices, default_params):
        """With positive returns and no slippage, equity should grow."""
        curve = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            **default_params,
        )
        assert curve[-1] >= default_params["initial_capital"]


# =============================================================================
# SECTION 2 -- SLIPPAGE REDUCES EQUITY (run_backtest)
# =============================================================================

class TestBacktestSlippageReducesEquity:
    """Verify that adding slippage reduces final equity."""

    def test_slippage_reduces_final_equity(
        self, stable_returns, stable_prices, default_params, slippage_model_small
    ):
        """Equity with slippage should be <= equity without slippage."""
        curve_no_slip = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            **default_params,
        )
        curve_with_slip = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            slippage_model=slippage_model_small,
            **default_params,
        )
        assert curve_with_slip[-1] <= curve_no_slip[-1]

    def test_larger_slippage_reduces_more(
        self, stable_returns, stable_prices, default_params,
        slippage_model_small, slippage_model_large,
    ):
        """Larger slippage model should reduce equity more."""
        curve_small = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            slippage_model=slippage_model_small,
            **default_params,
        )
        curve_large = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            slippage_model=slippage_model_large,
            **default_params,
        )
        assert curve_large[-1] <= curve_small[-1]

    def test_same_curve_length(
        self, stable_returns, stable_prices, default_params, slippage_model_small
    ):
        """Equity curve length should be the same with or without slippage."""
        curve_no_slip = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            **default_params,
        )
        curve_with_slip = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            slippage_model=slippage_model_small,
            **default_params,
        )
        assert len(curve_with_slip) == len(curve_no_slip)

    def test_equity_floor_preserved(self, default_params):
        """Even with extreme slippage, equity floor (1e-10) is preserved."""
        returns = [-0.005] * 30
        prices = [100.0] * 30
        model = SlippageModel(
            base_slippage_pct=0.5,
            vol_multiplier=1.0,
            size_impact=1.0,
        )
        curve = run_backtest(
            returns_series=returns,
            asset_price_series=prices,
            slippage_model=model,
            **default_params,
        )
        assert all(v >= 1e-10 for v in curve)


# =============================================================================
# SECTION 3 -- DETERMINISM (run_backtest)
# =============================================================================

class TestBacktestSlippageDeterminism:
    """Verify determinism: same inputs produce identical outputs."""

    def test_deterministic_with_slippage(
        self, stable_returns, stable_prices, default_params, slippage_model_small
    ):
        """Two runs with identical inputs produce bit-identical outputs."""
        curve1 = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            slippage_model=slippage_model_small,
            **default_params,
        )
        curve2 = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            slippage_model=slippage_model_small,
            **default_params,
        )
        assert curve1 == curve2

    def test_deterministic_large_slippage(
        self, stable_returns, stable_prices, default_params, slippage_model_large
    ):
        """Determinism holds even with large slippage values."""
        curve1 = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            slippage_model=slippage_model_large,
            **default_params,
        )
        curve2 = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            slippage_model=slippage_model_large,
            **default_params,
        )
        assert curve1 == curve2


# =============================================================================
# SECTION 4 -- ZERO SLIPPAGE MODEL
# =============================================================================

class TestZeroSlippageModel:
    """A SlippageModel with all-zero parameters should match no-slippage."""

    def test_zero_model_matches_none(self, stable_returns, stable_prices, default_params):
        """SlippageModel(0, 0, 0) produces same equity as slippage_model=None."""
        zero_model = SlippageModel(
            base_slippage_pct=0.0,
            vol_multiplier=0.0,
            size_impact=0.0,
        )
        curve_none = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            **default_params,
        )
        curve_zero = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            slippage_model=zero_model,
            **default_params,
        )
        assert curve_none == curve_zero


# =============================================================================
# SECTION 5 -- SLIPPAGE DELEGATION TO StrategyLab
# =============================================================================

class TestSlippageDelegation:
    """Verify that compute_slippage is used correctly."""

    def test_base_only_slippage(self, stable_returns, stable_prices, default_params):
        """Model with only base_slippage_pct applies constant drag."""
        base_only = SlippageModel(
            base_slippage_pct=0.001,
            vol_multiplier=0.0,
            size_impact=0.0,
        )
        curve_no = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            **default_params,
        )
        curve_base = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            slippage_model=base_only,
            **default_params,
        )
        # Base-only slippage should consistently reduce equity
        assert curve_base[-1] < curve_no[-1]

    def test_vol_only_slippage(self, stable_returns, stable_prices, default_params):
        """Model with only vol_multiplier applies volatility-dependent drag."""
        vol_only = SlippageModel(
            base_slippage_pct=0.0,
            vol_multiplier=0.1,
            size_impact=0.0,
        )
        curve_no = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            **default_params,
        )
        curve_vol = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            slippage_model=vol_only,
            **default_params,
        )
        assert curve_vol[-1] <= curve_no[-1]

    def test_size_only_slippage(self, stable_returns, stable_prices, default_params):
        """Model with only size_impact applies position-size-dependent drag."""
        size_only = SlippageModel(
            base_slippage_pct=0.0,
            vol_multiplier=0.0,
            size_impact=0.1,
        )
        curve_no = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            **default_params,
        )
        curve_size = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            slippage_model=size_only,
            **default_params,
        )
        assert curve_size[-1] <= curve_no[-1]


# =============================================================================
# SECTION 6 -- MULTI-ASSET BACKWARD COMPATIBILITY
# =============================================================================

class TestMultiAssetBackwardCompatibility:
    """Verify run_multi_asset_backtest without slippage_model."""

    def test_default_none(
        self, multi_asset_returns, multi_asset_prices, default_params
    ):
        """Calling without slippage_model works."""
        result = run_multi_asset_backtest(
            asset_returns=multi_asset_returns,
            asset_prices=multi_asset_prices,
            **default_params,
        )
        assert result.n_periods == 10

    def test_explicit_none_matches_default(
        self, multi_asset_returns, multi_asset_prices, default_params
    ):
        """Explicit None matches omitting slippage_model."""
        result_default = run_multi_asset_backtest(
            asset_returns=multi_asset_returns,
            asset_prices=multi_asset_prices,
            **default_params,
        )
        result_none = run_multi_asset_backtest(
            asset_returns=multi_asset_returns,
            asset_prices=multi_asset_prices,
            slippage_model=None,
            **default_params,
        )
        assert result_default.portfolio_equity == result_none.portfolio_equity


# =============================================================================
# SECTION 7 -- MULTI-ASSET SLIPPAGE REDUCES EQUITY
# =============================================================================

class TestMultiAssetSlippageReducesEquity:
    """Verify slippage reduces portfolio equity in multi-asset backtest."""

    def test_slippage_reduces_portfolio_equity(
        self, multi_asset_returns, multi_asset_prices, default_params,
        slippage_model_small,
    ):
        """Portfolio equity with slippage <= without slippage."""
        result_no = run_multi_asset_backtest(
            asset_returns=multi_asset_returns,
            asset_prices=multi_asset_prices,
            **default_params,
        )
        result_slip = run_multi_asset_backtest(
            asset_returns=multi_asset_returns,
            asset_prices=multi_asset_prices,
            slippage_model=slippage_model_small,
            **default_params,
        )
        assert result_slip.portfolio_equity[-1] <= result_no.portfolio_equity[-1]

    def test_per_asset_equity_reduced(
        self, multi_asset_returns, multi_asset_prices, default_params,
        slippage_model_small,
    ):
        """Each asset's final equity should be reduced by slippage."""
        result_no = run_multi_asset_backtest(
            asset_returns=multi_asset_returns,
            asset_prices=multi_asset_prices,
            **default_params,
        )
        result_slip = run_multi_asset_backtest(
            asset_returns=multi_asset_returns,
            asset_prices=multi_asset_prices,
            slippage_model=slippage_model_small,
            **default_params,
        )
        for s in ["A", "B"]:
            assert (result_slip.asset_results[s].equity_curve[-1]
                    <= result_no.asset_results[s].equity_curve[-1])

    def test_n_periods_unchanged(
        self, multi_asset_returns, multi_asset_prices, default_params,
        slippage_model_small,
    ):
        """Number of periods should not change with slippage."""
        result_no = run_multi_asset_backtest(
            asset_returns=multi_asset_returns,
            asset_prices=multi_asset_prices,
            **default_params,
        )
        result_slip = run_multi_asset_backtest(
            asset_returns=multi_asset_returns,
            asset_prices=multi_asset_prices,
            slippage_model=slippage_model_small,
            **default_params,
        )
        assert result_slip.n_periods == result_no.n_periods


# =============================================================================
# SECTION 8 -- MULTI-ASSET DETERMINISM
# =============================================================================

class TestMultiAssetSlippageDeterminism:
    """Determinism of multi-asset backtest with slippage."""

    def test_deterministic(
        self, multi_asset_returns, multi_asset_prices, default_params,
        slippage_model_small,
    ):
        """Two runs produce identical results."""
        result1 = run_multi_asset_backtest(
            asset_returns=multi_asset_returns,
            asset_prices=multi_asset_prices,
            slippage_model=slippage_model_small,
            **default_params,
        )
        result2 = run_multi_asset_backtest(
            asset_returns=multi_asset_returns,
            asset_prices=multi_asset_prices,
            slippage_model=slippage_model_small,
            **default_params,
        )
        assert result1.portfolio_equity == result2.portfolio_equity
        for s in ["A", "B"]:
            assert (result1.asset_results[s].equity_curve
                    == result2.asset_results[s].equity_curve)


# =============================================================================
# SECTION 9 -- MULTI-ASSET ZERO SLIPPAGE
# =============================================================================

class TestMultiAssetZeroSlippage:
    """Zero slippage model matches no-slippage result."""

    def test_zero_model_matches_none(
        self, multi_asset_returns, multi_asset_prices, default_params
    ):
        """SlippageModel(0, 0, 0) equals slippage_model=None."""
        zero_model = SlippageModel(
            base_slippage_pct=0.0,
            vol_multiplier=0.0,
            size_impact=0.0,
        )
        result_none = run_multi_asset_backtest(
            asset_returns=multi_asset_returns,
            asset_prices=multi_asset_prices,
            **default_params,
        )
        result_zero = run_multi_asset_backtest(
            asset_returns=multi_asset_returns,
            asset_prices=multi_asset_prices,
            slippage_model=zero_model,
            **default_params,
        )
        assert result_none.portfolio_equity == result_zero.portfolio_equity


# =============================================================================
# SECTION 10 -- IMPORT CONTRACT
# =============================================================================

class TestImportContract:
    """Verify SlippageModel is importable from expected locations."""

    def test_slippage_model_importable(self):
        """SlippageModel can be imported from jarvis.simulation.strategy_lab."""
        from jarvis.simulation.strategy_lab import SlippageModel as SM
        assert SM is not None

    def test_slippage_model_from_simulation(self):
        """SlippageModel can be imported from jarvis.simulation."""
        from jarvis.simulation import SlippageModel as SM
        assert SM is not None

    def test_strategy_lab_compute_slippage(self):
        """StrategyLab.compute_slippage is callable."""
        lab = StrategyLab()
        model = SlippageModel(0.001, 0.01, 0.001)
        result = lab.compute_slippage(model, 0.5, 0.2)
        assert isinstance(result, float)
        assert result >= 0.0


# =============================================================================
# SECTION 11 -- EDGE CASES
# =============================================================================

class TestSlippageEdgeCases:
    """Edge cases for slippage integration."""

    def test_empty_curve_with_slippage(self, default_params, slippage_model_small):
        """If returns_series length == window, empty curve returned."""
        returns = [0.01] * 20
        prices = [100.0] * 20
        curve = run_backtest(
            returns_series=returns,
            asset_price_series=prices,
            slippage_model=slippage_model_small,
            **default_params,
        )
        assert curve == []

    def test_crisis_regime_with_slippage(
        self, stable_returns, stable_prices, slippage_model_small
    ):
        """Slippage works under CRISIS regime."""
        curve = run_backtest(
            returns_series=stable_returns,
            asset_price_series=stable_prices,
            window=20,
            initial_capital=100_000.0,
            regime=GlobalRegimeState.CRISIS,
            meta_uncertainty=0.5,
            slippage_model=slippage_model_small,
        )
        assert len(curve) == 10
        assert all(isinstance(v, float) for v in curve)

    def test_negative_returns_with_slippage(self, default_params, slippage_model_small):
        """Slippage on negative returns still works correctly."""
        returns = [-0.0002] * 30
        prices = [100.0] * 30
        curve = run_backtest(
            returns_series=returns,
            asset_price_series=prices,
            slippage_model=slippage_model_small,
            **default_params,
        )
        assert len(curve) == 10
        # With negative returns + slippage, equity should decrease
        assert curve[-1] <= default_params["initial_capital"]

    def test_mixed_returns_with_slippage(self, default_params, slippage_model_small):
        """Slippage with alternating positive/negative returns."""
        returns = [0.001, -0.001] * 15
        prices = [100.0] * 30
        curve = run_backtest(
            returns_series=returns,
            asset_price_series=prices,
            slippage_model=slippage_model_small,
            **default_params,
        )
        assert len(curve) == 10
