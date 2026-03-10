# =============================================================================
# Tests for jarvis/core/global_state.py (S35)
# =============================================================================

import threading

import pytest

from jarvis.core.global_state import (
    GlobalSystemStateController,
    SystemState,
    EMERGENCY_CONDITIONS,
)
from jarvis.core.regime import GlobalRegimeState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ctrl():
    """Fresh controller per test (no singleton)."""
    return GlobalSystemStateController()


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton between tests."""
    GlobalSystemStateController.reset_instance()
    yield
    GlobalSystemStateController.reset_instance()


# ===========================================================================
# SystemState.initial()
# ===========================================================================

class TestSystemStateInitial:

    def test_initial_mode_is_running(self, ctrl):
        state = ctrl.get_state()
        assert state.mode == "RUNNING"

    def test_initial_deployment_blocked(self, ctrl):
        state = ctrl.get_state()
        assert state.deployment_blocked is True

    def test_initial_risk_compression(self, ctrl):
        state = ctrl.get_state()
        assert state.risk_compression is True

    def test_initial_meta_uncertainty(self, ctrl):
        state = ctrl.get_state()
        assert state.meta_uncertainty == 1.0

    def test_initial_regime_unknown(self, ctrl):
        state = ctrl.get_state()
        assert state.regime == GlobalRegimeState.UNKNOWN

    def test_initial_regime_confidence(self, ctrl):
        state = ctrl.get_state()
        assert state.regime_confidence == 0.0

    def test_initial_regime_probs_empty(self, ctrl):
        state = ctrl.get_state()
        assert state.regime_probs == {}

    def test_initial_regime_age_bars(self, ctrl):
        state = ctrl.get_state()
        assert state.regime_age_bars == 0

    def test_initial_regime_transition_flag(self, ctrl):
        state = ctrl.get_state()
        assert state.regime_transition_flag is False

    def test_initial_strategy_mode_minimal(self, ctrl):
        state = ctrl.get_state()
        assert state.strategy_mode == "MINIMAL"

    def test_initial_weight_scalar(self, ctrl):
        state = ctrl.get_state()
        assert state.weight_scalar == 0.0

    def test_initial_positions_empty(self, ctrl):
        state = ctrl.get_state()
        assert state.positions == {}

    def test_initial_vol_state(self, ctrl):
        state = ctrl.get_state()
        assert state.realized_vol == 0.0
        assert state.forecast_vol == 0.0
        assert state.vol_regime == "NORMAL"
        assert state.vol_percentile == 0.0
        assert state.vol_spike_flag is False
        assert state.nvu_normalized == 0.0

    def test_initial_hash_nonempty(self, ctrl):
        state = ctrl.get_state()
        assert state.state_hash != ""
        assert len(state.state_hash) == 16

    def test_initial_hash_verifies(self, ctrl):
        state = ctrl.get_state()
        assert state.verify_hash() is True

    def test_initial_not_tradeable(self, ctrl):
        """Initial state is blocked -> not tradeable."""
        state = ctrl.get_state()
        assert state.is_tradeable() is False


# ===========================================================================
# update() -- basic field updates
# ===========================================================================

class TestUpdateBasic:

    def test_update_regime(self, ctrl):
        new = ctrl.update(regime=GlobalRegimeState.RISK_ON)
        assert new.regime == GlobalRegimeState.RISK_ON

    def test_update_regime_by_string(self, ctrl):
        new = ctrl.update(regime="CRISIS")
        assert new.regime == GlobalRegimeState.CRISIS

    def test_update_meta_uncertainty(self, ctrl):
        new = ctrl.update(meta_uncertainty=0.3)
        assert abs(new.meta_uncertainty - 0.3) < 1e-9

    def test_update_multiple_fields(self, ctrl):
        new = ctrl.update(
            regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
            risk_mode="ELEVATED",
        )
        assert new.regime == GlobalRegimeState.RISK_ON
        assert abs(new.meta_uncertainty - 0.2) < 1e-9
        assert new.risk_mode == "ELEVATED"

    def test_update_preserves_unchanged(self, ctrl):
        ctrl.update(regime=GlobalRegimeState.RISK_ON)
        new = ctrl.update(meta_uncertainty=0.5)
        assert new.regime == GlobalRegimeState.RISK_ON
        assert abs(new.meta_uncertainty - 0.5) < 1e-9

    def test_update_returns_new_state(self, ctrl):
        old = ctrl.get_state()
        new = ctrl.update(meta_uncertainty=0.5)
        assert new is not old
        assert new.state_hash != old.state_hash

    def test_update_hash_changes(self, ctrl):
        old_hash = ctrl.get_state().state_hash
        ctrl.update(meta_uncertainty=0.5)
        assert ctrl.get_state().state_hash != old_hash

    def test_update_hash_verifies(self, ctrl):
        new = ctrl.update(meta_uncertainty=0.5)
        assert new.verify_hash() is True

    def test_update_timestamp_is_set(self, ctrl):
        new = ctrl.update(meta_uncertainty=0.5)
        assert new.timestamp  # non-empty ISO timestamp
        assert "T" in new.timestamp  # ISO format


# ===========================================================================
# update() -- RegimeState fields
# ===========================================================================

class TestUpdateRegimeState:

    def test_update_regime_confidence(self, ctrl):
        new = ctrl.update(regime_confidence=0.82)
        assert abs(new.regime_confidence - 0.82) < 1e-9

    def test_update_regime_probs(self, ctrl):
        probs = {"RISK_ON": 0.6, "RISK_OFF": 0.3, "UNKNOWN": 0.1}
        new = ctrl.update(regime_probs=probs)
        assert new.regime_probs == probs

    def test_update_regime_age_bars(self, ctrl):
        new = ctrl.update(regime_age_bars=42)
        assert new.regime_age_bars == 42

    def test_update_regime_transition_flag(self, ctrl):
        new = ctrl.update(regime_transition_flag=True)
        assert new.regime_transition_flag is True


# ===========================================================================
# update() -- StrategyState fields
# ===========================================================================

class TestUpdateStrategyState:

    def test_update_strategy_mode(self, ctrl):
        new = ctrl.update(strategy_mode="MOMENTUM")
        assert new.strategy_mode == "MOMENTUM"

    def test_update_active_strategy_id(self, ctrl):
        new = ctrl.update(active_strategy_id="strat_01")
        assert new.active_strategy_id == "strat_01"

    def test_update_entry_exit(self, ctrl):
        new = ctrl.update(entry_active=True, exit_active=True)
        assert new.entry_active is True
        assert new.exit_active is True

    def test_update_weight_scalar(self, ctrl):
        new = ctrl.update(weight_scalar=0.75)
        assert abs(new.weight_scalar - 0.75) < 1e-9

    def test_update_regime_alignment(self, ctrl):
        new = ctrl.update(regime_alignment=True)
        assert new.regime_alignment is True

    def test_update_last_updated_bar(self, ctrl):
        new = ctrl.update(last_updated_bar=100)
        assert new.last_updated_bar == 100


# ===========================================================================
# update() -- PortfolioState fields
# ===========================================================================

class TestUpdatePortfolioState:

    def test_update_positions(self, ctrl):
        pos = {"BTC": 0.5, "ETH": 1.2}
        new = ctrl.update(positions=pos)
        assert new.positions == pos

    def test_update_exposure(self, ctrl):
        new = ctrl.update(gross_exposure=0.8, net_exposure=0.3)
        assert abs(new.gross_exposure - 0.8) < 1e-9
        assert abs(new.net_exposure - 0.3) < 1e-9

    def test_update_diversification(self, ctrl):
        new = ctrl.update(diversification_ratio=0.65, portfolio_var=0.02)
        assert abs(new.diversification_ratio - 0.65) < 1e-9
        assert abs(new.portfolio_var - 0.02) < 1e-9


# ===========================================================================
# update() -- VolatilityState fields
# ===========================================================================

class TestUpdateVolatilityState:

    def test_update_vol_fields(self, ctrl):
        new = ctrl.update(
            realized_vol=0.15,
            forecast_vol=0.18,
            vol_regime="HIGH_VOL",
            vol_percentile=0.85,
            vol_spike_flag=True,
            nvu_normalized=1.5,
        )
        assert abs(new.realized_vol - 0.15) < 1e-9
        assert abs(new.forecast_vol - 0.18) < 1e-9
        assert new.vol_regime == "HIGH_VOL"
        assert abs(new.vol_percentile - 0.85) < 1e-9
        assert new.vol_spike_flag is True
        assert abs(new.nvu_normalized - 1.5) < 1e-9


# ===========================================================================
# update() -- validation
# ===========================================================================

class TestUpdateValidation:

    def test_unknown_field_raises(self, ctrl):
        with pytest.raises(ValueError, match="Unknown state fields"):
            ctrl.update(nonexistent_field="X")

    def test_regime_confidence_below_zero_raises(self, ctrl):
        with pytest.raises(ValueError, match="regime_confidence"):
            ctrl.update(regime_confidence=-0.1)

    def test_regime_confidence_above_one_raises(self, ctrl):
        with pytest.raises(ValueError, match="regime_confidence"):
            ctrl.update(regime_confidence=1.1)

    def test_meta_uncertainty_below_zero_raises(self, ctrl):
        with pytest.raises(ValueError, match="meta_uncertainty"):
            ctrl.update(meta_uncertainty=-0.01)

    def test_meta_uncertainty_above_one_raises(self, ctrl):
        with pytest.raises(ValueError, match="meta_uncertainty"):
            ctrl.update(meta_uncertainty=1.01)

    def test_weight_scalar_below_zero_raises(self, ctrl):
        with pytest.raises(ValueError, match="weight_scalar"):
            ctrl.update(weight_scalar=-0.1)

    def test_weight_scalar_above_one_raises(self, ctrl):
        with pytest.raises(ValueError, match="weight_scalar"):
            ctrl.update(weight_scalar=1.1)

    def test_vol_percentile_below_zero_raises(self, ctrl):
        with pytest.raises(ValueError, match="vol_percentile"):
            ctrl.update(vol_percentile=-0.1)

    def test_vol_percentile_above_one_raises(self, ctrl):
        with pytest.raises(ValueError, match="vol_percentile"):
            ctrl.update(vol_percentile=1.1)

    def test_nvu_normalized_negative_raises(self, ctrl):
        with pytest.raises(ValueError, match="nvu_normalized"):
            ctrl.update(nvu_normalized=-0.01)

    def test_regime_probs_bad_sum_raises(self, ctrl):
        with pytest.raises(ValueError, match="regime_probs must sum to 1.0"):
            ctrl.update(regime_probs={"A": 0.5, "B": 0.3})

    def test_regime_probs_valid_sum(self, ctrl):
        probs = {"RISK_ON": 0.7, "RISK_OFF": 0.3}
        new = ctrl.update(regime_probs=probs)
        assert new.regime_probs == probs

    def test_regime_probs_empty_is_valid(self, ctrl):
        new = ctrl.update(regime_probs={})
        assert new.regime_probs == {}

    def test_invalid_regime_string_raises(self, ctrl):
        with pytest.raises(ValueError):
            ctrl.update(regime="INVALID_REGIME")


# ===========================================================================
# is_tradeable()
# ===========================================================================

class TestIsTradeable:

    def test_blocked_initial(self, ctrl):
        assert ctrl.get_state().is_tradeable() is False

    def test_tradeable_when_all_ok(self, ctrl):
        ctrl.update(
            deployment_blocked=False,
            ood_status="NORMAL",
            calibration_status="OK",
            integrity_status="OK",
            risk_compression=False,
        )
        assert ctrl.get_state().is_tradeable() is True

    def test_not_tradeable_ood_critical(self, ctrl):
        ctrl.update(
            deployment_blocked=False,
            risk_compression=False,
            ood_status="CRITICAL",
        )
        assert ctrl.get_state().is_tradeable() is False

    def test_not_tradeable_ood_blocked(self, ctrl):
        ctrl.update(
            deployment_blocked=False,
            risk_compression=False,
            ood_status="BLOCKED",
        )
        assert ctrl.get_state().is_tradeable() is False

    def test_not_tradeable_calibration_failed(self, ctrl):
        ctrl.update(
            deployment_blocked=False,
            risk_compression=False,
            calibration_status="FAILED",
        )
        assert ctrl.get_state().is_tradeable() is False

    def test_not_tradeable_integrity_compromised(self, ctrl):
        ctrl.update(
            deployment_blocked=False,
            risk_compression=False,
            integrity_status="COMPROMISED",
        )
        assert ctrl.get_state().is_tradeable() is False

    def test_not_tradeable_risk_compression(self, ctrl):
        ctrl.update(
            deployment_blocked=False,
            risk_compression=True,
        )
        assert ctrl.get_state().is_tradeable() is False

    def test_not_tradeable_emergency_mode(self, ctrl):
        ctrl.update(
            deployment_blocked=False,
            risk_compression=False,
            mode="EMERGENCY",
        )
        assert ctrl.get_state().is_tradeable() is False


# ===========================================================================
# emergency_shutdown()
# ===========================================================================

class TestEmergencyShutdown:

    def test_sets_emergency_mode(self, ctrl):
        ctrl.emergency_shutdown("test reason")
        state = ctrl.get_state()
        assert state.mode == "EMERGENCY"

    def test_sets_deployment_blocked(self, ctrl):
        ctrl.update(deployment_blocked=False)
        ctrl.emergency_shutdown("test")
        assert ctrl.get_state().deployment_blocked is True

    def test_sets_risk_compression(self, ctrl):
        ctrl.update(risk_compression=False)
        ctrl.emergency_shutdown("test")
        assert ctrl.get_state().risk_compression is True

    def test_freezes_state_writes(self, ctrl):
        ctrl.emergency_shutdown("test")
        with pytest.raises(ValueError, match="EMERGENCY mode"):
            ctrl.update(meta_uncertainty=0.5)

    def test_emergency_allows_emergency_fields(self, ctrl):
        ctrl.emergency_shutdown("test")
        # These should still work (for controlled shutdown sequence)
        new = ctrl.update(deployment_blocked=True)
        assert new.deployment_blocked is True

    def test_is_emergency_property(self, ctrl):
        assert ctrl.is_emergency is False
        ctrl.emergency_shutdown("test")
        assert ctrl.is_emergency is True

    def test_not_tradeable_after_shutdown(self, ctrl):
        ctrl.update(
            deployment_blocked=False,
            risk_compression=False,
        )
        ctrl.emergency_shutdown("test")
        assert ctrl.get_state().is_tradeable() is False


# ===========================================================================
# check_emergency_conditions()
# ===========================================================================

class TestCheckEmergencyConditions:

    def test_no_emergency_normal_state(self, ctrl):
        ctrl.update(meta_uncertainty=0.5)
        assert ctrl.check_emergency_conditions() is None

    def test_high_meta_uncertainty(self, ctrl):
        ctrl.update(meta_uncertainty=0.95)
        reason = ctrl.check_emergency_conditions()
        assert reason is not None
        assert "meta_uncertainty" in reason

    def test_compromised_integrity(self, ctrl):
        ctrl.update(meta_uncertainty=0.5, integrity_status="COMPROMISED")
        reason = ctrl.check_emergency_conditions()
        assert reason is not None
        assert "COMPROMISED" in reason

    def test_ood_blocked(self, ctrl):
        ctrl.update(meta_uncertainty=0.5, ood_status="BLOCKED")
        reason = ctrl.check_emergency_conditions()
        assert reason is not None
        assert "ood_status" in reason

    def test_calibration_blocked(self, ctrl):
        ctrl.update(meta_uncertainty=0.5, calibration_status="BLOCKED")
        reason = ctrl.check_emergency_conditions()
        assert reason is not None
        assert "calibration_status" in reason


# ===========================================================================
# Singleton
# ===========================================================================

class TestSingleton:

    def test_get_instance_returns_same(self):
        a = GlobalSystemStateController.get_instance()
        b = GlobalSystemStateController.get_instance()
        assert a is b

    def test_reset_instance(self):
        a = GlobalSystemStateController.get_instance()
        GlobalSystemStateController.reset_instance()
        b = GlobalSystemStateController.get_instance()
        assert a is not b


# ===========================================================================
# History
# ===========================================================================

class TestHistory:

    def test_history_empty_initially(self, ctrl):
        assert ctrl.get_history() == []

    def test_history_grows_on_update(self, ctrl):
        ctrl.update(meta_uncertainty=0.5)
        ctrl.update(meta_uncertainty=0.6)
        history = ctrl.get_history(last_n=5)
        assert len(history) == 2

    def test_history_contains_old_states(self, ctrl):
        old_hash = ctrl.get_state().state_hash
        ctrl.update(meta_uncertainty=0.5)
        history = ctrl.get_history(last_n=1)
        assert history[0].state_hash == old_hash

    def test_history_capped_at_1000(self, ctrl):
        for i in range(1050):
            ctrl.update(meta_uncertainty=0.5 * (i % 2))
        history = ctrl.get_history(last_n=2000)
        assert len(history) <= 1000


# ===========================================================================
# Transition Callbacks
# ===========================================================================

class TestTransitionCallbacks:

    def test_callback_invoked(self, ctrl):
        calls = []
        ctrl.register_transition_callback(
            lambda old, new: calls.append((old.state_hash, new.state_hash))
        )
        ctrl.update(meta_uncertainty=0.5)
        assert len(calls) == 1
        assert calls[0][0] != calls[0][1]

    def test_callback_receives_old_and_new(self, ctrl):
        results = []
        ctrl.register_transition_callback(
            lambda old, new: results.append(
                (old.meta_uncertainty, new.meta_uncertainty)
            )
        )
        ctrl.update(meta_uncertainty=0.3)
        assert results[0] == (1.0, 0.3)

    def test_failing_callback_does_not_block(self, ctrl):
        def bad_callback(old, new):
            raise RuntimeError("boom")

        ctrl.register_transition_callback(bad_callback)
        new = ctrl.update(meta_uncertainty=0.5)
        assert abs(new.meta_uncertainty - 0.5) < 1e-9


# ===========================================================================
# Hash Integrity
# ===========================================================================

class TestHashIntegrity:

    def test_hash_is_16_chars(self, ctrl):
        state = ctrl.get_state()
        assert len(state.state_hash) == 16

    def test_hash_changes_on_field_change(self, ctrl):
        h1 = ctrl.get_state().state_hash
        ctrl.update(meta_uncertainty=0.42)
        h2 = ctrl.get_state().state_hash
        assert h1 != h2

    def test_verify_hash_true(self, ctrl):
        state = ctrl.get_state()
        assert state.verify_hash() is True

    def test_verify_hash_after_update(self, ctrl):
        ctrl.update(regime=GlobalRegimeState.CRISIS, risk_mode="DEFENSIVE")
        state = ctrl.get_state()
        assert state.verify_hash() is True


# ===========================================================================
# Thread Safety
# ===========================================================================

class TestThreadSafety:

    def test_concurrent_updates(self, ctrl):
        """Multiple threads updating concurrently should not corrupt state."""
        errors = []

        def updater(value):
            try:
                for _ in range(50):
                    ctrl.update(meta_uncertainty=value)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=updater, args=(0.3,)),
            threading.Thread(target=updater, args=(0.7,)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        state = ctrl.get_state()
        assert state.verify_hash() is True
        assert state.meta_uncertainty in (0.3, 0.7)

    def test_concurrent_reads(self, ctrl):
        """Concurrent reads should always return valid state."""
        errors = []

        def reader():
            try:
                for _ in range(100):
                    s = ctrl.get_state()
                    assert s.verify_hash()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=reader) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


# ===========================================================================
# Logging integration
# ===========================================================================

class TestLoggingIntegration:

    def test_log_layer_called_on_update(self):
        calls = []

        class MockLog:
            def log_event(self, event_type, data, timestamp):
                calls.append({"event_type": event_type, "data": data})

        ctrl = GlobalSystemStateController(log_layer=MockLog())
        ctrl.update(meta_uncertainty=0.5)
        assert len(calls) == 1
        assert calls[0]["event_type"] == "STATE_CHANGE"
        assert "changed_fields" in calls[0]["data"]

    def test_log_layer_called_on_emergency(self):
        calls = []

        class MockLog:
            def log_event(self, event_type, data, timestamp):
                calls.append(event_type)

        ctrl = GlobalSystemStateController(log_layer=MockLog())
        ctrl.emergency_shutdown("test reason")
        assert "STATE_CHANGE" in calls
        assert "EMERGENCY_SHUTDOWN" in calls

    def test_broken_log_does_not_block_update(self):
        class BrokenLog:
            def log_event(self, event_type, data, timestamp):
                raise RuntimeError("logging failed")

        ctrl = GlobalSystemStateController(log_layer=BrokenLog())
        new = ctrl.update(meta_uncertainty=0.5)
        assert abs(new.meta_uncertainty - 0.5) < 1e-9


# ===========================================================================
# EMERGENCY_CONDITIONS list
# ===========================================================================

class TestEmergencyConditions:

    def test_conditions_are_callable(self):
        for cond in EMERGENCY_CONDITIONS:
            assert callable(cond)

    def test_normal_state_no_trigger(self, ctrl):
        state = ctrl.get_state()
        # Initial state has meta_uncertainty=1.0 which triggers condition 0
        # but let's test with a safe state
        ctrl.update(meta_uncertainty=0.5, deployment_blocked=False)
        state = ctrl.get_state()
        # meta_uncertainty 0.5 -> no trigger on condition 0
        assert not EMERGENCY_CONDITIONS[0](state)
        # integrity OK -> no trigger on condition 1
        assert not EMERGENCY_CONDITIONS[1](state)
        # ood NORMAL -> no trigger on condition 2
        assert not EMERGENCY_CONDITIONS[2](state)
        # calibration OK -> no trigger on condition 3
        assert not EMERGENCY_CONDITIONS[3](state)
