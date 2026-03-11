# =============================================================================
# jarvis/core/state_refresh_policy.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, lines 6917-7008
# =============================================================================
#
# SCOPE
# -----
# Mode-aware state refresh policy controlling batch vs. incremental update
# behavior.  Defines per-mode constraints for state updates across all
# three operating modes (HISTORICAL, LIVE_ANALYTICAL, HYBRID).
#
# Public symbols:
#   RefreshPolicy               Frozen dataclass for mode-specific constraints
#   REFRESH_POLICIES            Dict mapping SystemMode -> RefreshPolicy
#   get_refresh_policy          Lookup function with validation
#   is_recompute_allowed        Quick predicate for full recompute permission
#   is_incremental_only         Quick predicate for incremental constraint
#
# INVARIANTS
# ----------
# 1. Policies are immutable (frozen dataclass).
# 2. REFRESH_POLICIES is a complete mapping -- every SystemMode has a policy.
# 3. All state updates route through GlobalSystemStateController.update().
# 4. Modes affect ONLY data sourcing, refresh timing, window management.
# 5. Modes must NOT disable analytical layers, modify thresholds, alter P0.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, typing
#   internal:  jarvis.core.system_mode (SystemMode)
#   PROHIBITED: numpy, logging, random, file IO, network IO, datetime.now()
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-06  Fixed literals are not parametrisable.
# DET-07  Same inputs = identical outputs.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from jarvis.core.system_mode import SystemMode

__all__ = [
    "RefreshPolicy",
    "REFRESH_POLICIES",
    "get_refresh_policy",
    "is_recompute_allowed",
    "is_incremental_only",
]


# =============================================================================
# SECTION 1 -- REFRESH POLICY DATACLASS
# =============================================================================

@dataclass(frozen=True)
class RefreshPolicy:
    """
    Mode-specific state refresh constraints.

    Fields:
        mode:                       Which operating mode this policy applies to.
        full_recompute_allowed:     Can state be completely reset from scratch?
        backtest_loop_allowed:      Can state be backtest-looped (backward)?
        incremental_only:           Are updates restricted to incremental diffs?
        rolling_window_updates:     Are updates constrained to rolling window?
        deterministic_cycle:        Is there a fixed, reproducible update cycle?
        backfill_allowed:           Can historical backfill proceed?
        live_sync_point_required:   Is sync_point enforcement required?
    """
    mode:                     SystemMode
    full_recompute_allowed:   bool
    backtest_loop_allowed:    bool
    incremental_only:         bool
    rolling_window_updates:   bool
    deterministic_cycle:      bool
    backfill_allowed:         bool
    live_sync_point_required: bool


# =============================================================================
# SECTION 2 -- POLICY TABLE
# =============================================================================

REFRESH_POLICIES: Dict[SystemMode, RefreshPolicy] = {

    # HISTORICAL: Full recompute, backtest loops, batch processing.
    SystemMode.HISTORICAL: RefreshPolicy(
        mode=SystemMode.HISTORICAL,
        full_recompute_allowed=True,
        backtest_loop_allowed=True,
        incremental_only=False,
        rolling_window_updates=False,
        deterministic_cycle=True,
        backfill_allowed=True,
        live_sync_point_required=False,
    ),

    # LIVE_ANALYTICAL: Incremental only, rolling window, no state reset.
    SystemMode.LIVE_ANALYTICAL: RefreshPolicy(
        mode=SystemMode.LIVE_ANALYTICAL,
        full_recompute_allowed=False,
        backtest_loop_allowed=False,
        incremental_only=True,
        rolling_window_updates=True,
        deterministic_cycle=True,
        backfill_allowed=False,
        live_sync_point_required=False,
    ),

    # HYBRID: Backfill then live; strict window separation via sync_point.
    SystemMode.HYBRID: RefreshPolicy(
        mode=SystemMode.HYBRID,
        full_recompute_allowed=True,
        backtest_loop_allowed=True,
        incremental_only=False,
        rolling_window_updates=True,
        deterministic_cycle=True,
        backfill_allowed=True,
        live_sync_point_required=True,
    ),
}


# =============================================================================
# SECTION 3 -- LOOKUP FUNCTIONS
# =============================================================================

def get_refresh_policy(mode: SystemMode) -> RefreshPolicy:
    """
    Look up the refresh policy for a given operating mode.

    Args:
        mode: SystemMode instance.

    Returns:
        RefreshPolicy for the requested mode.

    Raises:
        TypeError:  If mode is not a SystemMode instance.
        KeyError:   If mode is not in REFRESH_POLICIES (should not happen
                    if SystemMode enum is complete).
    """
    if not isinstance(mode, SystemMode):
        raise TypeError(
            f"mode must be a SystemMode instance, "
            f"got {type(mode).__name__}"
        )
    return REFRESH_POLICIES[mode]


def is_recompute_allowed(mode: SystemMode) -> bool:
    """
    Quick predicate: is full state recompute allowed in this mode?

    Args:
        mode: SystemMode instance.

    Returns:
        True if full_recompute_allowed is True for this mode.

    Raises:
        TypeError: If mode is not a SystemMode instance.
    """
    return get_refresh_policy(mode).full_recompute_allowed


def is_incremental_only(mode: SystemMode) -> bool:
    """
    Quick predicate: are only incremental updates allowed in this mode?

    Args:
        mode: SystemMode instance.

    Returns:
        True if incremental_only is True for this mode.

    Raises:
        TypeError: If mode is not a SystemMode instance.
    """
    return get_refresh_policy(mode).incremental_only
