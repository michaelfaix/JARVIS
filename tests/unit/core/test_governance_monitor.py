# =============================================================================
# tests/unit/core/test_governance_monitor.py
# Tests for jarvis/core/governance_monitor.py
# =============================================================================

import pytest

from jarvis.core.governance_monitor import (
    GOVERNANCE_CHECKS,
    PERMITTED_CALLERS,
    GovernanceViolation,
    GovernanceAuditEntry,
    GovernanceMonitor,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_governance_checks_keys(self):
        assert set(GOVERNANCE_CHECKS.keys()) == {
            "no_recursive_emit",
            "single_ctrl_update",
            "no_sandbox_ctrl_access",
            "confidence_trigger_required",
            "sync_point_immutability",
        }

    def test_governance_checks_values_are_strings(self):
        for v in GOVERNANCE_CHECKS.values():
            assert isinstance(v, str)
            assert len(v) > 0

    def test_permitted_callers_keys(self):
        expected = {
            "regime_engine", "volatility_layer", "strategy_selector",
            "risk_engine", "portfolio_context", "confidence_engine",
            "failure_handler", "hybrid_coordinator", "replay_engine",
        }
        assert set(PERMITTED_CALLERS.keys()) == expected

    def test_permitted_callers_frozen_sets(self):
        for v in PERMITTED_CALLERS.values():
            assert isinstance(v, frozenset)

    def test_replay_engine_has_all(self):
        assert "ALL" in PERMITTED_CALLERS["replay_engine"]

    def test_confidence_engine_fields(self):
        assert PERMITTED_CALLERS["confidence_engine"] == frozenset({"meta_uncertainty"})

    def test_risk_engine_fields(self):
        assert PERMITTED_CALLERS["risk_engine"] == frozenset({"risk_mode", "risk_compression"})


# =============================================================================
# SECTION 2 -- GOVERNANCE VIOLATION DATACLASS
# =============================================================================

class TestGovernanceViolation:
    def test_frozen(self):
        v = GovernanceViolation("rule", "module", "field", "desc")
        with pytest.raises(AttributeError):
            v.rule_name = "other"

    def test_fields(self):
        v = GovernanceViolation(
            rule_name="single_ctrl_update",
            caller_module="unknown_module",
            attempted_field="regime_state",
            description="violation desc",
        )
        assert v.rule_name == "single_ctrl_update"
        assert v.caller_module == "unknown_module"
        assert v.attempted_field == "regime_state"
        assert v.description == "violation desc"

    def test_optional_field(self):
        v = GovernanceViolation("rule", "mod", None, "desc")
        assert v.attempted_field is None

    def test_equality(self):
        v1 = GovernanceViolation("r", "m", "f", "d")
        v2 = GovernanceViolation("r", "m", "f", "d")
        assert v1 == v2


# =============================================================================
# SECTION 3 -- GOVERNANCE AUDIT ENTRY DATACLASS
# =============================================================================

class TestGovernanceAuditEntry:
    def test_frozen(self):
        e = GovernanceAuditEntry("mod", ("f1",), True, None)
        with pytest.raises(AttributeError):
            e.permitted = False

    def test_fields_permitted(self):
        e = GovernanceAuditEntry(
            caller_module="regime_engine",
            fields_modified=("regime_state",),
            permitted=True,
            violation=None,
        )
        assert e.caller_module == "regime_engine"
        assert e.fields_modified == ("regime_state",)
        assert e.permitted is True
        assert e.violation is None

    def test_fields_violation(self):
        v = GovernanceViolation("rule", "mod", "f", "d")
        e = GovernanceAuditEntry("mod", ("f",), False, v)
        assert e.permitted is False
        assert e.violation == v

    def test_equality(self):
        e1 = GovernanceAuditEntry("m", ("f",), True, None)
        e2 = GovernanceAuditEntry("m", ("f",), True, None)
        assert e1 == e2


# =============================================================================
# SECTION 4 -- CHECK UPDATE PERMISSION: PERMITTED
# =============================================================================

class TestCheckPermissionPermitted:
    def test_regime_engine_permitted(self):
        mon = GovernanceMonitor()
        e = mon.check_update_permission("regime_engine", ("regime_state",))
        assert e.permitted is True
        assert e.violation is None

    def test_risk_engine_permitted(self):
        mon = GovernanceMonitor()
        e = mon.check_update_permission("risk_engine", ("risk_mode",))
        assert e.permitted is True

    def test_risk_engine_multiple_fields(self):
        mon = GovernanceMonitor()
        e = mon.check_update_permission(
            "risk_engine", ("risk_mode", "risk_compression")
        )
        assert e.permitted is True

    def test_confidence_engine_permitted(self):
        mon = GovernanceMonitor()
        e = mon.check_update_permission("confidence_engine", ("meta_uncertainty",))
        assert e.permitted is True

    def test_replay_engine_any_field(self):
        mon = GovernanceMonitor()
        e = mon.check_update_permission("replay_engine", ("anything", "else"))
        assert e.permitted is True

    def test_hybrid_coordinator_sync_point(self):
        mon = GovernanceMonitor()
        e = mon.check_update_permission(
            "hybrid_coordinator", ("hybrid_sync_point",)
        )
        assert e.permitted is True

    def test_all_permitted_callers(self):
        """Every permitted caller can access at least one field."""
        mon = GovernanceMonitor()
        for caller, fields in PERMITTED_CALLERS.items():
            if "ALL" in fields:
                test_field = ("test_field",)
            else:
                test_field = (sorted(fields)[0],)
            e = mon.check_update_permission(caller, test_field)
            assert e.permitted is True, f"{caller} should be permitted"


# =============================================================================
# SECTION 5 -- CHECK UPDATE PERMISSION: VIOLATIONS
# =============================================================================

class TestCheckPermissionViolations:
    def test_unknown_caller(self):
        mon = GovernanceMonitor()
        e = mon.check_update_permission("unknown_module", ("regime_state",))
        assert e.permitted is False
        assert e.violation is not None
        assert e.violation.rule_name == "single_ctrl_update"
        assert "unknown_module" in e.violation.description

    def test_unauthorized_field(self):
        mon = GovernanceMonitor()
        e = mon.check_update_permission("risk_engine", ("regime_state",))
        assert e.permitted is False
        assert e.violation.attempted_field == "regime_state"

    def test_partial_unauthorized(self):
        """One permitted + one not → violation."""
        mon = GovernanceMonitor()
        e = mon.check_update_permission(
            "risk_engine", ("risk_mode", "regime_state")
        )
        assert e.permitted is False
        assert "regime_state" in e.violation.description

    def test_confidence_engine_wrong_field(self):
        mon = GovernanceMonitor()
        e = mon.check_update_permission("confidence_engine", ("regime_state",))
        assert e.permitted is False

    def test_violation_has_caller_module(self):
        mon = GovernanceMonitor()
        e = mon.check_update_permission("bad_module", ("x",))
        assert e.violation.caller_module == "bad_module"

    def test_single_field_in_attempted(self):
        """Single unauthorized field from unknown caller → attempted_field set."""
        mon = GovernanceMonitor()
        e = mon.check_update_permission("bad_module", ("single_field",))
        assert e.violation.attempted_field == "single_field"

    def test_multi_field_unknown_caller(self):
        """Multiple fields from unknown caller → attempted_field is None."""
        mon = GovernanceMonitor()
        e = mon.check_update_permission("bad_module", ("f1", "f2"))
        assert e.violation.attempted_field is None


# =============================================================================
# SECTION 6 -- CHECK UPDATE PERMISSION: VALIDATION
# =============================================================================

class TestCheckPermissionValidation:
    def test_caller_type_error(self):
        mon = GovernanceMonitor()
        with pytest.raises(TypeError, match="caller_module must be a string"):
            mon.check_update_permission(123, ("field",))

    def test_fields_type_error(self):
        mon = GovernanceMonitor()
        with pytest.raises(TypeError, match="fields must be a tuple"):
            mon.check_update_permission("mod", ["field"])

    def test_empty_fields(self):
        mon = GovernanceMonitor()
        with pytest.raises(ValueError, match="fields must not be empty"):
            mon.check_update_permission("mod", ())


# =============================================================================
# SECTION 7 -- CHECK SYNC POINT IMMUTABILITY
# =============================================================================

class TestCheckSyncPointImmutability:
    def test_not_set(self):
        mon = GovernanceMonitor()
        v = mon.check_sync_point_immutability(False, "hybrid_coordinator")
        assert v is None

    def test_already_set(self):
        mon = GovernanceMonitor()
        v = mon.check_sync_point_immutability(True, "hybrid_coordinator")
        assert v is not None
        assert v.rule_name == "sync_point_immutability"
        assert v.attempted_field == "hybrid_sync_point"

    def test_already_set_different_caller(self):
        mon = GovernanceMonitor()
        v = mon.check_sync_point_immutability(True, "some_module")
        assert "some_module" in v.description

    def test_already_set_type_error(self):
        mon = GovernanceMonitor()
        with pytest.raises(TypeError, match="already_set must be bool"):
            mon.check_sync_point_immutability(1, "mod")

    def test_caller_type_error(self):
        mon = GovernanceMonitor()
        with pytest.raises(TypeError, match="caller_module must be a string"):
            mon.check_sync_point_immutability(True, 123)


# =============================================================================
# SECTION 8 -- CHECK CONFIDENCE EMITTER
# =============================================================================

class TestCheckConfidenceEmitter:
    def test_confidence_engine_permitted(self):
        mon = GovernanceMonitor()
        v = mon.check_confidence_emitter("confidence_engine")
        assert v is None

    def test_other_module_violation(self):
        mon = GovernanceMonitor()
        v = mon.check_confidence_emitter("risk_engine")
        assert v is not None
        assert v.rule_name == "confidence_trigger_required"
        assert "risk_engine" in v.description

    def test_unknown_module_violation(self):
        mon = GovernanceMonitor()
        v = mon.check_confidence_emitter("unknown")
        assert v is not None

    def test_type_error(self):
        mon = GovernanceMonitor()
        with pytest.raises(TypeError, match="emitter_module must be a string"):
            mon.check_confidence_emitter(123)


# =============================================================================
# SECTION 9 -- VALIDATE BATCH
# =============================================================================

class TestValidateBatch:
    def test_empty_batch(self):
        mon = GovernanceMonitor()
        results = mon.validate_batch([])
        assert results == []

    def test_single_entry(self):
        mon = GovernanceMonitor()
        results = mon.validate_batch([
            ("regime_engine", ("regime_state",)),
        ])
        assert len(results) == 1
        assert results[0].permitted is True

    def test_mixed_batch(self):
        mon = GovernanceMonitor()
        results = mon.validate_batch([
            ("regime_engine", ("regime_state",)),
            ("unknown", ("bad_field",)),
            ("risk_engine", ("risk_mode",)),
        ])
        assert len(results) == 3
        assert results[0].permitted is True
        assert results[1].permitted is False
        assert results[2].permitted is True

    def test_all_violations(self):
        mon = GovernanceMonitor()
        results = mon.validate_batch([
            ("bad1", ("f1",)),
            ("bad2", ("f2",)),
        ])
        assert all(not r.permitted for r in results)

    def test_type_error(self):
        mon = GovernanceMonitor()
        with pytest.raises(TypeError, match="entries must be a list"):
            mon.validate_batch(("tuple",))


# =============================================================================
# SECTION 10 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_check_permission_deterministic(self):
        mon = GovernanceMonitor()
        results = [
            mon.check_update_permission("risk_engine", ("risk_mode",))
            for _ in range(10)
        ]
        assert all(r == results[0] for r in results)

    def test_violation_deterministic(self):
        mon = GovernanceMonitor()
        results = [
            mon.check_update_permission("unknown", ("field",))
            for _ in range(10)
        ]
        assert all(r == results[0] for r in results)

    def test_independent_monitors(self):
        r1 = GovernanceMonitor().check_update_permission("risk_engine", ("risk_mode",))
        r2 = GovernanceMonitor().check_update_permission("risk_engine", ("risk_mode",))
        assert r1 == r2

    def test_batch_deterministic(self):
        entries = [
            ("regime_engine", ("regime_state",)),
            ("unknown", ("x",)),
        ]
        r1 = GovernanceMonitor().validate_batch(entries)
        r2 = GovernanceMonitor().validate_batch(entries)
        assert r1 == r2
