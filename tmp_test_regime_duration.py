# =============================================================================
# Unit Tests for jarvis/intelligence/regime_duration_model.py
# =============================================================================

import pytest

from jarvis.intelligence.regime_duration_model import (
    DURATION_STRESS_Z_LIMIT,
    RegimeDurationResult,
    RegimeDurationModel,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _model() -> RegimeDurationModel:
    return RegimeDurationModel()


def _compute(**kwargs) -> RegimeDurationResult:
    defaults = dict(
        regime_start_timestamp=1000.0,
        current_timestamp=1100.0,
        historical_avg_duration=100.0,
        historical_std_duration=20.0,
    )
    defaults.update(kwargs)
    return _model().compute(**defaults)


# ===================================================================
# TestConstants
# ===================================================================

class TestConstants:
    def test_duration_stress_z_limit_value(self):
        assert DURATION_STRESS_Z_LIMIT == 2.0

    def test_duration_stress_z_limit_type(self):
        assert isinstance(DURATION_STRESS_Z_LIMIT, float)

    def test_class_constant_matches_module(self):
        m = _model()
        assert m.DURATION_STRESS_Z_LIMIT == DURATION_STRESS_Z_LIMIT


# ===================================================================
# TestRegimeDurationResult
# ===================================================================

class TestRegimeDurationResult:
    def test_creation(self):
        r = RegimeDurationResult(
            regime_age_ratio=1.0,
            duration_z_score=0.0,
            transition_acceleration_flag=False,
        )
        assert r.regime_age_ratio == 1.0
        assert r.duration_z_score == 0.0
        assert r.transition_acceleration_flag is False

    def test_frozen(self):
        r = RegimeDurationResult(
            regime_age_ratio=1.0,
            duration_z_score=0.0,
            transition_acceleration_flag=False,
        )
        with pytest.raises(AttributeError):
            r.regime_age_ratio = 2.0

    def test_equality(self):
        a = RegimeDurationResult(1.0, 0.0, False)
        b = RegimeDurationResult(1.0, 0.0, False)
        assert a == b

    def test_inequality(self):
        a = RegimeDurationResult(1.0, 0.0, False)
        b = RegimeDurationResult(1.0, 0.0, True)
        assert a != b

    def test_frozen_dataclass_params(self):
        assert RegimeDurationResult.__dataclass_params__.frozen is True


# ===================================================================
# TestComputeValidation
# ===================================================================

class TestComputeValidation:
    def test_current_before_start_raises(self):
        with pytest.raises(ValueError, match="current_timestamp must be >= regime_start_timestamp"):
            _compute(regime_start_timestamp=200.0, current_timestamp=100.0)

    def test_current_equals_start_valid(self):
        r = _compute(regime_start_timestamp=100.0, current_timestamp=100.0)
        assert r.regime_age_ratio == 0.0

    def test_avg_duration_zero_raises(self):
        with pytest.raises(ValueError, match="historical_avg_duration must be > 0"):
            _compute(historical_avg_duration=0.0)

    def test_avg_duration_negative_raises(self):
        with pytest.raises(ValueError, match="historical_avg_duration must be > 0"):
            _compute(historical_avg_duration=-10.0)

    def test_avg_duration_small_positive_valid(self):
        r = _compute(historical_avg_duration=0.001)
        assert r.regime_age_ratio >= 0.0

    def test_std_duration_zero_valid(self):
        # std=0 is valid; internally clipped to 1.0
        r = _compute(historical_std_duration=0.0)
        assert isinstance(r, RegimeDurationResult)

    def test_std_duration_negative_valid(self):
        # negative std clipped to 1.0 internally
        r = _compute(historical_std_duration=-5.0)
        assert isinstance(r, RegimeDurationResult)


# ===================================================================
# TestComputeAgeRatio
# ===================================================================

class TestComputeAgeRatio:
    def test_age_equals_avg(self):
        """Age == avg => ratio == 1.0"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=100.0,
            historical_avg_duration=100.0,
        )
        assert r.regime_age_ratio == pytest.approx(1.0)

    def test_age_half_of_avg(self):
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=50.0,
            historical_avg_duration=100.0,
        )
        assert r.regime_age_ratio == pytest.approx(0.5)

    def test_age_double_avg(self):
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=200.0,
            historical_avg_duration=100.0,
        )
        assert r.regime_age_ratio == pytest.approx(2.0)

    def test_age_zero(self):
        r = _compute(
            regime_start_timestamp=100.0,
            current_timestamp=100.0,
            historical_avg_duration=100.0,
        )
        assert r.regime_age_ratio == pytest.approx(0.0)

    def test_clipped_upper_at_5(self):
        """Age >> avg => ratio clipped to 5.0"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=1000.0,
            historical_avg_duration=100.0,
        )
        assert r.regime_age_ratio == pytest.approx(5.0)

    def test_ratio_is_float(self):
        r = _compute()
        assert isinstance(r.regime_age_ratio, float)

    def test_small_avg_large_age_clips(self):
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=100.0,
            historical_avg_duration=1.0,
        )
        assert r.regime_age_ratio == 5.0  # 100/1 = 100, clipped to 5.0


# ===================================================================
# TestComputeZScore
# ===================================================================

class TestComputeZScore:
    def test_age_equals_avg_zscore_zero(self):
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=100.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.duration_z_score == pytest.approx(0.0)

    def test_one_std_above(self):
        """Age = avg + 1*std => z = 1.0"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=120.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.duration_z_score == pytest.approx(1.0)

    def test_one_std_below(self):
        """Age = avg - 1*std => z = -1.0"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=80.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.duration_z_score == pytest.approx(-1.0)

    def test_two_std_above(self):
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=140.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.duration_z_score == pytest.approx(2.0)

    def test_clipped_upper_at_5(self):
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=1000.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.duration_z_score == pytest.approx(5.0)

    def test_clipped_lower_at_minus_5(self):
        """Age 0, avg 100, std 10 => z = (0-100)/10 = -10 => clipped to -5"""
        r = _compute(
            regime_start_timestamp=100.0,
            current_timestamp=100.0,
            historical_avg_duration=100.0,
            historical_std_duration=10.0,
        )
        assert r.duration_z_score == pytest.approx(-5.0)

    def test_std_zero_uses_floor_of_1(self):
        """std=0 => std_safe=1.0; age=120, avg=100 => z=(120-100)/1=20 => clipped 5"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=120.0,
            historical_avg_duration=100.0,
            historical_std_duration=0.0,
        )
        assert r.duration_z_score == pytest.approx(5.0)

    def test_zscore_is_float(self):
        r = _compute()
        assert isinstance(r.duration_z_score, float)

    def test_exact_hand_computation(self):
        """age=150, avg=100, std=25 => z=(150-100)/25=2.0"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=150.0,
            historical_avg_duration=100.0,
            historical_std_duration=25.0,
        )
        assert r.duration_z_score == pytest.approx(2.0)


# ===================================================================
# TestTransitionAccelerationFlag
# ===================================================================

class TestTransitionAccelerationFlag:
    def test_zscore_below_threshold_no_flag(self):
        """z=1.0 < 2.0 => False"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=120.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.transition_acceleration_flag is False

    def test_zscore_at_threshold_flag_set(self):
        """z=2.0 >= 2.0 => True"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=140.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.transition_acceleration_flag is True

    def test_zscore_above_threshold_flag_set(self):
        """z=3.0 >= 2.0 => True"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=160.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.transition_acceleration_flag is True

    def test_negative_zscore_at_threshold_flag_set(self):
        """z=-2.0 => |z|=2.0 >= 2.0 => True"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=60.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.transition_acceleration_flag is True

    def test_negative_zscore_below_threshold_no_flag(self):
        """z=-1.5 => |z|=1.5 < 2.0 => False"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=70.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.transition_acceleration_flag is False

    def test_zscore_zero_no_flag(self):
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=100.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.transition_acceleration_flag is False

    def test_just_below_threshold_no_flag(self):
        """z=1.99 < 2.0 => False"""
        # age = avg + z*std = 100 + 1.99*20 = 139.8
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=139.8,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.transition_acceleration_flag is False

    def test_flag_is_bool(self):
        r = _compute()
        assert isinstance(r.transition_acceleration_flag, bool)


# ===================================================================
# TestComputeDeterminism
# ===================================================================

class TestComputeDeterminism:
    def test_identical_inputs_identical_outputs(self):
        m = _model()
        kwargs = dict(
            regime_start_timestamp=500.0,
            current_timestamp=750.0,
            historical_avg_duration=200.0,
            historical_std_duration=30.0,
        )
        r1 = m.compute(**kwargs)
        r2 = m.compute(**kwargs)
        assert r1 == r2

    def test_different_instances_same_result(self):
        kwargs = dict(
            regime_start_timestamp=500.0,
            current_timestamp=750.0,
            historical_avg_duration=200.0,
            historical_std_duration=30.0,
        )
        r1 = RegimeDurationModel().compute(**kwargs)
        r2 = RegimeDurationModel().compute(**kwargs)
        assert r1 == r2

    def test_bitwise_identical_fields(self):
        kwargs = dict(
            regime_start_timestamp=0.0,
            current_timestamp=150.0,
            historical_avg_duration=100.0,
            historical_std_duration=25.0,
        )
        r1 = _model().compute(**kwargs)
        r2 = _model().compute(**kwargs)
        assert r1.regime_age_ratio == r2.regime_age_ratio
        assert r1.duration_z_score == r2.duration_z_score
        assert r1.transition_acceleration_flag == r2.transition_acceleration_flag


# ===================================================================
# TestComputeEdgeCases
# ===================================================================

class TestComputeEdgeCases:
    def test_very_large_timestamps(self):
        r = _compute(
            regime_start_timestamp=1e12,
            current_timestamp=1e12 + 100.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.regime_age_ratio == pytest.approx(1.0)

    def test_very_small_avg_duration(self):
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=10.0,
            historical_avg_duration=0.001,
            historical_std_duration=0.0001,
        )
        assert r.regime_age_ratio == 5.0  # clipped
        assert r.duration_z_score == 5.0  # clipped

    def test_very_large_std_no_flag(self):
        """Large std => small z-score => no flag"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=200.0,
            historical_avg_duration=100.0,
            historical_std_duration=10000.0,
        )
        assert r.transition_acceleration_flag is False

    def test_std_exactly_one(self):
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=103.0,
            historical_avg_duration=100.0,
            historical_std_duration=1.0,
        )
        assert r.duration_z_score == pytest.approx(3.0)

    def test_age_exactly_zero(self):
        r = _compute(
            regime_start_timestamp=500.0,
            current_timestamp=500.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.regime_age_ratio == 0.0
        assert r.duration_z_score == pytest.approx(-5.0)  # (0-100)/20=-5


# ===================================================================
# TestHandComputations
# ===================================================================

class TestHandComputations:
    """Verify against manually computed expected values."""

    def test_case_normal(self):
        """age=100, avg=100, std=20 => ratio=1.0, z=0.0, flag=False"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=100.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.regime_age_ratio == pytest.approx(1.0)
        assert r.duration_z_score == pytest.approx(0.0)
        assert r.transition_acceleration_flag is False

    def test_case_stressed(self):
        """age=200, avg=100, std=25 => ratio=2.0, z=(200-100)/25=4.0, flag=True"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=200.0,
            historical_avg_duration=100.0,
            historical_std_duration=25.0,
        )
        assert r.regime_age_ratio == pytest.approx(2.0)
        assert r.duration_z_score == pytest.approx(4.0)
        assert r.transition_acceleration_flag is True

    def test_case_young_regime(self):
        """age=30, avg=100, std=20 => ratio=0.3, z=(30-100)/20=-3.5, flag=True"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=30.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.regime_age_ratio == pytest.approx(0.3)
        assert r.duration_z_score == pytest.approx(-3.5)
        assert r.transition_acceleration_flag is True

    def test_case_borderline(self):
        """age=140, avg=100, std=20 => ratio=1.4, z=(140-100)/20=2.0, flag=True"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=140.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.regime_age_ratio == pytest.approx(1.4)
        assert r.duration_z_score == pytest.approx(2.0)
        assert r.transition_acceleration_flag is True

    def test_case_just_under_borderline(self):
        """age=139, avg=100, std=20 => ratio=1.39, z=(139-100)/20=1.95, flag=False"""
        r = _compute(
            regime_start_timestamp=0.0,
            current_timestamp=139.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        assert r.regime_age_ratio == pytest.approx(1.39)
        assert r.duration_z_score == pytest.approx(1.95)
        assert r.transition_acceleration_flag is False


# ===================================================================
# TestModelStateless
# ===================================================================

class TestModelStateless:
    def test_no_instance_state_mutation(self):
        m = _model()
        m.compute(
            regime_start_timestamp=0.0,
            current_timestamp=100.0,
            historical_avg_duration=100.0,
            historical_std_duration=20.0,
        )
        # Model has no instance attributes beyond class-level constant
        assert not hasattr(m, '_records')
        assert not hasattr(m, '_cache')

    def test_multiple_calls_independent(self):
        m = _model()
        r1 = m.compute(0.0, 100.0, 100.0, 20.0)
        r2 = m.compute(0.0, 200.0, 100.0, 20.0)
        assert r1.regime_age_ratio != r2.regime_age_ratio


# ===================================================================
# TestGovernanceConstraints
# ===================================================================

class TestGovernanceConstraints:
    def test_result_is_frozen_dataclass(self):
        assert RegimeDurationResult.__dataclass_params__.frozen is True

    def test_no_capital_fields(self):
        field_names = {f.name for f in RegimeDurationResult.__dataclass_fields__.values()}
        forbidden = {"capital", "pnl", "balance", "broker_id", "order_id", "account_id"}
        assert field_names.isdisjoint(forbidden)

    def test_model_has_no_mutable_state(self):
        """Model class should have no mutable instance attributes."""
        m = _model()
        instance_attrs = {k for k in m.__dict__ if not k.startswith('__')}
        assert len(instance_attrs) == 0

    def test_result_fields_correct(self):
        field_names = {f.name for f in RegimeDurationResult.__dataclass_fields__.values()}
        assert field_names == {
            "regime_age_ratio",
            "duration_z_score",
            "transition_acceleration_flag",
        }


# ===================================================================
# TestModuleAll
# ===================================================================

class TestModuleAll:
    def test_contains_duration_stress_z_limit(self):
        from jarvis.intelligence.regime_duration_model import __all__
        assert "DURATION_STRESS_Z_LIMIT" in __all__

    def test_contains_regime_duration_result(self):
        from jarvis.intelligence.regime_duration_model import __all__
        assert "RegimeDurationResult" in __all__

    def test_contains_regime_duration_model(self):
        from jarvis.intelligence.regime_duration_model import __all__
        assert "RegimeDurationModel" in __all__

    def test_all_length(self):
        from jarvis.intelligence.regime_duration_model import __all__
        assert len(__all__) == 3
