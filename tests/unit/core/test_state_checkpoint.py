# =============================================================================
# tests/unit/core/test_state_checkpoint.py
# Tests for jarvis/core/state_checkpoint.py
# =============================================================================

import hashlib
import json
from dataclasses import fields as dc_fields

import pytest

from jarvis.core.state_checkpoint import (
    CHECKPOINT_SCHEMA_VERSION,
    GLOBAL_STATE_VERSION,
    STRATEGY_OBJECT_VERSION,
    CONFIDENCE_BUNDLE_VERSION,
    StateCheckpoint,
    CheckpointValidationError,
    export_snapshot,
    import_snapshot,
    compute_integrity_hash,
)
from jarvis.core.global_state_controller import (
    GlobalState,
    GlobalSystemStateController,
    UPDATABLE_FIELDS,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset singleton before and after every test."""
    GlobalSystemStateController._reset_singleton()
    yield
    GlobalSystemStateController._reset_singleton()


@pytest.fixture
def ctrl():
    """Fresh controller instance."""
    return GlobalSystemStateController.get_instance()


def _make_checkpoint(**overrides):
    """Helper to build a valid StateCheckpoint with computed integrity hash."""
    defaults = {
        "checkpoint_id": "CP-001",
        "session_id": "SESSION-001",
        "sequence_id": 0,
        "timestamp": 1000.0,
        "checkpoint_version": CHECKPOINT_SCHEMA_VERSION,
        "global_state_version": GLOBAL_STATE_VERSION,
        "strategy_object_version": STRATEGY_OBJECT_VERSION,
        "confidence_bundle_version": CONFIDENCE_BUNDLE_VERSION,
        "asset_scope": ("BTC", "ETH"),
        "global_state": {
            "mode": "RUNNING",
            "ood_status": "NORMAL",
            "risk_mode": "NORMAL",
            "meta_uncertainty": 0.0,
            "regime": "UNKNOWN",
            "risk_compression": False,
            "deployment_blocked": False,
            "regime_confidence": 0.0,
            "regime_probs": (),
            "regime_age_bars": 0,
            "regime_transition_flag": False,
            "realized_vol": 0.0,
            "forecast_vol": 0.0,
            "vol_regime": "NORMAL",
            "vol_percentile": 0.0,
            "vol_spike_flag": False,
            "strategy_mode": "MOMENTUM",
            "weight_scalar": 1.0,
            "gross_exposure": 0.0,
            "net_exposure": 0.0,
            "version": 1,
        },
        "regime_states": {},
        "volatility_states": {},
        "strategy_states": {},
        "portfolio_state": {},
        "active_failure_modes": (),
        "operating_mode": "HISTORICAL",
    }
    defaults.update(overrides)

    # Compute integrity hash
    hash_dict = {k: v for k, v in defaults.items()}
    integrity_hash = compute_integrity_hash(hash_dict)
    defaults["integrity_hash"] = integrity_hash

    return StateCheckpoint(**defaults)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    """Test schema version constants."""

    def test_checkpoint_schema_version(self):
        assert CHECKPOINT_SCHEMA_VERSION == "1.0.0"

    def test_global_state_version(self):
        assert GLOBAL_STATE_VERSION == "1.0.0"

    def test_strategy_object_version(self):
        assert STRATEGY_OBJECT_VERSION == "1.0.0"

    def test_confidence_bundle_version(self):
        assert CONFIDENCE_BUNDLE_VERSION == "1.0.0"

    def test_versions_are_strings(self):
        for v in [CHECKPOINT_SCHEMA_VERSION, GLOBAL_STATE_VERSION,
                   STRATEGY_OBJECT_VERSION, CONFIDENCE_BUNDLE_VERSION]:
            assert isinstance(v, str)


# =============================================================================
# SECTION 2 -- EXCEPTIONS
# =============================================================================

class TestCheckpointValidationError:
    """Test CheckpointValidationError."""

    def test_is_exception(self):
        assert issubclass(CheckpointValidationError, Exception)

    def test_message(self):
        err = CheckpointValidationError("version mismatch")
        assert str(err) == "version mismatch"

    def test_raise_catch(self):
        with pytest.raises(CheckpointValidationError, match="test"):
            raise CheckpointValidationError("test")


# =============================================================================
# SECTION 3 -- StateCheckpoint DATACLASS
# =============================================================================

class TestStateCheckpoint:
    """Test StateCheckpoint frozen dataclass."""

    def test_frozen(self):
        cp = _make_checkpoint()
        with pytest.raises(AttributeError):
            cp.checkpoint_id = "new"

    def test_all_fields_present(self):
        cp = _make_checkpoint()
        field_names = {f.name for f in dc_fields(cp)}
        expected = {
            "checkpoint_id", "session_id", "sequence_id", "timestamp",
            "checkpoint_version", "global_state_version",
            "strategy_object_version", "confidence_bundle_version",
            "asset_scope", "global_state", "regime_states",
            "volatility_states", "strategy_states", "portfolio_state",
            "active_failure_modes", "operating_mode", "integrity_hash",
        }
        assert field_names == expected

    def test_field_count(self):
        assert len(dc_fields(StateCheckpoint)) == 17

    def test_equality(self):
        cp1 = _make_checkpoint()
        cp2 = _make_checkpoint()
        assert cp1 == cp2

    def test_inequality_different_id(self):
        cp1 = _make_checkpoint(checkpoint_id="CP-001")
        cp2 = _make_checkpoint(checkpoint_id="CP-002")
        assert cp1 != cp2


# =============================================================================
# SECTION 4 -- COMPUTE INTEGRITY HASH
# =============================================================================

class TestComputeIntegrityHash:
    """Test compute_integrity_hash function."""

    def test_returns_hex_string(self):
        result = compute_integrity_hash({"key": "value"})
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex length

    def test_deterministic(self):
        d = {"a": 1, "b": "test", "c": [1, 2, 3]}
        h1 = compute_integrity_hash(d)
        h2 = compute_integrity_hash(d)
        assert h1 == h2

    def test_excludes_integrity_hash_field(self):
        d1 = {"a": 1, "integrity_hash": "old_hash"}
        d2 = {"a": 1, "integrity_hash": "different_hash"}
        d3 = {"a": 1}
        assert compute_integrity_hash(d1) == compute_integrity_hash(d2)
        assert compute_integrity_hash(d1) == compute_integrity_hash(d3)

    def test_different_data_different_hash(self):
        h1 = compute_integrity_hash({"a": 1})
        h2 = compute_integrity_hash({"a": 2})
        assert h1 != h2

    def test_order_independent(self):
        h1 = compute_integrity_hash({"b": 2, "a": 1})
        h2 = compute_integrity_hash({"a": 1, "b": 2})
        assert h1 == h2  # sort_keys=True

    def test_type_error_non_dict(self):
        with pytest.raises(TypeError, match="must be a dict"):
            compute_integrity_hash("not a dict")

    def test_type_error_none(self):
        with pytest.raises(TypeError, match="must be a dict"):
            compute_integrity_hash(None)

    def test_manual_verification(self):
        """Verify hash matches manual SHA-256 computation."""
        d = {"x": 42}
        canonical = json.dumps(d, sort_keys=True, default=str)
        expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        assert compute_integrity_hash(d) == expected

    def test_empty_dict(self):
        result = compute_integrity_hash({})
        assert isinstance(result, str)
        assert len(result) == 64

    def test_nested_structures(self):
        d = {"nested": {"a": 1}, "list": [1, 2, 3]}
        result = compute_integrity_hash(d)
        assert isinstance(result, str)


# =============================================================================
# SECTION 5 -- EXPORT SNAPSHOT
# =============================================================================

class TestExportSnapshot:
    """Test export_snapshot function."""

    def test_basic_export(self, ctrl):
        cp = export_snapshot(
            ctrl=ctrl,
            checkpoint_id="CP-001",
            session_id="SESSION-001",
            sequence_id=0,
            timestamp=1000.0,
        )
        assert isinstance(cp, StateCheckpoint)
        assert cp.checkpoint_id == "CP-001"
        assert cp.session_id == "SESSION-001"
        assert cp.sequence_id == 0
        assert cp.timestamp == 1000.0

    def test_schema_versions_set(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert cp.checkpoint_version == CHECKPOINT_SCHEMA_VERSION
        assert cp.global_state_version == GLOBAL_STATE_VERSION
        assert cp.strategy_object_version == STRATEGY_OBJECT_VERSION
        assert cp.confidence_bundle_version == CONFIDENCE_BUNDLE_VERSION

    def test_global_state_captured(self, ctrl):
        ctrl.update(meta_uncertainty=0.5, regime="RISK_ON")
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert cp.global_state["meta_uncertainty"] == 0.5
        assert cp.global_state["regime"] == "RISK_ON"

    def test_asset_scope(self, ctrl):
        cp = export_snapshot(
            ctrl, "CP-001", "S-001", 0, 1000.0,
            asset_scope=("BTC", "ETH", "SPY"),
        )
        assert cp.asset_scope == ("BTC", "ETH", "SPY")

    def test_default_asset_scope_empty(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert cp.asset_scope == ()

    def test_regime_states(self, ctrl):
        rs = {"BTC": {"regime": "RISK_ON", "confidence": 0.9}}
        cp = export_snapshot(
            ctrl, "CP-001", "S-001", 0, 1000.0,
            regime_states=rs,
        )
        assert cp.regime_states == rs

    def test_volatility_states(self, ctrl):
        vs = {"BTC": {"realized_vol": 0.25}}
        cp = export_snapshot(
            ctrl, "CP-001", "S-001", 0, 1000.0,
            volatility_states=vs,
        )
        assert cp.volatility_states == vs

    def test_strategy_states(self, ctrl):
        ss = {"BTC": {"signal": 0.7}}
        cp = export_snapshot(
            ctrl, "CP-001", "S-001", 0, 1000.0,
            strategy_states=ss,
        )
        assert cp.strategy_states == ss

    def test_portfolio_state(self, ctrl):
        ps = {"total_exposure": 0.8}
        cp = export_snapshot(
            ctrl, "CP-001", "S-001", 0, 1000.0,
            portfolio_state=ps,
        )
        assert cp.portfolio_state == ps

    def test_active_failure_modes(self, ctrl):
        cp = export_snapshot(
            ctrl, "CP-001", "S-001", 0, 1000.0,
            active_failure_modes=("FM-03", "FM-06"),
        )
        assert cp.active_failure_modes == ("FM-03", "FM-06")

    def test_operating_mode(self, ctrl):
        cp = export_snapshot(
            ctrl, "CP-001", "S-001", 0, 1000.0,
            operating_mode="LIVE_ANALYTICAL",
        )
        assert cp.operating_mode == "LIVE_ANALYTICAL"

    def test_default_operating_mode(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert cp.operating_mode == "HISTORICAL"

    def test_integrity_hash_computed(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert isinstance(cp.integrity_hash, str)
        assert len(cp.integrity_hash) == 64

    def test_integrity_hash_valid(self, ctrl):
        """Hash should match recomputation from checkpoint fields."""
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        cp_dict = {f.name: getattr(cp, f.name) for f in dc_fields(cp)}
        recomputed = compute_integrity_hash(cp_dict)
        assert cp.integrity_hash == recomputed

    def test_checkpoint_is_frozen(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        with pytest.raises(AttributeError):
            cp.checkpoint_id = "MODIFIED"

    def test_global_state_is_copy(self, ctrl):
        """Global state dict should be an independent copy."""
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        # Modifying the dict should not affect controller
        cp.global_state["mode"] = "MODIFIED"
        assert ctrl.get_state().mode == "RUNNING"

    def test_timestamp_converted_to_float(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000)
        assert isinstance(cp.timestamp, float)
        assert cp.timestamp == 1000.0

    def test_sequence_id_zero(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert cp.sequence_id == 0

    def test_sequence_id_positive(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 42, 1000.0)
        assert cp.sequence_id == 42


class TestExportSnapshotValidation:
    """Test export_snapshot argument validation."""

    def test_ctrl_type_error(self):
        with pytest.raises(TypeError, match="GlobalSystemStateController"):
            export_snapshot("not_ctrl", "CP-001", "S-001", 0, 1000.0)

    def test_checkpoint_id_type_error(self, ctrl):
        with pytest.raises(TypeError, match="checkpoint_id must be a string"):
            export_snapshot(ctrl, 123, "S-001", 0, 1000.0)

    def test_session_id_type_error(self, ctrl):
        with pytest.raises(TypeError, match="session_id must be a string"):
            export_snapshot(ctrl, "CP-001", 123, 0, 1000.0)

    def test_sequence_id_type_error(self, ctrl):
        with pytest.raises(TypeError, match="sequence_id must be an int"):
            export_snapshot(ctrl, "CP-001", "S-001", "zero", 1000.0)

    def test_sequence_id_bool_rejected(self, ctrl):
        with pytest.raises(TypeError, match="sequence_id must be an int"):
            export_snapshot(ctrl, "CP-001", "S-001", True, 1000.0)

    def test_timestamp_type_error(self, ctrl):
        with pytest.raises(TypeError, match="timestamp must be numeric"):
            export_snapshot(ctrl, "CP-001", "S-001", 0, "now")

    def test_checkpoint_id_empty(self, ctrl):
        with pytest.raises(ValueError, match="checkpoint_id must not be empty"):
            export_snapshot(ctrl, "", "S-001", 0, 1000.0)

    def test_session_id_empty(self, ctrl):
        with pytest.raises(ValueError, match="session_id must not be empty"):
            export_snapshot(ctrl, "CP-001", "", 0, 1000.0)

    def test_sequence_id_negative(self, ctrl):
        with pytest.raises(ValueError, match="sequence_id must be >= 0"):
            export_snapshot(ctrl, "CP-001", "S-001", -1, 1000.0)


# =============================================================================
# SECTION 6 -- IMPORT SNAPSHOT
# =============================================================================

class TestImportSnapshot:
    """Test import_snapshot function."""

    def test_basic_import(self, ctrl):
        # Export, modify state, import to restore
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        ctrl.update(meta_uncertainty=0.9, regime="CRISIS")
        result = import_snapshot(cp, ctrl)
        assert isinstance(result, GlobalState)
        assert result.meta_uncertainty == 0.0
        assert result.regime == "UNKNOWN"

    def test_restores_all_updatable_fields(self, ctrl):
        # Set non-default values
        ctrl.update(
            meta_uncertainty=0.7,
            regime="RISK_ON",
            risk_mode="ELEVATED",
            vol_regime="SPIKE",
            regime_confidence=0.85,
        )
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)

        # Reset state
        GlobalSystemStateController._reset_singleton()
        ctrl2 = GlobalSystemStateController.get_instance()
        assert ctrl2.get_state().meta_uncertainty == 0.0

        # Restore from checkpoint
        result = import_snapshot(cp, ctrl2)
        assert result.meta_uncertainty == 0.7
        assert result.regime == "RISK_ON"
        assert result.risk_mode == "ELEVATED"
        assert result.vol_regime == "SPIKE"
        assert result.regime_confidence == 0.85

    def test_version_field_not_restored(self, ctrl):
        """The version field is managed by ctrl, not restored from checkpoint."""
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        ctrl.update(meta_uncertainty=0.1)  # version bumps
        old_version = ctrl.get_state().version
        result = import_snapshot(cp, ctrl)
        # Version should be incremented by ctrl.update(), not restored
        assert result.version == old_version + 1

    def test_uses_ctrl_update_path(self, ctrl):
        """Import must use ctrl.update() -- verify via version increment."""
        initial_version = ctrl.get_state().version
        ctrl.update(meta_uncertainty=0.5)
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)

        GlobalSystemStateController._reset_singleton()
        ctrl2 = GlobalSystemStateController.get_instance()
        v_before = ctrl2.get_state().version
        import_snapshot(cp, ctrl2)
        assert ctrl2.get_state().version == v_before + 1

    def test_import_with_no_updatable_fields(self, ctrl):
        """Checkpoint with empty global_state should return current state."""
        cp = _make_checkpoint(global_state={"version": 1})
        result = import_snapshot(cp, ctrl)
        assert result == ctrl.get_state()


class TestImportSnapshotValidation:
    """Test import_snapshot argument validation."""

    def test_checkpoint_type_error(self, ctrl):
        with pytest.raises(TypeError, match="must be a StateCheckpoint"):
            import_snapshot("not_a_checkpoint", ctrl)

    def test_ctrl_type_error(self):
        cp = _make_checkpoint()
        with pytest.raises(TypeError, match="must be a GlobalSystemStateController"):
            import_snapshot(cp, "not_ctrl")

    def test_checkpoint_version_mismatch(self, ctrl):
        cp = _make_checkpoint(checkpoint_version="2.0.0")
        with pytest.raises(CheckpointValidationError, match="checkpoint_version mismatch"):
            import_snapshot(cp, ctrl)

    def test_global_state_version_mismatch(self, ctrl):
        cp = _make_checkpoint(global_state_version="2.0.0")
        with pytest.raises(CheckpointValidationError, match="global_state_version mismatch"):
            import_snapshot(cp, ctrl)

    def test_strategy_object_version_mismatch(self, ctrl):
        cp = _make_checkpoint(strategy_object_version="2.0.0")
        with pytest.raises(CheckpointValidationError, match="strategy_object_version mismatch"):
            import_snapshot(cp, ctrl)

    def test_confidence_bundle_version_mismatch(self, ctrl):
        cp = _make_checkpoint(confidence_bundle_version="2.0.0")
        with pytest.raises(CheckpointValidationError, match="confidence_bundle_version mismatch"):
            import_snapshot(cp, ctrl)

    def test_integrity_hash_mismatch(self, ctrl):
        """Tampered checkpoint should be rejected."""
        cp = _make_checkpoint()
        # Tamper by creating a new checkpoint with wrong hash
        tampered = StateCheckpoint(
            checkpoint_id=cp.checkpoint_id,
            session_id=cp.session_id,
            sequence_id=cp.sequence_id,
            timestamp=cp.timestamp,
            checkpoint_version=cp.checkpoint_version,
            global_state_version=cp.global_state_version,
            strategy_object_version=cp.strategy_object_version,
            confidence_bundle_version=cp.confidence_bundle_version,
            asset_scope=cp.asset_scope,
            global_state={"mode": "EMERGENCY"},  # tampered
            regime_states=cp.regime_states,
            volatility_states=cp.volatility_states,
            strategy_states=cp.strategy_states,
            portfolio_state=cp.portfolio_state,
            active_failure_modes=cp.active_failure_modes,
            operating_mode=cp.operating_mode,
            integrity_hash=cp.integrity_hash,  # old hash
        )
        with pytest.raises(CheckpointValidationError, match="Integrity hash mismatch"):
            import_snapshot(tampered, ctrl)

    def test_all_four_versions_checked(self, ctrl):
        """Each of the 4 versions is independently validated."""
        versions = [
            "checkpoint_version",
            "global_state_version",
            "strategy_object_version",
            "confidence_bundle_version",
        ]
        for v in versions:
            cp = _make_checkpoint(**{v: "9.9.9"})
            with pytest.raises(CheckpointValidationError, match=f"{v} mismatch"):
                import_snapshot(cp, ctrl)


# =============================================================================
# SECTION 7 -- ROUND-TRIP
# =============================================================================

class TestRoundTrip:
    """Test export -> import round-trip consistency."""

    def test_full_round_trip(self, ctrl):
        """Export, modify, import should restore original state."""
        ctrl.update(
            meta_uncertainty=0.42,
            regime="RISK_ON",
            risk_mode="ELEVATED",
            realized_vol=0.15,
            forecast_vol=0.18,
            vol_regime="ELEVATED",
            vol_percentile=0.75,
            regime_confidence=0.88,
            regime_age_bars=5,
            strategy_mode="MEAN_REVERSION",
            weight_scalar=0.6,
            gross_exposure=0.8,
            net_exposure=0.5,
        )
        cp = export_snapshot(
            ctrl, "CP-RT", "S-RT", 1, 2000.0,
            asset_scope=("BTC", "ETH"),
            active_failure_modes=("FM-03",),
            operating_mode="HYBRID",
        )

        # Modify state
        ctrl.update(meta_uncertainty=0.0, regime="UNKNOWN", risk_mode="NORMAL")

        # Restore
        result = import_snapshot(cp, ctrl)
        assert result.meta_uncertainty == 0.42
        assert result.regime == "RISK_ON"
        assert result.risk_mode == "ELEVATED"
        assert result.realized_vol == 0.15
        assert result.forecast_vol == 0.18
        assert result.vol_regime == "ELEVATED"

    def test_multiple_round_trips(self, ctrl):
        """Multiple export/import cycles should be consistent."""
        for i in range(5):
            mu = i * 0.1
            ctrl.update(meta_uncertainty=mu)
            cp = export_snapshot(ctrl, f"CP-{i}", "S-001", i, 1000.0 + i)

            ctrl.update(meta_uncertainty=0.99)
            import_snapshot(cp, ctrl)
            assert ctrl.get_state().meta_uncertainty == mu

    def test_round_trip_across_singleton_reset(self):
        """Checkpoint should survive singleton reset."""
        ctrl1 = GlobalSystemStateController.get_instance()
        ctrl1.update(meta_uncertainty=0.77, regime="CRISIS")
        cp = export_snapshot(ctrl1, "CP-001", "S-001", 0, 1000.0)

        GlobalSystemStateController._reset_singleton()
        ctrl2 = GlobalSystemStateController.get_instance()
        assert ctrl2.get_state().meta_uncertainty == 0.0

        import_snapshot(cp, ctrl2)
        assert ctrl2.get_state().meta_uncertainty == 0.77
        assert ctrl2.get_state().regime == "CRISIS"


# =============================================================================
# SECTION 8 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    """Test deterministic behavior (DET-07)."""

    def test_same_state_same_checkpoint(self, ctrl):
        """Same state should produce identical checkpoint (except version)."""
        cp1 = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        cp2 = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert cp1 == cp2

    def test_same_state_same_hash(self, ctrl):
        cp1 = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        cp2 = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert cp1.integrity_hash == cp2.integrity_hash

    def test_different_state_different_hash(self, ctrl):
        cp1 = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        ctrl.update(meta_uncertainty=0.5)
        cp2 = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert cp1.integrity_hash != cp2.integrity_hash


# =============================================================================
# SECTION 9 -- EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_large_sequence_id(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 999999, 1000.0)
        assert cp.sequence_id == 999999

    def test_zero_timestamp(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 0.0)
        assert cp.timestamp == 0.0

    def test_negative_timestamp(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, -100.0)
        assert cp.timestamp == -100.0

    def test_empty_regime_states_default(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert cp.regime_states == {}

    def test_empty_volatility_states_default(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert cp.volatility_states == {}

    def test_empty_strategy_states_default(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert cp.strategy_states == {}

    def test_empty_portfolio_state_default(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert cp.portfolio_state == {}

    def test_empty_failure_modes_default(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert cp.active_failure_modes == ()

    def test_none_regime_states_becomes_empty(self, ctrl):
        cp = export_snapshot(
            ctrl, "CP-001", "S-001", 0, 1000.0,
            regime_states=None,
        )
        assert cp.regime_states == {}

    def test_none_volatility_states_becomes_empty(self, ctrl):
        cp = export_snapshot(
            ctrl, "CP-001", "S-001", 0, 1000.0,
            volatility_states=None,
        )
        assert cp.volatility_states == {}

    def test_none_strategy_states_becomes_empty(self, ctrl):
        cp = export_snapshot(
            ctrl, "CP-001", "S-001", 0, 1000.0,
            strategy_states=None,
        )
        assert cp.strategy_states == {}

    def test_none_portfolio_state_becomes_empty(self, ctrl):
        cp = export_snapshot(
            ctrl, "CP-001", "S-001", 0, 1000.0,
            portfolio_state=None,
        )
        assert cp.portfolio_state == {}

    def test_global_state_includes_version(self, ctrl):
        cp = export_snapshot(ctrl, "CP-001", "S-001", 0, 1000.0)
        assert "version" in cp.global_state

    def test_checkpoint_preserves_tuple_types(self, ctrl):
        cp = export_snapshot(
            ctrl, "CP-001", "S-001", 0, 1000.0,
            asset_scope=("BTC",),
            active_failure_modes=("FM-03",),
        )
        assert isinstance(cp.asset_scope, tuple)
        assert isinstance(cp.active_failure_modes, tuple)
