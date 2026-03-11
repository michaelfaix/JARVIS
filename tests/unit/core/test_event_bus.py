# tests/unit/core/test_event_bus.py
# Coverage target: jarvis/core/event_bus.py -> 95%+
# Tests all event types, validation, immutability, and forbidden patterns.

import pytest

from jarvis.core.event_bus import (
    EventType,
    BaseEvent,
    MarketDataEvent,
    RegimeChangeEvent,
    FailureModeEvent,
    ExposureEvent,
    StrategyWeightChangeEvent,
    ConfidenceUpdateEvent,
    VALID_FAILURE_MODE_CODES,
    VALID_DATA_SOURCES,
)


# =============================================================================
# Helpers
# =============================================================================

def _base(**kwargs):
    defaults = dict(
        event_id="evt-001",
        event_type=EventType.MARKET_DATA,
        timestamp=1000.0,
        sequence_id=1,
    )
    defaults.update(kwargs)
    return BaseEvent(**defaults)


def _market(**kwargs):
    defaults = dict(
        event_id="evt-m01",
        event_type=EventType.MARKET_DATA,
        timestamp=1000.0,
        sequence_id=1,
        symbol="BTC-USD",
        timeframe="1h",
        close=65000.0,
        quality_score=0.95,
    )
    defaults.update(kwargs)
    return MarketDataEvent(**defaults)


def _regime(**kwargs):
    defaults = dict(
        event_id="evt-r01",
        event_type=EventType.REGIME_CHANGE,
        timestamp=1000.0,
        sequence_id=1,
        from_regime="RISK_ON",
        to_regime="RISK_OFF",
        confidence=0.8,
    )
    defaults.update(kwargs)
    return RegimeChangeEvent(**defaults)


def _failure(**kwargs):
    defaults = dict(
        event_id="evt-f01",
        event_type=EventType.FAILURE_MODE,
        timestamp=1000.0,
        sequence_id=1,
        failure_mode_code="FM-01",
        activated=True,
        trigger_condition="regime_confidence < 0.40",
        confidence_impact={"R": -0.40},
    )
    defaults.update(kwargs)
    return FailureModeEvent(**defaults)


def _exposure(**kwargs):
    defaults = dict(
        event_id="evt-e01",
        event_type=EventType.EXPOSURE,
        timestamp=1000.0,
        sequence_id=1,
        prior_gross_exposure=100000.0,
        current_gross_exposure=120000.0,
        trigger_source="risk_engine",
    )
    defaults.update(kwargs)
    return ExposureEvent(**defaults)


def _strategy(**kwargs):
    defaults = dict(
        event_id="evt-s01",
        event_type=EventType.STRATEGY_WEIGHT,
        timestamp=1000.0,
        sequence_id=1,
        strategy_id="momentum_v1",
        prior_weight=0.5,
        new_weight=0.7,
        regime_trigger="RISK_ON",
    )
    defaults.update(kwargs)
    return StrategyWeightChangeEvent(**defaults)


def _confidence(**kwargs):
    defaults = dict(
        event_id="evt-c01",
        event_type=EventType.CONFIDENCE_UPDATE,
        timestamp=1000.0,
        sequence_id=1,
        prior_mu=0.6,
        new_mu=0.55,
        prior_Q=0.7,
        new_Q=0.65,
        prior_U=0.2,
        new_U=0.25,
        trigger="regime_change",
    )
    defaults.update(kwargs)
    return ConfidenceUpdateEvent(**defaults)


# =============================================================================
# EventType enum
# =============================================================================

class TestEventType:
    def test_all_members_present(self):
        members = {e.value for e in EventType}
        assert members == {
            "market_data", "regime_change", "failure_mode",
            "exposure", "strategy_weight_change", "confidence_update",
        }

    def test_exactly_six_members(self):
        assert len(EventType) == 6

    def test_str_inheritance(self):
        assert isinstance(EventType.MARKET_DATA, str)
        assert EventType.MARKET_DATA == "market_data"


# =============================================================================
# Constants
# =============================================================================

class TestConstants:
    def test_valid_failure_mode_codes(self):
        assert VALID_FAILURE_MODE_CODES == (
            "FM-01", "FM-02", "FM-03", "FM-04", "FM-05", "FM-06",
        )

    def test_valid_data_sources(self):
        assert VALID_DATA_SOURCES == (
            "historical", "live", "hybrid_backfill", "hybrid_live",
        )


# =============================================================================
# BaseEvent
# =============================================================================

class TestBaseEvent:
    def test_valid_construction(self):
        e = _base()
        assert e.event_id == "evt-001"
        assert e.event_type == EventType.MARKET_DATA
        assert e.timestamp == 1000.0
        assert e.sequence_id == 1
        assert e.asset_id is None

    def test_with_asset_id(self):
        e = _base(asset_id="BTC-USD")
        assert e.asset_id == "BTC-USD"

    def test_frozen(self):
        e = _base()
        with pytest.raises(AttributeError):
            e.event_id = "new-id"

    def test_empty_event_id_raises(self):
        with pytest.raises(ValueError, match="event_id"):
            _base(event_id="")

    def test_none_event_id_raises(self):
        with pytest.raises(ValueError, match="event_id"):
            _base(event_id=None)

    def test_int_event_id_raises(self):
        with pytest.raises(ValueError, match="event_id"):
            _base(event_id=123)

    def test_invalid_event_type_raises(self):
        with pytest.raises(TypeError, match="EventType"):
            _base(event_type="market_data")

    def test_float_sequence_id_raises(self):
        with pytest.raises(TypeError, match="sequence_id"):
            _base(sequence_id=1.0)

    def test_bool_sequence_id_raises(self):
        with pytest.raises(TypeError, match="sequence_id"):
            _base(sequence_id=True)

    def test_negative_sequence_id_raises(self):
        with pytest.raises(ValueError, match="sequence_id"):
            _base(sequence_id=-1)

    def test_zero_sequence_id_valid(self):
        e = _base(sequence_id=0)
        assert e.sequence_id == 0


# =============================================================================
# MarketDataEvent
# =============================================================================

class TestMarketDataEvent:
    def test_valid_construction(self):
        e = _market()
        assert e.symbol == "BTC-USD"
        assert e.timeframe == "1h"
        assert e.close == 65000.0
        assert e.quality_score == 0.95
        assert e.gap_detected is False
        assert e.is_stale is False
        assert e.data_source == "historical"

    def test_all_data_sources(self):
        for ds in VALID_DATA_SOURCES:
            e = _market(data_source=ds)
            assert e.data_source == ds

    def test_invalid_data_source_raises(self):
        with pytest.raises(ValueError, match="data_source"):
            _market(data_source="broker_feed")

    def test_wrong_event_type_raises(self):
        with pytest.raises(ValueError, match="MARKET_DATA"):
            _market(event_type=EventType.REGIME_CHANGE)

    def test_gap_detected_true(self):
        e = _market(gap_detected=True, is_stale=True)
        assert e.gap_detected is True
        assert e.is_stale is True

    def test_is_base_event(self):
        e = _market()
        assert isinstance(e, BaseEvent)

    def test_frozen(self):
        e = _market()
        with pytest.raises(AttributeError):
            e.close = 70000.0


# =============================================================================
# RegimeChangeEvent
# =============================================================================

class TestRegimeChangeEvent:
    def test_valid_construction(self):
        e = _regime()
        assert e.from_regime == "RISK_ON"
        assert e.to_regime == "RISK_OFF"
        assert e.confidence == 0.8
        assert e.transition_flag is True

    def test_wrong_event_type_raises(self):
        with pytest.raises(ValueError, match="REGIME_CHANGE"):
            _regime(event_type=EventType.MARKET_DATA)

    def test_transition_flag_false(self):
        e = _regime(transition_flag=False)
        assert e.transition_flag is False

    def test_is_base_event(self):
        assert isinstance(_regime(), BaseEvent)


# =============================================================================
# FailureModeEvent
# =============================================================================

class TestFailureModeEvent:
    def test_valid_construction(self):
        e = _failure()
        assert e.failure_mode_code == "FM-01"
        assert e.activated is True
        assert e.trigger_condition == "regime_confidence < 0.40"
        assert e.confidence_impact == {"R": -0.40}

    def test_all_valid_failure_codes(self):
        for code in VALID_FAILURE_MODE_CODES:
            e = _failure(failure_mode_code=code)
            assert e.failure_mode_code == code

    def test_invalid_failure_code_raises(self):
        with pytest.raises(ValueError, match="failure_mode_code"):
            _failure(failure_mode_code="FM-99")

    def test_empty_failure_code_raises(self):
        with pytest.raises(ValueError, match="failure_mode_code"):
            _failure(failure_mode_code="")

    def test_wrong_event_type_raises(self):
        with pytest.raises(ValueError, match="FAILURE_MODE"):
            _failure(event_type=EventType.EXPOSURE)

    def test_deactivation_event(self):
        e = _failure(activated=False)
        assert e.activated is False

    def test_is_base_event(self):
        assert isinstance(_failure(), BaseEvent)


# =============================================================================
# ExposureEvent
# =============================================================================

class TestExposureEvent:
    def test_valid_construction(self):
        e = _exposure()
        assert e.prior_gross_exposure == 100000.0
        assert e.current_gross_exposure == 120000.0
        assert e.prior_net_exposure == 0.0
        assert e.current_net_exposure == 0.0
        assert e.trigger_source == "risk_engine"

    def test_wrong_event_type_raises(self):
        with pytest.raises(ValueError, match="EXPOSURE"):
            _exposure(event_type=EventType.MARKET_DATA)

    def test_negative_exposure_valid(self):
        e = _exposure(prior_net_exposure=-50000.0, current_net_exposure=-30000.0)
        assert e.prior_net_exposure == -50000.0

    def test_is_base_event(self):
        assert isinstance(_exposure(), BaseEvent)


# =============================================================================
# StrategyWeightChangeEvent
# =============================================================================

class TestStrategyWeightChangeEvent:
    def test_valid_construction(self):
        e = _strategy()
        assert e.strategy_id == "momentum_v1"
        assert e.prior_weight == 0.5
        assert e.new_weight == 0.7
        assert e.regime_trigger == "RISK_ON"

    def test_wrong_event_type_raises(self):
        with pytest.raises(ValueError, match="STRATEGY_WEIGHT"):
            _strategy(event_type=EventType.CONFIDENCE_UPDATE)

    def test_is_base_event(self):
        assert isinstance(_strategy(), BaseEvent)


# =============================================================================
# ConfidenceUpdateEvent
# =============================================================================

class TestConfidenceUpdateEvent:
    def test_valid_construction(self):
        e = _confidence()
        assert e.prior_mu == 0.6
        assert e.new_mu == 0.55
        assert e.prior_Q == 0.7
        assert e.new_Q == 0.65
        assert e.prior_U == 0.2
        assert e.new_U == 0.25
        assert e.trigger == "regime_change"

    def test_wrong_event_type_raises(self):
        with pytest.raises(ValueError, match="CONFIDENCE_UPDATE"):
            _confidence(event_type=EventType.REGIME_CHANGE)

    def test_is_base_event(self):
        assert isinstance(_confidence(), BaseEvent)


# =============================================================================
# Immutability across all types
# =============================================================================

class TestImmutability:
    def test_base_event_frozen(self):
        with pytest.raises(AttributeError):
            _base().event_id = "x"

    def test_market_data_event_frozen(self):
        with pytest.raises(AttributeError):
            _market().close = 1.0

    def test_regime_change_event_frozen(self):
        with pytest.raises(AttributeError):
            _regime().confidence = 0.0

    def test_failure_mode_event_frozen(self):
        with pytest.raises(AttributeError):
            _failure().activated = False

    def test_exposure_event_frozen(self):
        with pytest.raises(AttributeError):
            _exposure().trigger_source = "x"

    def test_strategy_weight_event_frozen(self):
        with pytest.raises(AttributeError):
            _strategy().new_weight = 0.0

    def test_confidence_update_event_frozen(self):
        with pytest.raises(AttributeError):
            _confidence().new_mu = 0.0


# =============================================================================
# Equality and identity
# =============================================================================

class TestEquality:
    def test_same_fields_are_equal(self):
        e1 = _base()
        e2 = _base()
        assert e1 == e2

    def test_different_fields_are_not_equal(self):
        e1 = _base(event_id="a")
        e2 = _base(event_id="b")
        assert e1 != e2

    def test_different_types_not_equal(self):
        b = _base(event_type=EventType.MARKET_DATA)
        m = _market(event_id="evt-001", sequence_id=1, timestamp=1000.0)
        assert type(b) != type(m)
