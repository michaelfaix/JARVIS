# tests/unit/core/test_global_state_controller.py
# Coverage target: jarvis/core/global_state_controller.py -> 95%+
# Tests singleton, state immutability, update validation, history, callbacks,
# emergency shutdown, and all field constraints.

import pytest
import threading

from jarvis.core.global_state_controller import (
    VALID_GLOBAL_MODES,
    VALID_OOD_STATUSES,
    VALID_RISK_MODES,
    VALID_VOL_REGIMES,
    UPDATABLE_FIELDS,
    MAX_HISTORY,
    GlobalState,
    GlobalSystemStateController,
)


# =============================================================================
# Fixture: fresh controller per test (reset singleton)
# =============================================================================

@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset singleton before and after each test."""
    GlobalSystemStateController._reset_singleton()
    yield
    GlobalSystemStateController._reset_singleton()


def _ctrl() -> GlobalSystemStateController:
    return GlobalSystemStateController.get_instance()


# =============================================================================
# Constants
# =============================================================================

class TestConstants:
    def test_valid_global_modes(self):
        assert VALID_GLOBAL_MODES == ("RUNNING", "DEGRADED", "EMERGENCY", "SHUTDOWN")

    def test_valid_ood_statuses(self):
        assert VALID_OOD_STATUSES == ("NORMAL", "ELEVATED", "CRITICAL", "BLOCKED")

    def test_valid_risk_modes(self):
        assert VALID_RISK_MODES == ("NORMAL", "ELEVATED", "CRITICAL", "DEFENSIVE")

    def test_valid_vol_regimes(self):
        assert VALID_VOL_REGIMES == ("QUIET", "NORMAL", "ELEVATED", "SPIKE")

    def test_max_history(self):
        assert MAX_HISTORY == 1000

    def test_updatable_fields_count(self):
        assert len(UPDATABLE_FIELDS) == 20


# =============================================================================
# GlobalState
# =============================================================================

class TestGlobalState:
    def test_default_construction(self):
        s = GlobalState()
        assert s.mode == "RUNNING"
        assert s.ood_status == "NORMAL"
        assert s.risk_mode == "NORMAL"
        assert s.meta_uncertainty == 0.0
        assert s.regime == "UNKNOWN"
        assert s.risk_compression is False
        assert s.deployment_blocked is False
        assert s.regime_confidence == 0.0
        assert s.vol_regime == "NORMAL"
        assert s.weight_scalar == 1.0
        assert s.version == 0

    def test_frozen(self):
        s = GlobalState()
        with pytest.raises(AttributeError):
            s.mode = "DEGRADED"

    def test_custom_fields(self):
        s = GlobalState(
            mode="DEGRADED",
            meta_uncertainty=0.5,
            regime="RISK_ON",
            version=42,
        )
        assert s.mode == "DEGRADED"
        assert s.meta_uncertainty == 0.5
        assert s.regime == "RISK_ON"
        assert s.version == 42

    def test_equality(self):
        s1 = GlobalState(mode="RUNNING")
        s2 = GlobalState(mode="RUNNING")
        assert s1 == s2

    def test_inequality(self):
        s1 = GlobalState(mode="RUNNING")
        s2 = GlobalState(mode="DEGRADED")
        assert s1 != s2

    def test_regime_probs_tuple(self):
        probs = (("RISK_ON", 0.6), ("RISK_OFF", 0.4))
        s = GlobalState(regime_probs=probs)
        assert s.regime_probs == probs


# =============================================================================
# Singleton Pattern
# =============================================================================

class TestSingleton:
    def test_get_instance_returns_same_object(self):
        c1 = GlobalSystemStateController.get_instance()
        c2 = GlobalSystemStateController.get_instance()
        assert c1 is c2

    def test_reset_creates_new_instance(self):
        c1 = GlobalSystemStateController.get_instance()
        GlobalSystemStateController._reset_singleton()
        c2 = GlobalSystemStateController.get_instance()
        assert c1 is not c2

    def test_direct_construction_gives_fresh_controller(self):
        c1 = GlobalSystemStateController()
        c2 = GlobalSystemStateController()
        assert c1 is not c2

    def test_singleton_thread_safety(self):
        results = []

        def get_ctrl():
            results.append(GlobalSystemStateController.get_instance())

        threads = [threading.Thread(target=get_ctrl) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        assert all(r is results[0] for r in results)


# =============================================================================
# get_state()
# =============================================================================

class TestGetState:
    def test_returns_global_state(self):
        ctrl = _ctrl()
        state = ctrl.get_state()
        assert isinstance(state, GlobalState)

    def test_initial_version_is_one(self):
        ctrl = _ctrl()
        assert ctrl.get_state().version == 1

    def test_returns_frozen_snapshot(self):
        ctrl = _ctrl()
        state = ctrl.get_state()
        with pytest.raises(AttributeError):
            state.mode = "DEGRADED"

    def test_snapshot_not_affected_by_later_update(self):
        ctrl = _ctrl()
        snap1 = ctrl.get_state()
        ctrl.update(regime="RISK_ON")
        snap2 = ctrl.get_state()
        assert snap1.regime == "UNKNOWN"
        assert snap2.regime == "RISK_ON"


# =============================================================================
# update() -- happy path
# =============================================================================

class TestUpdateHappyPath:
    def test_single_field_update(self):
        ctrl = _ctrl()
        new = ctrl.update(regime="RISK_ON")
        assert new.regime == "RISK_ON"
        assert new.version == 2

    def test_multiple_field_update(self):
        ctrl = _ctrl()
        new = ctrl.update(
            regime="CRISIS",
            risk_mode="CRITICAL",
            meta_uncertainty=0.8,
        )
        assert new.regime == "CRISIS"
        assert new.risk_mode == "CRITICAL"
        assert new.meta_uncertainty == 0.8

    def test_version_increments(self):
        ctrl = _ctrl()
        ctrl.update(regime="RISK_ON")
        ctrl.update(regime="RISK_OFF")
        ctrl.update(regime="CRISIS")
        assert ctrl.get_state().version == 4

    def test_unchanged_fields_preserved(self):
        ctrl = _ctrl()
        ctrl.update(regime="RISK_ON")
        state = ctrl.get_state()
        assert state.mode == "RUNNING"
        assert state.ood_status == "NORMAL"
        assert state.weight_scalar == 1.0

    def test_mode_update(self):
        ctrl = _ctrl()
        ctrl.update(mode="DEGRADED")
        assert ctrl.get_state().mode == "DEGRADED"

    def test_ood_status_update(self):
        ctrl = _ctrl()
        ctrl.update(ood_status="ELEVATED")
        assert ctrl.get_state().ood_status == "ELEVATED"

    def test_risk_compression_update(self):
        ctrl = _ctrl()
        ctrl.update(risk_compression=True)
        assert ctrl.get_state().risk_compression is True

    def test_deployment_blocked_update(self):
        ctrl = _ctrl()
        ctrl.update(deployment_blocked=True)
        assert ctrl.get_state().deployment_blocked is True

    def test_regime_state_fields(self):
        ctrl = _ctrl()
        ctrl.update(
            regime_confidence=0.85,
            regime_age_bars=42,
            regime_transition_flag=True,
        )
        state = ctrl.get_state()
        assert state.regime_confidence == 0.85
        assert state.regime_age_bars == 42
        assert state.regime_transition_flag is True

    def test_volatility_state_fields(self):
        ctrl = _ctrl()
        ctrl.update(
            realized_vol=0.25,
            forecast_vol=0.30,
            vol_regime="SPIKE",
            vol_percentile=0.95,
            vol_spike_flag=True,
        )
        state = ctrl.get_state()
        assert state.realized_vol == 0.25
        assert state.forecast_vol == 0.30
        assert state.vol_regime == "SPIKE"
        assert state.vol_percentile == 0.95
        assert state.vol_spike_flag is True

    def test_strategy_state_fields(self):
        ctrl = _ctrl()
        ctrl.update(strategy_mode="DEFENSIVE", weight_scalar=0.5)
        state = ctrl.get_state()
        assert state.strategy_mode == "DEFENSIVE"
        assert state.weight_scalar == 0.5

    def test_portfolio_state_fields(self):
        ctrl = _ctrl()
        ctrl.update(gross_exposure=100000.0, net_exposure=-5000.0)
        state = ctrl.get_state()
        assert state.gross_exposure == 100000.0
        assert state.net_exposure == -5000.0


# =============================================================================
# update() -- validation errors
# =============================================================================

class TestUpdateValidation:
    def test_empty_update_raises(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="at least one field"):
            ctrl.update()

    def test_unknown_field_raises(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="Unknown fields"):
            ctrl.update(nonexistent_field="value")

    def test_invalid_mode_raises(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="mode"):
            ctrl.update(mode="INVALID_MODE")

    def test_invalid_ood_status_raises(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="ood_status"):
            ctrl.update(ood_status="BAD")

    def test_invalid_risk_mode_raises(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="risk_mode"):
            ctrl.update(risk_mode="INVALID")

    def test_invalid_vol_regime_raises(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="vol_regime"):
            ctrl.update(vol_regime="ULTRA_SPIKE")

    def test_meta_uncertainty_below_zero(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="meta_uncertainty"):
            ctrl.update(meta_uncertainty=-0.1)

    def test_meta_uncertainty_above_one(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="meta_uncertainty"):
            ctrl.update(meta_uncertainty=1.1)

    def test_meta_uncertainty_not_numeric(self):
        ctrl = _ctrl()
        with pytest.raises(TypeError, match="meta_uncertainty"):
            ctrl.update(meta_uncertainty="high")

    def test_regime_confidence_below_zero(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="regime_confidence"):
            ctrl.update(regime_confidence=-0.1)

    def test_regime_confidence_above_one(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="regime_confidence"):
            ctrl.update(regime_confidence=1.5)

    def test_regime_confidence_not_numeric(self):
        ctrl = _ctrl()
        with pytest.raises(TypeError, match="regime_confidence"):
            ctrl.update(regime_confidence="bad")

    def test_vol_percentile_below_zero(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="vol_percentile"):
            ctrl.update(vol_percentile=-0.1)

    def test_vol_percentile_above_one(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="vol_percentile"):
            ctrl.update(vol_percentile=1.5)

    def test_vol_percentile_not_numeric(self):
        ctrl = _ctrl()
        with pytest.raises(TypeError, match="vol_percentile"):
            ctrl.update(vol_percentile="bad")

    def test_weight_scalar_below_zero(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="weight_scalar"):
            ctrl.update(weight_scalar=-0.1)

    def test_weight_scalar_above_one(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="weight_scalar"):
            ctrl.update(weight_scalar=1.5)

    def test_weight_scalar_not_numeric(self):
        ctrl = _ctrl()
        with pytest.raises(TypeError, match="weight_scalar"):
            ctrl.update(weight_scalar="bad")

    def test_regime_age_bars_negative(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="regime_age_bars"):
            ctrl.update(regime_age_bars=-1)

    def test_regime_age_bars_not_int(self):
        ctrl = _ctrl()
        with pytest.raises(TypeError, match="regime_age_bars"):
            ctrl.update(regime_age_bars=5.0)

    def test_regime_age_bars_bool(self):
        ctrl = _ctrl()
        with pytest.raises(TypeError, match="regime_age_bars"):
            ctrl.update(regime_age_bars=True)

    def test_failed_validation_does_not_mutate_state(self):
        ctrl = _ctrl()
        original = ctrl.get_state()
        with pytest.raises(ValueError):
            ctrl.update(mode="INVALID")
        assert ctrl.get_state() == original
        assert ctrl.get_state().version == 1


# =============================================================================
# update() -- boundary values
# =============================================================================

class TestUpdateBoundaryValues:
    def test_meta_uncertainty_zero(self):
        ctrl = _ctrl()
        ctrl.update(meta_uncertainty=0.0)
        assert ctrl.get_state().meta_uncertainty == 0.0

    def test_meta_uncertainty_one(self):
        ctrl = _ctrl()
        ctrl.update(meta_uncertainty=1.0)
        assert ctrl.get_state().meta_uncertainty == 1.0

    def test_regime_confidence_zero(self):
        ctrl = _ctrl()
        ctrl.update(regime_confidence=0.0)
        assert ctrl.get_state().regime_confidence == 0.0

    def test_regime_confidence_one(self):
        ctrl = _ctrl()
        ctrl.update(regime_confidence=1.0)
        assert ctrl.get_state().regime_confidence == 1.0

    def test_weight_scalar_zero(self):
        ctrl = _ctrl()
        ctrl.update(weight_scalar=0.0)
        assert ctrl.get_state().weight_scalar == 0.0

    def test_weight_scalar_one(self):
        ctrl = _ctrl()
        ctrl.update(weight_scalar=1.0)
        assert ctrl.get_state().weight_scalar == 1.0

    def test_vol_percentile_zero(self):
        ctrl = _ctrl()
        ctrl.update(vol_percentile=0.0)
        assert ctrl.get_state().vol_percentile == 0.0

    def test_vol_percentile_one(self):
        ctrl = _ctrl()
        ctrl.update(vol_percentile=1.0)
        assert ctrl.get_state().vol_percentile == 1.0

    def test_regime_age_bars_zero(self):
        ctrl = _ctrl()
        ctrl.update(regime_age_bars=0)
        assert ctrl.get_state().regime_age_bars == 0

    def test_meta_uncertainty_int_zero(self):
        ctrl = _ctrl()
        ctrl.update(meta_uncertainty=0)
        assert ctrl.get_state().meta_uncertainty == 0

    def test_meta_uncertainty_int_one(self):
        ctrl = _ctrl()
        ctrl.update(meta_uncertainty=1)
        assert ctrl.get_state().meta_uncertainty == 1


# =============================================================================
# History
# =============================================================================

class TestHistory:
    def test_initial_history_empty(self):
        ctrl = _ctrl()
        assert ctrl.get_history() == []
        assert ctrl.history_depth == 0

    def test_update_archives_old_state(self):
        ctrl = _ctrl()
        old_state = ctrl.get_state()
        ctrl.update(regime="RISK_ON")
        history = ctrl.get_history()
        assert len(history) == 1
        assert history[0] == old_state

    def test_multiple_updates_build_history(self):
        ctrl = _ctrl()
        ctrl.update(regime="RISK_ON")
        ctrl.update(regime="RISK_OFF")
        ctrl.update(regime="CRISIS")
        history = ctrl.get_history()
        assert len(history) == 3

    def test_get_history_last_n(self):
        ctrl = _ctrl()
        for i in range(5):
            ctrl.update(regime_age_bars=i)
        history = ctrl.get_history(last_n=2)
        assert len(history) == 2

    def test_get_history_more_than_available(self):
        ctrl = _ctrl()
        ctrl.update(regime="RISK_ON")
        history = ctrl.get_history(last_n=100)
        assert len(history) == 1

    def test_history_capped_at_max(self):
        ctrl = _ctrl()
        for i in range(MAX_HISTORY + 50):
            ctrl.update(regime_age_bars=i)
        assert ctrl.history_depth == MAX_HISTORY

    def test_get_history_invalid_type(self):
        ctrl = _ctrl()
        with pytest.raises(TypeError, match="last_n"):
            ctrl.get_history(last_n=5.0)

    def test_get_history_bool_raises(self):
        ctrl = _ctrl()
        with pytest.raises(TypeError, match="last_n"):
            ctrl.get_history(last_n=True)

    def test_get_history_zero_raises(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="last_n"):
            ctrl.get_history(last_n=0)

    def test_get_history_negative_raises(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="last_n"):
            ctrl.get_history(last_n=-1)

    def test_history_depth_property(self):
        ctrl = _ctrl()
        assert ctrl.history_depth == 0
        ctrl.update(regime="RISK_ON")
        assert ctrl.history_depth == 1

    def test_version_property(self):
        ctrl = _ctrl()
        assert ctrl.version == 1
        ctrl.update(regime="RISK_ON")
        assert ctrl.version == 2


# =============================================================================
# Callbacks
# =============================================================================

class TestCallbacks:
    def test_callback_fires_on_update(self):
        ctrl = _ctrl()
        calls = []
        ctrl.register_callback(lambda old, new: calls.append((old, new)))
        ctrl.update(regime="RISK_ON")
        assert len(calls) == 1
        old, new = calls[0]
        assert old.regime == "UNKNOWN"
        assert new.regime == "RISK_ON"

    def test_multiple_callbacks(self):
        ctrl = _ctrl()
        c1, c2 = [], []
        ctrl.register_callback(lambda o, n: c1.append(1))
        ctrl.register_callback(lambda o, n: c2.append(1))
        ctrl.update(regime="RISK_ON")
        assert len(c1) == 1
        assert len(c2) == 1

    def test_callback_exception_does_not_block(self):
        ctrl = _ctrl()
        calls = []

        def bad_callback(old, new):
            raise RuntimeError("boom")

        def good_callback(old, new):
            calls.append(1)

        ctrl.register_callback(bad_callback)
        ctrl.register_callback(good_callback)
        ctrl.update(regime="RISK_ON")
        # good_callback still fires even though bad_callback raised
        assert len(calls) == 1

    def test_register_non_callable_raises(self):
        ctrl = _ctrl()
        with pytest.raises(TypeError, match="callable"):
            ctrl.register_callback("not_a_function")

    def test_register_none_raises(self):
        ctrl = _ctrl()
        with pytest.raises(TypeError, match="callable"):
            ctrl.register_callback(None)

    def test_callback_receives_correct_versions(self):
        ctrl = _ctrl()
        versions = []
        ctrl.register_callback(lambda o, n: versions.append((o.version, n.version)))
        ctrl.update(regime="RISK_ON")
        ctrl.update(regime="RISK_OFF")
        assert versions == [(1, 2), (2, 3)]


# =============================================================================
# Emergency Shutdown
# =============================================================================

class TestEmergencyShutdown:
    def test_sets_emergency_mode(self):
        ctrl = _ctrl()
        ctrl.emergency_shutdown("test reason")
        state = ctrl.get_state()
        assert state.mode == "EMERGENCY"
        assert state.deployment_blocked is True
        assert state.risk_compression is True

    def test_returns_new_state(self):
        ctrl = _ctrl()
        state = ctrl.emergency_shutdown("critical failure")
        assert state.mode == "EMERGENCY"

    def test_empty_reason_raises(self):
        ctrl = _ctrl()
        with pytest.raises(ValueError, match="reason"):
            ctrl.emergency_shutdown("")

    def test_non_string_reason_raises(self):
        ctrl = _ctrl()
        with pytest.raises(TypeError, match="reason"):
            ctrl.emergency_shutdown(42)

    def test_none_reason_raises(self):
        ctrl = _ctrl()
        with pytest.raises(TypeError, match="reason"):
            ctrl.emergency_shutdown(None)

    def test_shutdown_fires_callback(self):
        ctrl = _ctrl()
        calls = []
        ctrl.register_callback(lambda o, n: calls.append(n.mode))
        ctrl.emergency_shutdown("test")
        assert calls == ["EMERGENCY"]


# =============================================================================
# Thread Safety
# =============================================================================

class TestThreadSafety:
    def test_concurrent_updates(self):
        ctrl = _ctrl()
        errors = []

        def do_updates(n):
            try:
                for i in range(n):
                    ctrl.update(regime_age_bars=i)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=do_updates, args=(20,)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        # 100 updates + initial = version 101
        assert ctrl.get_state().version == 101

    def test_concurrent_reads(self):
        ctrl = _ctrl()
        ctrl.update(regime="RISK_ON")
        results = []

        def read_state():
            for _ in range(50):
                results.append(ctrl.get_state().regime)

        threads = [threading.Thread(target=read_state) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 250
        assert all(r == "RISK_ON" for r in results)


# =============================================================================
# All valid enum values
# =============================================================================

class TestAllValidEnumValues:
    def test_all_global_modes_accepted(self):
        for mode in VALID_GLOBAL_MODES:
            ctrl = _ctrl()
            ctrl.update(mode=mode)
            assert ctrl.get_state().mode == mode
            GlobalSystemStateController._reset_singleton()

    def test_all_ood_statuses_accepted(self):
        for status in VALID_OOD_STATUSES:
            ctrl = _ctrl()
            ctrl.update(ood_status=status)
            assert ctrl.get_state().ood_status == status
            GlobalSystemStateController._reset_singleton()

    def test_all_risk_modes_accepted(self):
        for rm in VALID_RISK_MODES:
            ctrl = _ctrl()
            ctrl.update(risk_mode=rm)
            assert ctrl.get_state().risk_mode == rm
            GlobalSystemStateController._reset_singleton()

    def test_all_vol_regimes_accepted(self):
        for vr in VALID_VOL_REGIMES:
            ctrl = _ctrl()
            ctrl.update(vol_regime=vr)
            assert ctrl.get_state().vol_regime == vr
            GlobalSystemStateController._reset_singleton()


# =============================================================================
# Determinism
# =============================================================================

class TestDeterminism:
    def test_same_sequence_same_state(self):
        c1 = GlobalSystemStateController()
        c2 = GlobalSystemStateController()

        for ctrl in [c1, c2]:
            ctrl.update(regime="RISK_ON")
            ctrl.update(meta_uncertainty=0.5)
            ctrl.update(risk_mode="ELEVATED")

        s1 = c1.get_state()
        s2 = c2.get_state()
        assert s1.regime == s2.regime
        assert s1.meta_uncertainty == s2.meta_uncertainty
        assert s1.risk_mode == s2.risk_mode
        assert s1.version == s2.version

    def test_different_sequence_different_state(self):
        c1 = GlobalSystemStateController()
        c2 = GlobalSystemStateController()

        c1.update(regime="RISK_ON")
        c2.update(regime="CRISIS")

        assert c1.get_state().regime != c2.get_state().regime
