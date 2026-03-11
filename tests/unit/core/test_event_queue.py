# tests/unit/core/test_event_queue.py
# Coverage target: jarvis/core/event_queue.py -> 95%+
# Tests FIFO ordering, overflow, drain/emit constraint, peek, properties.

import pytest

from jarvis.core.event_bus import BaseEvent, EventType
from jarvis.core.event_queue import DeterministicEventQueue


# =============================================================================
# Helpers
# =============================================================================

def _evt(seq: int = 1, eid: str = "evt") -> BaseEvent:
    return BaseEvent(
        event_id=f"{eid}-{seq:03d}",
        event_type=EventType.MARKET_DATA,
        timestamp=1000.0 + seq,
        sequence_id=seq,
    )


# =============================================================================
# Construction
# =============================================================================

class TestConstruction:
    def test_default_max_size(self):
        q = DeterministicEventQueue()
        assert q.max_size == 10_000

    def test_custom_max_size(self):
        q = DeterministicEventQueue(max_size=5)
        assert q.max_size == 5

    def test_zero_max_size_raises(self):
        with pytest.raises(ValueError, match="max_size"):
            DeterministicEventQueue(max_size=0)

    def test_negative_max_size_raises(self):
        with pytest.raises(ValueError, match="max_size"):
            DeterministicEventQueue(max_size=-1)

    def test_float_max_size_raises(self):
        with pytest.raises(TypeError, match="max_size"):
            DeterministicEventQueue(max_size=5.0)

    def test_bool_max_size_raises(self):
        with pytest.raises(TypeError, match="max_size"):
            DeterministicEventQueue(max_size=True)

    def test_initial_depth_zero(self):
        q = DeterministicEventQueue()
        assert q.depth == 0

    def test_initial_processed_count_zero(self):
        q = DeterministicEventQueue()
        assert q.processed_count == 0

    def test_initial_sequence_counter_zero(self):
        q = DeterministicEventQueue()
        assert q.sequence_counter == 0


# =============================================================================
# emit()
# =============================================================================

class TestEmit:
    def test_emit_returns_sequence_number(self):
        q = DeterministicEventQueue()
        seq = q.emit(_evt(1))
        assert seq == 1

    def test_emit_increments_sequence(self):
        q = DeterministicEventQueue()
        s1 = q.emit(_evt(1))
        s2 = q.emit(_evt(2))
        s3 = q.emit(_evt(3))
        assert s1 == 1
        assert s2 == 2
        assert s3 == 3

    def test_emit_increases_depth(self):
        q = DeterministicEventQueue()
        q.emit(_evt(1))
        assert q.depth == 1
        q.emit(_evt(2))
        assert q.depth == 2

    def test_emit_non_event_raises_type_error(self):
        q = DeterministicEventQueue()
        with pytest.raises(TypeError, match="BaseEvent"):
            q.emit("not an event")

    def test_emit_none_raises_type_error(self):
        q = DeterministicEventQueue()
        with pytest.raises(TypeError, match="BaseEvent"):
            q.emit(None)

    def test_emit_dict_raises_type_error(self):
        q = DeterministicEventQueue()
        with pytest.raises(TypeError, match="BaseEvent"):
            q.emit({"event_id": "x"})

    def test_emit_overflow_raises(self):
        q = DeterministicEventQueue(max_size=2)
        q.emit(_evt(1))
        q.emit(_evt(2))
        with pytest.raises(OverflowError, match="full"):
            q.emit(_evt(3))

    def test_emit_at_exact_capacity(self):
        q = DeterministicEventQueue(max_size=3)
        q.emit(_evt(1))
        q.emit(_evt(2))
        q.emit(_evt(3))
        assert q.depth == 3


# =============================================================================
# drain()
# =============================================================================

class TestDrain:
    def test_drain_returns_all_events_fifo(self):
        q = DeterministicEventQueue()
        e1 = _evt(1)
        e2 = _evt(2)
        e3 = _evt(3)
        q.emit(e1)
        q.emit(e2)
        q.emit(e3)
        drained = list(q.drain())
        assert drained == [e1, e2, e3]

    def test_drain_clears_queue(self):
        q = DeterministicEventQueue()
        q.emit(_evt(1))
        q.emit(_evt(2))
        list(q.drain())
        assert q.depth == 0

    def test_drain_empty_queue(self):
        q = DeterministicEventQueue()
        drained = list(q.drain())
        assert drained == []

    def test_drain_increments_processed_count(self):
        q = DeterministicEventQueue()
        q.emit(_evt(1))
        q.emit(_evt(2))
        q.emit(_evt(3))
        list(q.drain())
        assert q.processed_count == 3

    def test_drain_cumulative_processed_count(self):
        q = DeterministicEventQueue()
        q.emit(_evt(1))
        list(q.drain())
        q.emit(_evt(2))
        q.emit(_evt(3))
        list(q.drain())
        assert q.processed_count == 3

    def test_drain_sequence_counter_persists(self):
        q = DeterministicEventQueue()
        q.emit(_evt(1))
        list(q.drain())
        seq = q.emit(_evt(2))
        assert seq == 2
        assert q.sequence_counter == 2

    def test_drain_allows_re_emit_after_complete(self):
        q = DeterministicEventQueue(max_size=2)
        q.emit(_evt(1))
        q.emit(_evt(2))
        list(q.drain())
        # Queue is now empty; should accept new events
        q.emit(_evt(3))
        assert q.depth == 1


# =============================================================================
# Constraint 1: No emit during drain
# =============================================================================

class TestNoEmitDuringDrain:
    def test_emit_during_drain_raises_runtime_error(self):
        q = DeterministicEventQueue()
        q.emit(_evt(1))
        q.emit(_evt(2))

        with pytest.raises(RuntimeError, match="Cannot emit"):
            for event in q.drain():
                q.emit(_evt(99))

    def test_drain_flag_reset_after_completion(self):
        q = DeterministicEventQueue()
        q.emit(_evt(1))
        list(q.drain())
        # Should work fine after drain completes
        q.emit(_evt(2))
        assert q.depth == 1

    def test_drain_flag_reset_after_exception(self):
        q = DeterministicEventQueue()
        q.emit(_evt(1))

        # Simulate exception during drain processing
        try:
            for event in q.drain():
                raise ValueError("processing error")
        except ValueError:
            pass

        # drain flag must be reset even after exception
        q.emit(_evt(2))
        assert q.depth == 1


# =============================================================================
# peek()
# =============================================================================

class TestPeek:
    def test_peek_returns_copy(self):
        q = DeterministicEventQueue()
        e1 = _evt(1)
        q.emit(e1)
        peeked = q.peek()
        assert peeked == [e1]
        assert q.depth == 1  # not consumed

    def test_peek_does_not_consume(self):
        q = DeterministicEventQueue()
        q.emit(_evt(1))
        q.emit(_evt(2))
        q.peek()
        q.peek()
        assert q.depth == 2

    def test_peek_empty_queue(self):
        q = DeterministicEventQueue()
        assert q.peek() == []

    def test_peek_returns_fifo_order(self):
        q = DeterministicEventQueue()
        e1 = _evt(1)
        e2 = _evt(2)
        q.emit(e1)
        q.emit(e2)
        peeked = q.peek()
        assert peeked[0] == e1
        assert peeked[1] == e2

    def test_peek_mutation_does_not_affect_queue(self):
        q = DeterministicEventQueue()
        q.emit(_evt(1))
        peeked = q.peek()
        peeked.clear()
        assert q.depth == 1


# =============================================================================
# Properties
# =============================================================================

class TestProperties:
    def test_depth_reflects_emit_and_drain(self):
        q = DeterministicEventQueue()
        assert q.depth == 0
        q.emit(_evt(1))
        assert q.depth == 1
        q.emit(_evt(2))
        assert q.depth == 2
        list(q.drain())
        assert q.depth == 0

    def test_max_size_property(self):
        q = DeterministicEventQueue(max_size=42)
        assert q.max_size == 42

    def test_sequence_counter_only_increases(self):
        q = DeterministicEventQueue()
        q.emit(_evt(1))
        q.emit(_evt(2))
        list(q.drain())
        assert q.sequence_counter == 2
        q.emit(_evt(3))
        assert q.sequence_counter == 3


# =============================================================================
# FIFO ordering guarantee
# =============================================================================

class TestFIFOOrdering:
    def test_100_events_fifo(self):
        q = DeterministicEventQueue()
        events = [_evt(i) for i in range(100)]
        for e in events:
            q.emit(e)
        drained = list(q.drain())
        assert drained == events

    def test_interleaved_emit_drain_fifo(self):
        q = DeterministicEventQueue()
        e1 = _evt(1)
        e2 = _evt(2)
        q.emit(e1)
        batch1 = list(q.drain())
        q.emit(e2)
        batch2 = list(q.drain())
        assert batch1 == [e1]
        assert batch2 == [e2]
