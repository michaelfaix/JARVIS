# =============================================================================
# JARVIS v6.1.0 -- SYSTEM MODE
# File:   jarvis/core/system_mode.py
# Version: 1.0.0
# =============================================================================
#
# SCOPE
# -----
# Canonical SystemMode enum and deterministic transition validation.
# Defines the three operating modes (HISTORICAL, LIVE_ANALYTICAL, HYBRID)
# and their permitted transitions per FAS v6.0.1 Section "Operating Modes".
#
# CLASSIFICATION: P1 Governance Control — below P0.
#
# PUBLIC SYMBOLS
# --------------
#   SystemMode              Enum with HISTORICAL, LIVE_ANALYTICAL, HYBRID
#   PERMITTED_TRANSITIONS   Dict mapping each mode to set of valid targets
#   is_valid_transition()   Pure predicate for transition legality
#   validate_transition()   Raises on illegal transition
#
# FAS MODE CONSTRAINTS
# --------------------
# Modes affect ONLY:
#   - Data source selection
#   - Update frequency and refresh policy
#   - State update cycle (batch vs incremental)
#
# Modes must NOT:
#   - Disable any analytical layer
#   - Modify logic thresholds or constants
#   - Bypass Risk Engine or Failure Modes
#   - Alter P0 classification rules
#   - Introduce execution semantics
#   - Enable broker API connections
#   - Permit order transmission in any mode
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  No I/O, no logging, no datetime.now().
# DET-05  All branching is deterministic.
# DET-06  Fixed literals are not parametrised.
# DET-07  Same inputs = bit-identical outputs.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No numpy / scipy
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
#   No threading (stateful controller belongs in a higher layer)
# =============================================================================

from __future__ import annotations

from enum import Enum, unique
from typing import Dict, FrozenSet


# ---------------------------------------------------------------------------
# CANONICAL ENUM
# ---------------------------------------------------------------------------

@unique
class SystemMode(Enum):
    """
    Operating mode for the JARVIS platform.

    HISTORICAL:
        Data source:      Static historical dataset.
        Update frequency: Batch / on-demand recompute.
        Refresh policy:   Full recompute allowed; backtest loops allowed.
        Use case:         Strategy research, backtesting, regime analysis.
        State behavior:   Full state reset permitted; no incremental constraint.

    LIVE_ANALYTICAL:
        Data source:      Live market data stream (read-only, research only).
        Update frequency: On confirmed candle / configurable tick aggregation.
        Refresh policy:   Incremental updates only; no full state reset.
        Use case:         Real-time analysis and monitoring (no execution).
        State behavior:   Rolling window updates; deterministic update cycle.
        Transition:       Terminal mode — no further transitions permitted.

    HYBRID:
        Data source:      Historical backfill + live incremental after sync point.
        Update frequency: Historical: batch; Live: on confirmed candle.
        Refresh policy:   Strict separation of backtest window and live window.
        Use case:         Transition from backtesting to live monitoring.
        State behavior:   Historical backfill first; live incremental after sync.

    All modes are analysis-only. No mode enables order transmission or
    broker API connections (P0 invariant).
    """
    HISTORICAL      = "HISTORICAL"
    LIVE_ANALYTICAL = "LIVE_ANALYTICAL"
    HYBRID          = "HYBRID"


# ---------------------------------------------------------------------------
# PERMITTED TRANSITIONS (per FAS v6.0.1 lines 15595-15613)
# ---------------------------------------------------------------------------
# HISTORICAL     -> LIVE_ANALYTICAL  (not recommended; requires full restart)
# HISTORICAL     -> HYBRID           (normal for hybrid session startup)
# HYBRID         -> LIVE_ANALYTICAL  (after sync_point stabilizes)
# LIVE_ANALYTICAL -> (none; terminal mode for session)
#
# Forbidden:
#   - Running two modes simultaneously
#   - Partial mode switch
#   - Reverse transitions (LIVE_ANALYTICAL -> HISTORICAL, etc.)

PERMITTED_TRANSITIONS: Dict[SystemMode, FrozenSet[SystemMode]] = {
    SystemMode.HISTORICAL:      frozenset({SystemMode.LIVE_ANALYTICAL, SystemMode.HYBRID}),
    SystemMode.LIVE_ANALYTICAL: frozenset(),
    SystemMode.HYBRID:          frozenset({SystemMode.LIVE_ANALYTICAL}),
}


# ---------------------------------------------------------------------------
# TRANSITION VALIDATION (pure functions)
# ---------------------------------------------------------------------------

def is_valid_transition(current: SystemMode, target: SystemMode) -> bool:
    """
    Check whether a mode transition is permitted.

    Args:
        current: The current SystemMode.
        target:  The desired SystemMode.

    Returns:
        True if the transition is permitted, False otherwise.
        Self-transitions (current == target) return False.
    """
    if not isinstance(current, SystemMode):
        raise TypeError(
            f"current must be a SystemMode instance; got {type(current).__name__}"
        )
    if not isinstance(target, SystemMode):
        raise TypeError(
            f"target must be a SystemMode instance; got {type(target).__name__}"
        )
    return target in PERMITTED_TRANSITIONS[current]


def validate_transition(current: SystemMode, target: SystemMode) -> None:
    """
    Validate a mode transition; raise on illegal transition.

    Args:
        current: The current SystemMode.
        target:  The desired SystemMode.

    Raises:
        TypeError:  If current or target is not a SystemMode instance.
        ValueError: If the transition is not permitted.
    """
    if not is_valid_transition(current, target):
        permitted = PERMITTED_TRANSITIONS.get(current, frozenset())
        if permitted:
            allowed_str = ", ".join(m.value for m in sorted(permitted, key=lambda m: m.value))
        else:
            allowed_str = "(none — terminal mode)"
        raise ValueError(
            f"Transition from {current.value} to {target.value} is not permitted. "
            f"Allowed transitions from {current.value}: {allowed_str}"
        )


__all__ = [
    "SystemMode",
    "PERMITTED_TRANSITIONS",
    "is_valid_transition",
    "validate_transition",
]
