# =============================================================================
# JARVIS v6.1.0 -- DECISION CONTEXT STATE
# File:   jarvis/core/decision_context_state.py
# Version: 1.0.0
# =============================================================================
#
# SCOPE
# -----
# Canonical sub-state for rolling analytical decision memory.
# Provides DecisionQualityEngine with historical pattern context for:
#   - streak instability detection
#   - repeated failure pattern penalty
#   - regime misalignment detection
#
# CLASSIFICATION: P0 — ANALYSIS AND STRATEGY RESEARCH TOOL.
# No execution, no real capital tracking, no broker/order/account IDs.
#
# PUBLIC SYMBOLS
# --------------
#   MAX_DECISION_CONTEXT        int constant (200)
#   OutcomeClassification       Literal type alias
#   DecisionRecord              frozen dataclass — single decision event
#   DecisionContextState        mutable dataclass — rolling deque + counter
#   DecisionContextSnapshot     frozen dataclass — point-in-time snapshot
#
# MUTATION CONTRACT
# -----------------
# DecisionRecord:         frozen — never mutated after construction.
# DecisionContextState:   mutable — mutations ONLY via GlobalSystemStateController.
# DecisionContextSnapshot: frozen — read-only consumption by DecisionQualityEngine.
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects (snapshot() returns a copy).
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
#   No global mutable state (instances are per-controller, not module-level)
#   No real capital / PnL / account balance references
#   No broker_id / order_id / account_id fields
# =============================================================================

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Literal, Tuple


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

MAX_DECISION_CONTEXT: int = 200
"""
Maximum number of analytical decision records stored in DecisionContextState.
Rolling window; oldest record evicted when limit exceeded.
Deterministic cap — no dynamic expansion.
"""


# ---------------------------------------------------------------------------
# TYPE ALIAS
# ---------------------------------------------------------------------------

OutcomeClassification = Literal["WIN", "LOSS", "NEUTRAL"]
"""
Purely analytical classification of a past signal outcome.
  WIN:     analytical signal was directionally correct.
  LOSS:    analytical signal was directionally incorrect.
  NEUTRAL: outcome indeterminate, insufficient data, or not yet classified.
No PnL, no real capital, no account balance referenced.
"""

_VALID_OUTCOMES = frozenset({"WIN", "LOSS", "NEUTRAL"})


# ---------------------------------------------------------------------------
# DECISION RECORD (frozen)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DecisionRecord:
    """
    Immutable record of a single analytical decision event.
    No execution semantics. No real capital references.

    Attributes:
        sequence_id:            Monotonically increasing identifier.
        regime_at_decision:     Regime value at decision time (snapshot string).
        confidence_at_decision: Confidence Q value at decision time, in [0.0, 1.0].
        outcome:                Analytical outcome classification.
        strategy_id:            Identifier of the strategy that produced the signal.
    """
    sequence_id:            int
    regime_at_decision:     str
    confidence_at_decision: float
    outcome:                str     # OutcomeClassification: "WIN" | "LOSS" | "NEUTRAL"
    strategy_id:            str

    def __post_init__(self) -> None:
        if self.sequence_id < 0:
            raise ValueError(
                f"sequence_id must be >= 0; got {self.sequence_id}"
            )
        if not (0.0 <= self.confidence_at_decision <= 1.0):
            raise ValueError(
                f"confidence_at_decision must be in [0.0, 1.0]; "
                f"got {self.confidence_at_decision}"
            )
        if self.outcome not in _VALID_OUTCOMES:
            raise ValueError(
                f"outcome must be one of {sorted(_VALID_OUTCOMES)}; "
                f"got {self.outcome!r}"
            )
        if not self.strategy_id:
            raise ValueError("strategy_id must be a non-empty string")


# ---------------------------------------------------------------------------
# DECISION CONTEXT SNAPSHOT (frozen)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DecisionContextSnapshot:
    """
    Frozen point-in-time snapshot of DecisionContextState.
    Consumed ONLY by DecisionQualityEngine (read-only).

    Attributes:
        records:         Tuple of DecisionRecord (ordered oldest-first).
                         Length <= MAX_DECISION_CONTEXT.
        total_appended:  Total records ever appended to the parent state.
    """
    records:        Tuple[DecisionRecord, ...]
    total_appended: int


# ---------------------------------------------------------------------------
# DECISION CONTEXT STATE (mutable — controller-managed)
# ---------------------------------------------------------------------------

@dataclass
class DecisionContextState:
    """
    Rolling analytical memory of the last N decision records.
    N is capped at MAX_DECISION_CONTEXT (200).

    Canonical sub-state of GlobalSystemState. All mutations MUST go through
    GlobalSystemStateController.update(). This class is never mutated
    directly by any module outside the controller.

    Attributes:
        records:         Rolling deque of DecisionRecord entries.
                         maxlen = MAX_DECISION_CONTEXT.
                         Oldest record auto-evicted when limit reached.
        total_appended:  Monotonically increasing count of total records
                         ever appended. Not reset on eviction.
    """
    records: deque = field(
        default_factory=lambda: deque(maxlen=MAX_DECISION_CONTEXT)
    )
    total_appended: int = 0

    def snapshot(self) -> DecisionContextSnapshot:
        """
        Return a frozen snapshot for use by DecisionQualityEngine.
        Snapshot is a point-in-time copy; does not hold a reference
        to the live deque.
        """
        return DecisionContextSnapshot(
            records=tuple(self.records),
            total_appended=self.total_appended,
        )

    def append_record(self, record: DecisionRecord) -> None:
        """
        Append a DecisionRecord to the rolling deque.
        Increments total_appended. maxlen enforcement is automatic.

        This method is intended to be called ONLY by
        GlobalSystemStateController.update().
        """
        if not isinstance(record, DecisionRecord):
            raise TypeError(
                f"record must be a DecisionRecord; got {type(record).__name__}"
            )
        self.records.append(record)
        self.total_appended += 1

    def update_outcome(
        self,
        sequence_id: int,
        new_outcome: str,
    ) -> bool:
        """
        Update the outcome of a record identified by sequence_id.
        Since DecisionRecord is frozen, this replaces the record with
        a new instance bearing the updated outcome.

        Returns True if the record was found and updated, False if the
        sequence_id is not in the current window (already evicted).

        This method is intended to be called ONLY by
        GlobalSystemStateController.update().
        """
        if new_outcome not in _VALID_OUTCOMES:
            raise ValueError(
                f"new_outcome must be one of {sorted(_VALID_OUTCOMES)}; "
                f"got {new_outcome!r}"
            )
        updated: list = []
        found: bool = False
        for rec in self.records:
            if rec.sequence_id == sequence_id:
                updated.append(DecisionRecord(
                    sequence_id=rec.sequence_id,
                    regime_at_decision=rec.regime_at_decision,
                    confidence_at_decision=rec.confidence_at_decision,
                    outcome=new_outcome,
                    strategy_id=rec.strategy_id,
                ))
                found = True
            else:
                updated.append(rec)
        if found:
            self.records.clear()
            self.records.extend(updated)
        return found


__all__ = [
    "MAX_DECISION_CONTEXT",
    "OutcomeClassification",
    "DecisionRecord",
    "DecisionContextState",
    "DecisionContextSnapshot",
]
