# =============================================================================
# tests/unit/research/test_walk_forward_validation.py
# Tests for jarvis/research/walk_forward_validation.py
# =============================================================================

import numpy as np
import pytest

from jarvis.research.walk_forward_validation import (
    WFV_MIN_OOS_RATIO,
    WFV_MIN_SEGMENTS,
    WFV_MIN_IS_BARS,
    CROSS_ASSET_MIN_POSITIVE,
    ROBUSTNESS_PENALTY,
    WalkForwardSegment,
    WalkForwardResult,
    CrossAssetRobustnessScore,
    WalkForwardValidationEngine,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_wfv_min_oos_ratio(self):
        assert WFV_MIN_OOS_RATIO == 0.30

    def test_wfv_min_segments(self):
        assert WFV_MIN_SEGMENTS == 3

    def test_wfv_min_is_bars(self):
        assert WFV_MIN_IS_BARS == 100

    def test_cross_asset_min_positive(self):
        assert CROSS_ASSET_MIN_POSITIVE == 2

    def test_robustness_penalty(self):
        assert ROBUSTNESS_PENALTY == 0.5


# =============================================================================
# SECTION 2 -- WALK FORWARD SEGMENT DATACLASS
# =============================================================================

class TestWalkForwardSegment:
    def test_frozen(self):
        s = WalkForwardSegment(0, 0, 100, 100, 130, 1.5, 1.2, 0.30)
        with pytest.raises(AttributeError):
            s.oos_sharpe = 0.0

    def test_fields(self):
        s = WalkForwardSegment(
            segment_id=0, is_start=0, is_end=100,
            oos_start=100, oos_end=130,
            is_sharpe=1.5, oos_sharpe=1.2, oos_ratio=0.30,
        )
        assert s.segment_id == 0
        assert s.is_start == 0
        assert s.is_end == 100
        assert s.oos_start == 100
        assert s.oos_end == 130
        assert s.is_sharpe == 1.5
        assert s.oos_sharpe == 1.2
        assert s.oos_ratio == 0.30

    def test_equality(self):
        s1 = WalkForwardSegment(0, 0, 100, 100, 130, 1.5, 1.2, 0.30)
        s2 = WalkForwardSegment(0, 0, 100, 100, 130, 1.5, 1.2, 0.30)
        assert s1 == s2


# =============================================================================
# SECTION 3 -- WALK FORWARD RESULT DATACLASS
# =============================================================================

class TestWalkForwardResult:
    def test_frozen(self):
        r = WalkForwardResult("S1", 3, (), 1.0, 0.1, 0.9, True, None)
        with pytest.raises(AttributeError):
            r.wfv_passed = False

    def test_fields(self):
        r = WalkForwardResult(
            strategy_id="S1", n_segments=3, segments=(),
            mean_oos_sharpe=1.0, std_oos_sharpe=0.1,
            stability_score=0.9, wfv_passed=True,
            failure_reason=None,
        )
        assert r.strategy_id == "S1"
        assert r.wfv_passed is True
        assert r.failure_reason is None


# =============================================================================
# SECTION 4 -- CROSS ASSET ROBUSTNESS DATACLASS
# =============================================================================

class TestCrossAssetRobustnessScore:
    def test_frozen(self):
        r = CrossAssetRobustnessScore("S1", (), (), 2, True, 1.0)
        with pytest.raises(AttributeError):
            r.robustness_passed = False

    def test_fields(self):
        r = CrossAssetRobustnessScore(
            strategy_id="S1",
            asset_classes_tested=("crypto", "equities"),
            oos_sharpe_by_class=(("crypto", 0.8), ("equities", 1.2)),
            classes_positive=2,
            robustness_passed=True,
            penalty_multiplier=1.0,
        )
        assert r.classes_positive == 2
        assert r.penalty_multiplier == 1.0


# =============================================================================
# SECTION 5 -- VALIDATE: BASIC
# =============================================================================

class TestValidateBasic:
    def _make_returns(self, n=1500):
        """Generate deterministic positive-drift returns."""
        np.random.seed(42)
        return np.random.normal(0.001, 0.02, n)

    def test_basic_validation(self):
        eng = WalkForwardValidationEngine()
        ret = self._make_returns(1500)
        result = eng.validate("S1", ret, n_segments=5)
        assert isinstance(result, WalkForwardResult)
        assert result.strategy_id == "S1"
        assert result.n_segments == 5
        assert len(result.segments) == 5

    def test_segments_cover_data(self):
        eng = WalkForwardValidationEngine()
        ret = self._make_returns(1500)
        result = eng.validate("S1", ret, n_segments=5)
        # First segment starts at 0
        assert result.segments[0].is_start == 0
        # Segments are sequential
        for i in range(len(result.segments) - 1):
            s1 = result.segments[i]
            s2 = result.segments[i + 1]
            assert s2.is_start > s1.is_start

    def test_oos_ratio_per_segment(self):
        eng = WalkForwardValidationEngine()
        ret = self._make_returns(1500)
        result = eng.validate("S1", ret, n_segments=5)
        for s in result.segments:
            assert s.oos_ratio >= WFV_MIN_OOS_RATIO - 0.01

    def test_sharpe_computed(self):
        eng = WalkForwardValidationEngine()
        ret = self._make_returns(1500)
        result = eng.validate("S1", ret, n_segments=3)
        for s in result.segments:
            assert isinstance(s.is_sharpe, float)
            assert isinstance(s.oos_sharpe, float)

    def test_mean_and_std(self):
        eng = WalkForwardValidationEngine()
        ret = self._make_returns(1500)
        result = eng.validate("S1", ret, n_segments=3)
        oos_sharpes = [s.oos_sharpe for s in result.segments]
        assert result.mean_oos_sharpe == pytest.approx(np.mean(oos_sharpes))
        assert result.std_oos_sharpe == pytest.approx(np.std(oos_sharpes))

    def test_stability_score_range(self):
        eng = WalkForwardValidationEngine()
        ret = self._make_returns(1500)
        result = eng.validate("S1", ret, n_segments=5)
        assert 0.0 <= result.stability_score <= 1.0

    def test_default_segments(self):
        eng = WalkForwardValidationEngine()
        ret = self._make_returns(2000)
        result = eng.validate("S1", ret)
        assert result.n_segments == 5


# =============================================================================
# SECTION 6 -- VALIDATE: WFV PASS/FAIL
# =============================================================================

class TestValidatePassFail:
    def test_passes_with_good_data(self):
        np.random.seed(42)
        ret = np.random.normal(0.001, 0.02, 1500)
        eng = WalkForwardValidationEngine()
        result = eng.validate("S1", ret, n_segments=3)
        assert result.wfv_passed is True
        assert result.failure_reason is None

    def test_constant_returns_zero_sharpe(self):
        """Constant returns → zero std → Sharpe = 0."""
        ret = np.full(1500, 0.001)
        eng = WalkForwardValidationEngine()
        result = eng.validate("S1", ret, n_segments=3)
        for s in result.segments:
            assert s.oos_sharpe == 0.0

    def test_zero_returns(self):
        ret = np.zeros(1500)
        eng = WalkForwardValidationEngine()
        result = eng.validate("S1", ret, n_segments=3)
        assert result.mean_oos_sharpe == 0.0

    def test_stability_perfect_if_uniform(self):
        """All segments identical → std=0 → stability=1."""
        ret = np.zeros(1500)
        eng = WalkForwardValidationEngine()
        result = eng.validate("S1", ret, n_segments=3)
        assert result.stability_score == pytest.approx(1.0)


# =============================================================================
# SECTION 7 -- VALIDATE: VALIDATION ERRORS
# =============================================================================

class TestValidateErrors:
    def test_too_few_segments(self):
        eng = WalkForwardValidationEngine()
        ret = np.random.normal(0.0, 0.01, 1500)
        with pytest.raises(ValueError, match="n_segments 2 < minimum"):
            eng.validate("S1", ret, n_segments=2)

    def test_insufficient_data(self):
        eng = WalkForwardValidationEngine()
        ret = np.random.normal(0.0, 0.01, 100)
        with pytest.raises(ValueError, match="Insufficient data"):
            eng.validate("S1", ret, n_segments=3)

    def test_strategy_id_type_error(self):
        eng = WalkForwardValidationEngine()
        with pytest.raises(TypeError, match="strategy_id must be a string"):
            eng.validate(123, np.zeros(1500), n_segments=3)

    def test_returns_type_error(self):
        eng = WalkForwardValidationEngine()
        with pytest.raises(TypeError, match="returns must be a numpy ndarray"):
            eng.validate("S1", [0.01] * 1500, n_segments=3)

    def test_n_segments_type_error(self):
        eng = WalkForwardValidationEngine()
        with pytest.raises(TypeError, match="n_segments must be int"):
            eng.validate("S1", np.zeros(1500), n_segments=3.0)


# =============================================================================
# SECTION 8 -- CROSS-ASSET ROBUSTNESS
# =============================================================================

class TestCrossAssetRobustness:
    def test_two_positive_passes(self):
        np.random.seed(42)
        eng = WalkForwardValidationEngine()
        result = eng.cross_asset_robustness("S1", {
            "crypto": np.random.normal(0.002, 0.02, 500),
            "equities": np.random.normal(0.001, 0.01, 500),
        })
        assert result.robustness_passed is True
        assert result.classes_positive == 2
        assert result.penalty_multiplier == 1.0

    def test_one_positive_fails(self):
        np.random.seed(42)
        eng = WalkForwardValidationEngine()
        result = eng.cross_asset_robustness("S1", {
            "crypto": np.random.normal(0.002, 0.02, 500),
            "forex": np.random.normal(-0.005, 0.02, 500),
        })
        # Only crypto positive
        assert result.classes_positive <= 1
        assert result.robustness_passed is False
        assert result.penalty_multiplier == ROBUSTNESS_PENALTY

    def test_three_classes(self):
        np.random.seed(42)
        eng = WalkForwardValidationEngine()
        result = eng.cross_asset_robustness("S1", {
            "crypto": np.random.normal(0.002, 0.02, 500),
            "equities": np.random.normal(0.001, 0.01, 500),
            "forex": np.random.normal(0.001, 0.01, 500),
        })
        assert result.classes_positive >= 2
        assert result.robustness_passed is True
        assert len(result.asset_classes_tested) == 3

    def test_all_negative(self):
        np.random.seed(42)
        eng = WalkForwardValidationEngine()
        result = eng.cross_asset_robustness("S1", {
            "crypto": np.random.normal(-0.005, 0.02, 500),
            "equities": np.random.normal(-0.005, 0.01, 500),
        })
        assert result.robustness_passed is False
        assert result.penalty_multiplier == ROBUSTNESS_PENALTY

    def test_zero_returns(self):
        eng = WalkForwardValidationEngine()
        result = eng.cross_asset_robustness("S1", {
            "crypto": np.zeros(500),
            "equities": np.zeros(500),
        })
        # Sharpe = 0.0, not > 0.0
        assert result.classes_positive == 0
        assert result.robustness_passed is False

    def test_asset_classes_sorted(self):
        eng = WalkForwardValidationEngine()
        result = eng.cross_asset_robustness("S1", {
            "forex": np.zeros(100),
            "crypto": np.zeros(100),
            "equities": np.zeros(100),
        })
        assert result.asset_classes_tested == ("crypto", "equities", "forex")

    def test_strategy_id_type_error(self):
        eng = WalkForwardValidationEngine()
        with pytest.raises(TypeError, match="strategy_id must be a string"):
            eng.cross_asset_robustness(123, {})

    def test_returns_dict_type_error(self):
        eng = WalkForwardValidationEngine()
        with pytest.raises(TypeError, match="returns_by_class must be a dict"):
            eng.cross_asset_robustness("S1", [])

    def test_returns_array_type_error(self):
        eng = WalkForwardValidationEngine()
        with pytest.raises(TypeError, match="must be numpy ndarray"):
            eng.cross_asset_robustness("S1", {"crypto": [0.01, 0.02]})


# =============================================================================
# SECTION 9 -- SHARPE HELPER EDGE CASES
# =============================================================================

class TestSharpeHelper:
    def test_single_return(self):
        eng = WalkForwardValidationEngine()
        assert eng._sharpe(np.array([0.01])) == 0.0

    def test_empty_returns(self):
        eng = WalkForwardValidationEngine()
        assert eng._sharpe(np.array([])) == 0.0

    def test_constant_returns(self):
        eng = WalkForwardValidationEngine()
        assert eng._sharpe(np.full(100, 0.01)) == 0.0

    def test_positive_drift(self):
        np.random.seed(42)
        eng = WalkForwardValidationEngine()
        ret = np.random.normal(0.001, 0.01, 252)
        sharpe = eng._sharpe(ret)
        assert sharpe > 0

    def test_negative_drift(self):
        np.random.seed(42)
        eng = WalkForwardValidationEngine()
        ret = np.random.normal(-0.005, 0.01, 252)
        sharpe = eng._sharpe(ret)
        assert sharpe < 0

    def test_annualized(self):
        """Sharpe should scale with sqrt(252)."""
        np.random.seed(42)
        eng = WalkForwardValidationEngine()
        ret = np.random.normal(0.001, 0.02, 252)
        sharpe = eng._sharpe(ret)
        # Manual calculation
        excess = ret - 0.0
        expected = float(np.mean(excess) / np.std(excess) * np.sqrt(252))
        assert sharpe == pytest.approx(expected)


# =============================================================================
# SECTION 10 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_validate_deterministic(self):
        np.random.seed(42)
        ret = np.random.normal(0.001, 0.02, 1500)
        eng = WalkForwardValidationEngine()
        r1 = eng.validate("S1", ret, n_segments=3)
        r2 = eng.validate("S1", ret, n_segments=3)
        assert r1 == r2

    def test_cross_asset_deterministic(self):
        np.random.seed(42)
        data = {"crypto": np.random.normal(0.002, 0.02, 500)}
        eng = WalkForwardValidationEngine()
        r1 = eng.cross_asset_robustness("S1", data)
        r2 = eng.cross_asset_robustness("S1", data)
        assert r1 == r2

    def test_independent_engines(self):
        np.random.seed(42)
        ret = np.random.normal(0.001, 0.02, 1500)
        r1 = WalkForwardValidationEngine().validate("S1", ret, 3)
        r2 = WalkForwardValidationEngine().validate("S1", ret, 3)
        assert r1 == r2
