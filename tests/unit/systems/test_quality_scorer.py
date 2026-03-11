# =============================================================================
# tests/unit/systems/test_quality_scorer.py
# Tests for jarvis/systems/quality_scorer.py (S11 Quality Scorer)
# =============================================================================

import math

import pytest

from jarvis.systems.quality_scorer import (
    QUALITY_WEIGHTS,
    STABILITY_WINDOW,
    QUALITY_FLOOR,
    QUALITY_CEILING,
    QualityScore,
    QualityScorer,
    calibration_score,
    confidence_score,
    stability_score,
    data_quality_score,
    regime_score,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_quality_weights_sum_to_one(self):
        total = sum(QUALITY_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_quality_weights_has_five_keys(self):
        assert len(QUALITY_WEIGHTS) == 5

    def test_quality_weights_keys(self):
        expected = {"calibration", "confidence", "stability", "data_quality", "regime"}
        assert set(QUALITY_WEIGHTS.keys()) == expected

    def test_quality_weights_calibration(self):
        assert QUALITY_WEIGHTS["calibration"] == 0.35

    def test_quality_weights_confidence(self):
        assert QUALITY_WEIGHTS["confidence"] == 0.25

    def test_quality_weights_stability(self):
        assert QUALITY_WEIGHTS["stability"] == 0.20

    def test_quality_weights_data_quality(self):
        assert QUALITY_WEIGHTS["data_quality"] == 0.10

    def test_quality_weights_regime(self):
        assert QUALITY_WEIGHTS["regime"] == 0.10

    def test_stability_window(self):
        assert STABILITY_WINDOW == 20

    def test_quality_floor(self):
        assert QUALITY_FLOOR == 0.0

    def test_quality_ceiling(self):
        assert QUALITY_CEILING == 1.0


# =============================================================================
# SECTION 2 -- QUALITY SCORE DATACLASS
# =============================================================================

class TestQualityScore:
    def test_frozen(self):
        qs = QualityScore(
            total=0.5, calibration_component=0.5, confidence_component=0.5,
            stability_component=0.5, data_quality_component=0.5, regime_component=0.5,
        )
        with pytest.raises(AttributeError):
            qs.total = 0.9

    def test_all_fields_in_range(self):
        qs = QualityScore(
            total=0.0, calibration_component=0.0, confidence_component=0.0,
            stability_component=0.0, data_quality_component=0.0, regime_component=0.0,
        )
        assert qs.total == 0.0
        qs2 = QualityScore(
            total=1.0, calibration_component=1.0, confidence_component=1.0,
            stability_component=1.0, data_quality_component=1.0, regime_component=1.0,
        )
        assert qs2.total == 1.0

    def test_rejects_nan_total(self):
        with pytest.raises(ValueError, match="finite"):
            QualityScore(
                total=float("nan"), calibration_component=0.5,
                confidence_component=0.5, stability_component=0.5,
                data_quality_component=0.5, regime_component=0.5,
            )

    def test_rejects_inf_component(self):
        with pytest.raises(ValueError, match="finite"):
            QualityScore(
                total=0.5, calibration_component=float("inf"),
                confidence_component=0.5, stability_component=0.5,
                data_quality_component=0.5, regime_component=0.5,
            )

    def test_rejects_negative(self):
        with pytest.raises(ValueError, match="\\[0, 1\\]"):
            QualityScore(
                total=-0.1, calibration_component=0.5,
                confidence_component=0.5, stability_component=0.5,
                data_quality_component=0.5, regime_component=0.5,
            )

    def test_rejects_above_one(self):
        with pytest.raises(ValueError, match="\\[0, 1\\]"):
            QualityScore(
                total=1.1, calibration_component=0.5,
                confidence_component=0.5, stability_component=0.5,
                data_quality_component=0.5, regime_component=0.5,
            )

    def test_rejects_non_numeric(self):
        with pytest.raises(TypeError, match="numeric"):
            QualityScore(
                total="bad", calibration_component=0.5,
                confidence_component=0.5, stability_component=0.5,
                data_quality_component=0.5, regime_component=0.5,
            )

    def test_total_is_weighted_sum(self):
        """Verify total equals weighted sum of components."""
        cal, conf, stab, dq, reg = 0.9, 0.8, 0.7, 0.6, 0.5
        total = (
            QUALITY_WEIGHTS["calibration"] * cal
            + QUALITY_WEIGHTS["confidence"] * conf
            + QUALITY_WEIGHTS["stability"] * stab
            + QUALITY_WEIGHTS["data_quality"] * dq
            + QUALITY_WEIGHTS["regime"] * reg
        )
        qs = QualityScore(
            total=total, calibration_component=cal,
            confidence_component=conf, stability_component=stab,
            data_quality_component=dq, regime_component=reg,
        )
        assert abs(qs.total - total) < 1e-12


# =============================================================================
# SECTION 3 -- CALIBRATION SCORE
# =============================================================================

class TestCalibrationScore:
    def test_ece_zero_returns_one(self):
        assert calibration_score(0.0) == 1.0

    def test_ece_half_returns_half(self):
        assert calibration_score(0.5) == 0.5

    def test_ece_one_returns_zero(self):
        assert calibration_score(1.0) == 0.0

    def test_ece_greater_than_one_returns_zero(self):
        assert calibration_score(1.5) == 0.0

    def test_negative_ece_capped_at_one(self):
        assert calibration_score(-0.5) == 1.0

    def test_nan_returns_zero(self):
        assert calibration_score(float("nan")) == 0.0

    def test_inf_returns_zero(self):
        assert calibration_score(float("inf")) == 0.0

    def test_neg_inf_returns_zero(self):
        assert calibration_score(float("-inf")) == 0.0


# =============================================================================
# SECTION 4 -- CONFIDENCE SCORE
# =============================================================================

class TestConfidenceScore:
    def test_sigma_zero_returns_one(self):
        assert confidence_score(0.0) == 1.0

    def test_sigma_one_returns_half(self):
        assert confidence_score(1.0) == 0.5

    def test_large_sigma_near_zero(self):
        result = confidence_score(1000.0)
        assert result < 0.01
        assert result > 0.0

    def test_negative_sigma_treated_as_zero(self):
        # max(sigma, 0) ensures negative sigma -> 0 -> result=1.0
        assert confidence_score(-1.0) == 1.0

    def test_nan_returns_zero(self):
        assert confidence_score(float("nan")) == 0.0

    def test_inf_returns_zero(self):
        assert confidence_score(float("inf")) == 0.0

    def test_small_sigma(self):
        result = confidence_score(0.1)
        expected = 1.0 / 1.1
        assert abs(result - expected) < 1e-12


# =============================================================================
# SECTION 5 -- STABILITY SCORE
# =============================================================================

class TestStabilityScore:
    def test_empty_returns_one(self):
        assert stability_score(()) == 1.0

    def test_single_returns_one(self):
        assert stability_score((0.5,)) == 1.0

    def test_constant_returns_one(self):
        """Zero variance -> score of 1.0."""
        assert stability_score((0.3, 0.3, 0.3, 0.3)) == 1.0

    def test_varied_less_than_one(self):
        result = stability_score((0.0, 1.0, 0.0, 1.0))
        assert result < 1.0
        assert result > 0.0

    def test_high_variance_near_zero(self):
        # Large variance values
        mus = tuple(float(i * 100) for i in range(20))
        result = stability_score(mus)
        assert result < 0.1

    def test_uses_last_stability_window(self):
        """Only last STABILITY_WINDOW items used."""
        prefix = tuple(float(i * 100) for i in range(100))
        suffix = (0.5,) * STABILITY_WINDOW
        result = stability_score(prefix + suffix)
        # The last 20 are all 0.5 -> zero variance -> 1.0
        assert result == 1.0

    def test_nan_values_skipped(self):
        mus = (0.5, float("nan"), 0.5)
        result = stability_score(mus)
        # Only two finite values, both 0.5 -> zero variance -> 1.0
        assert result == 1.0

    def test_non_tuple_returns_one(self):
        assert stability_score([0.5, 0.6]) == 1.0


# =============================================================================
# SECTION 6 -- DATA QUALITY SCORE
# =============================================================================

class TestDataQualityScore:
    def test_all_ones_returns_one(self):
        assert data_quality_score(1.0, 1.0, 1.0) == 1.0

    def test_all_zeros_returns_zero(self):
        assert data_quality_score(0.0, 0.0, 0.0) == 0.0

    def test_mixed_values(self):
        result = data_quality_score(0.6, 0.9, 0.3)
        expected = (0.6 + 0.9 + 0.3) / 3.0
        assert abs(result - expected) < 1e-12

    def test_values_above_one_clipped(self):
        result = data_quality_score(2.0, 1.5, 3.0)
        assert result == 1.0

    def test_values_below_zero_clipped(self):
        result = data_quality_score(-1.0, -0.5, -2.0)
        assert result == 0.0

    def test_nan_treated_as_zero(self):
        result = data_quality_score(float("nan"), 1.0, 1.0)
        expected = (0.0 + 1.0 + 1.0) / 3.0
        assert abs(result - expected) < 1e-12

    def test_inf_treated_as_zero(self):
        result = data_quality_score(float("inf"), 0.5, 0.5)
        expected = (0.0 + 0.5 + 0.5) / 3.0
        assert abs(result - expected) < 1e-12


# =============================================================================
# SECTION 7 -- REGIME SCORE
# =============================================================================

class TestRegimeScore:
    def test_one_returns_one(self):
        assert regime_score(1.0) == 1.0

    def test_zero_returns_zero(self):
        assert regime_score(0.0) == 0.0

    def test_clipping_above_one(self):
        assert regime_score(1.5) == 1.0

    def test_clipping_below_zero(self):
        assert regime_score(-0.5) == 0.0

    def test_nan_returns_zero(self):
        assert regime_score(float("nan")) == 0.0

    def test_mid_value(self):
        assert regime_score(0.7) == 0.7


# =============================================================================
# SECTION 8 -- QUALITY SCORER CLASS
# =============================================================================

class TestQualityScorer:
    def test_perfect_inputs_high_score(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(
            ece=0.0, sigma=0.0, recent_mus=(0.5,) * 20,
            feature_completeness=1.0, data_freshness=1.0,
            source_reliability=1.0, regime_confidence=1.0,
        )
        assert result.total == 1.0

    def test_worst_inputs_low_score(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(
            ece=1.0, sigma=1000.0, recent_mus=tuple(float(i) for i in range(20)),
            feature_completeness=0.0, data_freshness=0.0,
            source_reliability=0.0, regime_confidence=0.0,
        )
        assert result.total < 0.1

    def test_default_params_reasonable(self):
        scorer = QualityScorer()
        result = scorer.compute_quality()
        # Defaults: ece=0 (cal=1), sigma=0 (conf=1), empty mus (stab=1),
        # completeness/freshness/reliability=1 (dq=1), regime=1 (reg=1)
        # total = 0.35*1 + 0.25*1 + 0.20*1 + 0.10*1 + 0.10*1 = 1.0
        assert result.total == 1.0

    def test_all_components_contribute(self):
        scorer = QualityScorer()
        # Set one component at a time to a bad value
        baseline = scorer.compute_quality()
        bad_cal = scorer.compute_quality(ece=0.5)
        bad_conf = scorer.compute_quality(sigma=5.0)
        bad_stab = scorer.compute_quality(recent_mus=(0.0, 1.0, 0.0, 1.0))
        bad_dq = scorer.compute_quality(feature_completeness=0.0, data_freshness=0.0, source_reliability=0.0)
        bad_reg = scorer.compute_quality(regime_confidence=0.0)

        assert bad_cal.total < baseline.total
        assert bad_conf.total < baseline.total
        assert bad_stab.total < baseline.total
        assert bad_dq.total < baseline.total
        assert bad_reg.total < baseline.total

    def test_get_weights_returns_copy(self):
        scorer = QualityScorer()
        w = scorer.get_weights()
        assert w == QUALITY_WEIGHTS
        # Modifying the copy should not affect the original
        w["calibration"] = 999.0
        assert QUALITY_WEIGHTS["calibration"] == 0.35

    def test_get_weights_is_dict(self):
        scorer = QualityScorer()
        w = scorer.get_weights()
        assert isinstance(w, dict)

    def test_total_clipped_to_floor(self):
        """Total should never be below QUALITY_FLOOR."""
        scorer = QualityScorer()
        result = scorer.compute_quality(
            ece=2.0, sigma=1e6, feature_completeness=0.0,
            data_freshness=0.0, source_reliability=0.0,
            regime_confidence=0.0,
        )
        assert result.total >= QUALITY_FLOOR

    def test_total_clipped_to_ceiling(self):
        """Total should never exceed QUALITY_CEILING."""
        scorer = QualityScorer()
        result = scorer.compute_quality()
        assert result.total <= QUALITY_CEILING


# =============================================================================
# SECTION 9 -- WEIGHTED SUM VERIFICATION
# =============================================================================

class TestWeightedSum:
    def test_total_equals_weighted_sum(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(
            ece=0.1, sigma=0.5,
            recent_mus=(0.3, 0.4, 0.5, 0.6),
            feature_completeness=0.8, data_freshness=0.9,
            source_reliability=0.7, regime_confidence=0.85,
        )
        expected_total = (
            QUALITY_WEIGHTS["calibration"] * result.calibration_component
            + QUALITY_WEIGHTS["confidence"] * result.confidence_component
            + QUALITY_WEIGHTS["stability"] * result.stability_component
            + QUALITY_WEIGHTS["data_quality"] * result.data_quality_component
            + QUALITY_WEIGHTS["regime"] * result.regime_component
        )
        assert abs(result.total - expected_total) < 1e-12

    def test_weighted_sum_with_extreme_values(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(
            ece=0.0, sigma=0.0,
            recent_mus=(), feature_completeness=0.0,
            data_freshness=0.0, source_reliability=0.0,
            regime_confidence=0.0,
        )
        expected_total = (
            QUALITY_WEIGHTS["calibration"] * 1.0   # ece=0 -> cal=1
            + QUALITY_WEIGHTS["confidence"] * 1.0   # sigma=0 -> conf=1
            + QUALITY_WEIGHTS["stability"] * 1.0    # empty -> stab=1
            + QUALITY_WEIGHTS["data_quality"] * 0.0 # all 0 -> dq=0
            + QUALITY_WEIGHTS["regime"] * 0.0       # 0 -> reg=0
        )
        assert abs(result.total - expected_total) < 1e-12


# =============================================================================
# SECTION 10 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_same_inputs_identical_output(self):
        scorer = QualityScorer()
        args = dict(
            ece=0.05, sigma=0.3, recent_mus=(0.1, 0.2, 0.3),
            feature_completeness=0.9, data_freshness=0.8,
            source_reliability=0.95, regime_confidence=0.7,
        )
        r1 = scorer.compute_quality(**args)
        r2 = scorer.compute_quality(**args)
        assert r1.total == r2.total
        assert r1.calibration_component == r2.calibration_component
        assert r1.confidence_component == r2.confidence_component
        assert r1.stability_component == r2.stability_component
        assert r1.data_quality_component == r2.data_quality_component
        assert r1.regime_component == r2.regime_component

    def test_fresh_instances_same_result(self):
        args = dict(
            ece=0.1, sigma=0.2, recent_mus=(0.5, 0.6),
            feature_completeness=0.7, data_freshness=0.8,
            source_reliability=0.9, regime_confidence=0.6,
        )
        r1 = QualityScorer().compute_quality(**args)
        r2 = QualityScorer().compute_quality(**args)
        assert r1.total == r2.total
        assert r1.calibration_component == r2.calibration_component


# =============================================================================
# SECTION 11 -- NUMERICAL SAFETY
# =============================================================================

class TestNumericalSafety:
    def test_nan_ece(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(ece=float("nan"))
        assert math.isfinite(result.total)
        assert result.calibration_component == 0.0

    def test_inf_sigma(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(sigma=float("inf"))
        assert math.isfinite(result.total)
        assert result.confidence_component == 0.0

    def test_neg_inf_regime(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(regime_confidence=float("-inf"))
        assert math.isfinite(result.total)
        assert result.regime_component == 0.0

    def test_nan_in_recent_mus(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(recent_mus=(float("nan"), float("nan")))
        assert math.isfinite(result.total)

    def test_all_nan_inputs(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(
            ece=float("nan"), sigma=float("nan"),
            recent_mus=(float("nan"),),
            feature_completeness=float("nan"),
            data_freshness=float("nan"),
            source_reliability=float("nan"),
            regime_confidence=float("nan"),
        )
        assert math.isfinite(result.total)
        assert result.total >= QUALITY_FLOOR
        assert result.total <= QUALITY_CEILING

    def test_negative_values_handled(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(
            ece=-1.0, sigma=-1.0,
            feature_completeness=-1.0, data_freshness=-1.0,
            source_reliability=-1.0, regime_confidence=-1.0,
        )
        assert math.isfinite(result.total)
        assert result.total >= QUALITY_FLOOR
        assert result.total <= QUALITY_CEILING


# =============================================================================
# SECTION 12 -- IMPORT CONTRACT
# =============================================================================

class TestImportContract:
    def test_all_symbols_importable(self):
        from jarvis.systems.quality_scorer import __all__
        import jarvis.systems.quality_scorer as mod
        for name in __all__:
            assert hasattr(mod, name), f"Missing __all__ symbol: {name}"

    def test_all_contains_expected_symbols(self):
        from jarvis.systems.quality_scorer import __all__
        expected = {
            "QUALITY_WEIGHTS", "STABILITY_WINDOW",
            "QUALITY_FLOOR", "QUALITY_CEILING",
            "QualityScore", "QualityScorer",
            "calibration_score", "confidence_score",
            "stability_score", "data_quality_score", "regime_score",
        }
        assert set(__all__) == expected


# =============================================================================
# SECTION 13 -- EDGE CASES
# =============================================================================

class TestEdgeCases:
    def test_all_defaults(self):
        scorer = QualityScorer()
        result = scorer.compute_quality()
        assert math.isfinite(result.total)
        assert 0.0 <= result.total <= 1.0

    def test_extreme_ece(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(ece=100.0)
        assert result.calibration_component == 0.0

    def test_extreme_sigma(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(sigma=1e12)
        assert result.confidence_component < 1e-6

    def test_large_recent_mus(self):
        scorer = QualityScorer()
        mus = tuple(float(i) / 1000 for i in range(1000))
        result = scorer.compute_quality(recent_mus=mus)
        assert math.isfinite(result.stability_component)

    def test_boundary_zero_values(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(
            ece=0.0, sigma=0.0,
            feature_completeness=0.0, data_freshness=0.0,
            source_reliability=0.0, regime_confidence=0.0,
        )
        assert 0.0 <= result.total <= 1.0

    def test_boundary_one_values(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(
            ece=1.0, sigma=1.0,
            feature_completeness=1.0, data_freshness=1.0,
            source_reliability=1.0, regime_confidence=1.0,
        )
        assert 0.0 <= result.total <= 1.0

    def test_integer_inputs(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(
            ece=0, sigma=1, feature_completeness=1,
            data_freshness=1, source_reliability=1,
            regime_confidence=1,
        )
        assert math.isfinite(result.total)

    def test_quality_score_all_components_in_range(self):
        scorer = QualityScorer()
        result = scorer.compute_quality(
            ece=0.2, sigma=0.5, recent_mus=(0.1, 0.3, 0.5),
            feature_completeness=0.8, data_freshness=0.7,
            source_reliability=0.9, regime_confidence=0.6,
        )
        for field in [
            result.total, result.calibration_component,
            result.confidence_component, result.stability_component,
            result.data_quality_component, result.regime_component,
        ]:
            assert 0.0 <= field <= 1.0
            assert math.isfinite(field)
