# =============================================================================
# Tests for jarvis/core/strategy_schema.py (S26)
# =============================================================================

import pytest

from jarvis.core.strategy_schema import (
    STRATEGY_SCHEMA_VERSION,
    EntryModel,
    ExitModel,
    RegimeSensitivity,
    RiskModel,
    SessionSensitivity,
    StrategyObject,
    StrategyType,
    VolatilitySensitivity,
    WeightModel,
    apply_adaptive_weight,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _entry():
    return EntryModel(
        signal_type="momentum_cross",
        signal_threshold=0.5,
        confirmation_bars=3,
        max_entry_spread_bps=10.0,
    )


def _exit():
    return ExitModel(
        stop_loss_atr_multiple=2.0,
        take_profit_atr_multiple=3.0,
        time_exit_bars=50,
        trailing_stop=True,
        regime_exit=True,
    )


def _risk(base_risk=0.01, confidence_floor=0.3):
    return RiskModel(
        base_risk_per_trade=base_risk,
        max_position_size=0.1,
        kelly_fraction=0.25,
        confidence_floor=confidence_floor,
        var_contribution_cap=0.05,
    )


def _weight(base=0.3, min_w=0.05, max_w=0.5):
    return WeightModel(
        base_weight=base,
        regime_weight_map={"TRENDING": 0.4, "SHOCK": 0.1},
        volatility_scalar_fn="linear",
        min_weight=min_w,
        max_weight=max_w,
    )


def _strategy(**overrides):
    defaults = dict(
        Strategy_ID="MOM_BTC_H1",
        Strategy_Type=StrategyType.MOMENTUM,
        Entry_Model=_entry(),
        Exit_Model=_exit(),
        Risk_Model=_risk(),
        Weight_Model=_weight(),
        Regime_Sensitivity=RegimeSensitivity.HIGH,
        Volatility_Sensitivity=VolatilitySensitivity.CONTRACTS,
        Session_Sensitivity=SessionSensitivity.SESSION_FREE,
        Timeframe_Profile="H1",
        Expected_Holding_Duration=24,
        target_regime="TRENDING",
        asset_class_scope=["crypto"],
        version=STRATEGY_SCHEMA_VERSION,
    )
    defaults.update(overrides)
    return StrategyObject(**defaults)


# ---------------------------------------------------------------------------
# SCHEMA VERSION
# ---------------------------------------------------------------------------

class TestSchemaVersion:
    def test_version_is_1_0_0(self):
        assert STRATEGY_SCHEMA_VERSION == "1.0.0"


# ---------------------------------------------------------------------------
# ENUMS
# ---------------------------------------------------------------------------

class TestEnums:
    def test_strategy_types(self):
        assert len(StrategyType) == 7
        assert StrategyType.MOMENTUM.value == "momentum"
        assert StrategyType.DEFENSIVE.value == "defensive"

    def test_regime_sensitivity(self):
        assert len(RegimeSensitivity) == 3
        assert RegimeSensitivity.HIGH.value == "high"

    def test_volatility_sensitivity(self):
        assert len(VolatilitySensitivity) == 3
        assert VolatilitySensitivity.EXPANDS.value == "expands"

    def test_session_sensitivity(self):
        assert len(SessionSensitivity) == 3
        assert SessionSensitivity.SESSION_FREE.value == "session_free"


# ---------------------------------------------------------------------------
# SUB-MODELS
# ---------------------------------------------------------------------------

class TestSubModels:
    def test_entry_model(self):
        e = _entry()
        assert e.signal_type == "momentum_cross"
        assert e.confirmation_bars == 3

    def test_exit_model(self):
        ex = _exit()
        assert ex.stop_loss_atr_multiple == 2.0
        assert ex.trailing_stop is True

    def test_risk_model(self):
        r = _risk()
        assert r.base_risk_per_trade == 0.01
        assert r.kelly_fraction == 0.25

    def test_weight_model(self):
        w = _weight()
        assert w.base_weight == 0.3
        assert w.regime_weight_map["TRENDING"] == 0.4


# ---------------------------------------------------------------------------
# STRATEGY OBJECT
# ---------------------------------------------------------------------------

class TestStrategyObject:
    def test_creation(self):
        obj = _strategy()
        assert obj.Strategy_ID == "MOM_BTC_H1"
        assert obj.Strategy_Type == StrategyType.MOMENTUM

    def test_frozen(self):
        obj = _strategy()
        with pytest.raises(AttributeError):
            obj.Strategy_ID = "CHANGED"

    def test_version_field(self):
        obj = _strategy()
        assert obj.version == STRATEGY_SCHEMA_VERSION

    def test_asset_class_scope(self):
        obj = _strategy()
        assert obj.asset_class_scope == ["crypto"]


# ---------------------------------------------------------------------------
# VALIDATE
# ---------------------------------------------------------------------------

class TestValidate:
    def test_valid_object_passes(self):
        obj = _strategy()
        assert obj.validate() is True

    def test_base_risk_zero_fails(self):
        obj = _strategy(Risk_Model=_risk(base_risk=0.0))
        with pytest.raises(ValueError, match="base_risk_per_trade"):
            obj.validate()

    def test_base_risk_negative_fails(self):
        obj = _strategy(Risk_Model=_risk(base_risk=-0.01))
        with pytest.raises(ValueError, match="base_risk_per_trade"):
            obj.validate()

    def test_base_risk_above_002_fails(self):
        obj = _strategy(Risk_Model=_risk(base_risk=0.03))
        with pytest.raises(ValueError, match="base_risk_per_trade"):
            obj.validate()

    def test_base_risk_exactly_002_passes(self):
        obj = _strategy(Risk_Model=_risk(base_risk=0.02))
        assert obj.validate() is True

    def test_confidence_floor_negative_fails(self):
        obj = _strategy(Risk_Model=_risk(confidence_floor=-0.1))
        with pytest.raises(ValueError, match="confidence_floor"):
            obj.validate()

    def test_confidence_floor_above_1_fails(self):
        obj = _strategy(Risk_Model=_risk(confidence_floor=1.1))
        with pytest.raises(ValueError, match="confidence_floor"):
            obj.validate()

    def test_base_weight_negative_fails(self):
        obj = _strategy(Weight_Model=_weight(base=-0.1, min_w=-0.2))
        with pytest.raises(ValueError, match="base_weight"):
            obj.validate()

    def test_base_weight_above_1_fails(self):
        obj = _strategy(Weight_Model=_weight(base=1.1, max_w=1.2))
        with pytest.raises(ValueError, match="base_weight"):
            obj.validate()

    def test_weight_bounds_inconsistent_fails(self):
        # min_weight > base_weight
        obj = _strategy(Weight_Model=_weight(base=0.3, min_w=0.5, max_w=0.6))
        with pytest.raises(ValueError, match="weight bounds"):
            obj.validate()

    def test_weight_bounds_max_below_base_fails(self):
        obj = _strategy(Weight_Model=_weight(base=0.5, min_w=0.1, max_w=0.3))
        with pytest.raises(ValueError, match="weight bounds"):
            obj.validate()

    def test_expected_holding_zero_fails(self):
        obj = _strategy(Expected_Holding_Duration=0)
        with pytest.raises(ValueError, match="Expected_Holding_Duration"):
            obj.validate()

    def test_expected_holding_negative_fails(self):
        obj = _strategy(Expected_Holding_Duration=-5)
        with pytest.raises(ValueError, match="Expected_Holding_Duration"):
            obj.validate()


# ---------------------------------------------------------------------------
# APPLY ADAPTIVE WEIGHT
# ---------------------------------------------------------------------------

class TestApplyAdaptiveWeight:
    def test_regime_in_map(self):
        obj = _strategy()
        w = apply_adaptive_weight(obj, "TRENDING")
        assert w == pytest.approx(0.4)

    def test_regime_not_in_map_uses_base(self):
        obj = _strategy()
        w = apply_adaptive_weight(obj, "SOME_OTHER")
        assert w == pytest.approx(0.3)

    def test_clipped_to_min(self):
        obj = _strategy(Weight_Model=_weight(base=0.3, min_w=0.2, max_w=0.5))
        # SHOCK -> 0.1, but min_w = 0.2
        w = apply_adaptive_weight(obj, "SHOCK")
        assert w == pytest.approx(0.2)

    def test_clipped_to_max(self):
        wm = WeightModel(
            base_weight=0.3,
            regime_weight_map={"BULL": 0.9},
            volatility_scalar_fn="linear",
            min_weight=0.05,
            max_weight=0.5,
        )
        obj = _strategy(Weight_Model=wm)
        w = apply_adaptive_weight(obj, "BULL")
        assert w == pytest.approx(0.5)

    def test_base_weight_within_bounds(self):
        obj = _strategy()
        w = apply_adaptive_weight(obj, "NEUTRAL")
        assert 0.05 <= w <= 0.5
