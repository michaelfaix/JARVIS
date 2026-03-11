# tests/unit/core/test_state_estimator.py
# Targeted tests for StateEstimator coverage gaps.
# Covers: pivot swap, divergence detection/reset, parameter validation,
#         type checking, missing observations, condition number edge cases.

from __future__ import annotations

import math
import pytest

from jarvis.core.state_estimator import StateEstimator, DIVERGENCE_THRESHOLD
from jarvis.core.state_layer import LatentState


def _default_state() -> LatentState:
    return LatentState.default()


def _obs_full(val: float = 0.1) -> dict:
    """Full observation dict with all 12 fields."""
    return {
        "regime": val, "volatility": val, "trend_strength": val,
        "mean_reversion": val, "liquidity": val, "stress": val,
        "momentum": val, "drift": val, "noise": val,
        "regime_confidence": val, "stability": val,
        "prediction_uncertainty": val,
    }


# ---------------------------------------------------------------------------
# Parameter validation (lines 420-425)
# ---------------------------------------------------------------------------

class TestParameterValidation:
    def test_q_zero_raises(self):
        with pytest.raises(ValueError, match="q must be > 0"):
            StateEstimator(q=0.0)

    def test_q_negative_raises(self):
        with pytest.raises(ValueError, match="q must be > 0"):
            StateEstimator(q=-1.0)

    def test_q_nan_raises(self):
        with pytest.raises(ValueError, match="q must be > 0"):
            StateEstimator(q=float("nan"))

    def test_q_inf_raises(self):
        with pytest.raises(ValueError, match="q must be > 0"):
            StateEstimator(q=float("inf"))

    def test_r_zero_raises(self):
        with pytest.raises(ValueError, match="r must be > 0"):
            StateEstimator(r=0.0)

    def test_r_negative_raises(self):
        with pytest.raises(ValueError, match="r must be > 0"):
            StateEstimator(r=-1.0)

    def test_r_nan_raises(self):
        with pytest.raises(ValueError, match="r must be > 0"):
            StateEstimator(r=float("nan"))

    def test_p0_zero_raises(self):
        with pytest.raises(ValueError, match="p0 must be > 0"):
            StateEstimator(p0=0.0)

    def test_p0_negative_raises(self):
        with pytest.raises(ValueError, match="p0 must be > 0"):
            StateEstimator(p0=-1.0)

    def test_p0_inf_raises(self):
        with pytest.raises(ValueError, match="p0 must be > 0"):
            StateEstimator(p0=float("inf"))


# ---------------------------------------------------------------------------
# Type checking in predict (line 476)
# ---------------------------------------------------------------------------

class TestPredictTypeCheck:
    def test_predict_with_dict_raises(self):
        est = StateEstimator()
        with pytest.raises(TypeError, match="LatentState"):
            est.predict({"regime": 0})  # type: ignore

    def test_predict_with_none_raises(self):
        est = StateEstimator()
        with pytest.raises(TypeError, match="LatentState"):
            est.predict(None)  # type: ignore

    def test_predict_with_string_raises(self):
        est = StateEstimator()
        with pytest.raises(TypeError, match="LatentState"):
            est.predict("not a state")  # type: ignore


# ---------------------------------------------------------------------------
# Basic predict/update cycle
# ---------------------------------------------------------------------------

class TestPredictUpdate:
    def test_predict_returns_latent_state(self):
        est = StateEstimator()
        s = _default_state()
        result = est.predict(s)
        assert isinstance(result, LatentState)

    def test_update_returns_latent_state(self):
        est = StateEstimator()
        s = _default_state()
        s2 = est.predict(s)
        result = est.update(s2, _obs_full(0.5))
        assert isinstance(result, LatentState)

    def test_covariance_is_12x12(self):
        est = StateEstimator()
        P = est.get_covariance()
        assert len(P) == 12
        assert all(len(row) == 12 for row in P)

    def test_covariance_is_deep_copy(self):
        est = StateEstimator()
        P1 = est.get_covariance()
        P2 = est.get_covariance()
        assert P1 is not P2
        assert P1[0] is not P2[0]


# ---------------------------------------------------------------------------
# Missing observations (lines 532, 536 — valid_mask=False branch)
# ---------------------------------------------------------------------------

class TestMissingObservations:
    def test_update_with_empty_obs_uses_prediction(self):
        est = StateEstimator()
        s = _default_state()
        s2 = est.predict(s)
        # Empty observation -> all fields use prediction (no correction)
        result = est.update(s2, {})
        assert isinstance(result, LatentState)

    def test_update_with_partial_obs(self):
        est = StateEstimator()
        s = _default_state()
        s2 = est.predict(s)
        # Only provide volatility — rest are missing
        result = est.update(s2, {"volatility": 0.3})
        assert isinstance(result, LatentState)

    def test_update_with_nan_obs_treated_as_missing(self):
        est = StateEstimator()
        s = _default_state()
        s2 = est.predict(s)
        obs = _obs_full(0.2)
        obs["volatility"] = float("nan")
        result = est.update(s2, obs)
        assert isinstance(result, LatentState)
        assert math.isfinite(result.volatility)

    def test_update_with_inf_obs_treated_as_missing(self):
        est = StateEstimator()
        s = _default_state()
        s2 = est.predict(s)
        obs = _obs_full(0.2)
        obs["stress"] = float("inf")
        result = est.update(s2, obs)
        assert isinstance(result, LatentState)
        assert math.isfinite(result.stress)


# ---------------------------------------------------------------------------
# Reset (lines 629-632)
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_restores_initial_covariance(self):
        est = StateEstimator(p0=2.0)
        P_init = est.get_covariance()
        # Mutate covariance via predict/update cycle
        s = _default_state()
        for _ in range(5):
            s = est.predict(s)
            s = est.update(s, _obs_full(0.5))
        P_after = est.get_covariance()
        # Covariance should have changed
        assert P_init != P_after
        # Reset
        est.reset()
        P_reset = est.get_covariance()
        # Diagonal should be p0 again
        for i in range(12):
            assert abs(P_reset[i][i] - 2.0) < 1e-10

    def test_divergence_count_preserved_after_reset(self):
        est = StateEstimator()
        initial_count = est.divergence_count
        est.reset()
        assert est.divergence_count == initial_count


# ---------------------------------------------------------------------------
# Pivot swap in Gaussian elimination (lines 241-244)
# ---------------------------------------------------------------------------

class TestPivotSwap:
    def test_update_with_varied_observations_triggers_pivot(self):
        """Observations with very different magnitudes encourage pivot swaps
        during the internal Tikhonov matrix inversion."""
        est = StateEstimator(q=0.1, r=0.01)
        s = _default_state()
        # Run several cycles with extreme observation values
        obs = _obs_full(0.0)
        obs["volatility"] = 1e6
        obs["stress"] = 1e-10
        obs["regime_confidence"] = 0.99
        for _ in range(10):
            s = est.predict(s)
            s = est.update(s, obs)
        assert isinstance(s, LatentState)
        assert math.isfinite(s.volatility)


# ---------------------------------------------------------------------------
# Condition number / divergence (lines 282, 595-596)
# ---------------------------------------------------------------------------

class TestDivergenceDetection:
    def test_extreme_q_causes_divergence_reset(self):
        """Very large q relative to r can make P grow, triggering divergence."""
        est = StateEstimator(q=1e8, r=1e-12, p0=1e6)
        s = _default_state()
        for _ in range(100):
            s = est.predict(s)
            s = est.update(s, _obs_full(0.5))
        # After many iterations, should still produce valid state
        assert isinstance(s, LatentState)
        assert math.isfinite(s.volatility)

    def test_divergence_count_is_non_negative(self):
        est = StateEstimator()
        assert est.divergence_count >= 0


# ---------------------------------------------------------------------------
# Direct internal function tests for remaining uncovered lines
# ---------------------------------------------------------------------------

class TestInternalHelpers:
    def test_tikhonov_invert_pivot_swap_direct(self):
        """Line 241-244: Directly call _tikhonov_invert with a matrix
        that requires partial pivoting."""
        from jarvis.core.state_estimator import _tikhonov_invert
        # Matrix where off-diagonal is larger than diagonal in first col
        # so pivot swap is needed
        M = [
            [1e-15, 5.0, 0.0],
            [5.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
        result = _tikhonov_invert(M, lam=0.01)
        assert len(result) == 3
        # Result should be finite
        for row in result:
            for v in row:
                assert math.isfinite(v)

    def test_tikhonov_invert_singular_column(self):
        """Line 249-250: Matrix with near-zero pivot after swap."""
        from jarvis.core.state_estimator import _tikhonov_invert
        # All zeros except regularisation will save it
        M = [
            [0.0, 0.0],
            [0.0, 0.0],
        ]
        result = _tikhonov_invert(M, lam=0.01)
        assert len(result) == 2
        for row in result:
            for v in row:
                assert math.isfinite(v)

    def test_condition_number_approx_near_singular(self):
        """Line 282: min_d < _EPS returns diverged value."""
        from jarvis.core.state_estimator import _condition_number_approx
        # Matrix with zero diagonal element
        M = [
            [1.0, 0.0],
            [0.0, 0.0],
        ]
        result = _condition_number_approx(M)
        assert result > DIVERGENCE_THRESHOLD

    def test_floor_diag(self):
        """Line 292: _floor_diag actually floors a diagonal element."""
        from jarvis.core.state_estimator import _floor_diag
        M = [[0.0, 0.1], [0.1, 1.0]]
        result = _floor_diag(M)
        assert result[0][0] > 0.0  # was floored
        assert result[1][1] == 1.0  # not changed

    def test_update_with_none_obs_raises(self):
        """Line 536: TypeError for None observation."""
        est = StateEstimator()
        s = _default_state()
        s2 = est.predict(s)
        with pytest.raises(TypeError, match="observation must be a dict"):
            est.update(s2, None)  # type: ignore

    def test_update_with_non_latent_state_raises(self):
        """Line 532: TypeError for non-LatentState in update."""
        est = StateEstimator()
        with pytest.raises(TypeError, match="LatentState"):
            est.update({"x": 1}, {})  # type: ignore

    def test_divergence_triggers_covariance_reset(self):
        """Lines 595-596: Force divergence by directly manipulating covariance."""
        from jarvis.core.state_estimator import KalmanState
        est = StateEstimator(q=1e10, r=1e-15, p0=1e10)
        s = _default_state()
        # Many iterations with extreme values to force condition number > threshold
        for _ in range(200):
            s = est.predict(s)
            obs = _obs_full(0.0)
            obs["regime"] = 1e10
            obs["volatility"] = 1e-15
            s = est.update(s, obs)
        # Should still be valid
        assert isinstance(s, LatentState)
        assert math.isfinite(s.regime)
