# =============================================================================
# tests/unit/research/test_overfitting_detector.py
# Tests for jarvis/research/overfitting_detector.py
# =============================================================================

import numpy as np
import pytest

from jarvis.research.overfitting_detector import (
    PERFORMANCE_SPIKE_THRESHOLD,
    PARAM_SENSITIVITY_THRESHOLD,
    OverfittingReport,
    OverfittingDetector,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_performance_spike_threshold(self):
        assert PERFORMANCE_SPIKE_THRESHOLD == 3.0

    def test_param_sensitivity_threshold(self):
        assert PARAM_SENSITIVITY_THRESHOLD == 0.5


# =============================================================================
# SECTION 2 -- OVERFITTING REPORT DATACLASS
# =============================================================================

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

    def test_equality(self):
        r1 = OverfittingReport("S1", True, False, True, 4.0, 0.3)
        r2 = OverfittingReport("S1", True, False, True, 4.0, 0.3)
        assert r1 == r2


# =============================================================================
# SECTION 3 -- DETECT: NO OVERFITTING
# =============================================================================

class TestDetectNoOverfitting:
    def test_clean_strategy(self):
        det = OverfittingDetector()
        r = det.detect("S1", 1.5, 1.0, 0.3)
        assert r.overfitting_flag is False
        assert r.performance_spike is False
        assert r.param_sensitivity is False

    def test_equal_sharpes(self):
        det = OverfittingDetector()
        r = det.detect("S1", 1.0, 1.0, 0.2)
        assert r.is_to_oos_ratio == pytest.approx(1.0)
        assert r.overfitting_flag is False

    def test_oos_better_than_is(self):
        det = OverfittingDetector()
        r = det.detect("S1", 0.5, 1.5, 0.2)
        assert r.is_to_oos_ratio < 1.0
        assert r.overfitting_flag is False

    def test_sensitivity_below_threshold(self):
        det = OverfittingDetector()
        r = det.detect("S1", 2.0, 1.0, 0.49)
        assert r.param_sensitivity is False


# =============================================================================
# SECTION 4 -- DETECT: PERFORMANCE SPIKE
# =============================================================================

class TestDetectPerformanceSpike:
    def test_ratio_above_threshold(self):
        det = OverfittingDetector()
        r = det.detect("S1", 4.0, 1.0, 0.3)
        assert r.performance_spike is True
        assert r.overfitting_flag is True
        assert r.is_to_oos_ratio == pytest.approx(4.0)

    def test_ratio_at_threshold(self):
        """Exactly 3.0 is NOT > 3.0."""
        det = OverfittingDetector()
        r = det.detect("S1", 3.0, 1.0, 0.3)
        assert r.performance_spike is False

    def test_ratio_just_above(self):
        det = OverfittingDetector()
        r = det.detect("S1", 3.1, 1.0, 0.3)
        assert r.performance_spike is True

    def test_negative_sharpes(self):
        """Uses absolute values."""
        det = OverfittingDetector()
        r = det.detect("S1", -4.0, -1.0, 0.3)
        assert r.is_to_oos_ratio == pytest.approx(4.0)
        assert r.performance_spike is True

    def test_is_negative_oos_positive(self):
        det = OverfittingDetector()
        r = det.detect("S1", -4.0, 1.0, 0.3)
        assert r.is_to_oos_ratio == pytest.approx(4.0)
        assert r.performance_spike is True


# =============================================================================
# SECTION 5 -- DETECT: PARAM SENSITIVITY
# =============================================================================

class TestDetectParamSensitivity:
    def test_high_sensitivity(self):
        det = OverfittingDetector()
        r = det.detect("S1", 1.0, 1.0, 0.7)
        assert r.param_sensitivity is True
        assert r.overfitting_flag is True

    def test_at_threshold(self):
        """Exactly 0.5 is NOT > 0.5."""
        det = OverfittingDetector()
        r = det.detect("S1", 1.0, 1.0, 0.5)
        assert r.param_sensitivity is False

    def test_just_above_threshold(self):
        det = OverfittingDetector()
        r = det.detect("S1", 1.0, 1.0, 0.51)
        assert r.param_sensitivity is True

    def test_sensitivity_clipped_to_one(self):
        det = OverfittingDetector()
        r = det.detect("S1", 1.0, 1.0, 1.5)
        assert r.sensitivity_score == 1.0

    def test_sensitivity_clipped_to_zero(self):
        det = OverfittingDetector()
        r = det.detect("S1", 1.0, 1.0, -0.5)
        assert r.sensitivity_score == 0.0


# =============================================================================
# SECTION 6 -- DETECT: BOTH FLAGS
# =============================================================================

class TestDetectBothFlags:
    def test_both_trigger(self):
        det = OverfittingDetector()
        r = det.detect("S1", 5.0, 1.0, 0.8)
        assert r.performance_spike is True
        assert r.param_sensitivity is True
        assert r.overfitting_flag is True

    def test_only_spike(self):
        det = OverfittingDetector()
        r = det.detect("S1", 5.0, 1.0, 0.3)
        assert r.performance_spike is True
        assert r.param_sensitivity is False
        assert r.overfitting_flag is True

    def test_only_sensitivity(self):
        det = OverfittingDetector()
        r = det.detect("S1", 1.0, 1.0, 0.8)
        assert r.performance_spike is False
        assert r.param_sensitivity is True
        assert r.overfitting_flag is True


# =============================================================================
# SECTION 7 -- DETECT: EDGE CASES
# =============================================================================

class TestDetectEdgeCases:
    def test_zero_oos_sharpe_positive_is(self):
        """OOS ~0 with positive IS → spike."""
        det = OverfittingDetector()
        r = det.detect("S1", 2.0, 0.0, 0.3)
        assert r.performance_spike is True
        # ratio = 2.0 / 1e-6 = very large
        assert r.is_to_oos_ratio > PERFORMANCE_SPIKE_THRESHOLD

    def test_both_zero_sharpe(self):
        """Both ~0 → ratio near 0/1e-6 = 0."""
        det = OverfittingDetector()
        r = det.detect("S1", 0.0, 0.0, 0.3)
        assert r.is_to_oos_ratio == pytest.approx(0.0)
        assert r.performance_spike is False

    def test_very_small_oos(self):
        det = OverfittingDetector()
        r = det.detect("S1", 1.0, 1e-7, 0.3)
        # oos < 1e-6 → treated as 1e-6
        assert r.is_to_oos_ratio == pytest.approx(1.0 / 1e-6)
        assert r.performance_spike is True

    def test_strategy_id_stored(self):
        det = OverfittingDetector()
        r = det.detect("MY_STRAT", 1.0, 1.0, 0.3)
        assert r.strategy_id == "MY_STRAT"


# =============================================================================
# SECTION 8 -- DETECT FROM SEGMENTS
# =============================================================================

class TestDetectFromSegments:
    def test_basic(self):
        det = OverfittingDetector()
        is_s = np.array([1.5, 1.8, 1.6])
        oos_s = np.array([1.0, 0.9, 1.1])
        r = det.detect_from_segments("S1", is_s, oos_s, 0.3)
        assert isinstance(r, OverfittingReport)
        # Mean IS ≈ 1.633, Mean OOS = 1.0 → ratio ≈ 1.63
        assert r.is_to_oos_ratio < PERFORMANCE_SPIKE_THRESHOLD
        assert r.overfitting_flag is False

    def test_spike_from_segments(self):
        det = OverfittingDetector()
        is_s = np.array([5.0, 4.0, 6.0])
        oos_s = np.array([0.5, 0.3, 0.4])
        r = det.detect_from_segments("S1", is_s, oos_s, 0.3)
        assert r.performance_spike is True

    def test_empty_raises(self):
        det = OverfittingDetector()
        with pytest.raises(ValueError, match="must not be empty"):
            det.detect_from_segments("S1", np.array([]), np.array([1.0]), 0.3)

    def test_is_type_error(self):
        det = OverfittingDetector()
        with pytest.raises(TypeError, match="is_sharpes must be numpy ndarray"):
            det.detect_from_segments("S1", [1.0], np.array([1.0]), 0.3)

    def test_oos_type_error(self):
        det = OverfittingDetector()
        with pytest.raises(TypeError, match="oos_sharpes must be numpy ndarray"):
            det.detect_from_segments("S1", np.array([1.0]), [1.0], 0.3)


# =============================================================================
# SECTION 9 -- VALIDATION
# =============================================================================

class TestValidation:
    def test_strategy_id_type_error(self):
        det = OverfittingDetector()
        with pytest.raises(TypeError, match="strategy_id must be a string"):
            det.detect(123, 1.0, 1.0, 0.3)

    def test_is_sharpe_type_error(self):
        det = OverfittingDetector()
        with pytest.raises(TypeError, match="is_sharpe must be numeric"):
            det.detect("S1", "bad", 1.0, 0.3)

    def test_oos_sharpe_type_error(self):
        det = OverfittingDetector()
        with pytest.raises(TypeError, match="oos_sharpe must be numeric"):
            det.detect("S1", 1.0, "bad", 0.3)

    def test_sensitivity_type_error(self):
        det = OverfittingDetector()
        with pytest.raises(TypeError, match="param_sensitivity_score must be numeric"):
            det.detect("S1", 1.0, 1.0, "bad")

    def test_int_accepted(self):
        det = OverfittingDetector()
        r = det.detect("S1", 1, 1, 0)
        assert isinstance(r, OverfittingReport)


# =============================================================================
# SECTION 10 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_detect_deterministic(self):
        det = OverfittingDetector()
        results = [det.detect("S1", 4.0, 1.0, 0.6) for _ in range(10)]
        assert all(r == results[0] for r in results)

    def test_segments_deterministic(self):
        det = OverfittingDetector()
        is_s = np.array([2.0, 3.0])
        oos_s = np.array([1.0, 0.5])
        r1 = det.detect_from_segments("S1", is_s, oos_s, 0.4)
        r2 = det.detect_from_segments("S1", is_s, oos_s, 0.4)
        assert r1 == r2

    def test_independent_detectors(self):
        r1 = OverfittingDetector().detect("S1", 2.0, 1.0, 0.3)
        r2 = OverfittingDetector().detect("S1", 2.0, 1.0, 0.3)
        assert r1 == r2
