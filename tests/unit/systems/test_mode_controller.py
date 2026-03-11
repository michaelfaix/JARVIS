# =============================================================================
# tests/unit/systems/test_mode_controller.py
# Tests for jarvis/systems/mode_controller.py
# =============================================================================

import pytest

from jarvis.systems.mode_controller import (
    OperationalMode,
    TRANSITION_TABLE,
    VALID_TRIGGERS,
    ModeTransitionResult,
    ModeController,
)


# =============================================================================
# SECTION 1 -- ENUM
# =============================================================================

class TestOperationalMode:
    def test_four_modes(self):
        assert len(OperationalMode) == 4

    def test_normal(self):
        assert OperationalMode.NORMAL.value == "normal"

    def test_defensive(self):
        assert OperationalMode.DEFENSIVE.value == "defensive"

    def test_hold(self):
        assert OperationalMode.HOLD.value == "hold"

    def test_emergency(self):
        assert OperationalMode.EMERGENCY.value == "emergency"

    def test_unique(self):
        values = [m.value for m in OperationalMode]
        assert len(set(values)) == 4


# =============================================================================
# SECTION 2 -- TRANSITION TABLE STRUCTURE
# =============================================================================

class TestTransitionTable:
    def test_ten_transitions(self):
        assert len(TRANSITION_TABLE) == 10

    def test_all_keys_are_tuples(self):
        for key in TRANSITION_TABLE:
            assert isinstance(key, tuple)
            assert len(key) == 2
            assert isinstance(key[0], OperationalMode)
            assert isinstance(key[1], str)

    def test_all_values_are_modes(self):
        for val in TRANSITION_TABLE.values():
            assert isinstance(val, OperationalMode)

    def test_normal_has_four_transitions(self):
        normal_keys = [k for k in TRANSITION_TABLE if k[0] == OperationalMode.NORMAL]
        assert len(normal_keys) == 4

    def test_defensive_has_three_transitions(self):
        def_keys = [k for k in TRANSITION_TABLE if k[0] == OperationalMode.DEFENSIVE]
        assert len(def_keys) == 3

    def test_hold_has_two_transitions(self):
        hold_keys = [k for k in TRANSITION_TABLE if k[0] == OperationalMode.HOLD]
        assert len(hold_keys) == 2

    def test_emergency_has_one_transition(self):
        em_keys = [k for k in TRANSITION_TABLE if k[0] == OperationalMode.EMERGENCY]
        assert len(em_keys) == 1


# =============================================================================
# SECTION 3 -- VALID TRIGGERS
# =============================================================================

class TestValidTriggers:
    def test_nine_triggers(self):
        assert len(VALID_TRIGGERS) == 9

    def test_expected_triggers(self):
        expected = {
            "ood_detected", "ood_cleared", "high_uncertainty",
            "uncertainty_spike", "drawdown_warning", "drawdown_exceeded",
            "critical_failure", "stability_restored", "manual_recovery",
        }
        assert VALID_TRIGGERS == expected

    def test_frozen(self):
        assert isinstance(VALID_TRIGGERS, frozenset)


# =============================================================================
# SECTION 4 -- TRANSITION RESULT DATACLASS
# =============================================================================

class TestModeTransitionResult:
    def test_frozen(self):
        r = ModeTransitionResult(
            OperationalMode.NORMAL, "ood_detected",
            OperationalMode.DEFENSIVE, True, "ok"
        )
        with pytest.raises(AttributeError):
            r.accepted = False

    def test_fields(self):
        r = ModeTransitionResult(
            previous_mode=OperationalMode.NORMAL,
            trigger="ood_detected",
            new_mode=OperationalMode.DEFENSIVE,
            accepted=True,
            reason="NORMAL -> DEFENSIVE on trigger 'ood_detected'",
        )
        assert r.previous_mode == OperationalMode.NORMAL
        assert r.trigger == "ood_detected"
        assert r.new_mode == OperationalMode.DEFENSIVE
        assert r.accepted is True


# =============================================================================
# SECTION 5 -- NORMAL MODE TRANSITIONS
# =============================================================================

class TestNormalTransitions:
    def test_ood_detected(self):
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.NORMAL, "ood_detected")
        assert r.accepted is True
        assert r.new_mode == OperationalMode.DEFENSIVE

    def test_high_uncertainty(self):
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.NORMAL, "high_uncertainty")
        assert r.accepted is True
        assert r.new_mode == OperationalMode.DEFENSIVE

    def test_drawdown_warning(self):
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.NORMAL, "drawdown_warning")
        assert r.accepted is True
        assert r.new_mode == OperationalMode.DEFENSIVE

    def test_critical_failure(self):
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.NORMAL, "critical_failure")
        assert r.accepted is True
        assert r.new_mode == OperationalMode.EMERGENCY


# =============================================================================
# SECTION 6 -- DEFENSIVE MODE TRANSITIONS
# =============================================================================

class TestDefensiveTransitions:
    def test_ood_cleared(self):
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.DEFENSIVE, "ood_cleared")
        assert r.accepted is True
        assert r.new_mode == OperationalMode.NORMAL

    def test_uncertainty_spike(self):
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.DEFENSIVE, "uncertainty_spike")
        assert r.accepted is True
        assert r.new_mode == OperationalMode.HOLD

    def test_drawdown_exceeded(self):
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.DEFENSIVE, "drawdown_exceeded")
        assert r.accepted is True
        assert r.new_mode == OperationalMode.EMERGENCY


# =============================================================================
# SECTION 7 -- HOLD MODE TRANSITIONS
# =============================================================================

class TestHoldTransitions:
    def test_stability_restored(self):
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.HOLD, "stability_restored")
        assert r.accepted is True
        assert r.new_mode == OperationalMode.DEFENSIVE

    def test_critical_failure(self):
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.HOLD, "critical_failure")
        assert r.accepted is True
        assert r.new_mode == OperationalMode.EMERGENCY


# =============================================================================
# SECTION 8 -- EMERGENCY MODE TRANSITIONS
# =============================================================================

class TestEmergencyTransitions:
    def test_manual_recovery(self):
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.EMERGENCY, "manual_recovery")
        assert r.accepted is True
        assert r.new_mode == OperationalMode.HOLD

    def test_no_auto_recovery(self):
        """EMERGENCY has no automatic recovery — only manual_recovery."""
        ctrl = ModeController()
        for trigger in ["ood_cleared", "stability_restored", "ood_detected"]:
            r = ctrl.transition(OperationalMode.EMERGENCY, trigger)
            assert r.accepted is False
            assert r.new_mode == OperationalMode.EMERGENCY


# =============================================================================
# SECTION 9 -- REJECTED TRANSITIONS
# =============================================================================

class TestRejectedTransitions:
    def test_unknown_trigger(self):
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.NORMAL, "unknown_trigger")
        assert r.accepted is False
        assert r.new_mode == OperationalMode.NORMAL

    def test_normal_ood_cleared(self):
        """ood_cleared is not valid from NORMAL."""
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.NORMAL, "ood_cleared")
        assert r.accepted is False

    def test_hold_ood_detected(self):
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.HOLD, "ood_detected")
        assert r.accepted is False

    def test_reason_contains_info(self):
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.NORMAL, "bad")
        assert "No transition" in r.reason
        assert "normal" in r.reason

    def test_accepted_reason_contains_arrow(self):
        """Kills L185: -> mutated to ->= or +> in reason f-string."""
        ctrl = ModeController()
        r = ctrl.transition(OperationalMode.NORMAL, "ood_detected")
        assert r.accepted is True
        assert " -> " in r.reason
        # Verify no corruption of the arrow token
        assert "->=" not in r.reason
        assert "+>" not in r.reason


# =============================================================================
# SECTION 10 -- GET AVAILABLE TRIGGERS
# =============================================================================

class TestGetAvailableTriggers:
    def test_normal_triggers(self):
        ctrl = ModeController()
        triggers = ctrl.get_available_triggers(OperationalMode.NORMAL)
        assert triggers == frozenset({
            "ood_detected", "high_uncertainty",
            "drawdown_warning", "critical_failure",
        })

    def test_defensive_triggers(self):
        ctrl = ModeController()
        triggers = ctrl.get_available_triggers(OperationalMode.DEFENSIVE)
        assert triggers == frozenset({
            "ood_cleared", "uncertainty_spike", "drawdown_exceeded",
        })

    def test_hold_triggers(self):
        ctrl = ModeController()
        triggers = ctrl.get_available_triggers(OperationalMode.HOLD)
        assert triggers == frozenset({
            "stability_restored", "critical_failure",
        })

    def test_emergency_triggers(self):
        ctrl = ModeController()
        triggers = ctrl.get_available_triggers(OperationalMode.EMERGENCY)
        assert triggers == frozenset({"manual_recovery"})

    def test_type_error(self):
        ctrl = ModeController()
        with pytest.raises(TypeError, match="current_mode must be an OperationalMode"):
            ctrl.get_available_triggers("NORMAL")


# =============================================================================
# SECTION 11 -- IS VALID TRIGGER
# =============================================================================

class TestIsValidTrigger:
    def test_valid(self):
        ctrl = ModeController()
        assert ctrl.is_valid_trigger(OperationalMode.NORMAL, "ood_detected") is True

    def test_invalid(self):
        ctrl = ModeController()
        assert ctrl.is_valid_trigger(OperationalMode.NORMAL, "ood_cleared") is False

    def test_type_error_mode(self):
        ctrl = ModeController()
        with pytest.raises(TypeError):
            ctrl.is_valid_trigger("NORMAL", "ood_detected")

    def test_type_error_trigger(self):
        ctrl = ModeController()
        with pytest.raises(TypeError):
            ctrl.is_valid_trigger(OperationalMode.NORMAL, 123)


# =============================================================================
# SECTION 12 -- VALIDATION
# =============================================================================

class TestValidation:
    def test_transition_mode_type_error(self):
        ctrl = ModeController()
        with pytest.raises(TypeError, match="current_mode must be an OperationalMode"):
            ctrl.transition("NORMAL", "ood_detected")

    def test_transition_trigger_type_error(self):
        ctrl = ModeController()
        with pytest.raises(TypeError, match="trigger must be a string"):
            ctrl.transition(OperationalMode.NORMAL, 123)


# =============================================================================
# SECTION 13 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_same_inputs_same_output(self):
        ctrl = ModeController()
        results = [
            ctrl.transition(OperationalMode.NORMAL, "ood_detected")
            for _ in range(10)
        ]
        assert all(r == results[0] for r in results)

    def test_independent_controllers(self):
        r1 = ModeController().transition(OperationalMode.DEFENSIVE, "ood_cleared")
        r2 = ModeController().transition(OperationalMode.DEFENSIVE, "ood_cleared")
        assert r1 == r2

    def test_full_path_deterministic(self):
        """NORMAL → DEFENSIVE → HOLD → EMERGENCY → HOLD."""
        ctrl = ModeController()
        mode = OperationalMode.NORMAL
        path = [mode]

        r = ctrl.transition(mode, "ood_detected")
        mode = r.new_mode
        path.append(mode)

        r = ctrl.transition(mode, "uncertainty_spike")
        mode = r.new_mode
        path.append(mode)

        r = ctrl.transition(mode, "critical_failure")
        mode = r.new_mode
        path.append(mode)

        r = ctrl.transition(mode, "manual_recovery")
        mode = r.new_mode
        path.append(mode)

        assert path == [
            OperationalMode.NORMAL,
            OperationalMode.DEFENSIVE,
            OperationalMode.HOLD,
            OperationalMode.EMERGENCY,
            OperationalMode.HOLD,
        ]
