# tests/unit/core/test_logging_layer.py
# Coverage target: jarvis/core/logging_layer.py -> 95%+
# Missing lines: 106-111, 121, 147-157, 168, 215-217, 250-272, 300-303, 334-350, 374-382, 394

import math
from datetime import datetime

import pytest

from jarvis.core.logging_layer import (
    EventLogger,
    Event,
    EventFilter,
    LoggingError,
    _sanitize_numeric,
    _sanitize_data,
    _compute_hash,
    _make_event_id,
)


# =============================================================================
# _sanitize_numeric (lines 106-111)
# =============================================================================

class TestSanitizeNumeric:
    def test_nan_replaced(self):
        assert _sanitize_numeric(float("nan")) == "NaN_DETECTED"

    def test_inf_replaced(self):
        assert _sanitize_numeric(float("inf")) == "Inf_DETECTED"

    def test_neg_inf_replaced(self):
        assert _sanitize_numeric(float("-inf")) == "Inf_DETECTED"

    def test_normal_float_unchanged(self):
        assert _sanitize_numeric(3.14) == 3.14

    def test_zero_unchanged(self):
        assert _sanitize_numeric(0.0) == 0.0

    def test_int_unchanged(self):
        assert _sanitize_numeric(42) == 42

    def test_string_unchanged(self):
        assert _sanitize_numeric("hello") == "hello"

    def test_none_unchanged(self):
        assert _sanitize_numeric(None) is None


# =============================================================================
# _sanitize_data (line 121)
# =============================================================================

class TestSanitizeData:
    def test_sanitizes_nan_in_dict(self):
        result = _sanitize_data({"a": float("nan"), "b": 1.0})
        assert result["a"] == "NaN_DETECTED"
        assert result["b"] == 1.0

    def test_sanitizes_inf_in_dict(self):
        result = _sanitize_data({"x": float("inf")})
        assert result["x"] == "Inf_DETECTED"

    def test_empty_dict(self):
        assert _sanitize_data({}) == {}

    def test_original_not_mutated(self):
        d = {"a": float("nan")}
        _sanitize_data(d)
        assert math.isnan(d["a"])


# =============================================================================
# _compute_hash (lines 147-157)
# =============================================================================

class TestComputeHash:
    def test_returns_hex_string(self):
        ts = datetime(2026, 1, 1, 12, 0, 0)
        h = _compute_hash("EVT-001", "TEST", ts, {"k": "v"})
        assert isinstance(h, str)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_deterministic(self):
        ts = datetime(2026, 1, 1, 12, 0, 0)
        h1 = _compute_hash("EVT-001", "TEST", ts, {"k": "v"})
        h2 = _compute_hash("EVT-001", "TEST", ts, {"k": "v"})
        assert h1 == h2

    def test_different_inputs_different_hash(self):
        ts = datetime(2026, 1, 1, 12, 0, 0)
        h1 = _compute_hash("EVT-001", "A", ts, {})
        h2 = _compute_hash("EVT-001", "B", ts, {})
        assert h1 != h2


# =============================================================================
# _make_event_id (line 168)
# =============================================================================

class TestMakeEventId:
    def test_format(self):
        assert _make_event_id(1) == "EVT-0000000000000001"

    def test_zero(self):
        assert _make_event_id(0) == "EVT-0000000000000000"

    def test_large_number(self):
        assert _make_event_id(9999999999999999) == "EVT-9999999999999999"


# =============================================================================
# EventLogger.__init__ (lines 215-217)
# =============================================================================

class TestEventLoggerInit:
    def test_empty_store(self):
        logger = EventLogger()
        assert logger.event_count() == 0

    def test_counter_starts_zero(self):
        logger = EventLogger()
        assert logger._counter == 0


# =============================================================================
# EventLogger.log_event (lines 250-272)
# =============================================================================

class TestLogEvent:
    def test_basic_log(self):
        logger = EventLogger()
        ts = datetime(2026, 1, 1, 12, 0, 0)
        eid = logger.log_event("DECISION", {"signal": 0.5}, ts)
        assert eid == "EVT-0000000000000001"
        assert logger.event_count() == 1

    def test_sequential_ids(self):
        logger = EventLogger()
        ts = datetime(2026, 1, 1)
        e1 = logger.log_event("A", {}, ts)
        e2 = logger.log_event("B", {}, ts)
        assert e1 == "EVT-0000000000000001"
        assert e2 == "EVT-0000000000000002"

    def test_empty_event_type_raises(self):
        logger = EventLogger()
        with pytest.raises(LoggingError, match="non-empty string"):
            logger.log_event("", {}, datetime(2026, 1, 1))

    def test_none_timestamp_raises(self):
        logger = EventLogger()
        with pytest.raises(LoggingError, match="None is not permitted"):
            logger.log_event("X", {}, None)

    def test_invalid_timestamp_type_raises(self):
        logger = EventLogger()
        with pytest.raises(LoggingError, match="datetime instance"):
            logger.log_event("X", {}, "2026-01-01")

    def test_nan_in_data_sanitized(self):
        logger = EventLogger()
        ts = datetime(2026, 1, 1)
        logger.log_event("X", {"v": float("nan")}, ts)
        events = logger.query_events(EventFilter())
        assert events[0].data["v"] == "NaN_DETECTED"

    def test_event_has_hash(self):
        logger = EventLogger()
        ts = datetime(2026, 1, 1)
        logger.log_event("X", {}, ts)
        events = logger.query_events(EventFilter())
        assert len(events[0].hash) == 64


# =============================================================================
# EventLogger.log_state_change (lines 300-303)
# =============================================================================

class TestLogStateChange:
    def test_logs_state_change(self):
        logger = EventLogger()
        ts = datetime(2026, 1, 1)
        eid = logger.log_state_change("ACTIVE", ts)
        assert eid.startswith("EVT-")
        events = logger.query_events(EventFilter(event_type="STATE_CHANGE"))
        assert len(events) == 1
        assert events[0].data["state_repr"] == "'ACTIVE'"

    def test_none_state_raises(self):
        logger = EventLogger()
        with pytest.raises(LoggingError, match="must not be None"):
            logger.log_state_change(None, datetime(2026, 1, 1))


# =============================================================================
# EventLogger.query_events (lines 334-350)
# =============================================================================

class TestQueryEvents:
    def _populated_logger(self):
        logger = EventLogger()
        logger.log_event("A", {}, datetime(2026, 1, 1, 10, 0))
        logger.log_event("B", {}, datetime(2026, 1, 1, 12, 0))
        logger.log_event("A", {}, datetime(2026, 1, 1, 14, 0))
        logger.log_event("C", {}, datetime(2026, 1, 1, 16, 0))
        return logger

    def test_filter_none_raises(self):
        logger = EventLogger()
        with pytest.raises(LoggingError, match="must not be None"):
            logger.query_events(None)

    def test_no_filter(self):
        logger = self._populated_logger()
        assert len(logger.query_events(EventFilter())) == 4

    def test_filter_by_type(self):
        logger = self._populated_logger()
        results = logger.query_events(EventFilter(event_type="A"))
        assert len(results) == 2
        assert all(e.type == "A" for e in results)

    def test_filter_by_start_time(self):
        logger = self._populated_logger()
        results = logger.query_events(EventFilter(start_time=datetime(2026, 1, 1, 13, 0)))
        assert len(results) == 2

    def test_filter_by_end_time(self):
        logger = self._populated_logger()
        results = logger.query_events(EventFilter(end_time=datetime(2026, 1, 1, 11, 0)))
        assert len(results) == 1

    def test_filter_with_limit(self):
        logger = self._populated_logger()
        results = logger.query_events(EventFilter(limit=2))
        assert len(results) == 2

    def test_combined_filters(self):
        logger = self._populated_logger()
        results = logger.query_events(EventFilter(
            event_type="A",
            start_time=datetime(2026, 1, 1, 11, 0),
            end_time=datetime(2026, 1, 1, 15, 0),
        ))
        assert len(results) == 1


# =============================================================================
# EventLogger.get_event_stream (lines 374-382)
# =============================================================================

class TestGetEventStream:
    def test_basic_stream(self):
        logger = EventLogger()
        logger.log_event("A", {}, datetime(2026, 1, 1, 10, 0))
        logger.log_event("B", {}, datetime(2026, 1, 1, 12, 0))
        events = list(logger.get_event_stream(datetime(2026, 1, 1, 11, 0)))
        assert len(events) == 1
        assert events[0].type == "B"

    def test_none_start_time_raises(self):
        logger = EventLogger()
        with pytest.raises(LoggingError, match="None is not permitted"):
            list(logger.get_event_stream(None))

    def test_invalid_start_time_type_raises(self):
        logger = EventLogger()
        with pytest.raises(LoggingError, match="datetime instance"):
            list(logger.get_event_stream("2026-01-01"))

    def test_stream_all(self):
        logger = EventLogger()
        logger.log_event("X", {}, datetime(2026, 1, 1))
        events = list(logger.get_event_stream(datetime(2025, 1, 1)))
        assert len(events) == 1


# =============================================================================
# EventLogger.event_count (line 394)
# =============================================================================

class TestEventCount:
    def test_empty(self):
        assert EventLogger().event_count() == 0

    def test_after_logging(self):
        logger = EventLogger()
        logger.log_event("X", {}, datetime(2026, 1, 1))
        logger.log_event("Y", {}, datetime(2026, 1, 1))
        assert logger.event_count() == 2
