# =============================================================================
# tests/unit/core/test_event_log.py
# Tests for jarvis/core/event_log.py
# =============================================================================

import hashlib

import pytest

from jarvis.core.event_log import (
    VALID_EVENT_TYPES,
    MAX_ENTRIES,
    VALID_OPERATING_MODES,
    EventType,
    EventLogEntry,
    EventLog,
    EventLogOverflowError,
)
from jarvis.core.schema_versions import EVENT_LOG_VERSION


# =============================================================================
# HELPERS
# =============================================================================

def _entry(seq: int = 1, ts: float = 1000.0,
           event_type: str = "market_data",
           payload: dict = None,
           hash_before: str = "aaa",
           hash_after: str = "bbb") -> EventLogEntry:
    """Build a valid EventLogEntry."""
    return EventLogEntry(
        sequence_id=seq,
        timestamp=ts,
        event_type=event_type,
        event_payload=payload or {},
        state_hash_before=hash_before,
        state_hash_after=hash_after,
    )


def _log(**kwargs) -> EventLog:
    """Build a valid EventLog with defaults."""
    defaults = {
        "session_id": "SESSION-001",
        "operating_mode": "historical",
        "start_time": 1000.0,
    }
    defaults.update(kwargs)
    return EventLog(**defaults)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    """Test module-level constants."""

    def test_valid_event_types_count(self):
        assert len(VALID_EVENT_TYPES) == 7

    def test_valid_event_types_contents(self):
        expected = {
            "market_data", "regime_change", "failure_mode",
            "exposure", "strategy_weight_change", "confidence_update",
            "layer_transition",
        }
        assert set(VALID_EVENT_TYPES) == expected

    def test_max_entries(self):
        assert MAX_ENTRIES == 1_000_000

    def test_valid_operating_modes(self):
        assert VALID_OPERATING_MODES == (
            "historical", "live_analytical", "hybrid",
        )


# =============================================================================
# SECTION 2 -- EVENT TYPE ENUM
# =============================================================================

class TestEventType:
    """Test EventType enum."""

    def test_all_members(self):
        assert len(EventType) == 7

    def test_market_data(self):
        assert EventType.MARKET_DATA.value == "market_data"

    def test_regime_change(self):
        assert EventType.REGIME_CHANGE.value == "regime_change"

    def test_failure_mode(self):
        assert EventType.FAILURE_MODE.value == "failure_mode"

    def test_exposure(self):
        assert EventType.EXPOSURE.value == "exposure"

    def test_strategy_weight(self):
        assert EventType.STRATEGY_WEIGHT.value == "strategy_weight_change"

    def test_confidence_update(self):
        assert EventType.CONFIDENCE_UPDATE.value == "confidence_update"

    def test_is_str_enum(self):
        assert isinstance(EventType.MARKET_DATA, str)
        assert EventType.MARKET_DATA == "market_data"


# =============================================================================
# SECTION 3 -- EVENT LOG ENTRY
# =============================================================================

class TestEventLogEntry:
    """Test EventLogEntry frozen dataclass."""

    def test_construction(self):
        e = _entry()
        assert e.sequence_id == 1
        assert e.timestamp == 1000.0
        assert e.event_type == "market_data"
        assert e.event_payload == {}
        assert e.state_hash_before == "aaa"
        assert e.state_hash_after == "bbb"

    def test_frozen(self):
        e = _entry()
        with pytest.raises(AttributeError):
            e.sequence_id = 2

    def test_equality(self):
        e1 = _entry(seq=1)
        e2 = _entry(seq=1)
        assert e1 == e2

    def test_inequality(self):
        e1 = _entry(seq=1)
        e2 = _entry(seq=2)
        assert e1 != e2

    def test_with_payload(self):
        e = _entry(payload={"symbol": "BTC", "price": 65000.0})
        assert e.event_payload["symbol"] == "BTC"


# =============================================================================
# SECTION 4 -- EVENT LOG OVERFLOW ERROR
# =============================================================================

class TestEventLogOverflowError:
    """Test EventLogOverflowError."""

    def test_is_exception(self):
        assert issubclass(EventLogOverflowError, Exception)

    def test_message(self):
        err = EventLogOverflowError("overflow")
        assert str(err) == "overflow"


# =============================================================================
# SECTION 5 -- EVENT LOG CONSTRUCTION
# =============================================================================

class TestEventLogConstruction:
    """Test EventLog construction and validation."""

    def test_basic_construction(self):
        log = _log()
        assert log.session_id == "SESSION-001"
        assert log.operating_mode == "historical"
        assert log.start_time == 1000.0
        assert log.end_time is None
        assert log.schema_version == EVENT_LOG_VERSION
        assert log.entry_count == 0
        assert log.is_closed is False

    def test_with_asset_scope(self):
        log = _log(asset_scope=["BTC", "ETH"])
        assert log.asset_scope == ["BTC", "ETH"]

    def test_default_asset_scope_empty(self):
        log = _log()
        assert log.asset_scope == []

    def test_all_operating_modes(self):
        for mode in VALID_OPERATING_MODES:
            log = _log(operating_mode=mode)
            assert log.operating_mode == mode

    def test_session_id_type_error(self):
        with pytest.raises(TypeError, match="session_id must be a string"):
            EventLog(session_id=123, operating_mode="historical", start_time=1000.0)

    def test_session_id_empty(self):
        with pytest.raises(ValueError, match="session_id must not be empty"):
            EventLog(session_id="", operating_mode="historical", start_time=1000.0)

    def test_operating_mode_type_error(self):
        with pytest.raises(TypeError, match="operating_mode must be a string"):
            EventLog(session_id="S-001", operating_mode=123, start_time=1000.0)

    def test_operating_mode_invalid(self):
        with pytest.raises(ValueError, match="operating_mode must be one of"):
            EventLog(session_id="S-001", operating_mode="invalid", start_time=1000.0)

    def test_start_time_type_error(self):
        with pytest.raises(TypeError, match="start_time must be numeric"):
            EventLog(session_id="S-001", operating_mode="historical", start_time="now")

    def test_start_time_int_accepted(self):
        log = EventLog(session_id="S-001", operating_mode="historical", start_time=1000)
        assert log.start_time == 1000.0


# =============================================================================
# SECTION 6 -- GENESIS STATE HASH
# =============================================================================

class TestGenesisStateHash:
    """Test set_genesis_state_hash."""

    def test_set_once(self):
        log = _log()
        log.set_genesis_state_hash("abc123")
        assert log.genesis_state_hash == "abc123"

    def test_immutable_after_set(self):
        log = _log()
        log.set_genesis_state_hash("abc123")
        with pytest.raises(ValueError, match="already set"):
            log.set_genesis_state_hash("def456")

    def test_type_error(self):
        log = _log()
        with pytest.raises(TypeError, match="must be a string"):
            log.set_genesis_state_hash(123)

    def test_empty_error(self):
        log = _log()
        with pytest.raises(ValueError, match="must not be empty"):
            log.set_genesis_state_hash("")

    def test_default_empty(self):
        log = _log()
        assert log.genesis_state_hash == ""


# =============================================================================
# SECTION 7 -- APPEND ENTRIES
# =============================================================================

class TestAppendEntries:
    """Test EventLog.append()."""

    def test_append_single(self):
        log = _log()
        log.append(_entry(seq=1))
        assert log.entry_count == 1

    def test_append_multiple(self):
        log = _log()
        log.append(_entry(seq=1))
        log.append(_entry(seq=2))
        log.append(_entry(seq=3))
        assert log.entry_count == 3

    def test_monotonic_sequence_enforced(self):
        log = _log()
        log.append(_entry(seq=1))
        with pytest.raises(ValueError, match="monotonically increasing"):
            log.append(_entry(seq=1))

    def test_monotonic_sequence_decreasing(self):
        log = _log()
        log.append(_entry(seq=5))
        with pytest.raises(ValueError, match="monotonically increasing"):
            log.append(_entry(seq=3))

    def test_invalid_event_type(self):
        log = _log()
        with pytest.raises(ValueError, match="event_type must be one of"):
            log.append(_entry(event_type="invalid_type"))

    def test_all_event_types_accepted(self):
        log = _log()
        for i, et in enumerate(VALID_EVENT_TYPES, start=1):
            log.append(_entry(seq=i, event_type=et))
        assert log.entry_count == 7

    def test_type_error_non_entry(self):
        log = _log()
        with pytest.raises(TypeError, match="must be an EventLogEntry"):
            log.append("not an entry")

    def test_append_to_closed_log(self):
        log = _log()
        log.append(_entry(seq=1))
        log.close(end_time=2000.0, final_state_hash="final")
        with pytest.raises(ValueError, match="closed"):
            log.append(_entry(seq=2))

    def test_sequence_gap_allowed(self):
        """Gaps are allowed per FAS (no gaps except at session boundaries)."""
        log = _log()
        log.append(_entry(seq=1))
        log.append(_entry(seq=10))  # gap is allowed
        assert log.entry_count == 2


# =============================================================================
# SECTION 8 -- CLOSE SESSION
# =============================================================================

class TestCloseSession:
    """Test EventLog.close()."""

    def test_close_basic(self):
        log = _log()
        log.append(_entry(seq=1))
        log.close(end_time=2000.0, final_state_hash="final_hash")
        assert log.is_closed is True
        assert log.end_time == 2000.0
        assert log.final_state_hash == "final_hash"

    def test_close_computes_integrity_hash(self):
        log = _log()
        log.append(_entry(seq=1, hash_after="h1"))
        log.close(end_time=2000.0, final_state_hash="final")
        assert log.integrity_hash != ""
        assert len(log.integrity_hash) == 64

    def test_double_close_error(self):
        log = _log()
        log.close(end_time=2000.0, final_state_hash="final")
        with pytest.raises(ValueError, match="already closed"):
            log.close(end_time=3000.0, final_state_hash="final2")

    def test_end_time_type_error(self):
        log = _log()
        with pytest.raises(TypeError, match="end_time must be numeric"):
            log.close(end_time="later", final_state_hash="final")

    def test_final_state_hash_type_error(self):
        log = _log()
        with pytest.raises(TypeError, match="final_state_hash must be a string"):
            log.close(end_time=2000.0, final_state_hash=123)

    def test_final_state_hash_empty(self):
        log = _log()
        with pytest.raises(ValueError, match="final_state_hash must not be empty"):
            log.close(end_time=2000.0, final_state_hash="")

    def test_end_time_before_start(self):
        log = _log(start_time=1000.0)
        with pytest.raises(ValueError, match="end_time.*must be > start_time"):
            log.close(end_time=500.0, final_state_hash="final")

    def test_end_time_equal_start(self):
        log = _log(start_time=1000.0)
        with pytest.raises(ValueError, match="end_time.*must be > start_time"):
            log.close(end_time=1000.0, final_state_hash="final")

    def test_close_empty_log(self):
        log = _log()
        log.close(end_time=2000.0, final_state_hash="final")
        assert log.is_closed is True
        assert log.integrity_hash != ""


# =============================================================================
# SECTION 9 -- INTEGRITY
# =============================================================================

class TestIntegrity:
    """Test integrity hash computation and validation."""

    def test_compute_integrity_hash_single_entry(self):
        log = _log()
        log.append(_entry(seq=1, hash_after="h1"))
        expected = hashlib.sha256("h1".encode("utf-8")).hexdigest()
        assert log.compute_integrity_hash() == expected

    def test_compute_integrity_hash_multiple_entries(self):
        log = _log()
        log.append(_entry(seq=1, hash_after="h1"))
        log.append(_entry(seq=2, hash_after="h2"))
        log.append(_entry(seq=3, hash_after="h3"))
        expected = hashlib.sha256("h1|h2|h3".encode("utf-8")).hexdigest()
        assert log.compute_integrity_hash() == expected

    def test_compute_integrity_hash_empty(self):
        log = _log()
        expected = hashlib.sha256(b"").hexdigest()
        assert log.compute_integrity_hash() == expected

    def test_validate_integrity_after_close(self):
        log = _log()
        log.append(_entry(seq=1, hash_after="h1"))
        log.close(end_time=2000.0, final_state_hash="final")
        assert log.validate_integrity() is True

    def test_validate_integrity_before_close(self):
        log = _log()
        log.append(_entry(seq=1))
        # integrity_hash not yet computed
        assert log.validate_integrity() is False

    def test_integrity_deterministic(self):
        log1 = _log()
        log1.append(_entry(seq=1, hash_after="h1"))
        log1.append(_entry(seq=2, hash_after="h2"))

        log2 = _log()
        log2.append(_entry(seq=1, hash_after="h1"))
        log2.append(_entry(seq=2, hash_after="h2"))

        assert log1.compute_integrity_hash() == log2.compute_integrity_hash()

    def test_integrity_different_entries(self):
        log1 = _log()
        log1.append(_entry(seq=1, hash_after="h1"))

        log2 = _log()
        log2.append(_entry(seq=1, hash_after="h2"))

        assert log1.compute_integrity_hash() != log2.compute_integrity_hash()


# =============================================================================
# SECTION 10 -- QUERY METHODS
# =============================================================================

class TestQueryMethods:
    """Test get_entries and get_entries_by_type."""

    def test_get_entries_all(self):
        log = _log()
        log.append(_entry(seq=1))
        log.append(_entry(seq=2))
        entries = log.get_entries()
        assert len(entries) == 2

    def test_get_entries_last_n(self):
        log = _log()
        for i in range(1, 6):
            log.append(_entry(seq=i))
        entries = log.get_entries(last_n=2)
        assert len(entries) == 2
        assert entries[0].sequence_id == 4
        assert entries[1].sequence_id == 5

    def test_get_entries_returns_copy(self):
        log = _log()
        log.append(_entry(seq=1))
        entries = log.get_entries()
        entries.clear()
        assert log.entry_count == 1

    def test_get_entries_empty(self):
        log = _log()
        assert log.get_entries() == []

    def test_get_entries_by_type(self):
        log = _log()
        log.append(_entry(seq=1, event_type="market_data"))
        log.append(_entry(seq=2, event_type="regime_change"))
        log.append(_entry(seq=3, event_type="market_data"))
        result = log.get_entries_by_type("market_data")
        assert len(result) == 2

    def test_get_entries_by_type_empty(self):
        log = _log()
        log.append(_entry(seq=1, event_type="market_data"))
        result = log.get_entries_by_type("regime_change")
        assert result == []

    def test_get_entries_by_type_all_types(self):
        log = _log()
        for i, et in enumerate(VALID_EVENT_TYPES, start=1):
            log.append(_entry(seq=i, event_type=et))
        for et in VALID_EVENT_TYPES:
            result = log.get_entries_by_type(et)
            assert len(result) == 1


# =============================================================================
# SECTION 11 -- PROPERTIES
# =============================================================================

class TestProperties:
    """Test all EventLog properties."""

    def test_session_id(self):
        log = _log(session_id="MY-SESSION")
        assert log.session_id == "MY-SESSION"

    def test_operating_mode(self):
        log = _log(operating_mode="live_analytical")
        assert log.operating_mode == "live_analytical"

    def test_schema_version(self):
        log = _log()
        assert log.schema_version == EVENT_LOG_VERSION

    def test_genesis_default(self):
        log = _log()
        assert log.genesis_state_hash == ""

    def test_final_default(self):
        log = _log()
        assert log.final_state_hash == ""

    def test_asset_scope_copy(self):
        """asset_scope property should return a copy."""
        log = _log(asset_scope=["BTC"])
        scope = log.asset_scope
        scope.append("ETH")
        assert log.asset_scope == ["BTC"]

    def test_is_closed_default(self):
        log = _log()
        assert log.is_closed is False

    def test_entry_count(self):
        log = _log()
        assert log.entry_count == 0
        log.append(_entry(seq=1))
        assert log.entry_count == 1

    def test_integrity_hash_default(self):
        log = _log()
        assert log.integrity_hash == ""


# =============================================================================
# SECTION 12 -- OVERFLOW
# =============================================================================

class TestOverflow:
    """Test MAX_ENTRIES overflow behavior."""

    def test_overflow_error_type(self):
        assert issubclass(EventLogOverflowError, Exception)

    def test_overflow_at_limit(self):
        """Verify overflow is raised (using a small mock)."""
        log = _log()
        # Directly set entries to near limit to avoid slow loop
        log._entries = [_entry(seq=i) for i in range(1, MAX_ENTRIES + 1)]
        log._last_sequence_id = MAX_ENTRIES
        with pytest.raises(EventLogOverflowError, match="MAX_ENTRIES"):
            log.append(_entry(seq=MAX_ENTRIES + 1))


# =============================================================================
# SECTION 13 -- FULL LIFECYCLE
# =============================================================================

class TestFullLifecycle:
    """Test complete EventLog lifecycle."""

    def test_full_lifecycle(self):
        log = EventLog(
            session_id="LIFECYCLE-001",
            operating_mode="hybrid",
            start_time=1000.0,
            asset_scope=["BTC", "ETH"],
        )

        # Set genesis
        log.set_genesis_state_hash("genesis_hash_abc")

        # Append events
        log.append(_entry(seq=1, event_type="market_data", hash_after="h1"))
        log.append(_entry(seq=2, event_type="regime_change", hash_after="h2"))
        log.append(_entry(seq=3, event_type="exposure", hash_after="h3"))

        assert log.entry_count == 3
        assert log.is_closed is False

        # Close
        log.close(end_time=2000.0, final_state_hash="final_xyz")

        assert log.is_closed is True
        assert log.end_time == 2000.0
        assert log.final_state_hash == "final_xyz"
        assert log.validate_integrity() is True

        # Verify entries
        all_entries = log.get_entries()
        assert len(all_entries) == 3
        market = log.get_entries_by_type("market_data")
        assert len(market) == 1

    def test_lifecycle_no_entries(self):
        log = _log()
        log.set_genesis_state_hash("genesis")
        log.close(end_time=2000.0, final_state_hash="final")
        assert log.is_closed is True
        assert log.validate_integrity() is True


# =============================================================================
# SECTION 14 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    """Test deterministic behavior (DET-07)."""

    def test_same_sequence_same_hash(self):
        """Same append sequence produces identical integrity hash."""
        hashes = []
        for _ in range(3):
            log = _log()
            log.append(_entry(seq=1, hash_after="a"))
            log.append(_entry(seq=2, hash_after="b"))
            log.close(end_time=2000.0, final_state_hash="f")
            hashes.append(log.integrity_hash)
        assert len(set(hashes)) == 1
