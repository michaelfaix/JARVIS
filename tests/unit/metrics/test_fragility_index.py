# =============================================================================
# tests/unit/metrics/test_fragility_index.py
# Tests for jarvis/metrics/fragility_index.py
# =============================================================================

import pytest

from jarvis.metrics.fragility_index import (
    FRAGILITY_LOW_THRESHOLD,
    FRAGILITY_MEDIUM_THRESHOLD,
    FRAGILITY_HIGH_THRESHOLD,
    FRAGILITY_WEIGHT_COUPLING,
    FRAGILITY_WEIGHT_PROPAGATION,
    FRAGILITY_WEIGHT_RECOVERY,
    FRAGILITY_WEIGHT_CASCADE,
    FragilityAssessment,
    StructuralFragilityIndex,
    _clip01,
    _classify,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_low_threshold(self):
        assert FRAGILITY_LOW_THRESHOLD == 0.3

    def test_medium_threshold(self):
        assert FRAGILITY_MEDIUM_THRESHOLD == 0.6

    def test_high_threshold(self):
        assert FRAGILITY_HIGH_THRESHOLD == 0.8

    def test_weight_coupling(self):
        assert FRAGILITY_WEIGHT_COUPLING == 0.3

    def test_weight_propagation(self):
        assert FRAGILITY_WEIGHT_PROPAGATION == 0.3

    def test_weight_recovery(self):
        assert FRAGILITY_WEIGHT_RECOVERY == 0.2

    def test_weight_cascade(self):
        assert FRAGILITY_WEIGHT_CASCADE == 0.2

    def test_weights_sum_to_one(self):
        total = (
            FRAGILITY_WEIGHT_COUPLING
            + FRAGILITY_WEIGHT_PROPAGATION
            + FRAGILITY_WEIGHT_RECOVERY
            + FRAGILITY_WEIGHT_CASCADE
        )
        assert total == pytest.approx(1.0)


# =============================================================================
# SECTION 2 -- HELPERS
# =============================================================================

class TestClip01:
    def test_within_range(self):
        assert _clip01(0.5) == 0.5

    def test_below_zero(self):
        assert _clip01(-0.5) == 0.0

    def test_above_one(self):
        assert _clip01(1.5) == 1.0

    def test_at_zero(self):
        assert _clip01(0.0) == 0.0

    def test_at_one(self):
        assert _clip01(1.0) == 1.0


class TestClassify:
    def test_low(self):
        assert _classify(0.1) == "LOW"

    def test_low_boundary(self):
        assert _classify(0.29) == "LOW"

    def test_medium(self):
        assert _classify(0.3) == "MEDIUM"

    def test_medium_upper(self):
        assert _classify(0.59) == "MEDIUM"

    def test_high(self):
        assert _classify(0.6) == "HIGH"

    def test_high_upper(self):
        assert _classify(0.79) == "HIGH"

    def test_critical(self):
        assert _classify(0.8) == "CRITICAL"

    def test_critical_max(self):
        assert _classify(1.0) == "CRITICAL"

    def test_zero(self):
        assert _classify(0.0) == "LOW"


# =============================================================================
# SECTION 3 -- FRAGILITY ASSESSMENT DATACLASS
# =============================================================================

class TestFragilityAssessment:
    def test_frozen(self):
        a = FragilityAssessment(0.1, 0.2, 0.3, 0.4, 0.25, "LOW")
        with pytest.raises(AttributeError):
            a.fragility_index = 0.9

    def test_fields(self):
        a = FragilityAssessment(
            coupling_score=0.1,
            propagation_score=0.2,
            recovery_score=0.3,
            cascade_score=0.4,
            fragility_index=0.22,
            classification="LOW",
        )
        assert a.coupling_score == 0.1
        assert a.propagation_score == 0.2
        assert a.recovery_score == 0.3
        assert a.cascade_score == 0.4
        assert a.fragility_index == 0.22
        assert a.classification == "LOW"

    def test_equality(self):
        a1 = FragilityAssessment(0.1, 0.2, 0.3, 0.4, 0.25, "LOW")
        a2 = FragilityAssessment(0.1, 0.2, 0.3, 0.4, 0.25, "LOW")
        assert a1 == a2


# =============================================================================
# SECTION 4 -- COMPUTE: BASIC
# =============================================================================

class TestComputeBasic:
    def test_all_zero(self):
        eng = StructuralFragilityIndex()
        r = eng.compute(0.0, 0.0, 0.0, 0.0)
        assert r.fragility_index == pytest.approx(0.0)
        assert r.classification == "LOW"

    def test_all_one(self):
        eng = StructuralFragilityIndex()
        r = eng.compute(1.0, 1.0, 1.0, 1.0)
        assert r.fragility_index == pytest.approx(1.0)
        assert r.classification == "CRITICAL"

    def test_weighted_sum(self):
        eng = StructuralFragilityIndex()
        r = eng.compute(0.5, 0.5, 0.5, 0.5)
        expected = 0.3 * 0.5 + 0.3 * 0.5 + 0.2 * 0.5 + 0.2 * 0.5
        assert r.fragility_index == pytest.approx(expected)

    def test_only_coupling(self):
        eng = StructuralFragilityIndex()
        r = eng.compute(1.0, 0.0, 0.0, 0.0)
        assert r.fragility_index == pytest.approx(0.3)
        assert r.classification == "MEDIUM"

    def test_only_propagation(self):
        eng = StructuralFragilityIndex()
        r = eng.compute(0.0, 1.0, 0.0, 0.0)
        assert r.fragility_index == pytest.approx(0.3)

    def test_only_recovery(self):
        eng = StructuralFragilityIndex()
        r = eng.compute(0.0, 0.0, 1.0, 0.0)
        assert r.fragility_index == pytest.approx(0.2)

    def test_only_cascade(self):
        eng = StructuralFragilityIndex()
        r = eng.compute(0.0, 0.0, 0.0, 1.0)
        assert r.fragility_index == pytest.approx(0.2)

    def test_scores_clipped(self):
        eng = StructuralFragilityIndex()
        r = eng.compute(1.5, -0.5, 2.0, -1.0)
        assert r.coupling_score == 1.0
        assert r.propagation_score == 0.0
        assert r.recovery_score == 1.0
        assert r.cascade_score == 0.0


# =============================================================================
# SECTION 5 -- COMPUTE: CLASSIFICATION
# =============================================================================

class TestComputeClassification:
    def test_low(self):
        eng = StructuralFragilityIndex()
        r = eng.compute(0.1, 0.1, 0.1, 0.1)
        assert r.classification == "LOW"

    def test_medium(self):
        eng = StructuralFragilityIndex()
        r = eng.compute(0.5, 0.5, 0.5, 0.5)
        assert r.classification == "MEDIUM"

    def test_high(self):
        eng = StructuralFragilityIndex()
        r = eng.compute(0.8, 0.8, 0.5, 0.5)
        assert r.classification == "HIGH"

    def test_critical(self):
        eng = StructuralFragilityIndex()
        r = eng.compute(1.0, 1.0, 1.0, 1.0)
        assert r.classification == "CRITICAL"


# =============================================================================
# SECTION 6 -- COMPUTE: VALIDATION
# =============================================================================

class TestComputeValidation:
    def test_coupling_type_error(self):
        eng = StructuralFragilityIndex()
        with pytest.raises(TypeError, match="coupling_score must be numeric"):
            eng.compute("bad", 0.0, 0.0, 0.0)

    def test_propagation_type_error(self):
        eng = StructuralFragilityIndex()
        with pytest.raises(TypeError, match="propagation_score must be numeric"):
            eng.compute(0.0, "bad", 0.0, 0.0)

    def test_recovery_type_error(self):
        eng = StructuralFragilityIndex()
        with pytest.raises(TypeError, match="recovery_score must be numeric"):
            eng.compute(0.0, 0.0, "bad", 0.0)

    def test_cascade_type_error(self):
        eng = StructuralFragilityIndex()
        with pytest.raises(TypeError, match="cascade_score must be numeric"):
            eng.compute(0.0, 0.0, 0.0, "bad")

    def test_int_accepted(self):
        eng = StructuralFragilityIndex()
        r = eng.compute(0, 0, 0, 0)
        assert isinstance(r, FragilityAssessment)


# =============================================================================
# SECTION 7 -- COMPUTE FROM CORRELATIONS
# =============================================================================

class TestComputeFromCorrelations:
    def test_basic(self):
        eng = StructuralFragilityIndex()
        r = eng.compute_from_correlations(
            pairwise_correlations=[0.8, 0.6, 0.7],
            failure_count=1,
            total_components=10,
            recovery_time_bars=5,
            max_recovery_bars=20,
        )
        assert isinstance(r, FragilityAssessment)
        assert 0.0 <= r.fragility_index <= 1.0

    def test_coupling_from_correlations(self):
        eng = StructuralFragilityIndex()
        r = eng.compute_from_correlations(
            pairwise_correlations=[1.0, 1.0, 1.0],
            failure_count=0,
            total_components=5,
            recovery_time_bars=0,
            max_recovery_bars=10,
        )
        assert r.coupling_score == pytest.approx(1.0)

    def test_negative_correlations_abs(self):
        eng = StructuralFragilityIndex()
        r = eng.compute_from_correlations(
            pairwise_correlations=[-0.8, -0.6],
            failure_count=0,
            total_components=5,
            recovery_time_bars=0,
            max_recovery_bars=10,
        )
        assert r.coupling_score == pytest.approx(0.7)

    def test_empty_correlations(self):
        eng = StructuralFragilityIndex()
        r = eng.compute_from_correlations(
            pairwise_correlations=[],
            failure_count=0,
            total_components=5,
            recovery_time_bars=0,
            max_recovery_bars=10,
        )
        assert r.coupling_score == 0.0

    def test_propagation_score(self):
        eng = StructuralFragilityIndex()
        r = eng.compute_from_correlations(
            pairwise_correlations=[0.5],
            failure_count=3,
            total_components=10,
            recovery_time_bars=0,
            max_recovery_bars=10,
        )
        assert r.propagation_score == pytest.approx(0.3)

    def test_recovery_score(self):
        eng = StructuralFragilityIndex()
        r = eng.compute_from_correlations(
            pairwise_correlations=[0.5],
            failure_count=0,
            total_components=5,
            recovery_time_bars=10,
            max_recovery_bars=20,
        )
        assert r.recovery_score == pytest.approx(0.5)

    def test_cascade_is_product(self):
        eng = StructuralFragilityIndex()
        r = eng.compute_from_correlations(
            pairwise_correlations=[0.8],
            failure_count=5,
            total_components=10,
            recovery_time_bars=0,
            max_recovery_bars=10,
        )
        # coupling=0.8, propagation=0.5, cascade=0.8*0.5=0.4
        assert r.cascade_score == pytest.approx(0.4)

    def test_all_failed(self):
        eng = StructuralFragilityIndex()
        r = eng.compute_from_correlations(
            pairwise_correlations=[1.0],
            failure_count=10,
            total_components=10,
            recovery_time_bars=20,
            max_recovery_bars=20,
        )
        assert r.propagation_score == pytest.approx(1.0)
        assert r.recovery_score == pytest.approx(1.0)


# =============================================================================
# SECTION 8 -- COMPUTE FROM CORRELATIONS: VALIDATION
# =============================================================================

class TestComputeFromCorrelationsValidation:
    def test_correlations_type_error(self):
        eng = StructuralFragilityIndex()
        with pytest.raises(TypeError, match="pairwise_correlations must be a list"):
            eng.compute_from_correlations((0.5,), 0, 5, 0, 10)

    def test_failure_count_type_error(self):
        eng = StructuralFragilityIndex()
        with pytest.raises(TypeError, match="failure_count must be int"):
            eng.compute_from_correlations([], 0.5, 5, 0, 10)

    def test_total_components_type_error(self):
        eng = StructuralFragilityIndex()
        with pytest.raises(TypeError, match="total_components must be int"):
            eng.compute_from_correlations([], 0, 5.0, 0, 10)

    def test_recovery_time_type_error(self):
        eng = StructuralFragilityIndex()
        with pytest.raises(TypeError, match="recovery_time_bars must be int"):
            eng.compute_from_correlations([], 0, 5, 0.0, 10)

    def test_max_recovery_type_error(self):
        eng = StructuralFragilityIndex()
        with pytest.raises(TypeError, match="max_recovery_bars must be int"):
            eng.compute_from_correlations([], 0, 5, 0, 10.0)

    def test_total_components_zero(self):
        eng = StructuralFragilityIndex()
        with pytest.raises(ValueError, match="total_components must be >= 1"):
            eng.compute_from_correlations([], 0, 0, 0, 10)

    def test_max_recovery_zero(self):
        eng = StructuralFragilityIndex()
        with pytest.raises(ValueError, match="max_recovery_bars must be >= 1"):
            eng.compute_from_correlations([], 0, 5, 0, 0)


# =============================================================================
# SECTION 9 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_compute_deterministic(self):
        eng = StructuralFragilityIndex()
        results = [eng.compute(0.5, 0.6, 0.3, 0.4) for _ in range(10)]
        assert all(r == results[0] for r in results)

    def test_from_correlations_deterministic(self):
        eng = StructuralFragilityIndex()
        results = [
            eng.compute_from_correlations([0.8, 0.6], 2, 10, 5, 20)
            for _ in range(10)
        ]
        assert all(r == results[0] for r in results)

    def test_independent_engines(self):
        r1 = StructuralFragilityIndex().compute(0.5, 0.5, 0.5, 0.5)
        r2 = StructuralFragilityIndex().compute(0.5, 0.5, 0.5, 0.5)
        assert r1 == r2
