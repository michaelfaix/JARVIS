# =============================================================================
# tests/unit/risk/test_stress_detector.py
# Tests for jarvis/risk/stress_detector.py
# =============================================================================

import pytest

from jarvis.risk.stress_detector import (
    STRESS_THRESHOLD,
    VOL_SPIKE_FACTOR,
    VOLUME_SPIKE_FACTOR,
    CORRELATION_FLOOR,
    LIQUIDITY_FLOOR,
    StressIndicators,
    ExplicitStressDetector,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_stress_threshold(self):
        assert STRESS_THRESHOLD == 0.70

    def test_vol_spike_factor(self):
        assert VOL_SPIKE_FACTOR == 3.0

    def test_volume_spike_factor(self):
        assert VOLUME_SPIKE_FACTOR == 5.0

    def test_correlation_floor(self):
        assert CORRELATION_FLOOR == 0.20

    def test_liquidity_floor(self):
        assert LIQUIDITY_FLOOR == 0.20


# =============================================================================
# SECTION 2 -- STRESS INDICATORS DATACLASS
# =============================================================================

class TestStressIndicators:
    def test_frozen(self):
        s = StressIndicators(0.5, 0.3, 0.2, 0.1, 0.5, False)
        with pytest.raises(AttributeError):
            s.aggregate_stress = 0.9

    def test_fields(self):
        s = StressIndicators(
            volatility_stress=0.5,
            volume_stress=0.3,
            correlation_stress=0.2,
            liquidity_stress=0.1,
            aggregate_stress=0.5,
            is_stressed=False,
        )
        assert s.volatility_stress == 0.5
        assert s.volume_stress == 0.3
        assert s.correlation_stress == 0.2
        assert s.liquidity_stress == 0.1
        assert s.aggregate_stress == 0.5
        assert s.is_stressed is False

    def test_equality(self):
        s1 = StressIndicators(0.5, 0.3, 0.2, 0.1, 0.5, False)
        s2 = StressIndicators(0.5, 0.3, 0.2, 0.1, 0.5, False)
        assert s1 == s2


# =============================================================================
# SECTION 3 -- VOLATILITY STRESS DIMENSION
# =============================================================================

class TestVolatilityStress:
    def test_normal_vol_no_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.5, 0.5)
        assert result.volatility_stress == 0.0

    def test_below_normal_no_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(0.5, 1.0, 0.5, 0.5)
        assert result.volatility_stress == 0.0

    def test_double_vol_partial_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(2.0, 1.0, 0.5, 0.5)
        # (2.0 - 1.0) / (3.0 - 1.0) = 0.5
        assert result.volatility_stress == pytest.approx(0.5)

    def test_triple_vol_max_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(3.0, 1.0, 0.5, 0.5)
        assert result.volatility_stress == pytest.approx(1.0)

    def test_above_triple_clipped(self):
        det = ExplicitStressDetector()
        result = det.detect(5.0, 1.0, 0.5, 0.5)
        assert result.volatility_stress == pytest.approx(1.0)

    def test_just_above_normal(self):
        det = ExplicitStressDetector()
        result = det.detect(1.1, 1.0, 0.5, 0.5)
        expected = (1.1 - 1.0) / (3.0 - 1.0)
        assert result.volatility_stress == pytest.approx(expected)


# =============================================================================
# SECTION 4 -- VOLUME STRESS DIMENSION
# =============================================================================

class TestVolumeStress:
    def test_normal_volume_no_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.5, 0.5)
        assert result.volume_stress == 0.0

    def test_below_normal_no_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 0.5, 0.5, 0.5)
        assert result.volume_stress == 0.0

    def test_triple_volume_partial_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 3.0, 0.5, 0.5)
        # (3.0 - 1.0) / (5.0 - 1.0) = 0.5
        assert result.volume_stress == pytest.approx(0.5)

    def test_fivefold_volume_max_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 5.0, 0.5, 0.5)
        assert result.volume_stress == pytest.approx(1.0)

    def test_above_fivefold_clipped(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 10.0, 0.5, 0.5)
        assert result.volume_stress == pytest.approx(1.0)


# =============================================================================
# SECTION 5 -- CORRELATION STRESS DIMENSION
# =============================================================================

class TestCorrelationStress:
    def test_high_correlation_no_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.8, 0.5)
        assert result.correlation_stress == 0.0

    def test_at_floor_no_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.20, 0.5)
        assert result.correlation_stress == 0.0

    def test_half_floor_partial_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.10, 0.5)
        # 1.0 - (0.10 / 0.20) = 0.5
        assert result.correlation_stress == pytest.approx(0.5)

    def test_zero_correlation_max_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.0, 0.5)
        assert result.correlation_stress == pytest.approx(1.0)

    def test_just_below_floor(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.19, 0.5)
        expected = 1.0 - (0.19 / 0.20)
        assert result.correlation_stress == pytest.approx(expected)


# =============================================================================
# SECTION 6 -- LIQUIDITY STRESS DIMENSION
# =============================================================================

class TestLiquidityStress:
    def test_high_liquidity_no_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.5, 0.8)
        assert result.liquidity_stress == 0.0

    def test_at_floor_no_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.5, 0.20)
        assert result.liquidity_stress == 0.0

    def test_half_floor_partial_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.5, 0.10)
        # 1.0 - (0.10 / 0.20) = 0.5
        assert result.liquidity_stress == pytest.approx(0.5)

    def test_zero_liquidity_max_stress(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.5, 0.0)
        assert result.liquidity_stress == pytest.approx(1.0)


# =============================================================================
# SECTION 7 -- AGGREGATE AND IS_STRESSED
# =============================================================================

class TestAggregate:
    def test_aggregate_is_max(self):
        det = ExplicitStressDetector()
        # vol_stress=0.5, rest=0
        result = det.detect(2.0, 1.0, 0.5, 0.5)
        assert result.aggregate_stress == pytest.approx(0.5)

    def test_aggregate_max_of_all(self):
        det = ExplicitStressDetector()
        # vol_stress=1.0, volume_stress=0.5, corr=0, liq=0
        result = det.detect(3.0, 3.0, 0.5, 0.5)
        assert result.aggregate_stress == pytest.approx(1.0)

    def test_not_stressed_below_threshold(self):
        det = ExplicitStressDetector()
        result = det.detect(1.5, 1.0, 0.5, 0.5)
        # vol_stress = (1.5-1)/(3-1) = 0.25, below 0.7
        assert result.is_stressed is False

    def test_stressed_at_threshold(self):
        det = ExplicitStressDetector()
        # Need aggregate >= 0.7
        # vol_ratio = 1 + 0.7*2 = 2.4 → stress = 0.7
        result = det.detect(2.4, 1.0, 0.5, 0.5)
        assert result.volatility_stress == pytest.approx(0.7)
        assert result.is_stressed is True

    def test_stressed_above_threshold(self):
        det = ExplicitStressDetector()
        result = det.detect(3.0, 1.0, 0.5, 0.5)
        assert result.is_stressed is True

    def test_all_dimensions_calm(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.5, 0.5)
        assert result.aggregate_stress == 0.0
        assert result.is_stressed is False

    def test_worst_case_not_average(self):
        """Aggregate is max, not mean."""
        det = ExplicitStressDetector()
        # Only liquidity stressed at 1.0, rest calm
        result = det.detect(1.0, 1.0, 0.5, 0.0)
        assert result.aggregate_stress == pytest.approx(1.0)
        assert result.is_stressed is True


# =============================================================================
# SECTION 8 -- FAS CERTIFICATION SCENARIOS
# =============================================================================

class TestCertificationScenarios:
    def test_flash_crash_scenario(self):
        """Flash crash: extreme vol + liquidity crisis."""
        det = ExplicitStressDetector()
        result = det.detect(
            volatility_ratio=5.0,
            volume_ratio=8.0,
            correlation_score=0.05,
            liquidity_score=0.02,
        )
        assert result.is_stressed is True
        assert result.aggregate_stress == pytest.approx(1.0)

    def test_liquidity_crisis_scenario(self):
        """Liquidity dries up, other dimensions normal."""
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.5, 0.01)
        assert result.is_stressed is True
        assert result.liquidity_stress > 0.9

    def test_correlation_breakdown_scenario(self):
        """Correlation drops to zero, other dimensions normal."""
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.0, 0.5)
        assert result.is_stressed is True
        assert result.correlation_stress == pytest.approx(1.0)

    def test_volume_spike_scenario(self):
        """Extreme volume spike, other dimensions normal."""
        det = ExplicitStressDetector()
        result = det.detect(1.0, 6.0, 0.5, 0.5)
        assert result.is_stressed is True
        assert result.volume_stress == pytest.approx(1.0)

    def test_volatility_spike_scenario(self):
        """Extreme volatility spike, other dimensions normal."""
        det = ExplicitStressDetector()
        result = det.detect(4.0, 1.0, 0.5, 0.5)
        assert result.is_stressed is True
        assert result.volatility_stress == pytest.approx(1.0)

    def test_combined_stress_scenario(self):
        """All dimensions stressed simultaneously."""
        det = ExplicitStressDetector()
        result = det.detect(3.5, 6.0, 0.05, 0.05)
        assert result.is_stressed is True
        # All dimensions should be high
        assert result.volatility_stress > 0.8
        assert result.volume_stress > 0.8
        assert result.correlation_stress > 0.7
        assert result.liquidity_stress > 0.7

    def test_certification_detection_rate(self):
        """At least 5 of 6 scenarios detected (>= 95%)."""
        det = ExplicitStressDetector()
        scenarios = [
            det.detect(5.0, 8.0, 0.05, 0.02),  # flash crash
            det.detect(1.0, 1.0, 0.5, 0.01),    # liquidity crisis
            det.detect(1.0, 1.0, 0.0, 0.5),      # corr breakdown
            det.detect(1.0, 6.0, 0.5, 0.5),      # volume spike
            det.detect(4.0, 1.0, 0.5, 0.5),      # vol spike
            det.detect(3.5, 6.0, 0.05, 0.05),    # combined
        ]
        detected = sum(1 for s in scenarios if s.is_stressed)
        assert detected >= 5, f"Only {detected}/6 detected"


# =============================================================================
# SECTION 9 -- VALIDATION
# =============================================================================

class TestValidation:
    def test_volatility_ratio_type_error(self):
        det = ExplicitStressDetector()
        with pytest.raises(TypeError, match="volatility_ratio must be numeric"):
            det.detect("bad", 1.0, 0.5, 0.5)

    def test_volume_ratio_type_error(self):
        det = ExplicitStressDetector()
        with pytest.raises(TypeError, match="volume_ratio must be numeric"):
            det.detect(1.0, "bad", 0.5, 0.5)

    def test_correlation_score_type_error(self):
        det = ExplicitStressDetector()
        with pytest.raises(TypeError, match="correlation_score must be numeric"):
            det.detect(1.0, 1.0, "bad", 0.5)

    def test_liquidity_score_type_error(self):
        det = ExplicitStressDetector()
        with pytest.raises(TypeError, match="liquidity_score must be numeric"):
            det.detect(1.0, 1.0, 0.5, "bad")

    def test_volatility_ratio_negative(self):
        det = ExplicitStressDetector()
        with pytest.raises(ValueError, match="volatility_ratio must be >= 0"):
            det.detect(-1.0, 1.0, 0.5, 0.5)

    def test_volume_ratio_negative(self):
        det = ExplicitStressDetector()
        with pytest.raises(ValueError, match="volume_ratio must be >= 0"):
            det.detect(1.0, -1.0, 0.5, 0.5)

    def test_correlation_score_out_of_range(self):
        det = ExplicitStressDetector()
        with pytest.raises(ValueError, match="correlation_score must be in"):
            det.detect(1.0, 1.0, 1.5, 0.5)

    def test_liquidity_score_out_of_range(self):
        det = ExplicitStressDetector()
        with pytest.raises(ValueError, match="liquidity_score must be in"):
            det.detect(1.0, 1.0, 0.5, -0.1)

    def test_int_inputs_accepted(self):
        det = ExplicitStressDetector()
        result = det.detect(1, 1, 0, 0)
        assert isinstance(result, StressIndicators)

    def test_zero_vol_ratio(self):
        det = ExplicitStressDetector()
        result = det.detect(0.0, 1.0, 0.5, 0.5)
        assert result.volatility_stress == 0.0

    def test_zero_volume_ratio(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 0.0, 0.5, 0.5)
        assert result.volume_stress == 0.0


# =============================================================================
# SECTION 10 -- EDGE CASES
# =============================================================================

class TestEdgeCases:
    def test_all_zeros(self):
        det = ExplicitStressDetector()
        result = det.detect(0.0, 0.0, 0.0, 0.0)
        # corr=0 → stress=1.0, liq=0 → stress=1.0
        assert result.is_stressed is True
        assert result.aggregate_stress == pytest.approx(1.0)

    def test_all_normal(self):
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 1.0, 1.0)
        assert result.is_stressed is False
        assert result.aggregate_stress == 0.0

    def test_boundary_correlation_floor(self):
        det = ExplicitStressDetector()
        # Exactly at floor = no stress
        r1 = det.detect(1.0, 1.0, 0.20, 0.5)
        assert r1.correlation_stress == 0.0
        # Just below = stress
        r2 = det.detect(1.0, 1.0, 0.19, 0.5)
        assert r2.correlation_stress > 0.0

    def test_boundary_liquidity_floor(self):
        det = ExplicitStressDetector()
        r1 = det.detect(1.0, 1.0, 0.5, 0.20)
        assert r1.liquidity_stress == 0.0
        r2 = det.detect(1.0, 1.0, 0.5, 0.19)
        assert r2.liquidity_stress > 0.0

    def test_all_dimensions_at_zero_stress(self):
        """All dimensions exactly at no-stress boundary."""
        det = ExplicitStressDetector()
        result = det.detect(1.0, 1.0, 0.20, 0.20)
        assert result.volatility_stress == 0.0
        assert result.volume_stress == 0.0
        assert result.correlation_stress == 0.0
        assert result.liquidity_stress == 0.0
        assert result.aggregate_stress == 0.0


# =============================================================================
# SECTION 11 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_same_inputs_same_output(self):
        det = ExplicitStressDetector()
        results = [det.detect(2.5, 3.0, 0.1, 0.05) for _ in range(10)]
        for r in results[1:]:
            assert r == results[0]

    def test_independent_detectors(self):
        r1 = ExplicitStressDetector().detect(2.0, 1.0, 0.5, 0.5)
        r2 = ExplicitStressDetector().detect(2.0, 1.0, 0.5, 0.5)
        assert r1 == r2
