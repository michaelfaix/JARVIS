# tests/unit/core/test_volatility_tracker.py
# Coverage target: jarvis/core/volatility_tracker.py -> 95%+
# Missing lines: 120, 125, 130, 135, 140, 197, 199, 201, 205-207, 261, 263,
#                272-273, 326-343, 348, 353, 358, 363, 374

import math

import pytest

from jarvis.core.volatility_tracker import VolatilityTracker, VolResult


# =============================================================================
# VolResult dataclass validation (lines 118-143)
# =============================================================================

class TestVolResult:
    def test_valid_construction(self):
        r = VolResult(
            volatility=0.01, variance=0.0001,
            long_run_volatility=0.005, n_clean_returns=10, nan_replaced=0,
        )
        assert r.volatility == 0.01

    def test_zero_volatility_raises(self):
        # line 120
        with pytest.raises(ValueError, match="volatility"):
            VolResult(volatility=0.0, variance=0.0001,
                      long_run_volatility=0.01, n_clean_returns=1, nan_replaced=0)

    def test_nan_volatility_raises(self):
        with pytest.raises(ValueError, match="volatility"):
            VolResult(volatility=float("nan"), variance=0.0001,
                      long_run_volatility=0.01, n_clean_returns=1, nan_replaced=0)

    def test_zero_variance_raises(self):
        # line 125
        with pytest.raises(ValueError, match="variance"):
            VolResult(volatility=0.01, variance=0.0,
                      long_run_volatility=0.01, n_clean_returns=1, nan_replaced=0)

    def test_nan_variance_raises(self):
        with pytest.raises(ValueError, match="variance"):
            VolResult(volatility=0.01, variance=float("nan"),
                      long_run_volatility=0.01, n_clean_returns=1, nan_replaced=0)

    def test_zero_long_run_volatility_raises(self):
        # line 130
        with pytest.raises(ValueError, match="long_run_volatility"):
            VolResult(volatility=0.01, variance=0.0001,
                      long_run_volatility=0.0, n_clean_returns=1, nan_replaced=0)

    def test_inf_long_run_volatility_raises(self):
        with pytest.raises(ValueError, match="long_run_volatility"):
            VolResult(volatility=0.01, variance=0.0001,
                      long_run_volatility=float("inf"), n_clean_returns=1, nan_replaced=0)

    def test_negative_n_clean_raises(self):
        # line 135
        with pytest.raises(ValueError, match="n_clean_returns"):
            VolResult(volatility=0.01, variance=0.0001,
                      long_run_volatility=0.01, n_clean_returns=-1, nan_replaced=0)

    def test_negative_nan_replaced_raises(self):
        # line 140
        with pytest.raises(ValueError, match="nan_replaced"):
            VolResult(volatility=0.01, variance=0.0001,
                      long_run_volatility=0.01, n_clean_returns=0, nan_replaced=-1)


# =============================================================================
# VolatilityTracker.__init__ (lines 196-207)
# =============================================================================

class TestVolatilityTrackerInit:
    def test_default_params(self):
        t = VolatilityTracker()
        p = t.parameters
        assert p["omega"] == 1e-6
        assert p["alpha"] == 0.10
        assert p["beta"] == 0.85

    def test_invalid_omega_raises(self):
        # line 197
        with pytest.raises(ValueError, match="omega"):
            VolatilityTracker(omega=0.0)

    def test_negative_omega_raises(self):
        with pytest.raises(ValueError, match="omega"):
            VolatilityTracker(omega=-1.0)

    def test_inf_omega_raises(self):
        with pytest.raises(ValueError, match="omega"):
            VolatilityTracker(omega=float("inf"))

    def test_invalid_alpha_zero_raises(self):
        # line 199
        with pytest.raises(ValueError, match="alpha"):
            VolatilityTracker(alpha=0.0)

    def test_invalid_alpha_one_raises(self):
        with pytest.raises(ValueError, match="alpha"):
            VolatilityTracker(alpha=1.0)

    def test_invalid_beta_zero_raises(self):
        # line 201
        with pytest.raises(ValueError, match="beta"):
            VolatilityTracker(beta=0.0)

    def test_invalid_beta_one_raises(self):
        with pytest.raises(ValueError, match="beta"):
            VolatilityTracker(beta=1.0)

    def test_stationarity_rescaling(self):
        # lines 205-207: alpha + beta >= 1 triggers rescaling
        t = VolatilityTracker(alpha=0.5, beta=0.6)
        p = t.parameters
        assert p["alpha"] + p["beta"] < 1.0
        assert abs(p["alpha"] + p["beta"] - 0.95) < 1e-10


# =============================================================================
# VolatilityTracker.estimate_volatility (lines 261, 263, 272-273)
# =============================================================================

class TestEstimateVolatility:
    def test_basic_estimation(self):
        t = VolatilityTracker()
        returns = [0.01, -0.02, 0.015, -0.005, 0.008]
        result = t.estimate_volatility(returns)
        assert result.volatility > 0
        assert result.variance > 0
        assert result.n_clean_returns == 5
        assert result.nan_replaced == 0

    def test_none_returns_raises(self):
        # line 261
        t = VolatilityTracker()
        with pytest.raises(TypeError, match="None"):
            t.estimate_volatility(None)

    def test_empty_returns_raises(self):
        # line 263
        t = VolatilityTracker()
        with pytest.raises(ValueError, match="non-empty"):
            t.estimate_volatility([])

    def test_nan_in_returns_replaced(self):
        # lines 272-273
        t = VolatilityTracker()
        result = t.estimate_volatility([0.01, float("nan"), -0.02])
        assert result.nan_replaced == 1
        assert result.n_clean_returns == 2

    def test_inf_in_returns_replaced(self):
        t = VolatilityTracker()
        result = t.estimate_volatility([0.01, float("inf"), float("-inf")])
        assert result.nan_replaced == 2
        assert result.n_clean_returns == 1

    def test_all_nan_returns(self):
        t = VolatilityTracker()
        result = t.estimate_volatility([float("nan"), float("nan")])
        assert result.nan_replaced == 2
        assert result.n_clean_returns == 0
        assert result.volatility > 0

    def test_sequential_updates(self):
        t = VolatilityTracker()
        r1 = t.estimate_volatility([0.01])
        r2 = t.estimate_volatility([0.05])
        assert r2.variance != r1.variance

    def test_deterministic(self):
        t1 = VolatilityTracker()
        t2 = VolatilityTracker()
        returns = [0.01, -0.02, 0.015]
        r1 = t1.estimate_volatility(returns)
        r2 = t2.estimate_volatility(returns)
        assert r1.volatility == r2.volatility
        assert r1.variance == r2.variance


# =============================================================================
# VolatilityTracker.predict_volatility (lines 326-343)
# =============================================================================

class TestPredictVolatility:
    def test_basic_prediction(self):
        t = VolatilityTracker()
        t.estimate_volatility([0.01, -0.02, 0.015])
        pred = t.predict_volatility(1)
        assert pred > 0

    def test_horizon_zero_raises(self):
        # line 326-329
        t = VolatilityTracker()
        with pytest.raises(ValueError, match="horizon"):
            t.predict_volatility(0)

    def test_negative_horizon_raises(self):
        t = VolatilityTracker()
        with pytest.raises(ValueError, match="horizon"):
            t.predict_volatility(-1)

    def test_long_horizon_converges_to_long_run(self):
        t = VolatilityTracker()
        t.estimate_volatility([0.01, -0.02, 0.03, -0.01])
        lr = t.long_run_variance
        pred_100 = t.predict_volatility(100)
        assert abs(pred_100 - math.sqrt(lr)) < 0.01

    def test_horizon_1_vs_10(self):
        t = VolatilityTracker()
        t.estimate_volatility([0.05, -0.05, 0.05])
        p1 = t.predict_volatility(1)
        p10 = t.predict_volatility(10)
        # Both should be positive
        assert p1 > 0
        assert p10 > 0


# =============================================================================
# Properties (lines 348, 353, 358, 363)
# =============================================================================

class TestProperties:
    def test_current_variance(self):
        # line 348
        t = VolatilityTracker()
        assert t.current_variance > 0

    def test_current_volatility(self):
        # line 353
        t = VolatilityTracker()
        assert t.current_volatility > 0
        assert abs(t.current_volatility - math.sqrt(t.current_variance)) < 1e-10

    def test_long_run_variance(self):
        # line 358
        t = VolatilityTracker()
        assert t.long_run_variance > 0

    def test_parameters(self):
        # line 363
        t = VolatilityTracker(omega=2e-6, alpha=0.15, beta=0.80)
        p = t.parameters
        assert p["omega"] == 2e-6
        assert p["alpha"] == 0.15
        assert p["beta"] == 0.80


# =============================================================================
# VolatilityTracker.reset (line 374)
# =============================================================================

class TestReset:
    def test_reset_restores_long_run(self):
        # line 374
        t = VolatilityTracker()
        lr = t.current_variance
        t.estimate_volatility([0.1, -0.1, 0.1])
        assert t.current_variance != lr
        t.reset()
        assert t.current_variance == lr
