# =============================================================================
# Unit Tests for jarvis/confidence/adaptive_selectivity_model.py
# =============================================================================

import pytest

from jarvis.core.regime import CorrelationRegimeState
from jarvis.confidence.adaptive_selectivity_model import (
    BASE_SELECTIVITY_THRESHOLD,
    THRESHOLD_CEILING,
    AdaptiveSelectivityResult,
    AdaptiveSelectivityModel,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _model() -> AdaptiveSelectivityModel:
    return AdaptiveSelectivityModel()


def _compute(**overrides) -> AdaptiveSelectivityResult:
    """Convenience: compute_threshold with calm/no-stress defaults."""
    defaults = dict(
        regime_stability_score=0.8,
        total_uncertainty=0.2,
        correlation_regime=CorrelationRegimeState.NORMAL,
        active_failure_modes=frozenset(),
        transition_acceleration_flag=False,
    )
    defaults.update(overrides)
    return _model().compute_threshold(**defaults)


def _stressed(**overrides) -> AdaptiveSelectivityResult:
    """Convenience: compute_threshold with all stress indicators active."""
    defaults = dict(
        regime_stability_score=0.1,
        total_uncertainty=0.9,
        correlation_regime=CorrelationRegimeState.BREAKDOWN,
        active_failure_modes=frozenset({"FM-01", "FM-02", "FM-03"}),
        transition_acceleration_flag=True,
    )
    defaults.update(overrides)
    return _model().compute_threshold(**defaults)


# ===================================================================
# TestConstants
# ===================================================================

class TestConstants:
    def test_base_selectivity_threshold(self):
        assert BASE_SELECTIVITY_THRESHOLD == 0.55

    def test_threshold_ceiling(self):
        assert THRESHOLD_CEILING == 0.92

    def test_base_less_than_ceiling(self):
        assert BASE_SELECTIVITY_THRESHOLD < THRESHOLD_CEILING

    def test_class_constants_match_module(self):
        m = _model()
        assert m.BASE == BASE_SELECTIVITY_THRESHOLD
        assert m.THRESHOLD_CEILING == THRESHOLD_CEILING


# ===================================================================
# TestPenaltyConstants
# ===================================================================

class TestPenaltyConstants:
    def test_penalty_low_regime_stability(self):
        assert _model().PENALTY_LOW_REGIME_STABILITY == 0.10

    def test_penalty_high_uncertainty(self):
        assert _model().PENALTY_HIGH_UNCERTAINTY == 0.08

    def test_penalty_correlation_stress(self):
        assert _model().PENALTY_CORRELATION_STRESS == 0.07

    def test_penalty_per_active_fm(self):
        assert _model().PENALTY_PER_ACTIVE_FM == 0.05

    def test_penalty_duration_stress(self):
        assert _model().PENALTY_DURATION_STRESS == 0.05

    def test_regime_stability_threshold(self):
        assert _model().REGIME_STABILITY_THRESHOLD == 0.40

    def test_uncertainty_threshold(self):
        assert _model().UNCERTAINTY_THRESHOLD == 0.50

    def test_max_fm_count(self):
        assert _model().MAX_FM_COUNT == 3


# ===================================================================
# TestAdaptiveSelectivityResult
# ===================================================================

class TestAdaptiveSelectivityResult:
    def test_creation(self):
        r = AdaptiveSelectivityResult(
            resolved_threshold=0.60,
            adjustment_reason="TEST",
            base_used=0.55,
        )
        assert r.resolved_threshold == 0.60
        assert r.adjustment_reason == "TEST"
        assert r.base_used == 0.55

    def test_frozen(self):
        r = AdaptiveSelectivityResult(0.60, "TEST", 0.55)
        with pytest.raises(AttributeError):
            r.resolved_threshold = 0.99

    def test_equality(self):
        a = AdaptiveSelectivityResult(0.60, "A", 0.55)
        b = AdaptiveSelectivityResult(0.60, "A", 0.55)
        assert a == b

    def test_inequality(self):
        a = AdaptiveSelectivityResult(0.60, "A", 0.55)
        b = AdaptiveSelectivityResult(0.70, "A", 0.55)
        assert a != b

    def test_frozen_dataclass_params(self):
        assert AdaptiveSelectivityResult.__dataclass_params__.frozen is True

    def test_fields(self):
        names = {f.name for f in AdaptiveSelectivityResult.__dataclass_fields__.values()}
        assert names == {"resolved_threshold", "adjustment_reason", "base_used"}


# ===================================================================
# TestComputeValidation
# ===================================================================

class TestComputeValidation:
    def test_string_correlation_regime_raises(self):
        with pytest.raises(TypeError, match="correlation_regime must be a CorrelationRegimeState"):
            _compute(correlation_regime="HIGH")

    def test_int_correlation_regime_raises(self):
        with pytest.raises(TypeError):
            _compute(correlation_regime=1)

    def test_none_correlation_regime_raises(self):
        with pytest.raises(TypeError):
            _compute(correlation_regime=None)


# ===================================================================
# TestNoAdjustment
# ===================================================================

class TestNoAdjustment:
    """All indicators calm => threshold stays at BASE."""

    def test_threshold_equals_base(self):
        r = _compute()
        assert r.resolved_threshold == pytest.approx(BASE_SELECTIVITY_THRESHOLD)

    def test_reason_is_no_adjustment(self):
        r = _compute()
        assert r.adjustment_reason == "NO_ADJUSTMENT"

    def test_base_used_equals_constant(self):
        r = _compute()
        assert r.base_used == BASE_SELECTIVITY_THRESHOLD


# ===================================================================
# TestIndividualPenalties
# ===================================================================

class TestIndividualPenalties:
    def test_low_regime_stability_penalty(self):
        """stability=0.3 < 0.40 => +0.10"""
        r = _compute(regime_stability_score=0.3)
        expected = BASE_SELECTIVITY_THRESHOLD + 0.10
        assert r.resolved_threshold == pytest.approx(expected)

    def test_regime_stability_at_threshold_no_penalty(self):
        """stability=0.40 (not < 0.40) => no penalty"""
        r = _compute(regime_stability_score=0.40)
        assert r.resolved_threshold == pytest.approx(BASE_SELECTIVITY_THRESHOLD)

    def test_regime_stability_just_below_threshold(self):
        """stability=0.399 => penalty"""
        r = _compute(regime_stability_score=0.399)
        assert r.resolved_threshold > BASE_SELECTIVITY_THRESHOLD

    def test_high_uncertainty_penalty(self):
        """uncertainty=0.6 > 0.50 => +0.08"""
        r = _compute(total_uncertainty=0.6)
        expected = BASE_SELECTIVITY_THRESHOLD + 0.08
        assert r.resolved_threshold == pytest.approx(expected)

    def test_uncertainty_at_threshold_no_penalty(self):
        """uncertainty=0.50 (not > 0.50) => no penalty"""
        r = _compute(total_uncertainty=0.50)
        assert r.resolved_threshold == pytest.approx(BASE_SELECTIVITY_THRESHOLD)

    def test_uncertainty_just_above_threshold(self):
        """uncertainty=0.501 => penalty"""
        r = _compute(total_uncertainty=0.501)
        assert r.resolved_threshold > BASE_SELECTIVITY_THRESHOLD

    def test_correlation_stress_breakdown_penalty(self):
        """BREAKDOWN => +0.07"""
        r = _compute(correlation_regime=CorrelationRegimeState.BREAKDOWN)
        expected = BASE_SELECTIVITY_THRESHOLD + 0.07
        assert r.resolved_threshold == pytest.approx(expected)

    def test_correlation_coupled_no_penalty(self):
        """COUPLED => no penalty"""
        r = _compute(correlation_regime=CorrelationRegimeState.COUPLED)
        assert r.resolved_threshold == pytest.approx(BASE_SELECTIVITY_THRESHOLD)

    def test_correlation_normal_no_penalty(self):
        r = _compute(correlation_regime=CorrelationRegimeState.NORMAL)
        assert r.resolved_threshold == pytest.approx(BASE_SELECTIVITY_THRESHOLD)

    def test_correlation_divergence_no_penalty(self):
        r = _compute(correlation_regime=CorrelationRegimeState.DIVERGENCE)
        assert r.resolved_threshold == pytest.approx(BASE_SELECTIVITY_THRESHOLD)

    def test_one_failure_mode_penalty(self):
        """1 FM => +0.05"""
        r = _compute(active_failure_modes=frozenset({"FM-01"}))
        expected = BASE_SELECTIVITY_THRESHOLD + 0.05
        assert r.resolved_threshold == pytest.approx(expected)

    def test_two_failure_modes_penalty(self):
        """2 FMs => +0.10"""
        r = _compute(active_failure_modes=frozenset({"FM-01", "FM-02"}))
        expected = BASE_SELECTIVITY_THRESHOLD + 0.10
        assert r.resolved_threshold == pytest.approx(expected)

    def test_three_failure_modes_penalty(self):
        """3 FMs => +0.15"""
        r = _compute(active_failure_modes=frozenset({"FM-01", "FM-02", "FM-03"}))
        expected = BASE_SELECTIVITY_THRESHOLD + 0.15
        assert r.resolved_threshold == pytest.approx(expected)

    def test_four_failure_modes_capped_at_three(self):
        """4 FMs => capped at 3 => +0.15"""
        r = _compute(active_failure_modes=frozenset({"FM-01", "FM-02", "FM-03", "FM-04"}))
        expected = BASE_SELECTIVITY_THRESHOLD + 0.15
        assert r.resolved_threshold == pytest.approx(expected)

    def test_six_failure_modes_capped_at_three(self):
        fms = frozenset({f"FM-0{i}" for i in range(1, 7)})
        r = _compute(active_failure_modes=fms)
        expected = BASE_SELECTIVITY_THRESHOLD + 0.15
        assert r.resolved_threshold == pytest.approx(expected)

    def test_duration_stress_penalty(self):
        """transition_acceleration_flag=True => +0.05"""
        r = _compute(transition_acceleration_flag=True)
        expected = BASE_SELECTIVITY_THRESHOLD + 0.05
        assert r.resolved_threshold == pytest.approx(expected)

    def test_no_duration_stress_no_penalty(self):
        r = _compute(transition_acceleration_flag=False)
        assert r.resolved_threshold == pytest.approx(BASE_SELECTIVITY_THRESHOLD)


# ===================================================================
# TestCombinedPenalties
# ===================================================================

class TestCombinedPenalties:
    def test_two_penalties_additive(self):
        """Low stability + high uncertainty => +0.10 + 0.08 = +0.18"""
        r = _compute(
            regime_stability_score=0.2,
            total_uncertainty=0.7,
        )
        expected = BASE_SELECTIVITY_THRESHOLD + 0.10 + 0.08
        assert r.resolved_threshold == pytest.approx(expected)

    def test_all_penalties_max(self):
        """All stress active => BASE + 0.10 + 0.08 + 0.07 + 0.15 + 0.05 = 1.00 => clipped to 0.92"""
        r = _stressed()
        assert r.resolved_threshold == pytest.approx(THRESHOLD_CEILING)

    def test_hand_computed_partial(self):
        """stability=0.3, uncertainty=0.2, BREAKDOWN, 1 FM, no duration
        => 0.55 + 0.10 + 0.07 + 0.05 = 0.77"""
        r = _compute(
            regime_stability_score=0.3,
            total_uncertainty=0.2,
            correlation_regime=CorrelationRegimeState.BREAKDOWN,
            active_failure_modes=frozenset({"FM-01"}),
            transition_acceleration_flag=False,
        )
        assert r.resolved_threshold == pytest.approx(0.77)

    def test_cumulative_reasons(self):
        """Multiple penalties => multiple reasons separated by ';'"""
        r = _compute(
            regime_stability_score=0.2,
            transition_acceleration_flag=True,
        )
        assert "LOW_REGIME_STABILITY" in r.adjustment_reason
        assert "DURATION_STRESS_FLAG" in r.adjustment_reason
        assert ";" in r.adjustment_reason


# ===================================================================
# TestThresholdCeiling
# ===================================================================

class TestThresholdCeiling:
    def test_never_exceeds_ceiling(self):
        r = _stressed()
        assert r.resolved_threshold <= THRESHOLD_CEILING

    def test_ceiling_applied(self):
        """Total penalty = 0.45 => raw = 1.00 => clipped to 0.92"""
        r = _stressed()
        assert r.resolved_threshold == pytest.approx(THRESHOLD_CEILING)

    def test_below_ceiling_not_clipped(self):
        """Single penalty => 0.55 + 0.10 = 0.65 < 0.92"""
        r = _compute(regime_stability_score=0.1)
        assert r.resolved_threshold == pytest.approx(0.65)
        assert r.resolved_threshold < THRESHOLD_CEILING


# ===================================================================
# TestThresholdMonotonicity
# ===================================================================

class TestThresholdMonotonicity:
    """resolved_threshold >= BASE always."""

    def test_calm_market(self):
        r = _compute()
        assert r.resolved_threshold >= BASE_SELECTIVITY_THRESHOLD

    def test_stressed_market(self):
        r = _stressed()
        assert r.resolved_threshold >= BASE_SELECTIVITY_THRESHOLD

    def test_zero_stability(self):
        r = _compute(regime_stability_score=0.0)
        assert r.resolved_threshold >= BASE_SELECTIVITY_THRESHOLD

    def test_max_uncertainty(self):
        r = _compute(total_uncertainty=1.0)
        assert r.resolved_threshold >= BASE_SELECTIVITY_THRESHOLD


# ===================================================================
# TestAdjustmentReason
# ===================================================================

class TestAdjustmentReason:
    def test_no_adjustment_reason(self):
        r = _compute()
        assert r.adjustment_reason == "NO_ADJUSTMENT"

    def test_low_stability_reason(self):
        r = _compute(regime_stability_score=0.2)
        assert "LOW_REGIME_STABILITY(0.200)" in r.adjustment_reason

    def test_high_uncertainty_reason(self):
        r = _compute(total_uncertainty=0.7)
        assert "HIGH_UNCERTAINTY(0.700)" in r.adjustment_reason

    def test_correlation_stress_reason(self):
        r = _compute(correlation_regime=CorrelationRegimeState.BREAKDOWN)
        assert "CORRELATION_STRESS(BREAKDOWN)" in r.adjustment_reason

    def test_fm_count_reason(self):
        r = _compute(active_failure_modes=frozenset({"FM-01", "FM-02"}))
        assert "ACTIVE_FM_COUNT(2" in r.adjustment_reason

    def test_duration_stress_reason(self):
        r = _compute(transition_acceleration_flag=True)
        assert "DURATION_STRESS_FLAG(True)" in r.adjustment_reason


# ===================================================================
# TestBaseUsed
# ===================================================================

class TestBaseUsed:
    def test_always_equals_constant(self):
        r = _compute()
        assert r.base_used == BASE_SELECTIVITY_THRESHOLD

    def test_stressed_base_unchanged(self):
        r = _stressed()
        assert r.base_used == BASE_SELECTIVITY_THRESHOLD


# ===================================================================
# TestDeterminism
# ===================================================================

class TestDeterminism:
    def test_identical_inputs_identical_outputs(self):
        r1 = _compute(regime_stability_score=0.3, total_uncertainty=0.6)
        r2 = _compute(regime_stability_score=0.3, total_uncertainty=0.6)
        assert r1 == r2

    def test_different_instances_same_result(self):
        kwargs = dict(
            regime_stability_score=0.3,
            total_uncertainty=0.6,
            correlation_regime=CorrelationRegimeState.BREAKDOWN,
            active_failure_modes=frozenset({"FM-01"}),
            transition_acceleration_flag=True,
        )
        r1 = AdaptiveSelectivityModel().compute_threshold(**kwargs)
        r2 = AdaptiveSelectivityModel().compute_threshold(**kwargs)
        assert r1 == r2

    def test_bitwise_identical_fields(self):
        r1 = _stressed()
        r2 = _stressed()
        assert r1.resolved_threshold == r2.resolved_threshold
        assert r1.adjustment_reason == r2.adjustment_reason
        assert r1.base_used == r2.base_used


# ===================================================================
# TestEdgeCases
# ===================================================================

class TestEdgeCases:
    def test_empty_frozenset(self):
        r = _compute(active_failure_modes=frozenset())
        assert r.resolved_threshold == pytest.approx(BASE_SELECTIVITY_THRESHOLD)

    def test_stability_zero(self):
        r = _compute(regime_stability_score=0.0)
        assert r.resolved_threshold > BASE_SELECTIVITY_THRESHOLD

    def test_stability_one(self):
        r = _compute(regime_stability_score=1.0)
        assert r.resolved_threshold == pytest.approx(BASE_SELECTIVITY_THRESHOLD)

    def test_uncertainty_zero(self):
        r = _compute(total_uncertainty=0.0)
        assert r.resolved_threshold == pytest.approx(BASE_SELECTIVITY_THRESHOLD)

    def test_uncertainty_one(self):
        r = _compute(total_uncertainty=1.0)
        assert r.resolved_threshold > BASE_SELECTIVITY_THRESHOLD

    def test_negative_stability_penalty_still_applies(self):
        """Stability < 0 (edge) still triggers penalty (< 0.40)."""
        r = _compute(regime_stability_score=-0.1)
        assert r.resolved_threshold > BASE_SELECTIVITY_THRESHOLD


# ===================================================================
# TestHandComputations
# ===================================================================

class TestHandComputations:
    def test_all_calm(self):
        """No penalties => 0.55"""
        r = _compute()
        assert r.resolved_threshold == pytest.approx(0.55)

    def test_only_stability_stress(self):
        """0.55 + 0.10 = 0.65"""
        r = _compute(regime_stability_score=0.2)
        assert r.resolved_threshold == pytest.approx(0.65)

    def test_stability_plus_uncertainty(self):
        """0.55 + 0.10 + 0.08 = 0.73"""
        r = _compute(regime_stability_score=0.2, total_uncertainty=0.7)
        assert r.resolved_threshold == pytest.approx(0.73)

    def test_all_max_penalty(self):
        """0.55 + 0.10 + 0.08 + 0.07 + 0.15 + 0.05 = 1.00 => clipped 0.92"""
        r = _stressed()
        assert r.resolved_threshold == pytest.approx(0.92)

    def test_two_fms_plus_correlation(self):
        """0.55 + 0.10 + 0.07 = 0.72"""
        r = _compute(
            correlation_regime=CorrelationRegimeState.BREAKDOWN,
            active_failure_modes=frozenset({"FM-01", "FM-02"}),
        )
        # 0.55 + 0.07 + 0.10 = 0.72
        assert r.resolved_threshold == pytest.approx(0.72)


# ===================================================================
# TestModelStateless
# ===================================================================

class TestModelStateless:
    def test_no_instance_state(self):
        m = _model()
        m.compute_threshold(
            regime_stability_score=0.5,
            total_uncertainty=0.3,
            correlation_regime=CorrelationRegimeState.NORMAL,
            active_failure_modes=frozenset(),
            transition_acceleration_flag=False,
        )
        instance_attrs = {k for k in m.__dict__ if not k.startswith('__')}
        assert len(instance_attrs) == 0

    def test_multiple_calls_independent(self):
        m = _model()
        r1 = m.compute_threshold(
            regime_stability_score=0.2,
            total_uncertainty=0.3,
            correlation_regime=CorrelationRegimeState.NORMAL,
            active_failure_modes=frozenset(),
            transition_acceleration_flag=False,
        )
        r2 = m.compute_threshold(
            regime_stability_score=0.8,
            total_uncertainty=0.3,
            correlation_regime=CorrelationRegimeState.NORMAL,
            active_failure_modes=frozenset(),
            transition_acceleration_flag=False,
        )
        assert r1.resolved_threshold != r2.resolved_threshold


# ===================================================================
# TestGovernanceConstraints
# ===================================================================

class TestGovernanceConstraints:
    def test_result_is_frozen(self):
        assert AdaptiveSelectivityResult.__dataclass_params__.frozen is True

    def test_no_capital_fields(self):
        field_names = {f.name for f in AdaptiveSelectivityResult.__dataclass_fields__.values()}
        forbidden = {"capital", "pnl", "balance", "broker_id", "order_id", "account_id"}
        assert field_names.isdisjoint(forbidden)

    def test_threshold_never_below_base(self):
        """Invariant: resolved >= BASE in all tested scenarios."""
        scenarios = [
            dict(),
            dict(regime_stability_score=0.0),
            dict(total_uncertainty=1.0),
            dict(correlation_regime=CorrelationRegimeState.BREAKDOWN),
            dict(active_failure_modes=frozenset({f"FM-0{i}" for i in range(1, 7)})),
            dict(transition_acceleration_flag=True),
        ]
        for s in scenarios:
            r = _compute(**s)
            assert r.resolved_threshold >= BASE_SELECTIVITY_THRESHOLD, f"Failed for {s}"

    def test_threshold_never_above_ceiling(self):
        r = _stressed()
        assert r.resolved_threshold <= THRESHOLD_CEILING

    def test_uses_correlation_regime_enum(self):
        """Must use CorrelationRegimeState enum, not strings."""
        with pytest.raises(TypeError):
            _compute(correlation_regime="BREAKDOWN")


# ===================================================================
# TestModuleAll
# ===================================================================

class TestModuleAll:
    def test_contains_base_threshold(self):
        from jarvis.confidence.adaptive_selectivity_model import __all__
        assert "BASE_SELECTIVITY_THRESHOLD" in __all__

    def test_contains_ceiling(self):
        from jarvis.confidence.adaptive_selectivity_model import __all__
        assert "THRESHOLD_CEILING" in __all__

    def test_contains_result(self):
        from jarvis.confidence.adaptive_selectivity_model import __all__
        assert "AdaptiveSelectivityResult" in __all__

    def test_contains_model(self):
        from jarvis.confidence.adaptive_selectivity_model import __all__
        assert "AdaptiveSelectivityModel" in __all__

    def test_all_length(self):
        from jarvis.confidence.adaptive_selectivity_model import __all__
        assert len(__all__) == 4
