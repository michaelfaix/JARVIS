# =============================================================================
# Unit Tests for jarvis/core/system_mode.py
# =============================================================================

import pytest

from jarvis.core.system_mode import (
    SystemMode,
    PERMITTED_TRANSITIONS,
    is_valid_transition,
    validate_transition,
)


# ===================================================================
# TestSystemModeEnum
# ===================================================================

class TestSystemModeEnum:
    def test_has_historical(self):
        assert SystemMode.HISTORICAL.value == "HISTORICAL"

    def test_has_live_analytical(self):
        assert SystemMode.LIVE_ANALYTICAL.value == "LIVE_ANALYTICAL"

    def test_has_hybrid(self):
        assert SystemMode.HYBRID.value == "HYBRID"

    def test_exactly_three_members(self):
        assert len(SystemMode) == 3

    def test_unique_values(self):
        values = [m.value for m in SystemMode]
        assert len(values) == len(set(values))

    def test_construction_from_value(self):
        assert SystemMode("HISTORICAL") is SystemMode.HISTORICAL
        assert SystemMode("LIVE_ANALYTICAL") is SystemMode.LIVE_ANALYTICAL
        assert SystemMode("HYBRID") is SystemMode.HYBRID

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            SystemMode("INVALID")

    def test_identity(self):
        assert SystemMode.HISTORICAL is SystemMode.HISTORICAL

    def test_equality(self):
        assert SystemMode.HISTORICAL == SystemMode.HISTORICAL
        assert SystemMode.HISTORICAL != SystemMode.HYBRID

    def test_hashable(self):
        s = {SystemMode.HISTORICAL, SystemMode.LIVE_ANALYTICAL, SystemMode.HYBRID}
        assert len(s) == 3


# ===================================================================
# TestPermittedTransitions
# ===================================================================

class TestPermittedTransitions:
    def test_all_modes_have_entry(self):
        for mode in SystemMode:
            assert mode in PERMITTED_TRANSITIONS

    def test_historical_can_go_to_live(self):
        assert SystemMode.LIVE_ANALYTICAL in PERMITTED_TRANSITIONS[SystemMode.HISTORICAL]

    def test_historical_can_go_to_hybrid(self):
        assert SystemMode.HYBRID in PERMITTED_TRANSITIONS[SystemMode.HISTORICAL]

    def test_live_analytical_is_terminal(self):
        assert len(PERMITTED_TRANSITIONS[SystemMode.LIVE_ANALYTICAL]) == 0

    def test_hybrid_can_go_to_live(self):
        assert SystemMode.LIVE_ANALYTICAL in PERMITTED_TRANSITIONS[SystemMode.HYBRID]

    def test_hybrid_cannot_go_to_historical(self):
        assert SystemMode.HISTORICAL not in PERMITTED_TRANSITIONS[SystemMode.HYBRID]

    def test_live_cannot_go_to_historical(self):
        assert SystemMode.HISTORICAL not in PERMITTED_TRANSITIONS[SystemMode.LIVE_ANALYTICAL]

    def test_live_cannot_go_to_hybrid(self):
        assert SystemMode.HYBRID not in PERMITTED_TRANSITIONS[SystemMode.LIVE_ANALYTICAL]

    def test_transitions_are_frozensets(self):
        for mode in SystemMode:
            assert isinstance(PERMITTED_TRANSITIONS[mode], frozenset)

    def test_no_self_transitions(self):
        for mode in SystemMode:
            assert mode not in PERMITTED_TRANSITIONS[mode]

    def test_historical_has_exactly_two_targets(self):
        assert len(PERMITTED_TRANSITIONS[SystemMode.HISTORICAL]) == 2

    def test_hybrid_has_exactly_one_target(self):
        assert len(PERMITTED_TRANSITIONS[SystemMode.HYBRID]) == 1


# ===================================================================
# TestIsValidTransition
# ===================================================================

class TestIsValidTransition:
    # --- Valid transitions ---
    def test_historical_to_live(self):
        assert is_valid_transition(SystemMode.HISTORICAL, SystemMode.LIVE_ANALYTICAL) is True

    def test_historical_to_hybrid(self):
        assert is_valid_transition(SystemMode.HISTORICAL, SystemMode.HYBRID) is True

    def test_hybrid_to_live(self):
        assert is_valid_transition(SystemMode.HYBRID, SystemMode.LIVE_ANALYTICAL) is True

    # --- Invalid transitions ---
    def test_live_to_historical(self):
        assert is_valid_transition(SystemMode.LIVE_ANALYTICAL, SystemMode.HISTORICAL) is False

    def test_live_to_hybrid(self):
        assert is_valid_transition(SystemMode.LIVE_ANALYTICAL, SystemMode.HYBRID) is False

    def test_hybrid_to_historical(self):
        assert is_valid_transition(SystemMode.HYBRID, SystemMode.HISTORICAL) is False

    # --- Self-transitions ---
    def test_historical_to_historical(self):
        assert is_valid_transition(SystemMode.HISTORICAL, SystemMode.HISTORICAL) is False

    def test_live_to_live(self):
        assert is_valid_transition(SystemMode.LIVE_ANALYTICAL, SystemMode.LIVE_ANALYTICAL) is False

    def test_hybrid_to_hybrid(self):
        assert is_valid_transition(SystemMode.HYBRID, SystemMode.HYBRID) is False

    # --- Type errors ---
    def test_current_not_enum_raises(self):
        with pytest.raises(TypeError, match="current must be a SystemMode"):
            is_valid_transition("HISTORICAL", SystemMode.HYBRID)

    def test_target_not_enum_raises(self):
        with pytest.raises(TypeError, match="target must be a SystemMode"):
            is_valid_transition(SystemMode.HISTORICAL, "HYBRID")

    def test_none_raises(self):
        with pytest.raises(TypeError):
            is_valid_transition(None, SystemMode.HYBRID)

    def test_int_raises(self):
        with pytest.raises(TypeError):
            is_valid_transition(SystemMode.HISTORICAL, 1)

    # --- Determinism ---
    def test_determinism(self):
        r1 = is_valid_transition(SystemMode.HISTORICAL, SystemMode.HYBRID)
        r2 = is_valid_transition(SystemMode.HISTORICAL, SystemMode.HYBRID)
        assert r1 == r2

    # --- Exhaustive check: all 9 combinations ---
    def test_all_combinations(self):
        expected = {
            (SystemMode.HISTORICAL, SystemMode.HISTORICAL): False,
            (SystemMode.HISTORICAL, SystemMode.LIVE_ANALYTICAL): True,
            (SystemMode.HISTORICAL, SystemMode.HYBRID): True,
            (SystemMode.LIVE_ANALYTICAL, SystemMode.HISTORICAL): False,
            (SystemMode.LIVE_ANALYTICAL, SystemMode.LIVE_ANALYTICAL): False,
            (SystemMode.LIVE_ANALYTICAL, SystemMode.HYBRID): False,
            (SystemMode.HYBRID, SystemMode.HISTORICAL): False,
            (SystemMode.HYBRID, SystemMode.LIVE_ANALYTICAL): True,
            (SystemMode.HYBRID, SystemMode.HYBRID): False,
        }
        for (current, target), valid in expected.items():
            assert is_valid_transition(current, target) is valid, \
                f"Failed for {current.value} -> {target.value}"


# ===================================================================
# TestValidateTransition
# ===================================================================

class TestValidateTransition:
    # --- Valid transitions (no exception) ---
    def test_historical_to_live_ok(self):
        validate_transition(SystemMode.HISTORICAL, SystemMode.LIVE_ANALYTICAL)

    def test_historical_to_hybrid_ok(self):
        validate_transition(SystemMode.HISTORICAL, SystemMode.HYBRID)

    def test_hybrid_to_live_ok(self):
        validate_transition(SystemMode.HYBRID, SystemMode.LIVE_ANALYTICAL)

    # --- Invalid transitions raise ValueError ---
    def test_live_to_historical_raises(self):
        with pytest.raises(ValueError, match="not permitted"):
            validate_transition(SystemMode.LIVE_ANALYTICAL, SystemMode.HISTORICAL)

    def test_live_to_hybrid_raises(self):
        with pytest.raises(ValueError, match="not permitted"):
            validate_transition(SystemMode.LIVE_ANALYTICAL, SystemMode.HYBRID)

    def test_hybrid_to_historical_raises(self):
        with pytest.raises(ValueError, match="not permitted"):
            validate_transition(SystemMode.HYBRID, SystemMode.HISTORICAL)

    def test_self_transition_raises(self):
        with pytest.raises(ValueError, match="not permitted"):
            validate_transition(SystemMode.HISTORICAL, SystemMode.HISTORICAL)

    # --- Error message quality ---
    def test_error_mentions_terminal(self):
        with pytest.raises(ValueError, match="terminal mode"):
            validate_transition(SystemMode.LIVE_ANALYTICAL, SystemMode.HISTORICAL)

    def test_error_mentions_allowed(self):
        with pytest.raises(ValueError, match="LIVE_ANALYTICAL"):
            validate_transition(SystemMode.HYBRID, SystemMode.HISTORICAL)

    # --- Type errors propagate ---
    def test_type_error_current(self):
        with pytest.raises(TypeError):
            validate_transition("HISTORICAL", SystemMode.HYBRID)

    def test_type_error_target(self):
        with pytest.raises(TypeError):
            validate_transition(SystemMode.HISTORICAL, "HYBRID")


# ===================================================================
# TestModuleAll
# ===================================================================

class TestModuleAll:
    def test_contains_system_mode(self):
        from jarvis.core.system_mode import __all__
        assert "SystemMode" in __all__

    def test_contains_permitted_transitions(self):
        from jarvis.core.system_mode import __all__
        assert "PERMITTED_TRANSITIONS" in __all__

    def test_contains_is_valid_transition(self):
        from jarvis.core.system_mode import __all__
        assert "is_valid_transition" in __all__

    def test_contains_validate_transition(self):
        from jarvis.core.system_mode import __all__
        assert "validate_transition" in __all__

    def test_all_length(self):
        from jarvis.core.system_mode import __all__
        assert len(__all__) == 4


# ===================================================================
# TestFASConstraints
# ===================================================================

class TestFASConstraints:
    """Verify FAS-mandated constraints are encoded correctly."""

    def test_live_analytical_is_terminal(self):
        """FAS: LIVE_ANALYTICAL -> (none; terminal mode for session)"""
        for target in SystemMode:
            assert is_valid_transition(SystemMode.LIVE_ANALYTICAL, target) is False

    def test_no_reverse_transitions(self):
        """FAS: No reverse transitions permitted."""
        # LIVE -> HISTORICAL forbidden
        assert not is_valid_transition(SystemMode.LIVE_ANALYTICAL, SystemMode.HISTORICAL)
        # HYBRID -> HISTORICAL forbidden
        assert not is_valid_transition(SystemMode.HYBRID, SystemMode.HISTORICAL)

    def test_historical_to_hybrid_normal(self):
        """FAS: HISTORICAL -> HYBRID (normal for hybrid session startup)"""
        assert is_valid_transition(SystemMode.HISTORICAL, SystemMode.HYBRID)

    def test_hybrid_to_live_after_sync(self):
        """FAS: HYBRID -> LIVE_ANALYTICAL (after sync_point stabilizes)"""
        assert is_valid_transition(SystemMode.HYBRID, SystemMode.LIVE_ANALYTICAL)

    def test_permitted_transitions_immutable(self):
        """PERMITTED_TRANSITIONS uses frozensets — cannot be mutated."""
        for mode in SystemMode:
            targets = PERMITTED_TRANSITIONS[mode]
            with pytest.raises(AttributeError):
                targets.add(SystemMode.HISTORICAL)
