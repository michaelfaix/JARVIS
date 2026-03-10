# =============================================================================
# Tests for jarvis/core/strategy_registry.py (S26)
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
)
from jarvis.core import strategy_registry


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _make_obj(sid="TEST_001", version=STRATEGY_SCHEMA_VERSION):
    return StrategyObject(
        Strategy_ID=sid,
        Strategy_Type=StrategyType.MOMENTUM,
        Entry_Model=EntryModel("momentum_cross", 0.5, 3, 10.0),
        Exit_Model=ExitModel(2.0, 3.0, 50, True, True),
        Risk_Model=RiskModel(0.01, 0.1, 0.25, 0.3, 0.05),
        Weight_Model=WeightModel(0.3, {}, "linear", 0.05, 0.5),
        Regime_Sensitivity=RegimeSensitivity.HIGH,
        Volatility_Sensitivity=VolatilitySensitivity.CONTRACTS,
        Session_Sensitivity=SessionSensitivity.SESSION_FREE,
        Timeframe_Profile="H1",
        Expected_Holding_Duration=24,
        target_regime="TRENDING",
        asset_class_scope=["crypto"],
        version=version,
    )


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear registry before each test."""
    strategy_registry.clear()
    yield
    strategy_registry.clear()


# ---------------------------------------------------------------------------
# REGISTER
# ---------------------------------------------------------------------------

class TestRegister:
    def test_register_success(self):
        obj = _make_obj()
        strategy_registry.register(obj)
        assert strategy_registry.get("TEST_001") is obj

    def test_register_multiple(self):
        strategy_registry.register(_make_obj("A"))
        strategy_registry.register(_make_obj("B"))
        assert strategy_registry.list_ids() == ["A", "B"]

    def test_duplicate_raises(self):
        strategy_registry.register(_make_obj("DUP"))
        with pytest.raises(ValueError, match="Duplicate"):
            strategy_registry.register(_make_obj("DUP"))

    def test_version_mismatch_raises(self):
        obj = _make_obj(version="99.99.99")
        with pytest.raises(ValueError, match="Schema version mismatch"):
            strategy_registry.register(obj)

    def test_validation_failure_raises(self):
        obj = StrategyObject(
            Strategy_ID="BAD",
            Strategy_Type=StrategyType.MOMENTUM,
            Entry_Model=EntryModel("x", 0.5, 3, 10.0),
            Exit_Model=ExitModel(2.0, 3.0, 50, True, True),
            Risk_Model=RiskModel(0.05, 0.1, 0.25, 0.3, 0.05),  # base_risk > 0.02
            Weight_Model=WeightModel(0.3, {}, "linear", 0.05, 0.5),
            Regime_Sensitivity=RegimeSensitivity.HIGH,
            Volatility_Sensitivity=VolatilitySensitivity.CONTRACTS,
            Session_Sensitivity=SessionSensitivity.SESSION_FREE,
            Timeframe_Profile="H1",
            Expected_Holding_Duration=24,
            target_regime="TRENDING",
            asset_class_scope=["crypto"],
            version=STRATEGY_SCHEMA_VERSION,
        )
        with pytest.raises(ValueError, match="base_risk_per_trade"):
            strategy_registry.register(obj)


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------

class TestGet:
    def test_get_existing(self):
        obj = _make_obj("X")
        strategy_registry.register(obj)
        assert strategy_registry.get("X") is obj

    def test_get_unregistered_raises(self):
        with pytest.raises(KeyError, match="Unregistered"):
            strategy_registry.get("NONEXISTENT")


# ---------------------------------------------------------------------------
# LIST IDS
# ---------------------------------------------------------------------------

class TestListIds:
    def test_empty(self):
        assert strategy_registry.list_ids() == []

    def test_after_registrations(self):
        strategy_registry.register(_make_obj("A"))
        strategy_registry.register(_make_obj("B"))
        strategy_registry.register(_make_obj("C"))
        ids = strategy_registry.list_ids()
        assert "A" in ids
        assert "B" in ids
        assert "C" in ids
        assert len(ids) == 3


# ---------------------------------------------------------------------------
# CLEAR
# ---------------------------------------------------------------------------

class TestClear:
    def test_clear_empties_registry(self):
        strategy_registry.register(_make_obj("X"))
        assert len(strategy_registry.list_ids()) == 1
        strategy_registry.clear()
        assert len(strategy_registry.list_ids()) == 0

    def test_clear_allows_re_register(self):
        strategy_registry.register(_make_obj("X"))
        strategy_registry.clear()
        strategy_registry.register(_make_obj("X"))
        assert strategy_registry.get("X").Strategy_ID == "X"


# ---------------------------------------------------------------------------
# ISOLATION
# ---------------------------------------------------------------------------

class TestIsolation:
    def test_frozen_object_in_registry(self):
        obj = _make_obj("FROZEN")
        strategy_registry.register(obj)
        retrieved = strategy_registry.get("FROZEN")
        with pytest.raises(AttributeError):
            retrieved.Strategy_ID = "CHANGED"
