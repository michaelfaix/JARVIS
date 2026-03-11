# =============================================================================
# jarvis/core/event_queue.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, EVENT BUS FORMALIZATION
# ARCHITECTURE.md Section 13
# =============================================================================
#
# SCOPE
# -----
# Deterministic FIFO event queue for the analytical event system.
# Implements DeterministicEventQueue with emit/drain/peek API.
#
# INVARIANTS (non-negotiable, from S37)
# ------
# 1. FIFO ordering -- events processed in emission order.
# 2. No parallel mutation -- single-threaded event processing.
# 3. All state mutation routes through ctrl.update() -- never inside queue.
# 4. No execution events permitted -- queue is analytical only.
# 5. Queue is not a broker interface -- no order objects may enter.
# 6. Events are immutable (frozen dataclasses) -- never modified in transit.
#
# DEPENDENCIES
# ------------
#   stdlib:    collections.deque, threading
#   internal:  jarvis.core.event_bus.BaseEvent, EventType
#   PROHIBITED: numpy, logging, random, file IO, network IO
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  Queue state is encapsulated; no side effects beyond FIFO storage.
# DET-04  No arithmetic.
# DET-05  No datetime.now() / time.time().
# DET-06  max_size default (10_000) is a fixed literal per S37.
# =============================================================================

from __future__ import annotations

import threading
from collections import deque
from typing import Iterator, List

from jarvis.core.event_bus import BaseEvent, EventType

__all__ = [
    "DeterministicEventQueue",
]


class DeterministicEventQueue:
    """
    Deterministic FIFO event queue for the analytical event system.

    Thread-safe via internal lock. Events are frozen dataclasses and
    are never modified in transit.

    Constraint 1 (S37): Events must NOT emit new events during the same
    dispatch cycle. This is enforced by tracking whether drain() is active;
    calling emit() during drain() raises RuntimeError.
    """

    def __init__(self, max_size: int = 10_000) -> None:
        if not isinstance(max_size, int) or isinstance(max_size, bool):
            raise TypeError(
                f"max_size must be a positive int, got {type(max_size).__name__}"
            )
        if max_size < 1:
            raise ValueError(
                f"max_size must be >= 1, got {max_size}"
            )
        self._queue: deque = deque(maxlen=max_size)
        self._max_size: int = max_size
        self._lock: threading.Lock = threading.Lock()
        self._sequence_counter: int = 0
        self._processed_count: int = 0
        self._draining: bool = False

    def emit(self, event: BaseEvent) -> int:
        """
        Add an event to the queue. Returns assigned sequence number.

        Raises OverflowError if max_size exceeded (no silent drop).
        Raises RuntimeError if called during an active drain() cycle
        (Constraint 1: no recursive event loops).
        Raises TypeError if event is not a BaseEvent instance.
        """
        if not isinstance(event, BaseEvent):
            raise TypeError(
                f"event must be a BaseEvent instance, got {type(event).__name__}"
            )
        with self._lock:
            if self._draining:
                raise RuntimeError(
                    "Cannot emit() during an active drain() cycle. "
                    "Events must NOT trigger other events inside the same "
                    "dispatch cycle (S37 Constraint 1)."
                )
            if len(self._queue) >= self._max_size:
                raise OverflowError(
                    f"EventQueue full ({self._max_size} events). "
                    "System backpressure -- reduce event rate or increase max_size."
                )
            self._sequence_counter += 1
            self._queue.append(event)
            return self._sequence_counter

    def drain(self) -> Iterator[BaseEvent]:
        """
        Yields all pending events in FIFO order, removing them from the queue.

        Must be called from a single processing thread only. Sets the
        _draining flag to enforce Constraint 1 (no recursive emit).
        """
        with self._lock:
            if self._draining:
                raise RuntimeError(
                    "drain() is already active. Concurrent drain() calls "
                    "are not permitted."
                )
            self._draining = True
            pending = list(self._queue)
            self._queue.clear()

        try:
            for event in pending:
                self._processed_count += 1
                yield event
        finally:
            with self._lock:
                self._draining = False

    def peek(self) -> List[BaseEvent]:
        """
        Read-only view of current queue contents. Does not consume events.
        Returns a copy to prevent external mutation.
        """
        with self._lock:
            return list(self._queue)

    @property
    def depth(self) -> int:
        """Current number of events in the queue."""
        with self._lock:
            return len(self._queue)

    @property
    def processed_count(self) -> int:
        """Total number of events processed via drain() over the queue lifetime."""
        return self._processed_count

    @property
    def max_size(self) -> int:
        """Maximum queue capacity."""
        return self._max_size

    @property
    def sequence_counter(self) -> int:
        """Total number of events emitted over the queue lifetime."""
        return self._sequence_counter
