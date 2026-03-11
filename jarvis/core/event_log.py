# =============================================================================
# jarvis/core/event_log.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, lines 7048-7091
# =============================================================================
#
# SCOPE
# -----
# Immutable event log for session recording.  Enables deterministic replay
# and audit.  Each entry records event type, payload, and state hashes
# before/after the event.  SHA-256 integrity chain covers all entries.
#
# Public symbols:
#   VALID_EVENT_TYPES         Tuple of valid event type strings
#   MAX_ENTRIES               Maximum entries per session (1,000,000)
#   VALID_OPERATING_MODES     Tuple of valid operating mode strings
#   EventType                 Enum for event types
#   EventLogEntry             Frozen dataclass for a single event
#   EventLog                  Session event log with integrity chain
#   EventLogOverflowError     Raised when MAX_ENTRIES exceeded
#
# INVARIANTS
# ----------
# 1. EventLogEntry is immutable after creation (frozen dataclass).
# 2. EventLog.entries is append-only during session.
# 3. sequence_id must be monotonically increasing per log.
# 4. genesis_state_hash and final_state_hash are set-once (immutable).
# 5. integrity_hash = SHA-256 of "|".join(state_hash_after) in order.
# 6. schema_version must match EVENT_LOG_VERSION at creation.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, enum, hashlib, typing
#   internal:  jarvis.core.schema_versions (EVENT_LOG_VERSION)
#   PROHIBITED: numpy, logging, random, file IO, network IO, datetime.now()
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects beyond internal append.
# DET-05  No datetime.now() / time.time().
# DET-07  Same sequence of append() calls = identical log.
# =============================================================================

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Any, Dict, List, Optional, Tuple

from jarvis.core.schema_versions import EVENT_LOG_VERSION

__all__ = [
    "VALID_EVENT_TYPES",
    "MAX_ENTRIES",
    "VALID_OPERATING_MODES",
    "EventType",
    "EventLogEntry",
    "EventLog",
    "EventLogOverflowError",
]


# =============================================================================
# SECTION 1 -- CONSTANTS AND ENUMS
# =============================================================================

@unique
class EventType(str, Enum):
    """
    Canonical event types for the event log.

    MARKET_DATA:        New market data ingested.
    REGIME_CHANGE:      Regime transition detected.
    FAILURE_MODE:       Failure mode activated/deactivated.
    EXPOSURE:           Exposure weight changed.
    STRATEGY_WEIGHT:    Strategy weight updated.
    CONFIDENCE_UPDATE:  Confidence bundle updated.
    """
    MARKET_DATA       = "market_data"
    REGIME_CHANGE     = "regime_change"
    FAILURE_MODE      = "failure_mode"
    EXPOSURE          = "exposure"
    STRATEGY_WEIGHT   = "strategy_weight_change"
    CONFIDENCE_UPDATE = "confidence_update"
    LAYER_TRANSITION  = "layer_transition"


VALID_EVENT_TYPES: Tuple[str, ...] = tuple(e.value for e in EventType)

MAX_ENTRIES: int = 1_000_000
"""Maximum entries per session before rotation required."""

VALID_OPERATING_MODES: Tuple[str, ...] = (
    "historical", "live_analytical", "hybrid",
)


# =============================================================================
# SECTION 2 -- EXCEPTIONS
# =============================================================================

class EventLogOverflowError(Exception):
    """Raised when appending would exceed MAX_ENTRIES."""
    pass


# =============================================================================
# SECTION 3 -- EVENT LOG ENTRY
# =============================================================================

@dataclass(frozen=True)
class EventLogEntry:
    """
    Immutable record of a single event.

    Fields:
        sequence_id:        Global monotonic sequence number.
        timestamp:          Caller-provided event timestamp (DET-05).
        event_type:         EventType value string.
        event_payload:      Serialised event data (dict).
        state_hash_before:  State hash before ctrl.update().
        state_hash_after:   State hash after ctrl.update().
    """
    sequence_id:       int
    timestamp:         float
    event_type:        str
    event_payload:     Dict[str, Any]
    state_hash_before: str
    state_hash_after:  str


# =============================================================================
# SECTION 4 -- EVENT LOG
# =============================================================================

class EventLog:
    """
    Session event log with SHA-256 integrity chain.

    Lifecycle:
        1. Construct with session_id, operating_mode, start_time.
        2. Set genesis_state_hash once.
        3. Append entries via append().
        4. Close session via close() which sets end_time and final_state_hash.
        5. Compute and validate integrity hash.

    Thread safety: NOT thread-safe.  Single-threaded event processing assumed.
    """

    def __init__(
        self,
        session_id: str,
        operating_mode: str,
        start_time: float,
        asset_scope: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize event log for a new session.

        Args:
            session_id:      Unique session identifier.
            operating_mode:  One of VALID_OPERATING_MODES.
            start_time:      Session start timestamp (caller-provided).
            asset_scope:     List of asset symbols covered.

        Raises:
            TypeError:  If arguments have wrong types.
            ValueError: If session_id is empty or operating_mode invalid.
        """
        if not isinstance(session_id, str):
            raise TypeError(
                f"session_id must be a string, got {type(session_id).__name__}"
            )
        if not session_id:
            raise ValueError("session_id must not be empty")
        if not isinstance(operating_mode, str):
            raise TypeError(
                f"operating_mode must be a string, "
                f"got {type(operating_mode).__name__}"
            )
        if operating_mode not in VALID_OPERATING_MODES:
            raise ValueError(
                f"operating_mode must be one of {VALID_OPERATING_MODES}, "
                f"got {operating_mode!r}"
            )
        if not isinstance(start_time, (int, float)):
            raise TypeError(
                f"start_time must be numeric, got {type(start_time).__name__}"
            )

        self._session_id: str = session_id
        self._operating_mode: str = operating_mode
        self._start_time: float = float(start_time)
        self._end_time: Optional[float] = None
        self._schema_version: str = EVENT_LOG_VERSION
        self._entries: List[EventLogEntry] = []
        self._genesis_state_hash: str = ""
        self._final_state_hash: str = ""
        self._asset_scope: List[str] = list(asset_scope) if asset_scope else []
        self._integrity_hash: str = ""
        self._closed: bool = False
        self._last_sequence_id: Optional[int] = None

    # -----------------------------------------------------------------
    # Genesis state hash (set-once)
    # -----------------------------------------------------------------

    def set_genesis_state_hash(self, state_hash: str) -> None:
        """
        Set the genesis state hash.  Can only be set once.

        Args:
            state_hash: SHA-256 hex string of initial state.

        Raises:
            TypeError:  If state_hash is not a string.
            ValueError: If state_hash is empty.
            ValueError: If genesis_state_hash already set.
        """
        if not isinstance(state_hash, str):
            raise TypeError(
                f"state_hash must be a string, "
                f"got {type(state_hash).__name__}"
            )
        if not state_hash:
            raise ValueError("state_hash must not be empty")
        if self._genesis_state_hash:
            raise ValueError(
                "genesis_state_hash already set — immutable after first assignment"
            )
        self._genesis_state_hash = state_hash

    # -----------------------------------------------------------------
    # Append entries
    # -----------------------------------------------------------------

    def append(self, entry: EventLogEntry) -> None:
        """
        Append an event log entry.

        Enforces monotonic sequence_id, MAX_ENTRIES limit, and
        closed-log immutability.

        Args:
            entry: EventLogEntry to append.

        Raises:
            TypeError:               If entry is not an EventLogEntry.
            ValueError:              If log is closed.
            ValueError:              If sequence_id is not monotonically increasing.
            ValueError:              If event_type is not valid.
            EventLogOverflowError:   If MAX_ENTRIES would be exceeded.
        """
        if not isinstance(entry, EventLogEntry):
            raise TypeError(
                f"entry must be an EventLogEntry, "
                f"got {type(entry).__name__}"
            )
        if self._closed:
            raise ValueError("Cannot append to a closed EventLog")

        # Validate event_type
        if entry.event_type not in VALID_EVENT_TYPES:
            raise ValueError(
                f"event_type must be one of {VALID_EVENT_TYPES}, "
                f"got {entry.event_type!r}"
            )

        # Monotonic sequence check
        if self._last_sequence_id is not None:
            if entry.sequence_id <= self._last_sequence_id:
                raise ValueError(
                    f"sequence_id must be monotonically increasing: "
                    f"got {entry.sequence_id}, previous was "
                    f"{self._last_sequence_id}"
                )

        # Overflow check
        if len(self._entries) >= MAX_ENTRIES:
            raise EventLogOverflowError(
                f"EventLog has reached MAX_ENTRIES ({MAX_ENTRIES}). "
                f"Session must be rotated."
            )

        self._entries.append(entry)
        self._last_sequence_id = entry.sequence_id

    # -----------------------------------------------------------------
    # Close session
    # -----------------------------------------------------------------

    def close(self, end_time: float, final_state_hash: str) -> None:
        """
        Close the session.  Sets end_time and final_state_hash.
        Computes integrity_hash.  Terminal — no further appends allowed.

        Args:
            end_time:          Session end timestamp.
            final_state_hash:  State hash at session end.

        Raises:
            TypeError:  If arguments have wrong types.
            ValueError: If final_state_hash is empty.
            ValueError: If log is already closed.
            ValueError: If end_time <= start_time.
        """
        if self._closed:
            raise ValueError("EventLog is already closed")
        if not isinstance(end_time, (int, float)):
            raise TypeError(
                f"end_time must be numeric, got {type(end_time).__name__}"
            )
        if not isinstance(final_state_hash, str):
            raise TypeError(
                f"final_state_hash must be a string, "
                f"got {type(final_state_hash).__name__}"
            )
        if not final_state_hash:
            raise ValueError("final_state_hash must not be empty")
        if end_time <= self._start_time:
            raise ValueError(
                f"end_time ({end_time}) must be > start_time "
                f"({self._start_time})"
            )

        self._end_time = float(end_time)
        self._final_state_hash = final_state_hash
        self._integrity_hash = self.compute_integrity_hash()
        self._closed = True

    # -----------------------------------------------------------------
    # Integrity
    # -----------------------------------------------------------------

    def compute_integrity_hash(self) -> str:
        """
        Compute SHA-256 over all entry state_hash_after values in order.

        Algorithm:
            chain = "|".join(e.state_hash_after for e in entries)
            return sha256(chain).hexdigest()

        Returns:
            64-character hex SHA-256 string.  Empty string if no entries.
        """
        if not self._entries:
            return hashlib.sha256(b"").hexdigest()

        chain = "|".join(e.state_hash_after for e in self._entries)
        return hashlib.sha256(chain.encode("utf-8")).hexdigest()

    def validate_integrity(self) -> bool:
        """
        Validate that stored integrity_hash matches recomputation.

        Returns:
            True if integrity_hash matches, False otherwise.
            Always returns False if integrity_hash has not been computed.
        """
        if not self._integrity_hash:
            return False
        return self._integrity_hash == self.compute_integrity_hash()

    # -----------------------------------------------------------------
    # Query methods
    # -----------------------------------------------------------------

    def get_entries(
        self,
        last_n: Optional[int] = None,
    ) -> List[EventLogEntry]:
        """
        Return entries from the log.

        Args:
            last_n: If provided, return only the last N entries.

        Returns:
            List of EventLogEntry (oldest first).
        """
        if last_n is not None and last_n > 0:
            return list(self._entries[-last_n:])
        return list(self._entries)

    def get_entries_by_type(self, event_type: str) -> List[EventLogEntry]:
        """
        Return all entries matching a specific event type.

        Args:
            event_type: Event type string to filter by.

        Returns:
            List of matching EventLogEntry (oldest first).
        """
        return [e for e in self._entries if e.event_type == event_type]

    # -----------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def operating_mode(self) -> str:
        return self._operating_mode

    @property
    def start_time(self) -> float:
        return self._start_time

    @property
    def end_time(self) -> Optional[float]:
        return self._end_time

    @property
    def schema_version(self) -> str:
        return self._schema_version

    @property
    def genesis_state_hash(self) -> str:
        return self._genesis_state_hash

    @property
    def final_state_hash(self) -> str:
        return self._final_state_hash

    @property
    def asset_scope(self) -> List[str]:
        return list(self._asset_scope)

    @property
    def integrity_hash(self) -> str:
        return self._integrity_hash

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def entry_count(self) -> int:
        return len(self._entries)
