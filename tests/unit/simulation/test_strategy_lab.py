# =============================================================================
# Tests for jarvis/simulation/strategy_lab.py (S28)
# =============================================================================

import math

import numpy as np
import pytest

from jarvis.simulation.strategy_lab import (
    JARVIS_STRESS_SCENARIOS,
    MonteCarloResult,
    SlippageModel,
    StressTestResult,
    StrategyLab,
    WalkForwardResult,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

@pytest.fixture
def lab():
    return StrategyLab()


def _positive_returns(n=100):
    """Mildly positive returns for testing."""
    return [0.001] * n


def _mixed_returns(n=100):
    """Alternating positive/negative returns."""
    return [0.01 if i % 2 == 0 else -0.005 for i in range(n)]


def _crisis_returns(n=20):
    """Sharp drawdown scenario."""
    return [-0.05] * n


def _identity_strategy(train_returns):
    """Strategy that returns train_returns unchanged (passthrough)."""
    return train_returns


def _fixed_strategy(returns_list):
    """Strategy returning fixed mild returns."""
    return [0.001] * 30


def _failing_strategy(train_returns):
    """Strategy that always raises."""
    raise RuntimeError("Strategy exploded")


# ---------------------------------------------------------------------------
# MONTE CARLO RESULT DATACLASS
# ---------------------------------------------------------------------------

class TestMonteCarloResultDataclass:
    def test_all_fields(self):
        r = MonteCarloResult(
            n_paths=100,
            mean_final_pnl=0.05,
            std_final_pnl=0.02,
            var_95=-0.03,
            cvar_95=-0.05,
            max_drawdown_mean=0.08,
            max_drawdown_p95=0.15,
            win_rate=0.7,
        )
        assert r.n_paths == 100
        assert r.var_95 == -0.03
        assert r.win_rate == 0.7


# ---------------------------------------------------------------------------
# SLIPPAGE MODEL DATACLASS
# ---------------------------------------------------------------------------

class TestSlippageModelDataclass:
    def test_all_fields(self):
        m = SlippageModel(base_slippage_pct=0.01, vol_multiplier=0.5, size_impact=0.1)
        assert m.base_slippage_pct == 0.01
        assert m.vol_multiplier == 0.5
        assert m.size_impact == 0.1


# ---------------------------------------------------------------------------
# WALK FORWARD RESULT DATACLASS
# ---------------------------------------------------------------------------

class TestWalkForwardResultDataclass:
    def test_all_fields(self):
        r = WalkForwardResult(
            n_windows=10,
            oos_sharpe_mean=1.5,
            oos_sharpe_std=0.3,
            oos_win_rate=0.8,
            degradation_score=0.1,
        )
        assert r.n_windows == 10
        assert r.oos_win_rate == 0.8


# ---------------------------------------------------------------------------
# STRESS TEST RESULT DATACLASS
# ---------------------------------------------------------------------------

class TestStressTestResultDataclass:
    def test_all_fields(self):
        r = StressTestResult(
            scenario="TEST",
            pnl_impact=-0.1,
            max_drawdown=0.12,
            recovery_periods=5,
            survived=True,
        )
        assert r.scenario == "TEST"
        assert r.survived is True


# ---------------------------------------------------------------------------
# MONTE CARLO
# ---------------------------------------------------------------------------

class TestMonteCarlo:
    def test_basic_positive_returns(self, lab):
        result = lab.monte_carlo(_positive_returns(), n_paths=100, n_periods=50, seed=42)
        assert isinstance(result, MonteCarloResult)
        assert result.n_paths == 100
        assert result.mean_final_pnl > 0

    def test_determinism_same_seed(self, lab):
        r1 = lab.monte_carlo(_mixed_returns(), n_paths=500, n_periods=50, seed=42)
        r2 = lab.monte_carlo(_mixed_returns(), n_paths=500, n_periods=50, seed=42)
        assert r1.mean_final_pnl == r2.mean_final_pnl
        assert r1.var_95 == r2.var_95
        assert r1.cvar_95 == r2.cvar_95
        assert r1.win_rate == r2.win_rate

    def test_different_seed_different_result(self, lab):
        r1 = lab.monte_carlo(_mixed_returns(), n_paths=500, n_periods=50, seed=42)
        r2 = lab.monte_carlo(_mixed_returns(), n_paths=500, n_periods=50, seed=99)
        # With different seeds, results will differ (extremely unlikely to match)
        assert r1.mean_final_pnl != r2.mean_final_pnl

    def test_nan_in_returns_raises(self, lab):
        with pytest.raises(ValueError, match="NaN/Inf"):
            lab.monte_carlo([0.01, float("nan"), -0.01], seed=42)

    def test_inf_in_returns_raises(self, lab):
        with pytest.raises(ValueError, match="NaN/Inf"):
            lab.monte_carlo([0.01, float("inf"), -0.01], seed=42)

    def test_var_95_less_than_mean(self, lab):
        result = lab.monte_carlo(_mixed_returns(), n_paths=1000, n_periods=50, seed=42)
        assert result.var_95 <= result.mean_final_pnl

    def test_cvar_95_less_equal_var_95(self, lab):
        result = lab.monte_carlo(_mixed_returns(), n_paths=1000, n_periods=50, seed=42)
        assert result.cvar_95 <= result.var_95

    def test_win_rate_between_0_and_1(self, lab):
        result = lab.monte_carlo(_mixed_returns(), n_paths=500, n_periods=50, seed=42)
        assert 0.0 <= result.win_rate <= 1.0

    def test_max_drawdown_non_negative(self, lab):
        result = lab.monte_carlo(_positive_returns(), n_paths=100, n_periods=50, seed=42)
        assert result.max_drawdown_mean >= 0.0
        assert result.max_drawdown_p95 >= 0.0

    def test_max_drawdown_p95_gte_mean(self, lab):
        result = lab.monte_carlo(_mixed_returns(), n_paths=1000, n_periods=50, seed=42)
        assert result.max_drawdown_p95 >= result.max_drawdown_mean

    def test_all_positive_returns_high_win_rate(self, lab):
        result = lab.monte_carlo(_positive_returns(), n_paths=500, n_periods=50, seed=42)
        assert result.win_rate == 1.0

    def test_all_negative_returns_low_win_rate(self, lab):
        result = lab.monte_carlo([-0.001] * 100, n_paths=500, n_periods=50, seed=42)
        assert result.win_rate == 0.0

    def test_std_non_negative(self, lab):
        result = lab.monte_carlo(_mixed_returns(), n_paths=100, n_periods=50, seed=42)
        assert result.std_final_pnl >= 0.0

    def test_n_paths_in_result(self, lab):
        result = lab.monte_carlo(_positive_returns(), n_paths=77, n_periods=10, seed=42)
        assert result.n_paths == 77


# ---------------------------------------------------------------------------
# COMPUTE SLIPPAGE
# ---------------------------------------------------------------------------

class TestComputeSlippage:
    def test_basic_slippage(self, lab):
        model = SlippageModel(base_slippage_pct=0.01, vol_multiplier=0.5, size_impact=0.1)
        result = lab.compute_slippage(model, position_size_pct=0.05, current_volatility=0.2)
        # 0.01 + 0.5*0.2 + 0.1*0.05 = 0.01 + 0.1 + 0.005 = 0.115
        assert result == pytest.approx(0.115)

    def test_zero_volatility(self, lab):
        model = SlippageModel(base_slippage_pct=0.01, vol_multiplier=0.5, size_impact=0.1)
        result = lab.compute_slippage(model, position_size_pct=0.05, current_volatility=0.0)
        # 0.01 + 0 + 0.005 = 0.015
        assert result == pytest.approx(0.015)

    def test_zero_position_size(self, lab):
        model = SlippageModel(base_slippage_pct=0.01, vol_multiplier=0.5, size_impact=0.1)
        result = lab.compute_slippage(model, position_size_pct=0.0, current_volatility=0.2)
        # 0.01 + 0.1 + 0 = 0.11
        assert result == pytest.approx(0.11)

    def test_slippage_non_negative(self, lab):
        model = SlippageModel(base_slippage_pct=0.0, vol_multiplier=0.0, size_impact=0.0)
        result = lab.compute_slippage(model, position_size_pct=0.0, current_volatility=0.0)
        assert result >= 0.0

    def test_negative_position_size_raises(self, lab):
        model = SlippageModel(base_slippage_pct=0.01, vol_multiplier=0.5, size_impact=0.1)
        with pytest.raises(ValueError, match="position_size_pct"):
            lab.compute_slippage(model, position_size_pct=-0.1, current_volatility=0.2)

    def test_negative_volatility_raises(self, lab):
        model = SlippageModel(base_slippage_pct=0.01, vol_multiplier=0.5, size_impact=0.1)
        with pytest.raises(ValueError, match="Volatilitaet"):
            lab.compute_slippage(model, position_size_pct=0.05, current_volatility=-0.1)

    def test_nan_position_size_raises(self, lab):
        model = SlippageModel(base_slippage_pct=0.01, vol_multiplier=0.5, size_impact=0.1)
        with pytest.raises(ValueError, match="position_size_pct"):
            lab.compute_slippage(model, position_size_pct=float("nan"), current_volatility=0.2)

    def test_inf_volatility_raises(self, lab):
        model = SlippageModel(base_slippage_pct=0.01, vol_multiplier=0.5, size_impact=0.1)
        with pytest.raises(ValueError, match="Volatilitaet"):
            lab.compute_slippage(model, position_size_pct=0.05, current_volatility=float("inf"))

    def test_large_position_size_high_slippage(self, lab):
        model = SlippageModel(base_slippage_pct=0.01, vol_multiplier=0.5, size_impact=0.1)
        small = lab.compute_slippage(model, position_size_pct=0.01, current_volatility=0.2)
        large = lab.compute_slippage(model, position_size_pct=1.0, current_volatility=0.2)
        assert large > small

    def test_high_vol_high_slippage(self, lab):
        model = SlippageModel(base_slippage_pct=0.01, vol_multiplier=0.5, size_impact=0.1)
        low_vol = lab.compute_slippage(model, position_size_pct=0.05, current_volatility=0.1)
        high_vol = lab.compute_slippage(model, position_size_pct=0.05, current_volatility=0.5)
        assert high_vol > low_vol

    def test_result_is_float(self, lab):
        model = SlippageModel(base_slippage_pct=0.01, vol_multiplier=0.5, size_impact=0.1)
        result = lab.compute_slippage(model, position_size_pct=0.05, current_volatility=0.2)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# WALK FORWARD
# ---------------------------------------------------------------------------

class TestWalkForward:
    def test_basic_walk_forward(self, lab):
        returns = _mixed_returns(200)
        result = lab.walk_forward(returns, _identity_strategy, n_windows=5, train_pct=0.7)
        assert isinstance(result, WalkForwardResult)
        assert result.n_windows > 0

    def test_n_windows_returned(self, lab):
        returns = _mixed_returns(200)
        result = lab.walk_forward(returns, _identity_strategy, n_windows=5, train_pct=0.7)
        assert result.n_windows == 5

    def test_oos_sharpe_is_finite(self, lab):
        returns = _mixed_returns(200)
        result = lab.walk_forward(returns, _identity_strategy, n_windows=5, train_pct=0.7)
        assert np.isfinite(result.oos_sharpe_mean)
        assert np.isfinite(result.oos_sharpe_std)

    def test_oos_win_rate_between_0_and_1(self, lab):
        returns = _mixed_returns(200)
        result = lab.walk_forward(returns, _identity_strategy, n_windows=5, train_pct=0.7)
        assert 0.0 <= result.oos_win_rate <= 1.0

    def test_degradation_non_negative(self, lab):
        returns = _mixed_returns(200)
        result = lab.walk_forward(returns, _identity_strategy, n_windows=5, train_pct=0.7)
        assert result.degradation_score >= 0.0

    def test_nan_in_returns_raises(self, lab):
        returns = [0.01] * 50 + [float("nan")] + [0.01] * 49
        with pytest.raises(ValueError, match="NaN/Inf"):
            lab.walk_forward(returns, _identity_strategy, n_windows=5)

    def test_failing_strategy_negative_sharpe(self, lab):
        returns = _mixed_returns(200)
        result = lab.walk_forward(returns, _failing_strategy, n_windows=5, train_pct=0.7)
        assert result.oos_sharpe_mean < 0

    def test_no_valid_windows_raises(self, lab):
        # Empty returns → no valid windows
        with pytest.raises((RuntimeError, ValueError)):
            lab.walk_forward([], _identity_strategy, n_windows=10)

    def test_determinism(self, lab):
        returns = _mixed_returns(200)
        r1 = lab.walk_forward(returns, _identity_strategy, n_windows=5, train_pct=0.7)
        r2 = lab.walk_forward(returns, _identity_strategy, n_windows=5, train_pct=0.7)
        assert r1.oos_sharpe_mean == r2.oos_sharpe_mean
        assert r1.oos_sharpe_std == r2.oos_sharpe_std

    def test_positive_returns_positive_sharpe(self, lab):
        returns = _positive_returns(200)
        result = lab.walk_forward(returns, _identity_strategy, n_windows=5, train_pct=0.7)
        # All positive returns → positive sharpe, but std might be near 0
        # Since all returns are 0.001, std is 0 → sharpe uses 1e-10 floor
        assert result.oos_sharpe_mean > 0

    def test_single_return_per_window_sharpe_zero(self, lab):
        # window_sz = 10 // 10 = 1, train=0, oos=1 element
        # strategy_fn returns single element → sharpe = 0
        def single_return(train):
            return [0.01]
        returns = [0.01] * 10
        result = lab.walk_forward(returns, single_return, n_windows=10, train_pct=0.0)
        assert result.oos_sharpe_mean == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# STRESS TEST
# ---------------------------------------------------------------------------

class TestStressTest:
    def test_basic_stress_test(self, lab):
        result = lab.stress_test(
            "TEST_CRISIS",
            _crisis_returns(),
            _identity_strategy,
            drawdown_limit=0.15,
        )
        assert isinstance(result, StressTestResult)
        assert result.scenario == "TEST_CRISIS"

    def test_crisis_not_survived(self, lab):
        # 20 consecutive -5% drops → severe drawdown > 15%
        result = lab.stress_test(
            "DEEP_CRISIS",
            _crisis_returns(20),
            _identity_strategy,
            drawdown_limit=0.15,
        )
        assert result.survived is False
        assert result.max_drawdown > 0.15

    def test_mild_scenario_survived(self, lab):
        result = lab.stress_test(
            "MILD",
            _positive_returns(50),
            _identity_strategy,
            drawdown_limit=0.15,
        )
        assert result.survived is True
        assert result.max_drawdown < 0.15

    def test_strategy_exception_not_survived(self, lab):
        result = lab.stress_test(
            "FAIL_SCENARIO",
            _crisis_returns(),
            _failing_strategy,
            drawdown_limit=0.15,
        )
        assert result.survived is False
        assert result.pnl_impact == -1.0
        assert result.max_drawdown == 1.0
        assert result.recovery_periods == -1

    def test_pnl_impact_negative_in_crisis(self, lab):
        result = lab.stress_test(
            "CRISIS",
            _crisis_returns(10),
            _identity_strategy,
            drawdown_limit=0.50,
        )
        assert result.pnl_impact < 0

    def test_pnl_impact_positive_in_bull(self, lab):
        result = lab.stress_test(
            "BULL",
            _positive_returns(50),
            _identity_strategy,
            drawdown_limit=0.15,
        )
        assert result.pnl_impact > 0

    def test_max_drawdown_non_negative(self, lab):
        result = lab.stress_test(
            "TEST",
            _mixed_returns(50),
            _identity_strategy,
        )
        assert result.max_drawdown >= 0.0

    def test_drawdown_limit_boundary(self, lab):
        # Very high drawdown limit → should survive
        result = lab.stress_test(
            "CRISIS",
            _crisis_returns(5),
            _identity_strategy,
            drawdown_limit=0.99,
        )
        assert result.survived is True

    def test_nan_returns_handled(self, lab):
        """Strategy returning NaN should be handled gracefully."""
        def nan_strategy(returns):
            return [float("nan")] * len(returns)

        result = lab.stress_test(
            "NAN_SCENARIO",
            _crisis_returns(10),
            nan_strategy,
        )
        # arr replaced with zeros → no drawdown
        assert isinstance(result, StressTestResult)

    def test_recovery_periods_type(self, lab):
        result = lab.stress_test(
            "TEST",
            _positive_returns(50),
            _identity_strategy,
        )
        assert isinstance(result.recovery_periods, int)

    def test_scenario_name_preserved(self, lab):
        result = lab.stress_test(
            "CUSTOM_NAME_123",
            _positive_returns(10),
            _identity_strategy,
        )
        assert result.scenario == "CUSTOM_NAME_123"


# ---------------------------------------------------------------------------
# JARVIS_STRESS_SCENARIOS
# ---------------------------------------------------------------------------

class TestJarvisStressScenarios:
    def test_six_scenarios(self):
        assert len(JARVIS_STRESS_SCENARIOS) == 6

    def test_required_scenarios_present(self):
        assert "2008_FINANCIAL_CRISIS" in JARVIS_STRESS_SCENARIOS
        assert "2020_COVID_CRASH" in JARVIS_STRESS_SCENARIOS
        assert "2010_FLASH_CRASH" in JARVIS_STRESS_SCENARIOS
        assert "SYNTHETIC_VOL_SHOCK_3X" in JARVIS_STRESS_SCENARIOS
        assert "SYNTHETIC_LIQUIDITY_CRISIS" in JARVIS_STRESS_SCENARIOS
        assert "SYNTHETIC_CORRELATION_SHOCK" in JARVIS_STRESS_SCENARIOS

    def test_all_strings(self):
        for s in JARVIS_STRESS_SCENARIOS:
            assert isinstance(s, str)


# ---------------------------------------------------------------------------
# INTEGRATION: FULL LAB WORKFLOW
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_full_lab_workflow(self, lab):
        returns = _mixed_returns(300)

        # Monte Carlo
        mc = lab.monte_carlo(returns, n_paths=200, n_periods=50, seed=42)
        assert isinstance(mc, MonteCarloResult)

        # Slippage
        model = SlippageModel(base_slippage_pct=0.005, vol_multiplier=0.3, size_impact=0.05)
        slip = lab.compute_slippage(model, position_size_pct=0.1, current_volatility=0.25)
        assert slip > 0

        # Walk Forward
        wf = lab.walk_forward(returns, _identity_strategy, n_windows=5, train_pct=0.7)
        assert isinstance(wf, WalkForwardResult)

        # Stress Test
        st = lab.stress_test("CRISIS", _crisis_returns(20), _identity_strategy)
        assert isinstance(st, StressTestResult)

    def test_lab_instance_stateless(self, lab):
        """StrategyLab should be stateless — results depend only on inputs."""
        r1 = lab.monte_carlo(_positive_returns(), n_paths=100, n_periods=50, seed=42)
        lab.stress_test("CRISIS", _crisis_returns(), _identity_strategy)
        r2 = lab.monte_carlo(_positive_returns(), n_paths=100, n_periods=50, seed=42)
        assert r1.mean_final_pnl == r2.mean_final_pnl
