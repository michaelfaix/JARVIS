# =============================================================================
# Unit Tests for jarvis/strategy/signal_fragility_analyzer.py
# =============================================================================

import pytest

from jarvis.strategy.signal_fragility_analyzer import (
    FRAGILITY_VOL_DELTA,
    FRAGILITY_SPREAD_DELTA,
    FRAGILITY_CORR_DELTA,
    FRAGILITY_PARAM_DELTA,
    FRAGILITY_HIGH_THRESHOLD,
    W_PARAM,
    W_VOL,
    W_SPREAD,
    W_CORR,
    SignalFragilityResult,
    SignalFragilityAnalyzer,
    _safe_delta,
    _clip01,
    _normalized_sensitivity,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _analyzer() -> SignalFragilityAnalyzer:
    return SignalFragilityAnalyzer()


def _constant_signal(**kwargs) -> float:
    """Signal that ignores all inputs — zero sensitivity."""
    return 0.5


def _linear_vol_signal(**kwargs) -> float:
    """Signal that is linear in volatility: f = volatility."""
    return kwargs.get("volatility", 0.0)


def _linear_spread_signal(**kwargs) -> float:
    """Signal that is linear in spread: f = spread."""
    return kwargs.get("spread", 0.0)


def _linear_corr_signal(**kwargs) -> float:
    """Signal that is linear in correlation: f = correlation."""
    return kwargs.get("correlation", 0.0)


def _linear_param_signal(**kwargs) -> float:
    """Signal that is linear in 'lookback': f = lookback."""
    return kwargs.get("lookback", 0.0)


def _sum_all_signal(**kwargs) -> float:
    """Signal = sum of all kwargs values."""
    return sum(kwargs.values())


def _default_compute(**overrides):
    """Convenience: compute with sensible defaults."""
    defaults = dict(
        signal_fn=_constant_signal,
        base_volatility=0.2,
        base_spread=0.01,
        base_correlation=0.5,
        strategy_params={"lookback": 20.0},
    )
    defaults.update(overrides)
    return _analyzer().compute(**defaults)


# ===================================================================
# TestConstants
# ===================================================================

class TestConstants:
    def test_vol_delta(self):
        assert FRAGILITY_VOL_DELTA == 0.05

    def test_spread_delta(self):
        assert FRAGILITY_SPREAD_DELTA == 0.05

    def test_corr_delta(self):
        assert FRAGILITY_CORR_DELTA == 0.05

    def test_param_delta(self):
        assert FRAGILITY_PARAM_DELTA == 0.01

    def test_high_threshold(self):
        assert FRAGILITY_HIGH_THRESHOLD == 0.65

    def test_weights_sum_to_one(self):
        assert W_PARAM + W_VOL + W_SPREAD + W_CORR == pytest.approx(1.0)

    def test_w_param(self):
        assert W_PARAM == 0.30

    def test_w_vol(self):
        assert W_VOL == 0.30

    def test_w_spread(self):
        assert W_SPREAD == 0.20

    def test_w_corr(self):
        assert W_CORR == 0.20


# ===================================================================
# TestSignalFragilityResult
# ===================================================================

class TestSignalFragilityResult:
    def test_creation(self):
        r = SignalFragilityResult(
            parameter_sensitivity_score=0.1,
            volatility_sensitivity_score=0.2,
            spread_sensitivity_score=0.3,
            correlation_sensitivity_score=0.4,
            fragility_index=0.25,
        )
        assert r.parameter_sensitivity_score == 0.1
        assert r.volatility_sensitivity_score == 0.2
        assert r.spread_sensitivity_score == 0.3
        assert r.correlation_sensitivity_score == 0.4
        assert r.fragility_index == 0.25

    def test_frozen(self):
        r = SignalFragilityResult(0.1, 0.2, 0.3, 0.4, 0.25)
        with pytest.raises(AttributeError):
            r.fragility_index = 0.9

    def test_equality(self):
        a = SignalFragilityResult(0.1, 0.2, 0.3, 0.4, 0.25)
        b = SignalFragilityResult(0.1, 0.2, 0.3, 0.4, 0.25)
        assert a == b

    def test_inequality(self):
        a = SignalFragilityResult(0.1, 0.2, 0.3, 0.4, 0.25)
        b = SignalFragilityResult(0.1, 0.2, 0.3, 0.4, 0.99)
        assert a != b

    def test_frozen_dataclass_params(self):
        assert SignalFragilityResult.__dataclass_params__.frozen is True

    def test_fields(self):
        names = {f.name for f in SignalFragilityResult.__dataclass_fields__.values()}
        assert names == {
            "parameter_sensitivity_score",
            "volatility_sensitivity_score",
            "spread_sensitivity_score",
            "correlation_sensitivity_score",
            "fragility_index",
        }


# ===================================================================
# TestSafeDelta
# ===================================================================

class TestSafeDelta:
    def test_normal_case(self):
        assert _safe_delta(1.0, 0.05, 0.01) == pytest.approx(0.05)

    def test_minimum_used_when_base_small(self):
        assert _safe_delta(0.0, 0.05, 0.01) == pytest.approx(0.01)

    def test_negative_base_uses_abs(self):
        assert _safe_delta(-2.0, 0.05, 0.01) == pytest.approx(0.1)

    def test_large_base(self):
        assert _safe_delta(100.0, 0.05, 0.01) == pytest.approx(5.0)

    def test_minimum_floor(self):
        assert _safe_delta(0.001, 0.05, 0.01) == pytest.approx(0.01)


# ===================================================================
# TestClip01
# ===================================================================

class TestClip01:
    def test_within_range(self):
        assert _clip01(0.5) == 0.5

    def test_below_zero(self):
        assert _clip01(-0.1) == 0.0

    def test_above_one(self):
        assert _clip01(1.5) == 1.0

    def test_at_zero(self):
        assert _clip01(0.0) == 0.0

    def test_at_one(self):
        assert _clip01(1.0) == 1.0


# ===================================================================
# TestNormalizedSensitivity
# ===================================================================

class TestNormalizedSensitivity:
    def test_constant_function_zero_sensitivity(self):
        s = _normalized_sensitivity(
            _constant_signal,
            {"volatility": 0.2, "spread": 0.01, "correlation": 0.5, "lookback": 20.0},
            "volatility",
            0.01,
        )
        assert s == pytest.approx(0.0)

    def test_linear_function_sensitivity(self):
        """f = volatility => df/dvol = 1.0 => sensitivity = 1.0"""
        s = _normalized_sensitivity(
            _linear_vol_signal,
            {"volatility": 0.2, "spread": 0.01, "correlation": 0.5, "lookback": 20.0},
            "volatility",
            0.01,
        )
        assert s == pytest.approx(1.0)

    def test_sensitivity_clipped_to_one(self):
        """f = 10*volatility => df/dvol = 10 => clipped to 1.0"""
        def steep_fn(**kw):
            return kw.get("volatility", 0.0) * 10.0
        s = _normalized_sensitivity(
            steep_fn,
            {"volatility": 0.2, "spread": 0.01, "correlation": 0.5},
            "volatility",
            0.01,
        )
        assert s == pytest.approx(1.0)

    def test_half_sensitivity(self):
        """f = 0.5*volatility => df/dvol = 0.5"""
        def half_fn(**kw):
            return kw.get("volatility", 0.0) * 0.5
        s = _normalized_sensitivity(
            half_fn,
            {"volatility": 0.2, "spread": 0.01, "correlation": 0.5},
            "volatility",
            0.01,
        )
        assert s == pytest.approx(0.5)


# ===================================================================
# TestComputeValidation
# ===================================================================

class TestComputeValidation:
    def test_vol_zero_raises(self):
        with pytest.raises(ValueError, match="base_volatility must be > 0"):
            _default_compute(base_volatility=0.0)

    def test_vol_negative_raises(self):
        with pytest.raises(ValueError, match="base_volatility must be > 0"):
            _default_compute(base_volatility=-0.1)

    def test_empty_strategy_params_raises(self):
        with pytest.raises(ValueError, match="strategy_params must be non-empty"):
            _default_compute(strategy_params={})

    def test_vol_small_positive_valid(self):
        r = _default_compute(base_volatility=0.001)
        assert isinstance(r, SignalFragilityResult)

    def test_spread_zero_valid(self):
        r = _default_compute(base_spread=0.0)
        assert isinstance(r, SignalFragilityResult)

    def test_negative_correlation_valid(self):
        r = _default_compute(base_correlation=-0.8)
        assert isinstance(r, SignalFragilityResult)


# ===================================================================
# TestComputeConstantSignal
# ===================================================================

class TestComputeConstantSignal:
    """A constant signal has zero sensitivity on all dimensions."""

    def test_all_scores_zero(self):
        r = _default_compute(signal_fn=_constant_signal)
        assert r.parameter_sensitivity_score == pytest.approx(0.0)
        assert r.volatility_sensitivity_score == pytest.approx(0.0)
        assert r.spread_sensitivity_score == pytest.approx(0.0)
        assert r.correlation_sensitivity_score == pytest.approx(0.0)

    def test_fragility_index_zero(self):
        r = _default_compute(signal_fn=_constant_signal)
        assert r.fragility_index == pytest.approx(0.0)


# ===================================================================
# TestComputeLinearSignals
# ===================================================================

class TestComputeLinearSignals:
    def test_vol_linear_signal(self):
        """f = volatility => vol_sensitivity = 1.0, others ~ 0."""
        r = _default_compute(signal_fn=_linear_vol_signal)
        assert r.volatility_sensitivity_score == pytest.approx(1.0)
        assert r.spread_sensitivity_score == pytest.approx(0.0)
        assert r.correlation_sensitivity_score == pytest.approx(0.0)
        assert r.parameter_sensitivity_score == pytest.approx(0.0)

    def test_spread_linear_signal(self):
        """f = spread => spread_sensitivity = 1.0, others ~ 0."""
        r = _default_compute(signal_fn=_linear_spread_signal)
        assert r.spread_sensitivity_score == pytest.approx(1.0)
        assert r.volatility_sensitivity_score == pytest.approx(0.0)
        assert r.correlation_sensitivity_score == pytest.approx(0.0)

    def test_corr_linear_signal(self):
        """f = correlation => corr_sensitivity = 1.0, others ~ 0."""
        r = _default_compute(signal_fn=_linear_corr_signal)
        assert r.correlation_sensitivity_score == pytest.approx(1.0)
        assert r.volatility_sensitivity_score == pytest.approx(0.0)
        assert r.spread_sensitivity_score == pytest.approx(0.0)

    def test_param_linear_signal(self):
        """f = lookback => param_sensitivity = 1.0, others ~ 0."""
        r = _default_compute(
            signal_fn=_linear_param_signal,
            strategy_params={"lookback": 20.0},
        )
        assert r.parameter_sensitivity_score == pytest.approx(1.0)
        assert r.volatility_sensitivity_score == pytest.approx(0.0)

    def test_vol_linear_fragility_index(self):
        """f = volatility => vol=1.0, rest=0 => fragility = 0.30*0 + 0.30*1 + 0.20*0 + 0.20*0 = 0.30"""
        r = _default_compute(signal_fn=_linear_vol_signal)
        assert r.fragility_index == pytest.approx(W_VOL * 1.0)


# ===================================================================
# TestComputeCompositeIndex
# ===================================================================

class TestComputeCompositeIndex:
    def test_all_sensitive_signal(self):
        """f = sum(all inputs) => all sensitivities = 1.0 => fragility = 1.0"""
        r = _default_compute(
            signal_fn=_sum_all_signal,
            strategy_params={"lookback": 20.0},
        )
        assert r.volatility_sensitivity_score == pytest.approx(1.0)
        assert r.spread_sensitivity_score == pytest.approx(1.0)
        assert r.correlation_sensitivity_score == pytest.approx(1.0)
        assert r.parameter_sensitivity_score == pytest.approx(1.0)
        assert r.fragility_index == pytest.approx(1.0)

    def test_half_sensitive_signal(self):
        """f = 0.5*volatility => vol=0.5, rest=0 => fragility = 0.30*0 + 0.30*0.5 + 0.20*0 + 0.20*0 = 0.15"""
        def half_vol(**kw):
            return kw.get("volatility", 0.0) * 0.5
        r = _default_compute(signal_fn=half_vol)
        assert r.volatility_sensitivity_score == pytest.approx(0.5)
        assert r.fragility_index == pytest.approx(W_VOL * 0.5)

    def test_fragility_in_01(self):
        r = _default_compute(signal_fn=_sum_all_signal)
        assert 0.0 <= r.fragility_index <= 1.0

    def test_high_fragility_classification(self):
        """All sensitivities = 1.0 => fragility = 1.0 >= 0.65"""
        r = _default_compute(signal_fn=_sum_all_signal)
        assert r.fragility_index >= FRAGILITY_HIGH_THRESHOLD

    def test_low_fragility_classification(self):
        """Constant signal => fragility = 0.0 < 0.65"""
        r = _default_compute(signal_fn=_constant_signal)
        assert r.fragility_index < FRAGILITY_HIGH_THRESHOLD


# ===================================================================
# TestComputeMultipleParams
# ===================================================================

class TestComputeMultipleParams:
    def test_two_params_mean_sensitivity(self):
        """Two params, signal linear in one => mean param sensitivity = 0.5"""
        def one_param_signal(**kw):
            return kw.get("lookback", 0.0)
        r = _default_compute(
            signal_fn=one_param_signal,
            strategy_params={"lookback": 20.0, "threshold": 0.015},
        )
        # lookback sensitivity = 1.0 (linear), threshold sensitivity = 0.0
        assert r.parameter_sensitivity_score == pytest.approx(0.5)

    def test_three_params_all_linear(self):
        """Three params, signal = sum of params => each sensitivity = 1.0"""
        r = _default_compute(
            signal_fn=_sum_all_signal,
            strategy_params={"a": 0.1, "b": 0.2, "c": 0.3},
        )
        assert r.parameter_sensitivity_score == pytest.approx(1.0)

    def test_sorted_params_deterministic(self):
        """Parameters are iterated in sorted order for determinism."""
        r1 = _default_compute(
            signal_fn=_sum_all_signal,
            strategy_params={"z": 1.0, "a": 2.0},
        )
        r2 = _default_compute(
            signal_fn=_sum_all_signal,
            strategy_params={"a": 2.0, "z": 1.0},
        )
        assert r1 == r2


# ===================================================================
# TestComputeDeterminism
# ===================================================================

class TestComputeDeterminism:
    def test_identical_inputs_identical_outputs(self):
        r1 = _default_compute(signal_fn=_sum_all_signal)
        r2 = _default_compute(signal_fn=_sum_all_signal)
        assert r1 == r2

    def test_different_instances_same_result(self):
        kwargs = dict(
            signal_fn=_linear_vol_signal,
            base_volatility=0.3,
            base_spread=0.02,
            base_correlation=0.4,
            strategy_params={"lookback": 30.0},
        )
        r1 = SignalFragilityAnalyzer().compute(**kwargs)
        r2 = SignalFragilityAnalyzer().compute(**kwargs)
        assert r1 == r2

    def test_bitwise_identical_fields(self):
        r1 = _default_compute(signal_fn=_sum_all_signal)
        r2 = _default_compute(signal_fn=_sum_all_signal)
        assert r1.parameter_sensitivity_score == r2.parameter_sensitivity_score
        assert r1.volatility_sensitivity_score == r2.volatility_sensitivity_score
        assert r1.spread_sensitivity_score == r2.spread_sensitivity_score
        assert r1.correlation_sensitivity_score == r2.correlation_sensitivity_score
        assert r1.fragility_index == r2.fragility_index


# ===================================================================
# TestComputeEdgeCases
# ===================================================================

class TestComputeEdgeCases:
    def test_very_small_volatility(self):
        r = _default_compute(
            signal_fn=_constant_signal,
            base_volatility=1e-10,
        )
        assert isinstance(r, SignalFragilityResult)

    def test_very_large_volatility(self):
        r = _default_compute(
            signal_fn=_constant_signal,
            base_volatility=1000.0,
        )
        assert r.fragility_index == pytest.approx(0.0)

    def test_spread_zero(self):
        """Spread = 0 uses minimum delta."""
        r = _default_compute(
            signal_fn=_constant_signal,
            base_spread=0.0,
        )
        assert r.spread_sensitivity_score == pytest.approx(0.0)

    def test_negative_spread(self):
        """Negative spread works (abs used in delta)."""
        r = _default_compute(
            signal_fn=_constant_signal,
            base_spread=-0.01,
        )
        assert isinstance(r, SignalFragilityResult)

    def test_correlation_at_boundary(self):
        r = _default_compute(
            signal_fn=_constant_signal,
            base_correlation=1.0,
        )
        assert isinstance(r, SignalFragilityResult)

    def test_param_value_zero(self):
        """Param = 0 uses minimum delta (1e-6)."""
        r = _default_compute(
            signal_fn=_constant_signal,
            strategy_params={"alpha": 0.0},
        )
        assert r.parameter_sensitivity_score == pytest.approx(0.0)

    def test_single_param(self):
        r = _default_compute(strategy_params={"x": 5.0})
        assert isinstance(r, SignalFragilityResult)


# ===================================================================
# TestHandComputations
# ===================================================================

class TestHandComputations:
    def test_vol_sensitivity_hand_calc(self):
        """
        f = volatility, base_vol = 0.2
        vol_delta = max(0.2 * 0.05, 0.01) = 0.01
        f(0.21) = 0.21, f(0.19) = 0.19
        sensitivity = |0.21 - 0.19| / (2 * 0.01) = 0.02 / 0.02 = 1.0
        """
        r = _default_compute(
            signal_fn=_linear_vol_signal,
            base_volatility=0.2,
        )
        assert r.volatility_sensitivity_score == pytest.approx(1.0)

    def test_spread_sensitivity_hand_calc(self):
        """
        f = spread, base_spread = 0.01
        spread_delta = max(0.01 * 0.05, 0.0001) = 0.0005
        f(0.0105) = 0.0105, f(0.0095) = 0.0095
        sensitivity = |0.0105 - 0.0095| / (2 * 0.0005) = 0.001 / 0.001 = 1.0
        """
        r = _default_compute(
            signal_fn=_linear_spread_signal,
            base_spread=0.01,
        )
        assert r.spread_sensitivity_score == pytest.approx(1.0)

    def test_corr_sensitivity_hand_calc(self):
        """
        f = correlation, base_corr = 0.5
        corr_delta = 0.05 (absolute)
        f(0.55) = 0.55, f(0.45) = 0.45
        sensitivity = |0.55 - 0.45| / (2 * 0.05) = 0.1 / 0.1 = 1.0
        """
        r = _default_compute(
            signal_fn=_linear_corr_signal,
            base_correlation=0.5,
        )
        assert r.correlation_sensitivity_score == pytest.approx(1.0)

    def test_param_sensitivity_hand_calc(self):
        """
        f = lookback, lookback = 20.0
        p_delta = max(20.0 * 0.01, 1e-6) = 0.2
        f(20.2) = 20.2, f(19.8) = 19.8
        sensitivity = |20.2 - 19.8| / (2 * 0.2) = 0.4 / 0.4 = 1.0
        """
        r = _default_compute(
            signal_fn=_linear_param_signal,
            strategy_params={"lookback": 20.0},
        )
        assert r.parameter_sensitivity_score == pytest.approx(1.0)

    def test_composite_hand_calc(self):
        """
        f = volatility (linear in vol only)
        param=0.0, vol=1.0, spread=0.0, corr=0.0
        fragility = 0.30*0 + 0.30*1 + 0.20*0 + 0.20*0 = 0.30
        """
        r = _default_compute(signal_fn=_linear_vol_signal)
        expected = W_PARAM * 0.0 + W_VOL * 1.0 + W_SPREAD * 0.0 + W_CORR * 0.0
        assert r.fragility_index == pytest.approx(expected)


# ===================================================================
# TestAnalyzerStateless
# ===================================================================

class TestAnalyzerStateless:
    def test_no_instance_state_mutation(self):
        a = _analyzer()
        a.compute(
            signal_fn=_constant_signal,
            base_volatility=0.2,
            base_spread=0.01,
            base_correlation=0.5,
            strategy_params={"lookback": 20.0},
        )
        assert not hasattr(a, '_cache')
        assert not hasattr(a, '_records')

    def test_no_mutable_instance_attrs(self):
        a = _analyzer()
        instance_attrs = {k for k in a.__dict__ if not k.startswith('__')}
        assert len(instance_attrs) == 0

    def test_multiple_calls_independent(self):
        a = _analyzer()
        r1 = a.compute(
            signal_fn=_linear_vol_signal,
            base_volatility=0.2,
            base_spread=0.01,
            base_correlation=0.5,
            strategy_params={"lookback": 20.0},
        )
        r2 = a.compute(
            signal_fn=_constant_signal,
            base_volatility=0.2,
            base_spread=0.01,
            base_correlation=0.5,
            strategy_params={"lookback": 20.0},
        )
        assert r1.volatility_sensitivity_score != r2.volatility_sensitivity_score


# ===================================================================
# TestGovernanceConstraints
# ===================================================================

class TestGovernanceConstraints:
    def test_result_is_frozen_dataclass(self):
        assert SignalFragilityResult.__dataclass_params__.frozen is True

    def test_no_capital_fields(self):
        field_names = {f.name for f in SignalFragilityResult.__dataclass_fields__.values()}
        forbidden = {"capital", "pnl", "balance", "broker_id", "order_id", "account_id"}
        assert field_names.isdisjoint(forbidden)

    def test_all_scores_in_01(self):
        r = _default_compute(signal_fn=_sum_all_signal)
        assert 0.0 <= r.parameter_sensitivity_score <= 1.0
        assert 0.0 <= r.volatility_sensitivity_score <= 1.0
        assert 0.0 <= r.spread_sensitivity_score <= 1.0
        assert 0.0 <= r.correlation_sensitivity_score <= 1.0
        assert 0.0 <= r.fragility_index <= 1.0

    def test_weights_governance(self):
        """Weights must match FAS specification exactly."""
        assert W_PARAM == 0.30
        assert W_VOL == 0.30
        assert W_SPREAD == 0.20
        assert W_CORR == 0.20
        assert W_PARAM + W_VOL + W_SPREAD + W_CORR == pytest.approx(1.0)


# ===================================================================
# TestModuleAll
# ===================================================================

class TestModuleAll:
    def test_contains_fragility_result(self):
        from jarvis.strategy.signal_fragility_analyzer import __all__
        assert "SignalFragilityResult" in __all__

    def test_contains_fragility_analyzer(self):
        from jarvis.strategy.signal_fragility_analyzer import __all__
        assert "SignalFragilityAnalyzer" in __all__

    def test_contains_all_constants(self):
        from jarvis.strategy.signal_fragility_analyzer import __all__
        for name in [
            "FRAGILITY_VOL_DELTA", "FRAGILITY_SPREAD_DELTA",
            "FRAGILITY_CORR_DELTA", "FRAGILITY_PARAM_DELTA",
            "FRAGILITY_HIGH_THRESHOLD",
            "W_PARAM", "W_VOL", "W_SPREAD", "W_CORR",
        ]:
            assert name in __all__, f"{name} missing from __all__"

    def test_all_length(self):
        from jarvis.strategy.signal_fragility_analyzer import __all__
        assert len(__all__) == 11
