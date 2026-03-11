# =============================================================================
# jarvis/core/hybrid_coordinator.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, HYBRID MODE COORDINATION
# ARCHITECTURE.md Section 11 (Stage 0), Section 12 (Write Permission Matrix)
# =============================================================================
#
# SCOPE
# -----
# Orchestrates the transition from historical backfill to live incremental
# analysis in MODE_HYBRID.  Detects when live data becomes valid, atomically
# sets the sync_point, and manages phase transitions.
#
# PHASES
# ------
#   BACKFILL   Historical data provider active, batch recompute.
#   SYNCING    First valid live candle detected, setting sync_point.
#   LIVE       Live data provider active, incremental updates only.
#   COMPLETED  Session ended (terminal).
#   FAILED     Unrecoverable error during coordination (terminal).
#
# WRITE PERMISSIONS (from FAS S37 Write Permission Matrix)
# --------------------------------------------------------
#   hybrid_coordinator.py may ONLY write:
#     - hybrid_sync_point (once only, immutable after setting)
#     - operating_mode
#   All other state fields: FORBIDDEN.
#
# Public symbols:
#   VALID_PHASES                  Tuple of valid coordinator phases
#   MAX_BACKFILL_DURATION_S       Default max backfill duration (600s = 10 min)
#   HybridPhase                  Phase enum (str enum)
#   SyncPointResult              Frozen dataclass for sync attempt result
#   CoordinatorState             Frozen dataclass for coordinator snapshot
#   HybridCoordinator            Main coordinator class
#
# CLASSIFICATION
# --------------
# P0 — Pure analysis and strategy research platform.
# This module coordinates data sources.  It does not call broker APIs,
# does not emit execution events, does not manage real capital.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, enum, typing
#   internal:  NONE (coordinator is standalone; callers pass gate results)
#   PROHIBITED: numpy, logging, random, file IO, network IO, datetime.now()
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly (timestamps, gate results).
# DET-03  No side effects beyond internal phase state.
# DET-05  No datetime.now() / time.time().  All timestamps caller-provided.
# DET-07  Same sequence of calls = identical phase transitions.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique
from typing import List, Optional, Tuple

__all__ = [
    "VALID_PHASES",
    "MAX_BACKFILL_DURATION_S",
    "HybridPhase",
    "SyncPointResult",
    "CoordinatorState",
    "HybridCoordinator",
]


# =============================================================================
# SECTION 1 -- CONSTANTS AND ENUMS
# =============================================================================

@unique
class HybridPhase(str, Enum):
    """
    Coordinator phase in hybrid mode lifecycle.

    BACKFILL:   Historical data processing (batch recompute allowed).
    SYNCING:    Transition detected, sync_point being set.
    LIVE:       Live incremental mode active.
    COMPLETED:  Session ended normally (terminal).
    FAILED:     Unrecoverable error (terminal).
    """
    BACKFILL  = "BACKFILL"
    SYNCING   = "SYNCING"
    LIVE      = "LIVE"
    COMPLETED = "COMPLETED"
    FAILED    = "FAILED"


VALID_PHASES: Tuple[str, ...] = tuple(p.value for p in HybridPhase)

# Default maximum backfill duration: 10 minutes (FAS CONSTRAINT 8).
MAX_BACKFILL_DURATION_S: float = 600.0

# Permitted phase transitions (directed graph).
_PERMITTED_TRANSITIONS = {
    HybridPhase.BACKFILL:  frozenset({HybridPhase.SYNCING, HybridPhase.FAILED}),
    HybridPhase.SYNCING:   frozenset({HybridPhase.LIVE, HybridPhase.FAILED}),
    HybridPhase.LIVE:      frozenset({HybridPhase.COMPLETED, HybridPhase.FAILED}),
    HybridPhase.COMPLETED: frozenset(),
    HybridPhase.FAILED:    frozenset(),
}


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class SyncPointResult:
    """
    Result of a sync_point detection attempt.

    Fields:
        sync_detected:     True if sync_point conditions are met.
        sync_timestamp:    The live candle timestamp that triggered sync.
                           None if not detected.
        integrity_passed:  True if the live data integrity gate passed.
        reason:            Human-readable explanation.
    """
    sync_detected:    bool
    sync_timestamp:   Optional[float]
    integrity_passed: bool
    reason:           str


@dataclass(frozen=True)
class CoordinatorState:
    """
    Immutable snapshot of coordinator state.

    Fields:
        phase:                Current HybridPhase.
        sync_point:           Set once, then immutable.  None until sync detected.
        backfill_start:       Backfill start timestamp (caller-provided at init).
        backfill_end:         Latest timestamp accepted as backfill data.
        elapsed_backfill_s:   Accumulated backfill duration in seconds.
        candles_processed:    Total candles processed across all phases.
        sync_attempts:        Number of sync_point detection attempts.
        version:              Monotonically increasing snapshot version.
    """
    phase:              HybridPhase
    sync_point:         Optional[float]
    backfill_start:     float
    backfill_end:       float
    elapsed_backfill_s: float
    candles_processed:  int
    sync_attempts:      int
    version:            int


# =============================================================================
# SECTION 3 -- COORDINATOR
# =============================================================================

class HybridCoordinator:
    """
    Orchestrates hybrid mode transitions from backfill to live.

    Lifecycle:
        1. Construct with backfill_start, backfill_end, max_backfill_duration_s.
        2. Call process_backfill_candle() for each historical candle.
        3. Call attempt_sync() when live data becomes available.
        4. After sync, call process_live_candle() for each live candle.
        5. Call complete() when session ends.

    Thread safety: NOT thread-safe.  Single-threaded event processing assumed
    (per S37 Constraint 2: no parallel mutation).
    """

    def __init__(
        self,
        backfill_start: float,
        backfill_end: float,
        max_backfill_duration_s: float = MAX_BACKFILL_DURATION_S,
    ) -> None:
        """
        Initialize coordinator in BACKFILL phase.

        Args:
            backfill_start:         Timestamp of backfill start.
            backfill_end:           Latest timestamp accepted as backfill.
            max_backfill_duration_s: Max backfill duration (default 600s).

        Raises:
            TypeError:  If arguments are not numeric.
            ValueError: If backfill_end <= backfill_start or duration <= 0.
        """
        if not isinstance(backfill_start, (int, float)):
            raise TypeError(
                f"backfill_start must be numeric, got {type(backfill_start).__name__}"
            )
        if not isinstance(backfill_end, (int, float)):
            raise TypeError(
                f"backfill_end must be numeric, got {type(backfill_end).__name__}"
            )
        if not isinstance(max_backfill_duration_s, (int, float)):
            raise TypeError(
                f"max_backfill_duration_s must be numeric, "
                f"got {type(max_backfill_duration_s).__name__}"
            )
        if backfill_end <= backfill_start:
            raise ValueError(
                f"backfill_end ({backfill_end}) must be > "
                f"backfill_start ({backfill_start})"
            )
        if max_backfill_duration_s <= 0:
            raise ValueError(
                f"max_backfill_duration_s must be > 0, "
                f"got {max_backfill_duration_s}"
            )

        self._phase: HybridPhase = HybridPhase.BACKFILL
        self._sync_point: Optional[float] = None
        self._backfill_start: float = float(backfill_start)
        self._backfill_end: float = float(backfill_end)
        self._max_backfill_duration_s: float = float(max_backfill_duration_s)
        self._elapsed_backfill_s: float = 0.0
        self._candles_processed: int = 0
        self._sync_attempts: int = 0
        self._version: int = 1

    # -----------------------------------------------------------------
    # State snapshot
    # -----------------------------------------------------------------

    def get_state(self) -> CoordinatorState:
        """Return immutable snapshot of current coordinator state."""
        return CoordinatorState(
            phase=self._phase,
            sync_point=self._sync_point,
            backfill_start=self._backfill_start,
            backfill_end=self._backfill_end,
            elapsed_backfill_s=self._elapsed_backfill_s,
            candles_processed=self._candles_processed,
            sync_attempts=self._sync_attempts,
            version=self._version,
        )

    # -----------------------------------------------------------------
    # Phase transitions
    # -----------------------------------------------------------------

    def _transition(self, target: HybridPhase) -> None:
        """
        Transition to a new phase.  Validates against permitted transitions.

        Raises:
            ValueError: If transition is not permitted.
        """
        permitted = _PERMITTED_TRANSITIONS[self._phase]
        if target not in permitted:
            raise ValueError(
                f"Transition from {self._phase.value} to {target.value} "
                f"is not permitted. Allowed: "
                f"{sorted(p.value for p in permitted) if permitted else '(none — terminal)'}"
            )
        self._phase = target
        self._version += 1

    # -----------------------------------------------------------------
    # Backfill processing
    # -----------------------------------------------------------------

    def process_backfill_candle(self, duration_s: float) -> CoordinatorState:
        """
        Record processing of a single historical backfill candle.

        Accumulates elapsed backfill time.  Raises if backfill duration
        exceeds max_backfill_duration_s (FAS CONSTRAINT 8).

        Args:
            duration_s: Processing time for this candle in seconds.

        Returns:
            Updated CoordinatorState.

        Raises:
            ValueError: If not in BACKFILL phase.
            ValueError: If duration_s < 0.
            OverflowError: If elapsed backfill exceeds max duration.
        """
        if self._phase != HybridPhase.BACKFILL:
            raise ValueError(
                f"process_backfill_candle() requires BACKFILL phase, "
                f"current phase: {self._phase.value}"
            )
        if not isinstance(duration_s, (int, float)):
            raise TypeError(
                f"duration_s must be numeric, got {type(duration_s).__name__}"
            )
        if duration_s < 0:
            raise ValueError(f"duration_s must be >= 0, got {duration_s}")

        self._elapsed_backfill_s += duration_s
        self._candles_processed += 1
        self._version += 1

        if self._elapsed_backfill_s > self._max_backfill_duration_s:
            self._transition(HybridPhase.FAILED)
            raise OverflowError(
                f"Backfill duration {self._elapsed_backfill_s:.1f}s exceeds "
                f"maximum {self._max_backfill_duration_s:.1f}s "
                f"(FAS CONSTRAINT 8: NO_UNBOUNDED_BACKFILL_LOOPS)"
            )

        return self.get_state()

    # -----------------------------------------------------------------
    # Sync point detection
    # -----------------------------------------------------------------

    def attempt_sync(
        self,
        live_candle_timestamp: float,
        integrity_passed: bool,
    ) -> SyncPointResult:
        """
        Attempt to detect and set the sync_point.

        Conditions for sync_point (BOTH must be true):
          A. integrity_passed is True (all 5 Stage 0 checks passed).
          B. live_candle_timestamp > backfill_end.

        The sync_point is set ONCE and is immutable for the session.
        After sync, coordinator transitions BACKFILL -> SYNCING -> LIVE.

        Args:
            live_candle_timestamp: Timestamp of the live candle.
            integrity_passed:      Whether the integrity gate passed.

        Returns:
            SyncPointResult describing the outcome.

        Raises:
            ValueError: If not in BACKFILL phase.
            ValueError: If sync_point already set (immutability violation).
            TypeError:  If arguments have wrong types.
        """
        if self._phase != HybridPhase.BACKFILL:
            raise ValueError(
                f"attempt_sync() requires BACKFILL phase, "
                f"current phase: {self._phase.value}"
            )
        # sync_point immutability is enforced by the phase guard above:
        # after sync_point is set, phase transitions to LIVE, so any
        # subsequent attempt_sync() call is caught by the BACKFILL check.
        if not isinstance(live_candle_timestamp, (int, float)):
            raise TypeError(
                f"live_candle_timestamp must be numeric, "
                f"got {type(live_candle_timestamp).__name__}"
            )
        if not isinstance(integrity_passed, bool):
            raise TypeError(
                f"integrity_passed must be bool, "
                f"got {type(integrity_passed).__name__}"
            )

        self._sync_attempts += 1
        self._version += 1

        # Condition A: integrity gate must pass
        if not integrity_passed:
            return SyncPointResult(
                sync_detected=False,
                sync_timestamp=None,
                integrity_passed=False,
                reason="integrity gate failed — sync_point not set",
            )

        # Condition B: timestamp must exceed backfill_end
        if live_candle_timestamp <= self._backfill_end:
            return SyncPointResult(
                sync_detected=False,
                sync_timestamp=None,
                integrity_passed=True,
                reason=(
                    f"live_candle_timestamp {live_candle_timestamp} "
                    f"<= backfill_end {self._backfill_end} — "
                    f"sync_point not set"
                ),
            )

        # Both conditions met: set sync_point atomically
        self._sync_point = float(live_candle_timestamp)
        self._transition(HybridPhase.SYNCING)
        self._transition(HybridPhase.LIVE)

        return SyncPointResult(
            sync_detected=True,
            sync_timestamp=self._sync_point,
            integrity_passed=True,
            reason=(
                f"sync_point set at {self._sync_point} — "
                f"transitioned to LIVE"
            ),
        )

    # -----------------------------------------------------------------
    # Live processing
    # -----------------------------------------------------------------

    def process_live_candle(self) -> CoordinatorState:
        """
        Record processing of a single live candle after sync_point.

        Returns:
            Updated CoordinatorState.

        Raises:
            ValueError: If not in LIVE phase.
        """
        if self._phase != HybridPhase.LIVE:
            raise ValueError(
                f"process_live_candle() requires LIVE phase, "
                f"current phase: {self._phase.value}"
            )

        self._candles_processed += 1
        self._version += 1
        return self.get_state()

    # -----------------------------------------------------------------
    # Session completion
    # -----------------------------------------------------------------

    def complete(self) -> CoordinatorState:
        """
        Mark the session as completed.  Terminal state.

        Returns:
            Final CoordinatorState.

        Raises:
            ValueError: If not in LIVE phase.
        """
        if self._phase != HybridPhase.LIVE:
            raise ValueError(
                f"complete() requires LIVE phase, "
                f"current phase: {self._phase.value}"
            )
        self._transition(HybridPhase.COMPLETED)
        return self.get_state()

    # -----------------------------------------------------------------
    # Failure
    # -----------------------------------------------------------------

    def fail(self, reason: str) -> CoordinatorState:
        """
        Transition to FAILED state.  Terminal.

        Args:
            reason: Human-readable failure reason.

        Returns:
            Final CoordinatorState.

        Raises:
            TypeError:  If reason is not a string.
            ValueError: If reason is empty.
            ValueError: If already in a terminal phase.
        """
        if not isinstance(reason, str):
            raise TypeError(
                f"reason must be a string, got {type(reason).__name__}"
            )
        if not reason:
            raise ValueError("reason must not be empty")

        self._transition(HybridPhase.FAILED)
        return self.get_state()

    # -----------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------

    @property
    def phase(self) -> HybridPhase:
        """Current coordinator phase."""
        return self._phase

    @property
    def sync_point(self) -> Optional[float]:
        """Sync point timestamp, or None if not yet set."""
        return self._sync_point

    @property
    def is_terminal(self) -> bool:
        """True if coordinator is in a terminal phase (COMPLETED or FAILED)."""
        return self._phase in (HybridPhase.COMPLETED, HybridPhase.FAILED)

    @property
    def backfill_budget_remaining_s(self) -> float:
        """Remaining backfill time budget in seconds."""
        return max(0.0, self._max_backfill_duration_s - self._elapsed_backfill_s)
