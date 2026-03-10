# =============================================================================
# Unit Tests for jarvis/intelligence/decision_quality_engine.py
# =============================================================================

import pytest

from jarvis.core.decision_context_state import (
    DecisionRecord,
    DecisionContextSnapshot,
)
from jarvis.core.regime import CorrelationRegimeState
from jarvis.intelligence.regime_duration_model import RegimeDurationResult
from jarvis.strategy.signal_fragility_analyzer import SignalFragilityResult

from jarvis.intelligence.decision_quality_engine import (
    QUALITY_SCORE_CAP_UNDER_UNCERTAINTY,
    QUALITY_SCORE_MIN_FLOOR,
    DecisionQualityBundle,
    DecisionQualityEngine,
)


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

def _duration(z=0.0, flag=False):
    return RegimeDurationResult(
        regime_age_ratio=1.0,
        duration_z_score=z,
        transition_acceleration_flag=flag,
    )


def _fragility(index=0.0):
    return SignalFragilityResult(
        parameter_sensitivity_score=index,
        volatility_sensitivity_score=index,
        spread_sensitivity_score=index,
        correlation_sensitivity_score=index,
        fragility_index=index,
    )


def _snapshot(records=None):
    if records is None:
        records = ()
    return DecisionContextSnapshot(
        records=tuple(records),
        total_appended=len(records),
    )


def _rec(seq=0, regime="RISK_ON", conf=0.5, outcome="NEUTRAL", strategy="s"):
    return DecisionRecord(
        sequence_id=seq,
        regime_at_decision=regime,
        confidence_at_decision=conf,
        outcome=outcome,
        strategy_id=strategy,
    )


def _engine():
    return DecisionQualityEngine()


def _calm_compute(**overrides):
    defaults = dict(
        regime_transition_diagonal_mean=0.9,
        duration_result=_duration(z=0.0, flag=False),
        fragility_result=_fragility(0.0),
        correlation_regime=CorrelationRegimeState.NORMAL,
        overfitting_risk_score=0.0,
        total_uncertainty=0.1,
        decision_snapshot=_snapshot(),
        active_failure_modes=frozenset(),
    )
    defaults.update(overrides)
    return _engine().compute(**defaults)


def _stressed_compute(**overrides):
    defaults = dict(
        regime_transition_diagonal_mean=0.1,
        duration_result=_duration(z=4.0, flag=True),
        fragility_result=_fragility(1.0),
        correlation_regime=CorrelationRegimeState.BREAKDOWN,
        overfitting_risk_score=1.0,
        total_uncertainty=0.9,
        decision_snapshot=_snapshot([
            _rec(seq=i, outcome="LOSS") for i in range(10)
        ]),
        active_failure_modes=frozenset({"FM-01", "FM-02", "FM-03"}),
    )
    defaults.update(overrides)
    return _engine().compute(**defaults)


# ===================================================================
# TestConstants
# ===================================================================

class TestConstants:
    def test_quality_cap(self):
        assert QUALITY_SCORE_CAP_UNDER_UNCERTAINTY == 0.60

    def test_quality_floor(self):
        assert QUALITY_SCORE_MIN_FLOOR == 0.05

    def test_cap_greater_than_floor(self):
        assert QUALITY_SCORE_CAP_UNDER_UNCERTAINTY > QUALITY_SCORE_MIN_FLOOR


# ===================================================================
# TestWeightConstants
# ===================================================================

class TestWeightConstants:
    def test_weights_sum_to_one(self):
        e = _engine()
        total = (
            e.W_REGIME_STABILITY
            + e.W_DURATION_STRESS
            + e.W_SIGNAL_FRAGILITY
            + e.W_CORRELATION_RISK
            + e.W_OVERFIT_RISK
            + e.W_UNCERTAINTY
            + e.W_STREAK_INSTABILITY
            + e.W_REGIME_MISALIGNMENT
            + e.W_REPEATED_FAILURE_PENALTY
        )
        assert total == pytest.approx(1.0)

    def test_w_regime_stability(self):
        assert _engine().W_REGIME_STABILITY == 0.20

    def test_w_duration_stress(self):
        assert _engine().W_DURATION_STRESS == 0.15

    def test_w_signal_fragility(self):
        assert _engine().W_SIGNAL_FRAGILITY == 0.20

    def test_w_correlation_risk(self):
        assert _engine().W_CORRELATION_RISK == 0.15

    def test_w_overfit_risk(self):
        assert _engine().W_OVERFIT_RISK == 0.10

    def test_w_uncertainty(self):
        assert _engine().W_UNCERTAINTY == 0.10

    def test_w_streak_instability(self):
        assert _engine().W_STREAK_INSTABILITY == 0.05

    def test_w_regime_misalignment(self):
        assert _engine().W_REGIME_MISALIGNMENT == 0.03

    def test_w_repeated_failure_penalty(self):
        assert _engine().W_REPEATED_FAILURE_PENALTY == 0.02


# ===================================================================
# TestDecisionQualityBundle
# ===================================================================

class TestDecisionQualityBundle:
    def test_frozen(self):
        b = _calm_compute()
        with pytest.raises(AttributeError):
            b.composite_quality_score = 0.99

    def test_frozen_dataclass_params(self):
        assert DecisionQualityBundle.__dataclass_params__.frozen is True

    def test_all_fields_present(self):
        names = {f.name for f in DecisionQualityBundle.__dataclass_fields__.values()}
        expected = {
            "regime_stability_score",
            "regime_duration_stress_score",
            "signal_fragility_score",
            "correlation_risk_modifier",
            "overfit_risk_modifier",
            "uncertainty_modifier",
            "streak_instability",
            "regime_misalignment",
            "repeated_failure_penalty",
            "composite_quality_score",
            "selectivity_threshold",
            "signal_passes_selectivity",
        }
        assert names == expected

    def test_equality(self):
        a = _calm_compute()
        b = _calm_compute()
        assert a == b


# ===================================================================
# TestRegimeStabilityScore
# ===================================================================

class TestRegimeStabilityScore:
    def test_passthrough(self):
        b = _calm_compute(regime_transition_diagonal_mean=0.75)
        assert b.regime_stability_score == pytest.approx(0.75)

    def test_clipped_above_one(self):
        b = _calm_compute(regime_transition_diagonal_mean=1.5)
        assert b.regime_stability_score == pytest.approx(1.0)

    def test_clipped_below_zero(self):
        b = _calm_compute(regime_transition_diagonal_mean=-0.3)
        assert b.regime_stability_score == pytest.approx(0.0)


# ===================================================================
# TestDurationStressScore
# ===================================================================

class TestDurationStressScore:
    def test_zero_zscore_no_stress(self):
        b = _calm_compute(duration_result=_duration(z=0.0, flag=False))
        assert b.regime_duration_stress_score == pytest.approx(0.0)

    def test_zscore_maps_to_fifth(self):
        b = _calm_compute(duration_result=_duration(z=2.5, flag=False))
        assert b.regime_duration_stress_score == pytest.approx(0.5)

    def test_zscore_5_maps_to_1(self):
        b = _calm_compute(duration_result=_duration(z=5.0, flag=False))
        assert b.regime_duration_stress_score == pytest.approx(1.0)

    def test_negative_zscore_uses_abs(self):
        b = _calm_compute(duration_result=_duration(z=-2.5, flag=False))
        assert b.regime_duration_stress_score == pytest.approx(0.5)

    def test_flag_adds_030(self):
        b = _calm_compute(duration_result=_duration(z=1.0, flag=True))
        assert b.regime_duration_stress_score == pytest.approx(0.50)

    def test_flag_clipped_at_1(self):
        b = _calm_compute(duration_result=_duration(z=5.0, flag=True))
        assert b.regime_duration_stress_score == pytest.approx(1.0)


# ===================================================================
# TestSignalFragilityScore
# ===================================================================

class TestSignalFragilityScore:
    def test_passthrough(self):
        b = _calm_compute(fragility_result=_fragility(0.3))
        assert b.signal_fragility_score == pytest.approx(0.3)

    def test_zero(self):
        b = _calm_compute(fragility_result=_fragility(0.0))
        assert b.signal_fragility_score == pytest.approx(0.0)

    def test_one(self):
        b = _calm_compute(fragility_result=_fragility(1.0))
        assert b.signal_fragility_score == pytest.approx(1.0)


# ===================================================================
# TestCorrelationRiskModifier
# ===================================================================

class TestCorrelationRiskModifier:
    def test_normal(self):
        b = _calm_compute(correlation_regime=CorrelationRegimeState.NORMAL)
        assert b.correlation_risk_modifier == pytest.approx(0.0)

    def test_divergence(self):
        b = _calm_compute(correlation_regime=CorrelationRegimeState.DIVERGENCE)
        assert b.correlation_risk_modifier == pytest.approx(0.0)

    def test_coupled(self):
        b = _calm_compute(correlation_regime=CorrelationRegimeState.COUPLED)
        assert b.correlation_risk_modifier == pytest.approx(0.40)

    def test_breakdown(self):
        b = _calm_compute(correlation_regime=CorrelationRegimeState.BREAKDOWN)
        assert b.correlation_risk_modifier == pytest.approx(0.85)


# ===================================================================
# TestOverfitRiskModifier
# ===================================================================

class TestOverfitRiskModifier:
    def test_passthrough(self):
        b = _calm_compute(overfitting_risk_score=0.4)
        assert b.overfit_risk_modifier == pytest.approx(0.4)

    def test_clipped(self):
        b = _calm_compute(overfitting_risk_score=1.5)
        assert b.overfit_risk_modifier == pytest.approx(1.0)


# ===================================================================
# TestUncertaintyModifier
# ===================================================================

class TestUncertaintyModifier:
    def test_passthrough(self):
        b = _calm_compute(total_uncertainty=0.3)
        assert b.uncertainty_modifier == pytest.approx(0.3)

    def test_clipped(self):
        b = _calm_compute(total_uncertainty=1.5)
        assert b.uncertainty_modifier == pytest.approx(1.0)


# ===================================================================
# TestStreakInstability
# ===================================================================

class TestStreakInstability:
    def test_empty_snapshot(self):
        b = _calm_compute(decision_snapshot=_snapshot())
        assert b.streak_instability == pytest.approx(0.0)

    def test_single_record(self):
        b = _calm_compute(decision_snapshot=_snapshot([_rec(0)]))
        assert b.streak_instability == pytest.approx(0.0)

    def test_all_same_outcome(self):
        recs = [_rec(i, outcome="WIN") for i in range(5)]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.streak_instability == pytest.approx(0.0)

    def test_alternating_outcomes(self):
        outcomes = ["WIN", "LOSS", "WIN", "LOSS"]
        recs = [_rec(i, outcome=o) for i, o in enumerate(outcomes)]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.streak_instability == pytest.approx(1.0)

    def test_partial_transitions(self):
        outcomes = ["WIN", "WIN", "LOSS", "LOSS"]
        recs = [_rec(i, outcome=o) for i, o in enumerate(outcomes)]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.streak_instability == pytest.approx(1.0 / 3.0, abs=1e-6)

    def test_window_limited_to_10(self):
        recs = [_rec(i, outcome="WIN") for i in range(5)]
        for i in range(10):
            recs.append(_rec(5 + i, outcome="WIN" if i % 2 == 0 else "LOSS"))
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.streak_instability == pytest.approx(1.0)


# ===================================================================
# TestRegimeMisalignment
# ===================================================================

class TestRegimeMisalignment:
    def test_empty_snapshot(self):
        b = _calm_compute(decision_snapshot=_snapshot())
        assert b.regime_misalignment == pytest.approx(0.0)

    def test_all_same_regime(self):
        recs = [_rec(i, regime="RISK_ON") for i in range(5)]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.regime_misalignment == pytest.approx(0.0)

    def test_all_different_from_current(self):
        recs = [_rec(i, regime="RISK_ON") for i in range(4)]
        recs.append(_rec(4, regime="CRISIS"))
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.regime_misalignment == pytest.approx(4.0 / 5.0)

    def test_half_misaligned(self):
        recs = [_rec(i, regime="RISK_ON") for i in range(3)]
        recs += [_rec(i + 3, regime="CRISIS") for i in range(3)]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.regime_misalignment == pytest.approx(3.0 / 6.0)

    def test_window_limited_to_20(self):
        recs = [_rec(i, regime="RISK_OFF") for i in range(25)]
        recs.append(_rec(25, regime="RISK_ON"))
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.regime_misalignment == pytest.approx(19.0 / 20.0)


# ===================================================================
# TestRepeatedFailurePenalty
# ===================================================================

class TestRepeatedFailurePenalty:
    def test_empty_snapshot(self):
        b = _calm_compute(decision_snapshot=_snapshot())
        assert b.repeated_failure_penalty == pytest.approx(0.0)

    def test_no_losses(self):
        recs = [_rec(i, outcome="WIN") for i in range(5)]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.repeated_failure_penalty == pytest.approx(0.0)

    def test_loss_rate_at_threshold(self):
        recs = [_rec(i, outcome="LOSS") for i in range(6)]
        recs += [_rec(i + 6, outcome="WIN") for i in range(4)]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.repeated_failure_penalty == pytest.approx(0.0)

    def test_loss_rate_above_threshold(self):
        recs = [_rec(i, outcome="LOSS") for i in range(7)]
        recs += [_rec(i + 7, outcome="WIN") for i in range(3)]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.repeated_failure_penalty == pytest.approx(0.25)

    def test_all_losses(self):
        recs = [_rec(i, outcome="LOSS") for i in range(10)]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.repeated_failure_penalty == pytest.approx(1.0)

    def test_window_limited_to_10(self):
        recs = [_rec(i, outcome="LOSS") for i in range(5)]
        recs += [_rec(i + 5, outcome="WIN") for i in range(10)]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.repeated_failure_penalty == pytest.approx(0.0)


# ===================================================================
# TestCompositeQualityScore
# ===================================================================

class TestCompositeQualityScore:
    def test_all_calm_high_quality(self):
        b = _calm_compute()
        assert b.composite_quality_score > 0.8

    def test_all_stressed_low_quality(self):
        b = _stressed_compute()
        assert b.composite_quality_score <= QUALITY_SCORE_CAP_UNDER_UNCERTAINTY

    def test_quality_in_valid_range(self):
        b = _calm_compute()
        assert QUALITY_SCORE_MIN_FLOOR <= b.composite_quality_score <= 1.0

    def test_hand_computed_all_zero_stress(self):
        """All stress at 0, stability at 1.0 => raw = 1.0"""
        b = _calm_compute(
            regime_transition_diagonal_mean=1.0,
            duration_result=_duration(z=0.0, flag=False),
            fragility_result=_fragility(0.0),
            correlation_regime=CorrelationRegimeState.NORMAL,
            overfitting_risk_score=0.0,
            total_uncertainty=0.0,
            decision_snapshot=_snapshot(),
            active_failure_modes=frozenset(),
        )
        assert b.composite_quality_score == pytest.approx(1.0)

    def test_hand_computed_max_stress(self):
        """BREAKDOWN=0.85, not 1.0. All LOSS => streak=0, fail=1.0.
        raw = 0.20*0 + 0.15*(1-1) + 0.20*(1-1) + 0.15*(1-0.85)
            + 0.10*(1-1) + 0.10*(1-0.9) + 0.05*(1-0) + 0.03*(1-0) + 0.02*(1-1)
            = 0 + 0 + 0 + 0.0225 + 0 + 0.01 + 0.05 + 0.03 + 0 = 0.1125"""
        b = _calm_compute(
            regime_transition_diagonal_mean=0.0,
            duration_result=_duration(z=5.0, flag=True),
            fragility_result=_fragility(1.0),
            correlation_regime=CorrelationRegimeState.BREAKDOWN,
            overfitting_risk_score=1.0,
            total_uncertainty=0.9,
            decision_snapshot=_snapshot([
                _rec(i, outcome="LOSS") for i in range(10)
            ]),
        )
        assert b.composite_quality_score == pytest.approx(0.1125)


# ===================================================================
# TestUncertaintyCap
# ===================================================================

class TestUncertaintyCap:
    def test_cap_applied_when_uncertainty_high(self):
        b = _calm_compute(total_uncertainty=0.6)
        assert b.composite_quality_score <= QUALITY_SCORE_CAP_UNDER_UNCERTAINTY

    def test_no_cap_when_uncertainty_low(self):
        b = _calm_compute(
            regime_transition_diagonal_mean=1.0,
            total_uncertainty=0.1,
        )
        assert b.composite_quality_score > QUALITY_SCORE_CAP_UNDER_UNCERTAINTY

    def test_cap_at_boundary(self):
        b = _calm_compute(
            regime_transition_diagonal_mean=1.0,
            total_uncertainty=0.50,
        )
        assert b.composite_quality_score > QUALITY_SCORE_CAP_UNDER_UNCERTAINTY

    def test_cap_just_above_boundary(self):
        b = _calm_compute(total_uncertainty=0.501)
        assert b.composite_quality_score <= QUALITY_SCORE_CAP_UNDER_UNCERTAINTY


# ===================================================================
# TestQualityFloor
# ===================================================================

class TestQualityFloor:
    def test_floor_applied(self):
        b = _stressed_compute()
        assert b.composite_quality_score >= QUALITY_SCORE_MIN_FLOOR

    def test_floor_prevents_zero(self):
        b = _stressed_compute()
        assert b.composite_quality_score > 0.0


# ===================================================================
# TestSelectivityThreshold
# ===================================================================

class TestSelectivityThreshold:
    def test_calm_threshold_at_base(self):
        b = _calm_compute()
        assert b.selectivity_threshold == pytest.approx(0.55)

    def test_stressed_threshold_higher(self):
        b = _stressed_compute()
        assert b.selectivity_threshold > 0.55

    def test_threshold_never_below_base(self):
        b = _calm_compute()
        assert b.selectivity_threshold >= 0.55


# ===================================================================
# TestSignalPassesSelectivity
# ===================================================================

class TestSignalPassesSelectivity:
    def test_high_quality_passes(self):
        b = _calm_compute()
        assert b.signal_passes_selectivity is True

    def test_low_quality_fails(self):
        b = _stressed_compute()
        assert b.signal_passes_selectivity is False

    def test_pass_is_bool(self):
        b = _calm_compute()
        assert isinstance(b.signal_passes_selectivity, bool)


# ===================================================================
# TestDeterminism
# ===================================================================

class TestDeterminism:
    def test_identical_inputs_identical_outputs(self):
        b1 = _calm_compute()
        b2 = _calm_compute()
        assert b1 == b2

    def test_stressed_determinism(self):
        b1 = _stressed_compute()
        b2 = _stressed_compute()
        assert b1 == b2

    def test_different_instances_same_result(self):
        kwargs = dict(
            regime_transition_diagonal_mean=0.7,
            duration_result=_duration(z=1.5, flag=False),
            fragility_result=_fragility(0.3),
            correlation_regime=CorrelationRegimeState.COUPLED,
            overfitting_risk_score=0.2,
            total_uncertainty=0.3,
            decision_snapshot=_snapshot([_rec(i) for i in range(3)]),
            active_failure_modes=frozenset({"FM-01"}),
        )
        b1 = DecisionQualityEngine().compute(**kwargs)
        b2 = DecisionQualityEngine().compute(**kwargs)
        assert b1 == b2

    def test_bitwise_identical_composite(self):
        b1 = _calm_compute(regime_transition_diagonal_mean=0.6)
        b2 = _calm_compute(regime_transition_diagonal_mean=0.6)
        assert b1.composite_quality_score == b2.composite_quality_score


# ===================================================================
# TestEdgeCases
# ===================================================================

class TestEdgeCases:
    def test_empty_snapshot_valid(self):
        b = _calm_compute(decision_snapshot=_snapshot())
        assert isinstance(b, DecisionQualityBundle)

    def test_large_snapshot(self):
        recs = [_rec(i, outcome="WIN" if i % 2 == 0 else "LOSS")
                for i in range(200)]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert isinstance(b, DecisionQualityBundle)

    def test_all_neutral_outcomes(self):
        recs = [_rec(i, outcome="NEUTRAL") for i in range(10)]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.repeated_failure_penalty == pytest.approx(0.0)
        assert b.streak_instability == pytest.approx(0.0)

    def test_zero_diagonal_mean(self):
        b = _calm_compute(regime_transition_diagonal_mean=0.0)
        assert b.regime_stability_score == pytest.approx(0.0)
        assert b.composite_quality_score >= QUALITY_SCORE_MIN_FLOOR

    def test_empty_failure_modes(self):
        b = _calm_compute(active_failure_modes=frozenset())
        assert isinstance(b, DecisionQualityBundle)


# ===================================================================
# TestHandComputedComposite
# ===================================================================

class TestHandComputedComposite:
    def test_stability_only_contribution(self):
        """stability=0.5, all stress=0, uncertainty=0 =>
        raw = 0.20*0.5 + 0.80*1.0 = 0.10 + 0.80 = 0.90"""
        b = _calm_compute(
            regime_transition_diagonal_mean=0.5,
            total_uncertainty=0.0,
        )
        assert b.composite_quality_score == pytest.approx(0.90)

    def test_fragility_only_contribution(self):
        """stability=1.0, fragility=0.5, rest=0, unc=0 =>
        raw = 0.20 + 0.15 + 0.20*0.5 + 0.15 + 0.10 + 0.10 + 0.05 + 0.03 + 0.02 = 0.90"""
        b = _calm_compute(
            regime_transition_diagonal_mean=1.0,
            fragility_result=_fragility(0.5),
            total_uncertainty=0.0,
        )
        assert b.composite_quality_score == pytest.approx(0.90)

    def test_duration_stress_contribution(self):
        """stability=1.0, z=2.5 (stress=0.5), rest=0, unc=0 =>
        raw = 0.20 + 0.15*0.5 + 0.20 + 0.15 + 0.10 + 0.10 + 0.05 + 0.03 + 0.02 = 0.925"""
        b = _calm_compute(
            regime_transition_diagonal_mean=1.0,
            duration_result=_duration(z=2.5, flag=False),
            total_uncertainty=0.0,
        )
        assert b.composite_quality_score == pytest.approx(0.925)


# ===================================================================
# TestGovernanceConstraints
# ===================================================================

class TestGovernanceConstraints:
    def test_bundle_is_frozen(self):
        assert DecisionQualityBundle.__dataclass_params__.frozen is True

    def test_no_capital_fields(self):
        field_names = {f.name for f in DecisionQualityBundle.__dataclass_fields__.values()}
        forbidden = {"capital", "pnl", "balance", "broker_id", "order_id", "account_id"}
        assert field_names.isdisjoint(forbidden)

    def test_all_sub_scores_in_01(self):
        b = _calm_compute()
        assert 0.0 <= b.regime_stability_score <= 1.0
        assert 0.0 <= b.regime_duration_stress_score <= 1.0
        assert 0.0 <= b.signal_fragility_score <= 1.0
        assert 0.0 <= b.correlation_risk_modifier <= 1.0
        assert 0.0 <= b.overfit_risk_modifier <= 1.0
        assert 0.0 <= b.uncertainty_modifier <= 1.0
        assert 0.0 <= b.streak_instability <= 1.0
        assert 0.0 <= b.regime_misalignment <= 1.0
        assert 0.0 <= b.repeated_failure_penalty <= 1.0

    def test_stressed_sub_scores_in_01(self):
        b = _stressed_compute()
        assert 0.0 <= b.regime_stability_score <= 1.0
        assert 0.0 <= b.regime_duration_stress_score <= 1.0
        assert 0.0 <= b.signal_fragility_score <= 1.0
        assert 0.0 <= b.correlation_risk_modifier <= 1.0
        assert 0.0 <= b.overfit_risk_modifier <= 1.0
        assert 0.0 <= b.uncertainty_modifier <= 1.0
        assert 0.0 <= b.streak_instability <= 1.0
        assert 0.0 <= b.regime_misalignment <= 1.0
        assert 0.0 <= b.repeated_failure_penalty <= 1.0

    def test_composite_respects_floor(self):
        b = _stressed_compute()
        assert b.composite_quality_score >= QUALITY_SCORE_MIN_FLOOR

    def test_composite_respects_cap_under_uncertainty(self):
        b = _calm_compute(total_uncertainty=0.8)
        assert b.composite_quality_score <= QUALITY_SCORE_CAP_UNDER_UNCERTAINTY


# ===================================================================
# TestModuleAll
# ===================================================================

class TestModuleAll:
    def test_contains_quality_cap(self):
        from jarvis.intelligence.decision_quality_engine import __all__
        assert "QUALITY_SCORE_CAP_UNDER_UNCERTAINTY" in __all__

    def test_contains_quality_floor(self):
        from jarvis.intelligence.decision_quality_engine import __all__
        assert "QUALITY_SCORE_MIN_FLOOR" in __all__

    def test_contains_bundle(self):
        from jarvis.intelligence.decision_quality_engine import __all__
        assert "DecisionQualityBundle" in __all__

    def test_contains_engine(self):
        from jarvis.intelligence.decision_quality_engine import __all__
        assert "DecisionQualityEngine" in __all__

    def test_all_length(self):
        from jarvis.intelligence.decision_quality_engine import __all__
        assert len(__all__) == 4
