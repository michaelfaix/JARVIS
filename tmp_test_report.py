# =============================================================================
# Unit Tests for jarvis/report/engine.py
# =============================================================================

import copy
import pytest

from jarvis.report.engine import generate_report


# ===================================================================
# TestGenerateReportValidation
# ===================================================================

class TestGenerateReportValidation:
    def test_empty_curve_raises(self):
        with pytest.raises(ValueError, match="at least 2 values"):
            generate_report([])

    def test_single_value_raises(self):
        with pytest.raises(ValueError, match="at least 2 values"):
            generate_report([100.0])

    def test_two_values_valid(self):
        result = generate_report([100.0, 110.0])
        assert "metrics" in result

    def test_zero_equity_raises(self):
        # compute_metrics validates positivity
        with pytest.raises(ValueError):
            generate_report([100.0, 0.0])

    def test_negative_equity_raises(self):
        with pytest.raises(ValueError):
            generate_report([100.0, -10.0])


# ===================================================================
# TestGenerateReportOutputStructure
# ===================================================================

class TestGenerateReportOutputStructure:
    def setup_method(self):
        self.curve = [100.0, 105.0, 103.0, 108.0, 112.0]
        self.result = generate_report(self.curve)

    def test_top_level_keys(self):
        assert set(self.result.keys()) == {
            "equity_curve", "metrics", "periods_per_year",
        }

    def test_equity_curve_is_original_reference(self):
        assert self.result["equity_curve"] is self.curve

    def test_metrics_is_dict(self):
        assert isinstance(self.result["metrics"], dict)

    def test_metrics_has_total_return(self):
        assert "total_return" in self.result["metrics"]

    def test_metrics_has_cagr(self):
        assert "cagr" in self.result["metrics"]

    def test_metrics_has_volatility(self):
        assert "volatility" in self.result["metrics"]

    def test_metrics_has_sharpe(self):
        assert "sharpe_ratio" in self.result["metrics"]

    def test_metrics_has_max_drawdown(self):
        assert "max_drawdown" in self.result["metrics"]

    def test_periods_per_year_default(self):
        assert self.result["periods_per_year"] == 252

    def test_periods_per_year_custom(self):
        result = generate_report([100.0, 110.0], periods_per_year=12)
        assert result["periods_per_year"] == 12

    def test_metrics_values_are_floats(self):
        for key, val in self.result["metrics"].items():
            assert isinstance(val, float), f"{key} is {type(val)}"


# ===================================================================
# TestGenerateReportMetrics
# ===================================================================

class TestGenerateReportMetrics:
    def test_total_return_positive(self):
        result = generate_report([100.0, 120.0])
        assert result["metrics"]["total_return"] == pytest.approx(0.20)

    def test_total_return_negative(self):
        result = generate_report([100.0, 80.0])
        assert result["metrics"]["total_return"] == pytest.approx(-0.20)

    def test_total_return_zero(self):
        result = generate_report([100.0, 100.0])
        assert result["metrics"]["total_return"] == pytest.approx(0.0)

    def test_max_drawdown_no_drawdown(self):
        # Monotonically increasing -> no drawdown
        result = generate_report([100.0, 110.0, 120.0, 130.0])
        assert result["metrics"]["max_drawdown"] == pytest.approx(0.0)

    def test_max_drawdown_with_dip(self):
        result = generate_report([100.0, 110.0, 99.0, 105.0])
        # Peak 110, trough 99 -> drawdown = (110-99)/110 = 0.1
        assert result["metrics"]["max_drawdown"] == pytest.approx(0.1, abs=1e-6)

    def test_cagr_positive_for_gain(self):
        result = generate_report([100.0, 110.0, 120.0])
        assert result["metrics"]["cagr"] > 0.0

    def test_sharpe_positive_for_steady_gain(self):
        # Steady upward trend -> positive Sharpe
        curve = [100.0 + i * 2.0 for i in range(20)]
        result = generate_report(curve)
        assert result["metrics"]["sharpe_ratio"] > 0.0

    def test_volatility_positive(self):
        result = generate_report([100.0, 105.0, 95.0, 110.0])
        assert result["metrics"]["volatility"] > 0.0

    def test_volatility_zero_for_flat(self):
        result = generate_report([100.0, 100.0, 100.0])
        assert result["metrics"]["volatility"] == pytest.approx(0.0)


# ===================================================================
# TestGenerateReportDelegation
# ===================================================================

class TestGenerateReportDelegation:
    def test_delegates_to_compute_metrics(self):
        """Verify the report metrics match direct compute_metrics call."""
        from jarvis.metrics.engine import compute_metrics

        curve = [100.0, 105.0, 103.0, 108.0, 112.0]
        report = generate_report(curve, periods_per_year=52)
        direct = compute_metrics(curve, periods_per_year=52)

        assert report["metrics"] == direct

    def test_periods_per_year_passed_through(self):
        from jarvis.metrics.engine import compute_metrics

        curve = [100.0, 110.0, 120.0]
        r12 = generate_report(curve, periods_per_year=12)
        r252 = generate_report(curve, periods_per_year=252)

        d12 = compute_metrics(curve, 12)
        d252 = compute_metrics(curve, 252)

        assert r12["metrics"] == d12
        assert r252["metrics"] == d252
        # Different annualization -> different CAGR/vol
        assert r12["metrics"]["cagr"] != r252["metrics"]["cagr"]


# ===================================================================
# TestGenerateReportDeterminism
# ===================================================================

class TestGenerateReportDeterminism:
    def test_identical_calls(self):
        curve = [100.0, 105.0, 103.0, 108.0]
        r1 = generate_report(curve)
        r2 = generate_report(curve)
        assert r1["metrics"] == r2["metrics"]
        assert r1["periods_per_year"] == r2["periods_per_year"]

    def test_input_not_mutated(self):
        curve = [100.0, 105.0, 103.0, 108.0]
        original = list(curve)
        generate_report(curve)
        assert curve == original


# ===================================================================
# TestGenerateReportEdgeCases
# ===================================================================

class TestGenerateReportEdgeCases:
    def test_two_values_minimal(self):
        result = generate_report([100.0, 100.0])
        assert result["metrics"]["total_return"] == pytest.approx(0.0)

    def test_large_curve(self):
        curve = [100.0 + i * 0.01 for i in range(1000)]
        result = generate_report(curve)
        assert result["metrics"]["total_return"] > 0.0

    def test_very_small_values(self):
        result = generate_report([0.001, 0.002])
        assert result["metrics"]["total_return"] == pytest.approx(1.0)

    def test_periods_per_year_one(self):
        result = generate_report([100.0, 110.0], periods_per_year=1)
        assert result["periods_per_year"] == 1
        assert "cagr" in result["metrics"]


# ===================================================================
# TestModuleExports
# ===================================================================

class TestModuleExports:
    def test_init_exports_generate_report(self):
        from jarvis.report import generate_report as gr
        assert gr is generate_report

    def test_importable_from_engine(self):
        from jarvis.report.engine import generate_report as gr
        assert callable(gr)
