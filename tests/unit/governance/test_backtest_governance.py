# =============================================================================
# tests/unit/governance/test_backtest_governance.py
# Tests for jarvis/governance/backtest_governance.py
# =============================================================================

import pytest

from jarvis.governance.backtest_governance import (
    TRAIN_WINDOW_MIN,
    TEST_WINDOW,
    MIN_TRADES,
    TRANSACTION_COST_MIN,
    WFV_MIN_OOS_RATIO,
    WFV_MIN_SEGMENTS,
    WFV_MIN_IS_BARS,
    PERFORMANCE_SPIKE_THRESHOLD,
    BacktestValidationResult,
    WalkForwardSplit,
    OverfittingReport,
    BacktestGovernanceEngine,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_train_window_min(self):
        assert TRAIN_WINDOW_MIN == 365

    def test_test_window(self):
        assert TEST_WINDOW == 90

    def test_min_trades(self):
        assert MIN_TRADES == 30

    def test_transaction_cost_min(self):
        assert TRANSACTION_COST_MIN == 0.0001

    def test_wfv_min_oos_ratio(self):
        assert WFV_MIN_OOS_RATIO == 0.30

    def test_wfv_min_segments(self):
        assert WFV_MIN_SEGMENTS == 3

    def test_wfv_min_is_bars(self):
        assert WFV_MIN_IS_BARS == 100

    def test_performance_spike_threshold(self):
        assert PERFORMANCE_SPIKE_THRESHOLD == 3.0


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

class TestWalkForwardSplit:
    def test_frozen(self):
        s = WalkForwardSplit(0, 365, 365, 455)
        with pytest.raises(AttributeError):
            s.train_start = 10

    def test_fields(self):
        s = WalkForwardSplit(
            train_start=0, train_end=365,
            test_start=365, test_end=455,
        )
        assert s.train_start == 0
        assert s.train_end == 365
        assert s.test_start == 365
        assert s.test_end == 455

    def test_equality(self):
        s1 = WalkForwardSplit(0, 365, 365, 455)
        s2 = WalkForwardSplit(0, 365, 365, 455)
        assert s1 == s2


class TestBacktestValidationResult:
    def test_frozen(self):
        r = BacktestValidationResult(True, (), ())
        with pytest.raises(AttributeError):
            r.valid = False

    def test_fields(self):
        r = BacktestValidationResult(
            valid=False,
            violations=(("BACKTEST-01", "too short"),),
            warnings=(),
        )
        assert r.valid is False
        assert len(r.violations) == 1


class TestOverfittingReport:
    def test_frozen(self):
        r = OverfittingReport("S1", True, False, True, 4.0, 0.3)
        with pytest.raises(AttributeError):
            r.overfitting_flag = False

    def test_fields(self):
        r = OverfittingReport(
            strategy_id="S1",
            performance_spike=True,
            param_sensitivity=False,
            overfitting_flag=True,
            is_to_oos_ratio=4.0,
            sensitivity_score=0.3,
        )
        assert r.strategy_id == "S1"
        assert r.performance_spike is True
        assert r.param_sensitivity is False
        assert r.overfitting_flag is True
        assert r.is_to_oos_ratio == 4.0
        assert r.sensitivity_score == 0.3


# =============================================================================
# SECTION 3 -- VALIDATE BACKTEST
# =============================================================================

class TestValidateBacktest:
    def test_valid(self):
        eng = BacktestGovernanceEngine()
        r = eng.validate_backtest(
            total_data_days=1095,  # 3 years
            transaction_costs=0.001,
            n_trades=50,
        )
        assert r.valid is True
        assert len(r.violations) == 0

    def test_insufficient_data(self):
        eng = BacktestGovernanceEngine()
        r = eng.validate_backtest(
            total_data_days=400,  # < 365 + 90 = 455
            transaction_costs=0.001,
            n_trades=50,
        )
        assert r.valid is False
        assert any("BACKTEST-01" in v[0] for v in r.violations)

    def test_low_transaction_costs(self):
        eng = BacktestGovernanceEngine()
        r = eng.validate_backtest(
            total_data_days=1095,
            transaction_costs=0.00005,  # < 1 bps
            n_trades=50,
        )
        assert r.valid is False
        assert any("BACKTEST-02" in v[0] for v in r.violations)

    def test_too_few_trades(self):
        eng = BacktestGovernanceEngine()
        r = eng.validate_backtest(
            total_data_days=1095,
            transaction_costs=0.001,
            n_trades=10,  # < 30
        )
        assert r.valid is False
        assert any("BACKTEST-TRADES" in v[0] for v in r.violations)

    def test_insufficient_wf_segments(self):
        eng = BacktestGovernanceEngine()
        # 455 days = exactly 1 segment (365+90), need >= 3
        r = eng.validate_backtest(
            total_data_days=455,
            transaction_costs=0.001,
            n_trades=50,
        )
        assert r.valid is False
        assert any("BACKTEST-03" in v[0] for v in r.violations)

    def test_multiple_violations(self):
        eng = BacktestGovernanceEngine()
        r = eng.validate_backtest(
            total_data_days=200,
            transaction_costs=0.00001,
            n_trades=5,
        )
        assert r.valid is False
        assert len(r.violations) >= 3

    def test_exact_minimum(self):
        """Exact minimum for 3 segments: 365 + 90*3 = 635 days."""
        eng = BacktestGovernanceEngine()
        r = eng.validate_backtest(
            total_data_days=635,
            transaction_costs=0.0001,
            n_trades=30,
        )
        assert r.valid is True

    def test_type_error_days(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(TypeError, match="total_data_days must be int"):
            eng.validate_backtest(1095.0, 0.001, 50)

    def test_type_error_costs(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(TypeError, match="transaction_costs must be numeric"):
            eng.validate_backtest(1095, "bad", 50)

    def test_type_error_trades(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(TypeError, match="n_trades must be int"):
            eng.validate_backtest(1095, 0.001, 50.0)


# =============================================================================
# SECTION 4 -- WALK-FORWARD SPLITS
# =============================================================================

class TestWalkForwardSplits:
    def test_three_years(self):
        eng = BacktestGovernanceEngine()
        splits = eng.generate_walk_forward_splits(1095)
        # (1095 - 365) / 90 = 8.11 → 8 splits starting at day 0
        # But sliding: day 0 → 365+90=455, day 90 → 455+90=545, ...
        # Max start: 1095 - 365 - 90 = 640, starts at 0,90,180,...,630
        # That's 0,90,180,270,360,450,540,630 = 8 splits
        assert len(splits) == 8

    def test_exact_minimum(self):
        eng = BacktestGovernanceEngine()
        # 365 + 90 = 455 days → exactly 1 split
        splits = eng.generate_walk_forward_splits(455)
        assert len(splits) == 1
        assert splits[0] == WalkForwardSplit(0, 365, 365, 455)

    def test_first_split(self):
        eng = BacktestGovernanceEngine()
        splits = eng.generate_walk_forward_splits(1095)
        assert splits[0].train_start == 0
        assert splits[0].train_end == 365
        assert splits[0].test_start == 365
        assert splits[0].test_end == 455

    def test_second_split(self):
        eng = BacktestGovernanceEngine()
        splits = eng.generate_walk_forward_splits(1095)
        assert splits[1].train_start == 90
        assert splits[1].train_end == 455
        assert splits[1].test_start == 455
        assert splits[1].test_end == 545

    def test_no_overlap_test_windows(self):
        eng = BacktestGovernanceEngine()
        splits = eng.generate_walk_forward_splits(1095)
        for i in range(len(splits) - 1):
            # Test windows should be non-overlapping and sequential
            assert splits[i].test_end == splits[i + 1].test_start

    def test_train_window_size(self):
        eng = BacktestGovernanceEngine()
        splits = eng.generate_walk_forward_splits(1095)
        for s in splits:
            assert s.train_end - s.train_start == TRAIN_WINDOW_MIN

    def test_test_window_size(self):
        eng = BacktestGovernanceEngine()
        splits = eng.generate_walk_forward_splits(1095)
        for s in splits:
            assert s.test_end - s.test_start == TEST_WINDOW

    def test_insufficient_data_empty(self):
        eng = BacktestGovernanceEngine()
        splits = eng.generate_walk_forward_splits(400)
        assert len(splits) == 0

    def test_zero_days(self):
        eng = BacktestGovernanceEngine()
        splits = eng.generate_walk_forward_splits(0)
        assert len(splits) == 0

    def test_type_error(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(TypeError, match="total_data_days must be int"):
            eng.generate_walk_forward_splits(1095.0)

    def test_negative_raises(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(ValueError, match="total_data_days must be >= 0"):
            eng.generate_walk_forward_splits(-1)


# =============================================================================
# SECTION 5 -- OOS RATIO VALIDATION
# =============================================================================

class TestOOSRatio:
    def test_valid_ratio(self):
        eng = BacktestGovernanceEngine()
        # 100 IS, 50 OOS → ratio = 50/150 ≈ 0.333 >= 0.30
        assert eng.validate_oos_ratio(100, 50) is True

    def test_exact_threshold(self):
        eng = BacktestGovernanceEngine()
        # 70 IS, 30 OOS → ratio = 30/100 = 0.30 >= 0.30
        assert eng.validate_oos_ratio(70, 30) is True

    def test_below_threshold(self):
        eng = BacktestGovernanceEngine()
        # 90 IS, 10 OOS → ratio = 10/100 = 0.10 < 0.30
        assert eng.validate_oos_ratio(90, 10) is False

    def test_all_oos(self):
        eng = BacktestGovernanceEngine()
        assert eng.validate_oos_ratio(0, 100) is True

    def test_zero_total_raises(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(ValueError, match="Total bars must be > 0"):
            eng.validate_oos_ratio(0, 0)

    def test_negative_raises(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(ValueError, match="Bars must be >= 0"):
            eng.validate_oos_ratio(-1, 50)

    def test_type_error_is(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(TypeError, match="is_bars must be int"):
            eng.validate_oos_ratio(100.0, 50)

    def test_type_error_oos(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(TypeError, match="oos_bars must be int"):
            eng.validate_oos_ratio(100, 50.0)


# =============================================================================
# SECTION 6 -- IS BARS VALIDATION
# =============================================================================

class TestISBars:
    def test_sufficient(self):
        eng = BacktestGovernanceEngine()
        assert eng.validate_is_bars(100) is True

    def test_above_minimum(self):
        eng = BacktestGovernanceEngine()
        assert eng.validate_is_bars(200) is True

    def test_below_minimum(self):
        eng = BacktestGovernanceEngine()
        assert eng.validate_is_bars(50) is False

    def test_exact_minimum(self):
        eng = BacktestGovernanceEngine()
        assert eng.validate_is_bars(100) is True

    def test_type_error(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(TypeError, match="is_bars must be int"):
            eng.validate_is_bars(100.0)


# =============================================================================
# SECTION 7 -- OVERFITTING DETECTION
# =============================================================================

class TestOverfittingDetection:
    def test_no_overfitting(self):
        eng = BacktestGovernanceEngine()
        r = eng.detect_overfitting("S1", 1.5, 1.0, 0.3)
        assert r.overfitting_flag is False
        assert r.performance_spike is False
        assert r.param_sensitivity is False

    def test_performance_spike(self):
        eng = BacktestGovernanceEngine()
        # IS=4.0, OOS=1.0 → ratio=4.0 > 3.0
        r = eng.detect_overfitting("S1", 4.0, 1.0, 0.3)
        assert r.performance_spike is True
        assert r.overfitting_flag is True
        assert r.is_to_oos_ratio == pytest.approx(4.0)

    def test_at_threshold_no_spike(self):
        eng = BacktestGovernanceEngine()
        # IS=3.0, OOS=1.0 → ratio=3.0, NOT > 3.0
        r = eng.detect_overfitting("S1", 3.0, 1.0, 0.3)
        assert r.performance_spike is False

    def test_param_sensitivity(self):
        eng = BacktestGovernanceEngine()
        r = eng.detect_overfitting("S1", 1.5, 1.0, 0.6)
        assert r.param_sensitivity is True
        assert r.overfitting_flag is True

    def test_sensitivity_at_threshold(self):
        eng = BacktestGovernanceEngine()
        # sensitivity=0.5, NOT > 0.5
        r = eng.detect_overfitting("S1", 1.5, 1.0, 0.5)
        assert r.param_sensitivity is False

    def test_both_flags(self):
        eng = BacktestGovernanceEngine()
        r = eng.detect_overfitting("S1", 5.0, 1.0, 0.8)
        assert r.performance_spike is True
        assert r.param_sensitivity is True
        assert r.overfitting_flag is True

    def test_zero_oos_sharpe(self):
        eng = BacktestGovernanceEngine()
        # OOS ≈ 0, IS > 0 → spike
        r = eng.detect_overfitting("S1", 2.0, 0.0, 0.3)
        assert r.performance_spike is True
        assert r.is_to_oos_ratio == float("inf")

    def test_both_zero(self):
        eng = BacktestGovernanceEngine()
        r = eng.detect_overfitting("S1", 0.0, 0.0, 0.3)
        assert r.is_to_oos_ratio == 1.0
        assert r.performance_spike is False

    def test_negative_sharpe(self):
        eng = BacktestGovernanceEngine()
        # IS=-1.0, OOS=-0.5 → abs ratio=2.0
        r = eng.detect_overfitting("S1", -1.0, -0.5, 0.3)
        assert r.is_to_oos_ratio == pytest.approx(2.0)
        assert r.performance_spike is False

    def test_strategy_id_stored(self):
        eng = BacktestGovernanceEngine()
        r = eng.detect_overfitting("MY_STRAT", 1.0, 1.0, 0.3)
        assert r.strategy_id == "MY_STRAT"

    def test_type_error_strategy_id(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(TypeError, match="strategy_id must be a string"):
            eng.detect_overfitting(123, 1.0, 1.0, 0.3)

    def test_type_error_is_sharpe(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(TypeError, match="is_sharpe must be numeric"):
            eng.detect_overfitting("S1", "bad", 1.0, 0.3)

    def test_type_error_oos_sharpe(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(TypeError, match="oos_sharpe must be numeric"):
            eng.detect_overfitting("S1", 1.0, "bad", 0.3)

    def test_type_error_sensitivity(self):
        eng = BacktestGovernanceEngine()
        with pytest.raises(TypeError, match="sensitivity_score must be numeric"):
            eng.detect_overfitting("S1", 1.0, 1.0, "bad")


# =============================================================================
# SECTION 8 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_validate_deterministic(self):
        eng = BacktestGovernanceEngine()
        results = [
            eng.validate_backtest(1095, 0.001, 50)
            for _ in range(10)
        ]
        assert all(r == results[0] for r in results)

    def test_splits_deterministic(self):
        eng = BacktestGovernanceEngine()
        r1 = eng.generate_walk_forward_splits(1095)
        r2 = eng.generate_walk_forward_splits(1095)
        assert r1 == r2

    def test_overfitting_deterministic(self):
        eng = BacktestGovernanceEngine()
        r1 = eng.detect_overfitting("S1", 4.0, 1.0, 0.6)
        r2 = eng.detect_overfitting("S1", 4.0, 1.0, 0.6)
        assert r1 == r2

    def test_independent_engines(self):
        r1 = BacktestGovernanceEngine().validate_backtest(1095, 0.001, 50)
        r2 = BacktestGovernanceEngine().validate_backtest(1095, 0.001, 50)
        assert r1 == r2
