# =============================================================================
# test_metrics_engine.py -- Unit tests for jarvis/metrics/engine.py
#
# Covers all 5 public functions:
#   sharpe_ratio, max_drawdown, calmar_ratio,
#   regime_conditional_returns, compute_metrics
#
# Mutation-killing strategy:
#   - Every boundary, edge case, and operator is tested
#   - Expected values computed by hand from raw formulas
#   - Determinism verified via repeated calls
#   - Input immutability verified
#   - All error paths exercised
# =============================================================================

from __future__ import annotations

import math

import pytest

from jarvis.metrics.engine import (
    _mean,
    _std,
    calmar_ratio,
    compute_metrics,
    max_drawdown,
    regime_conditional_returns,
    sharpe_ratio,
)


# =============================================================================
# SECTION 1 -- HELPERS (_mean, _std)
# =============================================================================

class TestMean:
    def test_empty(self):
        assert _mean([]) == 0.0

    def test_single(self):
        assert _mean([5.0]) == 5.0

    def test_two_values(self):
        assert _mean([2.0, 4.0]) == 3.0

    def test_negative(self):
        assert _mean([-1.0, 1.0]) == 0.0

    def test_all_same(self):
        assert _mean([3.0, 3.0, 3.0]) == 3.0


class TestStd:
    def test_empty(self):
        assert _std([]) == 0.0

    def test_single_ddof1(self):
        assert _std([5.0], ddof=1) == 0.0

    def test_two_identical(self):
        assert _std([3.0, 3.0], ddof=1) == 0.0

    def test_two_values(self):
        # variance = ((1-1.5)^2 + (2-1.5)^2) / (2-1) = 0.5
        assert _std([1.0, 2.0], ddof=1) == pytest.approx(math.sqrt(0.5))

    def test_ddof0(self):
        # population std
        assert _std([1.0, 2.0], ddof=0) == pytest.approx(0.5)

    def test_n_equals_ddof(self):
        assert _std([1.0], ddof=1) == 0.0


# =============================================================================
# SECTION 2 -- SHARPE RATIO
# =============================================================================

class TestSharpeRatio:
    def test_empty_returns_zero(self):
        assert sharpe_ratio([]) == 0.0

    def test_single_return_zero(self):
        assert sharpe_ratio([0.01]) == 0.0

    def test_constant_returns_zero(self):
        # all same -> std=0 -> return 0
        assert sharpe_ratio([0.01, 0.01, 0.01]) == 0.0

    def test_positive_returns(self):
        rets = [0.01, 0.02, 0.03]
        mu = sum(rets) / 3
        var = sum((r - mu) ** 2 for r in rets) / 2  # ddof=1
        sd = math.sqrt(var)
        expected = (mu / sd) * math.sqrt(252)
        assert sharpe_ratio(rets) == pytest.approx(expected)

    def test_with_risk_free_rate(self):
        rets = [0.01, 0.02, 0.03]
        rf = 0.05
        daily_rf = rf / 252
        excess = [r - daily_rf for r in rets]
        mu = sum(excess) / 3
        var = sum((e - mu) ** 2 for e in excess) / 2
        sd = math.sqrt(var)
        expected = (mu / sd) * math.sqrt(252)
        assert sharpe_ratio(rets, risk_free_rate=rf) == pytest.approx(expected)

    def test_custom_periods(self):
        rets = [0.01, 0.02]
        mu = sum(rets) / 2
        var = sum((r - mu) ** 2 for r in rets) / 1
        sd = math.sqrt(var)
        expected = (mu / sd) * math.sqrt(12)
        assert sharpe_ratio(rets, periods_per_year=12) == pytest.approx(expected)

    def test_periods_per_year_zero_raises(self):
        with pytest.raises(ValueError, match="periods_per_year must be >= 1"):
            sharpe_ratio([0.01, 0.02], periods_per_year=0)

    def test_periods_per_year_negative_raises(self):
        with pytest.raises(ValueError, match="periods_per_year must be >= 1"):
            sharpe_ratio([0.01, 0.02], periods_per_year=-1)

    def test_negative_returns(self):
        rets = [-0.01, -0.02, -0.03]
        result = sharpe_ratio(rets)
        assert result < 0.0

    def test_determinism(self):
        rets = [0.01, -0.005, 0.02, -0.01, 0.015]
        r1 = sharpe_ratio(rets)
        r2 = sharpe_ratio(rets)
        assert r1 == r2

    def test_input_not_mutated(self):
        rets = [0.01, 0.02, 0.03]
        original = rets.copy()
        sharpe_ratio(rets)
        assert rets == original


# =============================================================================
# SECTION 3 -- MAX DRAWDOWN
# =============================================================================

class TestMaxDrawdown:
    def test_empty_returns_zero(self):
        assert max_drawdown([]) == 0.0

    def test_single_returns_zero(self):
        assert max_drawdown([0.05]) == 0.0

    def test_all_positive_returns(self):
        # monotonically increasing -> no drawdown
        assert max_drawdown([0.01, 0.01, 0.01]) == 0.0

    def test_single_drop(self):
        # 1.0 -> 1.1 -> 0.99 (drop from 1.1)
        # dd = (1.1 - 0.99) / 1.1 = 0.1/1.1
        rets = [0.10, -0.10]
        cum_after_first = 1.0 * 1.10
        cum_after_second = cum_after_first * 0.90
        peak = cum_after_first
        expected_dd = (peak - cum_after_second) / peak
        assert max_drawdown(rets) == pytest.approx(expected_dd)

    def test_recovery(self):
        # up, down, up -> drawdown should be the single dip
        rets = [0.10, -0.05, 0.10]
        result = max_drawdown(rets)
        assert result > 0.0
        assert result < 0.10  # less than 10%

    def test_total_loss(self):
        # -100% return
        rets = [0.0, -1.0]
        assert max_drawdown(rets) == pytest.approx(1.0)

    def test_two_dips_takes_larger(self):
        # first dip: small, then recovery, then bigger dip
        rets = [0.10, -0.02, 0.10, -0.15]
        result = max_drawdown(rets)
        # the second dip is larger
        # verify it's close to 0.15 adjusted for compounding
        assert result > 0.10

    def test_determinism(self):
        rets = [0.01, -0.05, 0.02, -0.10, 0.03]
        r1 = max_drawdown(rets)
        r2 = max_drawdown(rets)
        assert r1 == r2

    def test_non_negative(self):
        rets = [0.01, -0.05, 0.02, -0.10, 0.03]
        assert max_drawdown(rets) >= 0.0

    def test_input_not_mutated(self):
        rets = [0.01, -0.05, 0.02]
        original = rets.copy()
        max_drawdown(rets)
        assert rets == original


# =============================================================================
# SECTION 4 -- CALMAR RATIO
# =============================================================================

class TestCalmarRatio:
    def test_empty_returns_zero(self):
        assert calmar_ratio([]) == 0.0

    def test_single_returns_zero(self):
        assert calmar_ratio([0.05]) == 0.0

    def test_no_drawdown_returns_zero(self):
        # all positive -> max_drawdown=0 -> calmar=0
        assert calmar_ratio([0.01, 0.01, 0.01]) == 0.0

    def test_positive_returns_with_drawdown(self):
        rets = [0.10, -0.05, 0.10, -0.02]
        result = calmar_ratio(rets)
        # ann_return / max_drawdown; both positive
        n = len(rets)
        total = 1.0
        for r in rets:
            total *= (1.0 + r)
        ann_ret = total ** (252 / n) - 1.0
        mdd = max_drawdown(rets)
        expected = ann_ret / mdd
        assert result == pytest.approx(expected)

    def test_custom_periods(self):
        rets = [0.10, -0.05, 0.10]
        result = calmar_ratio(rets, periods_per_year=12)
        n = len(rets)
        total = 1.0
        for r in rets:
            total *= (1.0 + r)
        ann_ret = total ** (12 / n) - 1.0
        mdd = max_drawdown(rets)
        expected = ann_ret / mdd
        assert result == pytest.approx(expected)

    def test_periods_per_year_zero_raises(self):
        with pytest.raises(ValueError, match="periods_per_year must be >= 1"):
            calmar_ratio([0.01, -0.01], periods_per_year=0)

    def test_determinism(self):
        rets = [0.05, -0.03, 0.08, -0.06]
        r1 = calmar_ratio(rets)
        r2 = calmar_ratio(rets)
        assert r1 == r2


# =============================================================================
# SECTION 5 -- REGIME-CONDITIONAL RETURNS
# =============================================================================

class TestRegimeConditionalReturns:
    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="equal length"):
            regime_conditional_returns([0.01], ["A", "B"])

    def test_empty_returns_empty_dict(self):
        assert regime_conditional_returns([], []) == {}

    def test_single_regime(self):
        result = regime_conditional_returns(
            [0.01, 0.02, 0.03], ["A", "A", "A"]
        )
        assert "A" in result
        assert result["A"]["count"] == 3.0
        assert result["A"]["mean"] == pytest.approx(0.02)
        assert result["A"]["total"] == pytest.approx(0.06)

    def test_two_regimes(self):
        result = regime_conditional_returns(
            [0.01, 0.02, 0.03, 0.04],
            ["A", "B", "A", "B"],
        )
        assert sorted(result.keys()) == ["A", "B"]
        assert result["A"]["count"] == 2.0
        assert result["A"]["mean"] == pytest.approx(0.02)  # (0.01+0.03)/2
        assert result["B"]["count"] == 2.0
        assert result["B"]["mean"] == pytest.approx(0.03)  # (0.02+0.04)/2

    def test_sorted_by_label(self):
        result = regime_conditional_returns(
            [0.01, 0.02, 0.03],
            ["C", "A", "B"],
        )
        assert list(result.keys()) == ["A", "B", "C"]

    def test_determinism(self):
        rets = [0.01, -0.02, 0.03]
        labels = ["X", "Y", "X"]
        r1 = regime_conditional_returns(rets, labels)
        r2 = regime_conditional_returns(rets, labels)
        assert r1 == r2

    def test_input_not_mutated(self):
        rets = [0.01, 0.02]
        labels = ["A", "B"]
        rets_orig = rets.copy()
        labels_orig = labels.copy()
        regime_conditional_returns(rets, labels)
        assert rets == rets_orig
        assert labels == labels_orig


# =============================================================================
# SECTION 6 -- COMPUTE METRICS
# =============================================================================

class TestComputeMetrics:
    def test_basic_output_keys(self):
        result = compute_metrics([100.0, 105.0, 110.0])
        expected_keys = {"total_return", "cagr", "volatility", "sharpe", "max_drawdown"}
        assert set(result.keys()) == expected_keys

    def test_all_values_finite(self):
        result = compute_metrics([100.0, 105.0, 103.0, 110.0])
        for k, v in result.items():
            assert math.isfinite(v), f"{k} is not finite: {v}"

    def test_total_return(self):
        curve = [100.0, 110.0]
        result = compute_metrics(curve)
        assert result["total_return"] == pytest.approx(0.10)

    def test_total_return_decline(self):
        curve = [100.0, 90.0]
        result = compute_metrics(curve)
        assert result["total_return"] == pytest.approx(-0.10)

    def test_total_return_flat(self):
        curve = [100.0, 100.0, 100.0]
        result = compute_metrics(curve)
        assert result["total_return"] == pytest.approx(0.0)

    def test_cagr_one_period(self):
        # With 1 return period and periods_per_year=1:
        # growth=1.10, cagr = 1.10^(1/1) - 1 = 0.10
        curve = [100.0, 110.0]
        result = compute_metrics(curve, periods_per_year=1)
        assert result["cagr"] == pytest.approx(0.10)

    def test_cagr_multi_period(self):
        curve = [100.0, 105.0, 110.25]
        # growth = 110.25/100 = 1.1025
        # n=2, periods=252 -> cagr = 1.1025^(252/2) - 1
        growth = 1.1025
        expected_cagr = growth ** (252 / 2) - 1.0
        result = compute_metrics(curve)
        assert result["cagr"] == pytest.approx(expected_cagr)

    def test_volatility_constant_curve_is_zero(self):
        curve = [100.0, 100.0, 100.0, 100.0]
        result = compute_metrics(curve)
        assert result["volatility"] == pytest.approx(0.0)

    def test_volatility_positive(self):
        curve = [100.0, 105.0, 103.0, 110.0]
        result = compute_metrics(curve)
        assert result["volatility"] > 0.0

    def test_volatility_hand_computed(self):
        curve = [100.0, 110.0, 105.0]
        # returns: [0.10, -0.04545...]
        r0 = 110.0 / 100.0 - 1.0
        r1 = 105.0 / 110.0 - 1.0
        rets = [r0, r1]
        mu = sum(rets) / 2
        var = sum((r - mu) ** 2 for r in rets) / 1  # ddof=1
        expected_vol = math.sqrt(var) * math.sqrt(252)
        result = compute_metrics(curve)
        assert result["volatility"] == pytest.approx(expected_vol)

    def test_sharpe_delegates_correctly(self):
        curve = [100.0, 105.0, 103.0, 110.0]
        result = compute_metrics(curve)
        # Recompute manually
        rets = [curve[i] / curve[i - 1] - 1.0 for i in range(1, len(curve))]
        expected_sharpe = sharpe_ratio(rets, 252, risk_free_rate=0.0)
        assert result["sharpe"] == pytest.approx(expected_sharpe)

    def test_max_drawdown_delegates_correctly(self):
        curve = [100.0, 110.0, 95.0, 105.0]
        result = compute_metrics(curve)
        rets = [curve[i] / curve[i - 1] - 1.0 for i in range(1, len(curve))]
        expected_mdd = max_drawdown(rets)
        assert result["max_drawdown"] == pytest.approx(expected_mdd)

    def test_max_drawdown_no_drawdown(self):
        curve = [100.0, 101.0, 102.0, 103.0]
        result = compute_metrics(curve)
        assert result["max_drawdown"] == 0.0

    def test_custom_periods_per_year(self):
        curve = [100.0, 105.0, 110.0]
        r252 = compute_metrics(curve, periods_per_year=252)
        r12 = compute_metrics(curve, periods_per_year=12)
        # Different annualisation -> different cagr & vol
        assert r252["cagr"] != r12["cagr"]
        assert r252["volatility"] != r12["volatility"]

    # --- Validation ---

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="at least 2"):
            compute_metrics([100.0])

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="at least 2"):
            compute_metrics([])

    def test_zero_value_raises(self):
        with pytest.raises(ValueError, match="must be finite and > 0"):
            compute_metrics([100.0, 0.0, 110.0])

    def test_negative_value_raises(self):
        with pytest.raises(ValueError, match="must be finite and > 0"):
            compute_metrics([100.0, -50.0])

    def test_nan_value_raises(self):
        with pytest.raises(ValueError, match="must be finite and > 0"):
            compute_metrics([100.0, float("nan"), 110.0])

    def test_inf_value_raises(self):
        with pytest.raises(ValueError, match="must be finite and > 0"):
            compute_metrics([100.0, float("inf")])

    def test_periods_zero_raises(self):
        with pytest.raises(ValueError, match="periods_per_year must be >= 1"):
            compute_metrics([100.0, 110.0], periods_per_year=0)

    def test_periods_negative_raises(self):
        with pytest.raises(ValueError, match="periods_per_year must be >= 1"):
            compute_metrics([100.0, 110.0], periods_per_year=-5)

    # --- Determinism & immutability ---

    def test_determinism(self):
        curve = [100.0, 105.0, 103.0, 108.0, 112.0]
        r1 = compute_metrics(curve)
        r2 = compute_metrics(curve)
        assert r1 == r2

    def test_input_not_mutated(self):
        curve = [100.0, 105.0, 103.0]
        original = curve.copy()
        compute_metrics(curve)
        assert curve == original

    def test_error_reports_index(self):
        with pytest.raises(ValueError, match=r"equity_curve\[2\]"):
            compute_metrics([100.0, 105.0, 0.0, 110.0])


# =============================================================================
# SECTION 7 -- MODULE __all__
# =============================================================================

class TestModuleAll:
    def test_all_contains_sharpe(self):
        from jarvis.metrics.engine import __all__
        assert "sharpe_ratio" in __all__

    def test_all_contains_max_drawdown(self):
        from jarvis.metrics.engine import __all__
        assert "max_drawdown" in __all__

    def test_all_contains_calmar(self):
        from jarvis.metrics.engine import __all__
        assert "calmar_ratio" in __all__

    def test_all_contains_regime(self):
        from jarvis.metrics.engine import __all__
        assert "regime_conditional_returns" in __all__

    def test_all_contains_compute_metrics(self):
        from jarvis.metrics.engine import __all__
        assert "compute_metrics" in __all__

    def test_all_length(self):
        from jarvis.metrics.engine import __all__
        assert len(__all__) == 5
