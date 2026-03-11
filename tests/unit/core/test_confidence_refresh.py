# tests/unit/core/test_confidence_refresh.py
# Coverage target: jarvis/core/confidence_refresh.py -> 95%+
# Tests all gate functions, validation, data types, and S37 constraints.

import pytest

from jarvis.core.confidence_refresh import (
    VALID_OPERATING_MODES,
    REFRESH_TRIGGER_FIELDS,
    RefreshTrigger,
    RefreshDecision,
    ConfidenceStateSnapshot,
    should_refresh_confidence,
    identify_refresh_triggers,
    evaluate_refresh,
)


# =============================================================================
# Helpers
# =============================================================================

def _snap(**kwargs) -> ConfidenceStateSnapshot:
    defaults = dict(
        regime="RISK_ON",
        risk_mode="NORMAL",
        strategy_mode="momentum",
        ood_status=False,
        meta_uncertainty=0.2,
    )
    defaults.update(kwargs)
    return ConfidenceStateSnapshot(**defaults)


# =============================================================================
# Constants
# =============================================================================

class TestConstants:
    def test_valid_operating_modes(self):
        assert VALID_OPERATING_MODES == ("historical", "live_analytical", "hybrid")

    def test_refresh_trigger_fields(self):
        assert REFRESH_TRIGGER_FIELDS == (
            "regime", "risk_mode", "strategy_mode", "ood_status", "meta_uncertainty",
        )

    def test_exactly_three_modes(self):
        assert len(VALID_OPERATING_MODES) == 3

    def test_exactly_five_trigger_fields(self):
        assert len(REFRESH_TRIGGER_FIELDS) == 5


# =============================================================================
# ConfidenceStateSnapshot
# =============================================================================

class TestConfidenceStateSnapshot:
    def test_valid_construction(self):
        s = _snap()
        assert s.regime == "RISK_ON"
        assert s.risk_mode == "NORMAL"
        assert s.strategy_mode == "momentum"
        assert s.ood_status is False
        assert s.meta_uncertainty == 0.2

    def test_frozen(self):
        s = _snap()
        with pytest.raises(AttributeError):
            s.regime = "RISK_OFF"

    def test_equality(self):
        s1 = _snap()
        s2 = _snap()
        assert s1 == s2

    def test_inequality_on_regime(self):
        s1 = _snap(regime="RISK_ON")
        s2 = _snap(regime="CRISIS")
        assert s1 != s2


# =============================================================================
# RefreshTrigger
# =============================================================================

class TestRefreshTrigger:
    def test_valid_construction(self):
        t = RefreshTrigger(field_name="regime", prev_value="RISK_ON", curr_value="RISK_OFF")
        assert t.field_name == "regime"
        assert t.prev_value == "RISK_ON"
        assert t.curr_value == "RISK_OFF"

    def test_all_valid_field_names(self):
        for name in REFRESH_TRIGGER_FIELDS:
            t = RefreshTrigger(field_name=name, prev_value="a", curr_value="b")
            assert t.field_name == name

    def test_invalid_field_name_raises(self):
        with pytest.raises(ValueError, match="field_name"):
            RefreshTrigger(field_name="invalid_field", prev_value="a", curr_value="b")

    def test_frozen(self):
        t = RefreshTrigger(field_name="regime", prev_value="a", curr_value="b")
        with pytest.raises(AttributeError):
            t.field_name = "risk_mode"


# =============================================================================
# RefreshDecision
# =============================================================================

class TestRefreshDecision:
    def test_valid_construction(self):
        d = RefreshDecision(
            should_refresh=True,
            operating_mode="historical",
            triggers=[],
            reason="batch recompute",
        )
        assert d.should_refresh is True
        assert d.operating_mode == "historical"
        assert d.triggers == []
        assert d.reason == "batch recompute"

    def test_frozen(self):
        d = RefreshDecision(
            should_refresh=False,
            operating_mode="live_analytical",
            triggers=[],
            reason="no change",
        )
        with pytest.raises(AttributeError):
            d.should_refresh = True


# =============================================================================
# should_refresh_confidence -- HISTORICAL mode
# =============================================================================

class TestShouldRefreshHistorical:
    def test_always_true_identical_states(self):
        s = _snap()
        assert should_refresh_confidence(s, s, "historical") is True

    def test_always_true_different_states(self):
        s1 = _snap(regime="RISK_ON")
        s2 = _snap(regime="CRISIS")
        assert should_refresh_confidence(s1, s2, "historical") is True

    def test_always_true_regardless_of_fields(self):
        s1 = _snap()
        s2 = _snap()
        assert should_refresh_confidence(s1, s2, "historical") is True


# =============================================================================
# should_refresh_confidence -- LIVE mode (no change = no refresh)
# =============================================================================

class TestShouldRefreshLiveNoChange:
    def test_identical_states_returns_false(self):
        s = _snap()
        assert should_refresh_confidence(s, s, "live_analytical") is False

    def test_identical_states_hybrid_returns_false(self):
        s = _snap()
        assert should_refresh_confidence(s, s, "hybrid") is False

    def test_two_equal_snapshots_returns_false(self):
        s1 = _snap()
        s2 = _snap()
        assert should_refresh_confidence(s1, s2, "live_analytical") is False


# =============================================================================
# should_refresh_confidence -- LIVE mode (state change = refresh)
# =============================================================================

class TestShouldRefreshLiveWithChange:
    def test_regime_change_triggers_refresh(self):
        s1 = _snap(regime="RISK_ON")
        s2 = _snap(regime="RISK_OFF")
        assert should_refresh_confidence(s1, s2, "live_analytical") is True

    def test_risk_mode_change_triggers_refresh(self):
        s1 = _snap(risk_mode="NORMAL")
        s2 = _snap(risk_mode="ELEVATED")
        assert should_refresh_confidence(s1, s2, "live_analytical") is True

    def test_strategy_mode_change_triggers_refresh(self):
        s1 = _snap(strategy_mode="momentum")
        s2 = _snap(strategy_mode="mean_reversion")
        assert should_refresh_confidence(s1, s2, "live_analytical") is True

    def test_ood_status_change_triggers_refresh(self):
        s1 = _snap(ood_status=False)
        s2 = _snap(ood_status=True)
        assert should_refresh_confidence(s1, s2, "live_analytical") is True

    def test_meta_uncertainty_change_triggers_refresh(self):
        s1 = _snap(meta_uncertainty=0.2)
        s2 = _snap(meta_uncertainty=0.5)
        assert should_refresh_confidence(s1, s2, "live_analytical") is True

    def test_multiple_changes_trigger_refresh(self):
        s1 = _snap(regime="RISK_ON", risk_mode="NORMAL")
        s2 = _snap(regime="CRISIS", risk_mode="CRITICAL")
        assert should_refresh_confidence(s1, s2, "hybrid") is True

    def test_all_fields_changed_triggers_refresh(self):
        s1 = _snap()
        s2 = ConfidenceStateSnapshot(
            regime="CRISIS",
            risk_mode="CRITICAL",
            strategy_mode="defensive",
            ood_status=True,
            meta_uncertainty=0.9,
        )
        assert should_refresh_confidence(s1, s2, "live_analytical") is True


# =============================================================================
# should_refresh_confidence -- S37 forbidden patterns
# =============================================================================

class TestShouldRefreshForbiddenPatterns:
    def test_tick_without_state_change_does_not_refresh(self):
        # "A tick arrives but no state has changed" -> must return False
        s = _snap()
        assert should_refresh_confidence(s, s, "live_analytical") is False

    def test_only_sequence_id_change_does_not_refresh(self):
        # "Only sequence_id incremented" -> not in compared fields -> False
        s1 = _snap()
        s2 = _snap()
        assert should_refresh_confidence(s1, s2, "hybrid") is False


# =============================================================================
# should_refresh_confidence -- validation
# =============================================================================

class TestShouldRefreshValidation:
    def test_invalid_mode_raises_value_error(self):
        s = _snap()
        with pytest.raises(ValueError, match="operating_mode"):
            should_refresh_confidence(s, s, "invalid_mode")

    def test_non_string_mode_raises_type_error(self):
        s = _snap()
        with pytest.raises(TypeError, match="operating_mode"):
            should_refresh_confidence(s, s, 42)

    def test_none_prev_state_raises_type_error(self):
        s = _snap()
        with pytest.raises(TypeError, match="prev_state"):
            should_refresh_confidence(None, s, "historical")

    def test_none_curr_state_raises_type_error(self):
        s = _snap()
        with pytest.raises(TypeError, match="curr_state"):
            should_refresh_confidence(s, None, "historical")

    def test_missing_field_raises_attribute_error(self):
        class Incomplete:
            regime = "RISK_ON"
        s = _snap()
        with pytest.raises(AttributeError, match="risk_mode"):
            should_refresh_confidence(Incomplete(), s, "live_analytical")


# =============================================================================
# identify_refresh_triggers
# =============================================================================

class TestIdentifyRefreshTriggers:
    def test_no_changes_returns_empty(self):
        s = _snap()
        triggers = identify_refresh_triggers(s, s)
        assert triggers == []

    def test_single_change_returns_one_trigger(self):
        s1 = _snap(regime="RISK_ON")
        s2 = _snap(regime="CRISIS")
        triggers = identify_refresh_triggers(s1, s2)
        assert len(triggers) == 1
        assert triggers[0].field_name == "regime"
        assert triggers[0].prev_value == "RISK_ON"
        assert triggers[0].curr_value == "CRISIS"

    def test_multiple_changes_returns_multiple_triggers(self):
        s1 = _snap(regime="RISK_ON", ood_status=False)
        s2 = _snap(regime="RISK_OFF", ood_status=True)
        triggers = identify_refresh_triggers(s1, s2)
        assert len(triggers) == 2
        field_names = {t.field_name for t in triggers}
        assert field_names == {"regime", "ood_status"}

    def test_all_five_changes(self):
        s1 = _snap()
        s2 = ConfidenceStateSnapshot(
            regime="CRISIS",
            risk_mode="CRITICAL",
            strategy_mode="defensive",
            ood_status=True,
            meta_uncertainty=0.9,
        )
        triggers = identify_refresh_triggers(s1, s2)
        assert len(triggers) == 5
        field_names = {t.field_name for t in triggers}
        assert field_names == set(REFRESH_TRIGGER_FIELDS)

    def test_meta_uncertainty_float_comparison(self):
        s1 = _snap(meta_uncertainty=0.20)
        s2 = _snap(meta_uncertainty=0.20)
        assert identify_refresh_triggers(s1, s2) == []

    def test_meta_uncertainty_slight_change(self):
        s1 = _snap(meta_uncertainty=0.200)
        s2 = _snap(meta_uncertainty=0.201)
        triggers = identify_refresh_triggers(s1, s2)
        assert len(triggers) == 1
        assert triggers[0].field_name == "meta_uncertainty"

    def test_none_prev_raises(self):
        with pytest.raises(TypeError, match="prev_state"):
            identify_refresh_triggers(None, _snap())

    def test_none_curr_raises(self):
        with pytest.raises(TypeError, match="curr_state"):
            identify_refresh_triggers(_snap(), None)

    def test_trigger_order_matches_field_order(self):
        s1 = _snap(regime="A", risk_mode="B")
        s2 = _snap(regime="X", risk_mode="Y")
        triggers = identify_refresh_triggers(s1, s2)
        assert triggers[0].field_name == "regime"
        assert triggers[1].field_name == "risk_mode"


# =============================================================================
# evaluate_refresh
# =============================================================================

class TestEvaluateRefresh:
    def test_historical_always_refreshes(self):
        s = _snap()
        d = evaluate_refresh(s, s, "historical")
        assert d.should_refresh is True
        assert d.operating_mode == "historical"
        assert d.triggers == []
        assert "batch recompute" in d.reason

    def test_live_no_change(self):
        s = _snap()
        d = evaluate_refresh(s, s, "live_analytical")
        assert d.should_refresh is False
        assert d.triggers == []
        assert "no analytical state change" in d.reason

    def test_live_with_change(self):
        s1 = _snap(regime="RISK_ON")
        s2 = _snap(regime="CRISIS")
        d = evaluate_refresh(s1, s2, "live_analytical")
        assert d.should_refresh is True
        assert len(d.triggers) == 1
        assert d.triggers[0].field_name == "regime"
        assert "regime" in d.reason

    def test_hybrid_with_multiple_changes(self):
        s1 = _snap(risk_mode="NORMAL", ood_status=False)
        s2 = _snap(risk_mode="CRITICAL", ood_status=True)
        d = evaluate_refresh(s1, s2, "hybrid")
        assert d.should_refresh is True
        assert len(d.triggers) == 2
        assert "risk_mode" in d.reason
        assert "ood_status" in d.reason

    def test_invalid_mode_raises(self):
        s = _snap()
        with pytest.raises(ValueError, match="operating_mode"):
            evaluate_refresh(s, s, "bad_mode")

    def test_none_state_raises(self):
        with pytest.raises(TypeError):
            evaluate_refresh(None, _snap(), "historical")


# =============================================================================
# Duck typing: any object with the 5 fields works
# =============================================================================

class TestDuckTyping:
    def test_plain_object_with_fields_works(self):
        class State:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        s1 = State(regime="A", risk_mode="B", strategy_mode="C",
                    ood_status=False, meta_uncertainty=0.1)
        s2 = State(regime="A", risk_mode="B", strategy_mode="C",
                    ood_status=False, meta_uncertainty=0.1)
        assert should_refresh_confidence(s1, s2, "live_analytical") is False

    def test_plain_object_with_change(self):
        class State:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        s1 = State(regime="A", risk_mode="B", strategy_mode="C",
                    ood_status=False, meta_uncertainty=0.1)
        s2 = State(regime="X", risk_mode="B", strategy_mode="C",
                    ood_status=False, meta_uncertainty=0.1)
        assert should_refresh_confidence(s1, s2, "hybrid") is True

    def test_dict_does_not_work(self):
        # dicts don't have attribute access -> AttributeError
        with pytest.raises(AttributeError):
            should_refresh_confidence(
                {"regime": "A"}, _snap(), "live_analytical"
            )


# =============================================================================
# Determinism (DET-07)
# =============================================================================

class TestDeterminism:
    def test_same_inputs_same_output_live(self):
        s1 = _snap(regime="RISK_ON")
        s2 = _snap(regime="CRISIS")
        r1 = should_refresh_confidence(s1, s2, "live_analytical")
        r2 = should_refresh_confidence(s1, s2, "live_analytical")
        assert r1 == r2 == True

    def test_same_inputs_same_output_no_change(self):
        s = _snap()
        r1 = should_refresh_confidence(s, s, "hybrid")
        r2 = should_refresh_confidence(s, s, "hybrid")
        assert r1 == r2 == False

    def test_evaluate_refresh_deterministic(self):
        s1 = _snap()
        s2 = _snap(meta_uncertainty=0.9)
        d1 = evaluate_refresh(s1, s2, "live_analytical")
        d2 = evaluate_refresh(s1, s2, "live_analytical")
        assert d1.should_refresh == d2.should_refresh
        assert d1.reason == d2.reason
        assert len(d1.triggers) == len(d2.triggers)
