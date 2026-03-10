# =============================================================================
# Unit Tests for jarvis/optimization/engine.py
# =============================================================================

import copy
from unittest.mock import patch, MagicMock
import pytest

from jarvis.core.regime import GlobalRegimeState
from jarvis.optimization.engine import run_optimization


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _dummy_strategy_output():
    """Minimal valid run_strategy() return value."""
    return {
        "segments": [],
        "segment_metrics": [],
        "aggregate": {
            "cagr": 0.05,
            "sharpe_ratio": 1.0,
            "max_drawdown": 0.1,
        },
    }


_RETURNS = [0.01 * (i % 5 - 2) for i in range(50)]
_PRICES = [100.0 + i * 0.5 for i in range(50)]
_REGIME = GlobalRegimeState.RISK_ON
_CAPITAL = 100_000.0


# ===================================================================
# TestRunOptimizationValidation
# ===================================================================

class TestRunOptimizationValidation:
    def test_empty_windows_raises(self):
        with pytest.raises(ValueError, match="windows must not be empty"):
            run_optimization(_RETURNS, _PRICES, [], [1], [0.2], _CAPITAL, _REGIME)

    def test_empty_steps_raises(self):
        with pytest.raises(ValueError, match="steps must not be empty"):
            run_optimization(_RETURNS, _PRICES, [20], [], [0.2], _CAPITAL, _REGIME)

    def test_empty_meta_uncertainties_raises(self):
        with pytest.raises(ValueError, match="meta_uncertainties must not be empty"):
            run_optimization(_RETURNS, _PRICES, [20], [1], [], _CAPITAL, _REGIME)

    def test_window_below_20_raises(self):
        with pytest.raises(ValueError, match="All windows must be >= 20"):
            run_optimization(_RETURNS, _PRICES, [10], [1], [0.2], _CAPITAL, _REGIME)

    def test_window_mixed_invalid_raises(self):
        with pytest.raises(ValueError, match="All windows must be >= 20"):
            run_optimization(_RETURNS, _PRICES, [20, 5], [1], [0.2], _CAPITAL, _REGIME)

    def test_step_zero_raises(self):
        with pytest.raises(ValueError, match="All steps must be >= 1"):
            run_optimization(_RETURNS, _PRICES, [20], [0], [0.2], _CAPITAL, _REGIME)

    def test_step_negative_raises(self):
        with pytest.raises(ValueError, match="All steps must be >= 1"):
            run_optimization(_RETURNS, _PRICES, [20], [-1], [0.2], _CAPITAL, _REGIME)

    def test_meta_below_zero_raises(self):
        with pytest.raises(ValueError, match="All meta_uncertainties must be in"):
            run_optimization(_RETURNS, _PRICES, [20], [1], [-0.1], _CAPITAL, _REGIME)

    def test_meta_above_one_raises(self):
        with pytest.raises(ValueError, match="All meta_uncertainties must be in"):
            run_optimization(_RETURNS, _PRICES, [20], [1], [1.1], _CAPITAL, _REGIME)

    def test_meta_mixed_invalid_raises(self):
        with pytest.raises(ValueError, match="All meta_uncertainties must be in"):
            run_optimization(_RETURNS, _PRICES, [20], [1], [0.5, 2.0], _CAPITAL, _REGIME)

    def test_valid_boundary_meta_zero(self):
        with patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output()):
            result = run_optimization(_RETURNS, _PRICES, [20], [1], [0.0], _CAPITAL, _REGIME)
            assert len(result) == 1

    def test_valid_boundary_meta_one(self):
        with patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output()):
            result = run_optimization(_RETURNS, _PRICES, [20], [1], [1.0], _CAPITAL, _REGIME)
            assert len(result) == 1

    def test_valid_boundary_window_20(self):
        with patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output()):
            result = run_optimization(_RETURNS, _PRICES, [20], [1], [0.2], _CAPITAL, _REGIME)
            assert len(result) == 1

    def test_valid_boundary_step_1(self):
        with patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output()):
            result = run_optimization(_RETURNS, _PRICES, [20], [1], [0.2], _CAPITAL, _REGIME)
            assert len(result) == 1


# ===================================================================
# TestRunOptimizationOutputStructure
# ===================================================================

class TestRunOptimizationOutputStructure:
    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_returns_list(self, mock_rs):
        result = run_optimization(_RETURNS, _PRICES, [20], [1], [0.2], _CAPITAL, _REGIME)
        assert isinstance(result, list)

    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_entry_has_required_keys(self, mock_rs):
        result = run_optimization(_RETURNS, _PRICES, [20], [1], [0.2], _CAPITAL, _REGIME)
        entry = result[0]
        assert "window" in entry
        assert "step" in entry
        assert "meta_uncertainty" in entry
        assert "result" in entry

    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_result_contains_strategy_output(self, mock_rs):
        result = run_optimization(_RETURNS, _PRICES, [20], [1], [0.2], _CAPITAL, _REGIME)
        r = result[0]["result"]
        assert "segments" in r
        assert "segment_metrics" in r
        assert "aggregate" in r

    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_window_value_matches(self, mock_rs):
        result = run_optimization(_RETURNS, _PRICES, [25], [3], [0.5], _CAPITAL, _REGIME)
        assert result[0]["window"] == 25
        assert result[0]["step"] == 3
        assert result[0]["meta_uncertainty"] == 0.5


# ===================================================================
# TestRunOptimizationCartesianProduct
# ===================================================================

class TestRunOptimizationCartesianProduct:
    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_single_combination(self, mock_rs):
        result = run_optimization(_RETURNS, _PRICES, [20], [1], [0.2], _CAPITAL, _REGIME)
        assert len(result) == 1

    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_multiple_windows(self, mock_rs):
        result = run_optimization(_RETURNS, _PRICES, [20, 25], [1], [0.2], _CAPITAL, _REGIME)
        assert len(result) == 2
        assert result[0]["window"] == 20
        assert result[1]["window"] == 25

    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_multiple_steps(self, mock_rs):
        result = run_optimization(_RETURNS, _PRICES, [20], [1, 5], [0.2], _CAPITAL, _REGIME)
        assert len(result) == 2
        assert result[0]["step"] == 1
        assert result[1]["step"] == 5

    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_multiple_metas(self, mock_rs):
        result = run_optimization(_RETURNS, _PRICES, [20], [1], [0.1, 0.5], _CAPITAL, _REGIME)
        assert len(result) == 2
        assert result[0]["meta_uncertainty"] == 0.1
        assert result[1]["meta_uncertainty"] == 0.5

    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_full_cartesian_product_count(self, mock_rs):
        result = run_optimization(
            _RETURNS, _PRICES,
            [20, 25, 30], [1, 5], [0.1, 0.3, 0.5],
            _CAPITAL, _REGIME,
        )
        assert len(result) == 3 * 2 * 3  # 18

    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_iteration_order_windows_outer(self, mock_rs):
        result = run_optimization(
            _RETURNS, _PRICES,
            [20, 25], [1, 5], [0.1, 0.3],
            _CAPITAL, _REGIME,
        )
        # Expected order: (20,1,0.1), (20,1,0.3), (20,5,0.1), (20,5,0.3),
        #                 (25,1,0.1), (25,1,0.3), (25,5,0.1), (25,5,0.3)
        assert len(result) == 8
        assert result[0]["window"] == 20
        assert result[0]["step"] == 1
        assert result[0]["meta_uncertainty"] == 0.1
        assert result[1]["meta_uncertainty"] == 0.3
        assert result[2]["step"] == 5
        assert result[4]["window"] == 25

    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_call_count_matches_product(self, mock_rs):
        run_optimization(
            _RETURNS, _PRICES,
            [20, 25], [1, 5], [0.1, 0.5, 0.9],
            _CAPITAL, _REGIME,
        )
        assert mock_rs.call_count == 2 * 2 * 3


# ===================================================================
# TestRunOptimizationDelegation
# ===================================================================

class TestRunOptimizationDelegation:
    @patch("jarvis.optimization.engine.run_strategy")
    def test_passes_returns_series(self, mock_rs):
        mock_rs.return_value = _dummy_strategy_output()
        run_optimization(_RETURNS, _PRICES, [20], [1], [0.2], _CAPITAL, _REGIME)
        call_kwargs = mock_rs.call_args[1]
        assert call_kwargs["returns_series"] is _RETURNS

    @patch("jarvis.optimization.engine.run_strategy")
    def test_passes_asset_price_series(self, mock_rs):
        mock_rs.return_value = _dummy_strategy_output()
        run_optimization(_RETURNS, _PRICES, [20], [1], [0.2], _CAPITAL, _REGIME)
        call_kwargs = mock_rs.call_args[1]
        assert call_kwargs["asset_price_series"] is _PRICES

    @patch("jarvis.optimization.engine.run_strategy")
    def test_passes_window(self, mock_rs):
        mock_rs.return_value = _dummy_strategy_output()
        run_optimization(_RETURNS, _PRICES, [25], [3], [0.2], _CAPITAL, _REGIME)
        call_kwargs = mock_rs.call_args[1]
        assert call_kwargs["window"] == 25

    @patch("jarvis.optimization.engine.run_strategy")
    def test_passes_step(self, mock_rs):
        mock_rs.return_value = _dummy_strategy_output()
        run_optimization(_RETURNS, _PRICES, [20], [7], [0.2], _CAPITAL, _REGIME)
        call_kwargs = mock_rs.call_args[1]
        assert call_kwargs["step"] == 7

    @patch("jarvis.optimization.engine.run_strategy")
    def test_passes_meta_uncertainty(self, mock_rs):
        mock_rs.return_value = _dummy_strategy_output()
        run_optimization(_RETURNS, _PRICES, [20], [1], [0.75], _CAPITAL, _REGIME)
        call_kwargs = mock_rs.call_args[1]
        assert call_kwargs["meta_uncertainty"] == 0.75

    @patch("jarvis.optimization.engine.run_strategy")
    def test_passes_initial_capital(self, mock_rs):
        mock_rs.return_value = _dummy_strategy_output()
        run_optimization(_RETURNS, _PRICES, [20], [1], [0.2], 50_000.0, _REGIME)
        call_kwargs = mock_rs.call_args[1]
        assert call_kwargs["initial_capital"] == 50_000.0

    @patch("jarvis.optimization.engine.run_strategy")
    def test_passes_regime(self, mock_rs):
        mock_rs.return_value = _dummy_strategy_output()
        run_optimization(_RETURNS, _PRICES, [20], [1], [0.2], _CAPITAL, GlobalRegimeState.CRISIS)
        call_kwargs = mock_rs.call_args[1]
        assert call_kwargs["regime"] is GlobalRegimeState.CRISIS


# ===================================================================
# TestRunOptimizationDeterminism
# ===================================================================

class TestRunOptimizationDeterminism:
    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_identical_calls_identical_output(self, mock_rs):
        args = (_RETURNS, _PRICES, [20, 25], [1, 5], [0.1, 0.5], _CAPITAL, _REGIME)
        r1 = run_optimization(*args)
        r2 = run_optimization(*args)
        assert len(r1) == len(r2)
        for a, b in zip(r1, r2):
            assert a["window"] == b["window"]
            assert a["step"] == b["step"]
            assert a["meta_uncertainty"] == b["meta_uncertainty"]

    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_input_lists_not_mutated(self, mock_rs):
        windows = [20, 25]
        steps_list = [1, 5]
        metas = [0.1, 0.5]
        returns = list(_RETURNS)
        prices = list(_PRICES)
        w_orig, s_orig, m_orig = list(windows), list(steps_list), list(metas)
        r_orig, p_orig = list(returns), list(prices)

        run_optimization(returns, prices, windows, steps_list, metas, _CAPITAL, _REGIME)

        assert windows == w_orig
        assert steps_list == s_orig
        assert metas == m_orig
        assert returns == r_orig
        assert prices == p_orig


# ===================================================================
# TestRunOptimizationIntegration
# ===================================================================

class TestRunOptimizationIntegration:
    """Integration test using real run_strategy (no mocking)."""

    def test_single_combination_real(self):
        returns = [0.01, -0.005, 0.008, -0.003, 0.012] * 10  # 50 points
        prices = [100.0 + i * 0.1 for i in range(50)]
        result = run_optimization(
            returns, prices,
            windows=[20],
            steps=[5],
            meta_uncertainties=[0.2],
            initial_capital=100_000.0,
            regime=GlobalRegimeState.RISK_ON,
        )
        assert len(result) == 1
        entry = result[0]
        assert entry["window"] == 20
        assert entry["step"] == 5
        assert entry["meta_uncertainty"] == 0.2
        assert "segments" in entry["result"]
        assert "aggregate" in entry["result"]

    def test_multiple_regimes(self):
        returns = [0.01, -0.005, 0.008, -0.003, 0.012] * 10
        prices = [100.0 + i * 0.1 for i in range(50)]
        for regime in GlobalRegimeState:
            result = run_optimization(
                returns, prices,
                windows=[20],
                steps=[5],
                meta_uncertainties=[0.2],
                initial_capital=100_000.0,
                regime=regime,
            )
            assert len(result) == 1


# ===================================================================
# TestRunOptimizationEdgeCases
# ===================================================================

class TestRunOptimizationEdgeCases:
    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_single_element_lists(self, mock_rs):
        result = run_optimization(_RETURNS, _PRICES, [20], [1], [0.0], _CAPITAL, _REGIME)
        assert len(result) == 1

    @patch("jarvis.optimization.engine.run_strategy", return_value=_dummy_strategy_output())
    def test_large_window(self, mock_rs):
        result = run_optimization(_RETURNS, _PRICES, [100], [1], [0.2], _CAPITAL, _REGIME)
        assert result[0]["window"] == 100

    @patch("jarvis.optimization.engine.run_strategy")
    def test_strategy_error_propagates(self, mock_rs):
        mock_rs.side_effect = ValueError("series too short")
        with pytest.raises(ValueError, match="series too short"):
            run_optimization(_RETURNS, _PRICES, [20], [1], [0.2], _CAPITAL, _REGIME)

    def test_validation_before_strategy_call(self):
        """Validation errors fire before any run_strategy call."""
        with patch("jarvis.optimization.engine.run_strategy") as mock_rs:
            with pytest.raises(ValueError, match="windows must not be empty"):
                run_optimization(_RETURNS, _PRICES, [], [1], [0.2], _CAPITAL, _REGIME)
            mock_rs.assert_not_called()


# ===================================================================
# TestModuleExports
# ===================================================================

class TestModuleExports:
    def test_init_exports_run_optimization(self):
        from jarvis.optimization import run_optimization as ro
        assert ro is run_optimization

    def test_importable_from_engine(self):
        from jarvis.optimization.engine import run_optimization as ro
        assert callable(ro)
