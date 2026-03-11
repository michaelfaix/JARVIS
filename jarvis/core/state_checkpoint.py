# =============================================================================
# jarvis/core/state_checkpoint.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, State Checkpointing
# ARCHITECTURE.md Section 11 (Master Data Flow), Section 12 (Write Permissions)
# =============================================================================
#
# SCOPE
# -----
# State checkpoint export/import for session persistence and recovery.
# Captures full system state as an immutable snapshot, computes integrity
# hash for tamper detection, and restores state via the canonical
# ctrl.update() mutation path.
#
# Public symbols:
#   CHECKPOINT_SCHEMA_VERSION    Current checkpoint schema version string
#   GLOBAL_STATE_VERSION         Current global state schema version string
#   STRATEGY_OBJECT_VERSION      Current strategy object schema version string
#   CONFIDENCE_BUNDLE_VERSION    Current confidence bundle schema version string
#   StateCheckpoint              Frozen dataclass for checkpoint snapshot
#   CheckpointValidationError    Error for checkpoint validation failures
#   export_snapshot              Export current system state to checkpoint
#   import_snapshot              Restore checkpoint state to controller
#   compute_integrity_hash       Compute SHA-256 integrity hash
#
# INVARIANTS
# ----------
# 1. Checkpoints are immutable after creation (frozen dataclass).
# 2. Integrity hash covers ALL state fields except itself.
# 3. Import validates 4 schema versions + integrity hash (all hard errors).
# 4. Restoration uses ONLY ctrl.update() -- no direct field assignment.
# 5. Zero execution fields in checkpoint (P0 classification).
#
# WRITE PERMISSIONS
# -----------------
#   state_checkpoint.py may write: nothing (read-only export + ctrl.update())
#   FORBIDDEN from writing: Any state object directly
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, hashlib, json, typing
#   internal:  jarvis.core.global_state_controller (GlobalState,
#              GlobalSystemStateController, UPDATABLE_FIELDS)
#   PROHIBITED: numpy, logging, random, file IO, network IO, datetime.now()
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects beyond ctrl.update() on import.
# DET-05  No datetime.now() / time.time().
# DET-07  Same inputs = identical checkpoint.
# =============================================================================

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields as dc_fields
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from jarvis.core.global_state_controller import (
    GlobalState,
    GlobalSystemStateController,
    UPDATABLE_FIELDS,
)

__all__ = [
    "CHECKPOINT_SCHEMA_VERSION",
    "GLOBAL_STATE_VERSION",
    "STRATEGY_OBJECT_VERSION",
    "CONFIDENCE_BUNDLE_VERSION",
    "StateCheckpoint",
    "CheckpointValidationError",
    "export_snapshot",
    "import_snapshot",
    "compute_integrity_hash",
]


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

CHECKPOINT_SCHEMA_VERSION: str = "1.0.0"
GLOBAL_STATE_VERSION: str = "1.0.0"
STRATEGY_OBJECT_VERSION: str = "1.0.0"
CONFIDENCE_BUNDLE_VERSION: str = "1.0.0"


# =============================================================================
# SECTION 2 -- EXCEPTIONS
# =============================================================================

class CheckpointValidationError(Exception):
    """Raised when checkpoint validation fails during import."""
    pass


# =============================================================================
# SECTION 3 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class StateCheckpoint:
    """
    Immutable state checkpoint snapshot.

    Captures the full system state at a point in time for persistence
    and recovery.  The integrity_hash covers all fields except itself.

    Fields:
        checkpoint_id:              Unique checkpoint identifier.
        session_id:                 Session this checkpoint belongs to.
        sequence_id:                Monotonic sequence within session.
        timestamp:                  Caller-provided timestamp (DET-05).
        checkpoint_version:         Checkpoint schema version.
        global_state_version:       GlobalState schema version.
        strategy_object_version:    Strategy object schema version.
        confidence_bundle_version:  Confidence bundle schema version.
        asset_scope:                Tuple of asset symbols in scope.
        global_state:               Dict of all GlobalState field values.
        regime_states:              Dict of regime state per asset.
        volatility_states:          Dict of volatility state per asset.
        strategy_states:            Dict of strategy state per asset.
        portfolio_state:            Dict of portfolio-level state.
        active_failure_modes:       Tuple of active failure mode codes.
        operating_mode:             Current operating mode string.
        integrity_hash:             SHA-256 hash for tamper detection.
    """
    checkpoint_id:              str
    session_id:                 str
    sequence_id:                int
    timestamp:                  float
    checkpoint_version:         str
    global_state_version:       str
    strategy_object_version:    str
    confidence_bundle_version:  str
    asset_scope:                Tuple[str, ...]
    global_state:               Dict[str, Any]
    regime_states:              Dict[str, Any]
    volatility_states:          Dict[str, Any]
    strategy_states:            Dict[str, Any]
    portfolio_state:            Dict[str, Any]
    active_failure_modes:       Tuple[str, ...]
    operating_mode:             str
    integrity_hash:             str


# =============================================================================
# SECTION 4 -- INTEGRITY HASH
# =============================================================================

def compute_integrity_hash(checkpoint_dict: Dict[str, Any]) -> str:
    """
    Compute SHA-256 integrity hash over all checkpoint fields
    except 'integrity_hash' itself.

    Uses canonical JSON serialization (sort_keys=True, default=str)
    for deterministic hashing.

    Args:
        checkpoint_dict: Dictionary of checkpoint field values.

    Returns:
        Hex-encoded SHA-256 hash string.

    Raises:
        TypeError: If checkpoint_dict is not a dict.
    """
    if not isinstance(checkpoint_dict, dict):
        raise TypeError(
            f"checkpoint_dict must be a dict, "
            f"got {type(checkpoint_dict).__name__}"
        )

    # Exclude integrity_hash from the hash computation
    hashable = {
        k: v for k, v in checkpoint_dict.items()
        if k != "integrity_hash"
    }

    canonical = json.dumps(hashable, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# =============================================================================
# SECTION 5 -- EXPORT
# =============================================================================

def export_snapshot(
    ctrl: GlobalSystemStateController,
    checkpoint_id: str,
    session_id: str,
    sequence_id: int,
    timestamp: float,
    asset_scope: Tuple[str, ...] = (),
    regime_states: Optional[Dict[str, Any]] = None,
    volatility_states: Optional[Dict[str, Any]] = None,
    strategy_states: Optional[Dict[str, Any]] = None,
    portfolio_state: Optional[Dict[str, Any]] = None,
    active_failure_modes: Tuple[str, ...] = (),
    operating_mode: str = "HISTORICAL",
) -> StateCheckpoint:
    """
    Export current system state to an immutable checkpoint.

    Reads the current GlobalState from the controller and packages
    it with session metadata into a StateCheckpoint with integrity hash.

    Args:
        ctrl:                   GlobalSystemStateController instance.
        checkpoint_id:          Unique checkpoint ID.
        session_id:             Session ID.
        sequence_id:            Monotonic sequence within session.
        timestamp:              Caller-provided timestamp (DET-05).
        asset_scope:            Asset symbols in scope.
        regime_states:          Per-asset regime state (default empty).
        volatility_states:      Per-asset volatility state (default empty).
        strategy_states:        Per-asset strategy state (default empty).
        portfolio_state:        Portfolio-level state (default empty).
        active_failure_modes:   Active failure mode codes.
        operating_mode:         Operating mode string.

    Returns:
        StateCheckpoint with computed integrity hash.

    Raises:
        TypeError: If arguments have wrong types.
        ValueError: If required string fields are empty or sequence_id < 0.
    """
    # Type validation
    if not isinstance(ctrl, GlobalSystemStateController):
        raise TypeError(
            f"ctrl must be a GlobalSystemStateController, "
            f"got {type(ctrl).__name__}"
        )
    if not isinstance(checkpoint_id, str):
        raise TypeError(
            f"checkpoint_id must be a string, "
            f"got {type(checkpoint_id).__name__}"
        )
    if not isinstance(session_id, str):
        raise TypeError(
            f"session_id must be a string, "
            f"got {type(session_id).__name__}"
        )
    if not isinstance(sequence_id, int) or isinstance(sequence_id, bool):
        raise TypeError(
            f"sequence_id must be an int, "
            f"got {type(sequence_id).__name__}"
        )
    if not isinstance(timestamp, (int, float)):
        raise TypeError(
            f"timestamp must be numeric, "
            f"got {type(timestamp).__name__}"
        )

    # Value validation
    if not checkpoint_id:
        raise ValueError("checkpoint_id must not be empty")
    if not session_id:
        raise ValueError("session_id must not be empty")
    if sequence_id < 0:
        raise ValueError(f"sequence_id must be >= 0, got {sequence_id}")

    # Read current state from controller
    state = ctrl.get_state()
    global_state_dict = {
        f.name: getattr(state, f.name)
        for f in dc_fields(state)
    }

    # Build checkpoint dict (without integrity_hash)
    checkpoint_dict: Dict[str, Any] = {
        "checkpoint_id": checkpoint_id,
        "session_id": session_id,
        "sequence_id": sequence_id,
        "timestamp": float(timestamp),
        "checkpoint_version": CHECKPOINT_SCHEMA_VERSION,
        "global_state_version": GLOBAL_STATE_VERSION,
        "strategy_object_version": STRATEGY_OBJECT_VERSION,
        "confidence_bundle_version": CONFIDENCE_BUNDLE_VERSION,
        "asset_scope": tuple(asset_scope),
        "global_state": dict(global_state_dict),
        "regime_states": dict(regime_states) if regime_states else {},
        "volatility_states": dict(volatility_states) if volatility_states else {},
        "strategy_states": dict(strategy_states) if strategy_states else {},
        "portfolio_state": dict(portfolio_state) if portfolio_state else {},
        "active_failure_modes": tuple(active_failure_modes),
        "operating_mode": operating_mode,
    }

    # Compute integrity hash
    integrity_hash = compute_integrity_hash(checkpoint_dict)

    return StateCheckpoint(
        checkpoint_id=checkpoint_dict["checkpoint_id"],
        session_id=checkpoint_dict["session_id"],
        sequence_id=checkpoint_dict["sequence_id"],
        timestamp=checkpoint_dict["timestamp"],
        checkpoint_version=checkpoint_dict["checkpoint_version"],
        global_state_version=checkpoint_dict["global_state_version"],
        strategy_object_version=checkpoint_dict["strategy_object_version"],
        confidence_bundle_version=checkpoint_dict["confidence_bundle_version"],
        asset_scope=checkpoint_dict["asset_scope"],
        global_state=checkpoint_dict["global_state"],
        regime_states=checkpoint_dict["regime_states"],
        volatility_states=checkpoint_dict["volatility_states"],
        strategy_states=checkpoint_dict["strategy_states"],
        portfolio_state=checkpoint_dict["portfolio_state"],
        active_failure_modes=checkpoint_dict["active_failure_modes"],
        operating_mode=checkpoint_dict["operating_mode"],
        integrity_hash=integrity_hash,
    )


# =============================================================================
# SECTION 6 -- IMPORT
# =============================================================================

def _validate_checkpoint_versions(checkpoint: StateCheckpoint) -> None:
    """
    Validate all 4 schema versions in the checkpoint.

    Hard errors -- no silent migration allowed.

    Raises:
        CheckpointValidationError: If any version mismatches.
    """
    checks = [
        ("checkpoint_version", checkpoint.checkpoint_version, CHECKPOINT_SCHEMA_VERSION),
        ("global_state_version", checkpoint.global_state_version, GLOBAL_STATE_VERSION),
        ("strategy_object_version", checkpoint.strategy_object_version, STRATEGY_OBJECT_VERSION),
        ("confidence_bundle_version", checkpoint.confidence_bundle_version, CONFIDENCE_BUNDLE_VERSION),
    ]
    for field_name, actual, expected in checks:
        if actual != expected:
            raise CheckpointValidationError(
                f"{field_name} mismatch: checkpoint has {actual!r}, "
                f"current system expects {expected!r}. "
                f"No silent migration — version must match exactly."
            )


def _validate_checkpoint_integrity(checkpoint: StateCheckpoint) -> None:
    """
    Validate the integrity hash of the checkpoint.

    Recomputes the hash from checkpoint fields and compares
    against the stored integrity_hash.

    Raises:
        CheckpointValidationError: If hash does not match.
    """
    checkpoint_dict = {
        f.name: getattr(checkpoint, f.name)
        for f in dc_fields(checkpoint)
    }
    expected_hash = compute_integrity_hash(checkpoint_dict)
    if checkpoint.integrity_hash != expected_hash:
        raise CheckpointValidationError(
            f"Integrity hash mismatch: stored={checkpoint.integrity_hash!r}, "
            f"computed={expected_hash!r}. Checkpoint may be tampered."
        )


def import_snapshot(
    checkpoint: StateCheckpoint,
    ctrl: GlobalSystemStateController,
) -> GlobalState:
    """
    Restore checkpoint state to the controller.

    Validates 4 schema versions and integrity hash (all hard errors),
    then restores global_state fields via ctrl.update().

    Only fields in UPDATABLE_FIELDS are restored to the controller.
    The 'version' field is excluded (managed by the controller).

    Args:
        checkpoint: StateCheckpoint to restore.
        ctrl:       GlobalSystemStateController to update.

    Returns:
        New GlobalState after restoration.

    Raises:
        TypeError:                  If arguments have wrong types.
        CheckpointValidationError:  If version or integrity validation fails.
    """
    if not isinstance(checkpoint, StateCheckpoint):
        raise TypeError(
            f"checkpoint must be a StateCheckpoint, "
            f"got {type(checkpoint).__name__}"
        )
    if not isinstance(ctrl, GlobalSystemStateController):
        raise TypeError(
            f"ctrl must be a GlobalSystemStateController, "
            f"got {type(ctrl).__name__}"
        )

    # Step 1: Validate schema versions (4 checks, all hard errors)
    _validate_checkpoint_versions(checkpoint)

    # Step 2: Validate integrity hash
    _validate_checkpoint_integrity(checkpoint)

    # Step 3: Extract updatable fields from global_state
    update_kwargs = {
        k: v for k, v in checkpoint.global_state.items()
        if k in UPDATABLE_FIELDS
    }

    # Step 4: Restore via canonical mutation path
    if update_kwargs:
        return ctrl.update(**update_kwargs)

    # No updatable fields -- return current state unchanged
    return ctrl.get_state()
