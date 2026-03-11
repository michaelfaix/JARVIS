# tests/unit/core/test_hybrid_coordinator.py
# Coverage target: jarvis/core/hybrid_coordinator.py -> 95%+
# Tests all phases, transitions, sync_point detection, backfill limits,
# immutability, terminal states, and edge cases.

import pytest

from jarvis.core.hybrid_coordinator import (
    VALID_PHASES,
    MAX_BACKFILL_DURATION_S,
    HybridPhase,
    SyncPointResult,
    CoordinatorState,
    HybridCoordinator,
)


# =============================================================================
# Helpers
# =============================================================================

def _coord(**kwargs) -> HybridCoordinator:
    defaults = dict(
        backfill_start=1000.0,
        backfill_end=2000.0,
    )
    defaults.update(kwargs)
    return HybridCoordinator(**defaults)


def _synced_coord() -> HybridCoordinator:
    """Return a coordinator that has completed sync and is in LIVE phase."""
    c = _coord()
    c.process_backfill_candle(0.1)
    c.attempt_sync(2001.0, True)
    return c


# =============================================================================
# Constants
# =============================================================================

class TestConstants:
    def test_valid_phases(self):
        assert VALID_PHASES == (
            "BACKFILL", "SYNCING", "LIVE", "COMPLETED", "FAILED",
        )

    def test_max_backfill_duration(self):
        assert MAX_BACKFILL_DURATION_S == 600.0

    def test_hybrid_phase_values(self):
        assert HybridPhase.BACKFILL.value == "BACKFILL"
        assert HybridPhase.LIVE.value == "LIVE"
        assert HybridPhase.COMPLETED.value == "COMPLETED"
        assert HybridPhase.FAILED.value == "FAILED"
        assert HybridPhase.SYNCING.value == "SYNCING"

    def test_hybrid_phase_is_str(self):
        assert isinstance(HybridPhase.BACKFILL, str)

    def test_exactly_five_phases(self):
        assert len(HybridPhase) == 5


# =============================================================================
# Data Types
# =============================================================================

class TestSyncPointResult:
    def test_construction(self):
        r = SyncPointResult(
            sync_detected=True,
            sync_timestamp=2001.0,
            integrity_passed=True,
            reason="sync set",
        )
        assert r.sync_detected is True
        assert r.sync_timestamp == 2001.0
        assert r.integrity_passed is True

    def test_frozen(self):
        r = SyncPointResult(False, None, False, "no sync")
        with pytest.raises(AttributeError):
            r.sync_detected = True


class TestCoordinatorState:
    def test_construction(self):
        s = CoordinatorState(
            phase=HybridPhase.BACKFILL,
            sync_point=None,
            backfill_start=1000.0,
            backfill_end=2000.0,
            elapsed_backfill_s=0.0,
            candles_processed=0,
            sync_attempts=0,
            version=1,
        )
        assert s.phase == HybridPhase.BACKFILL
        assert s.sync_point is None
        assert s.version == 1

    def test_frozen(self):
        s = CoordinatorState(
            HybridPhase.BACKFILL, None, 1000.0, 2000.0, 0.0, 0, 0, 1,
        )
        with pytest.raises(AttributeError):
            s.phase = HybridPhase.LIVE


# =============================================================================
# Construction
# =============================================================================

class TestConstruction:
    def test_valid_construction(self):
        c = _coord()
        assert c.phase == HybridPhase.BACKFILL
        assert c.sync_point is None
        assert c.is_terminal is False

    def test_custom_backfill_duration(self):
        c = _coord(max_backfill_duration_s=120.0)
        assert c.backfill_budget_remaining_s == 120.0

    def test_int_timestamps_accepted(self):
        c = HybridCoordinator(backfill_start=1000, backfill_end=2000)
        assert c.phase == HybridPhase.BACKFILL

    def test_backfill_end_equals_start_raises(self):
        with pytest.raises(ValueError, match="backfill_end"):
            HybridCoordinator(backfill_start=1000.0, backfill_end=1000.0)

    def test_backfill_end_before_start_raises(self):
        with pytest.raises(ValueError, match="backfill_end"):
            HybridCoordinator(backfill_start=2000.0, backfill_end=1000.0)

    def test_zero_duration_raises(self):
        with pytest.raises(ValueError, match="max_backfill_duration_s"):
            _coord(max_backfill_duration_s=0)

    def test_negative_duration_raises(self):
        with pytest.raises(ValueError, match="max_backfill_duration_s"):
            _coord(max_backfill_duration_s=-1.0)

    def test_non_numeric_start_raises(self):
        with pytest.raises(TypeError, match="backfill_start"):
            HybridCoordinator(backfill_start="now", backfill_end=2000.0)

    def test_non_numeric_end_raises(self):
        with pytest.raises(TypeError, match="backfill_end"):
            HybridCoordinator(backfill_start=1000.0, backfill_end="later")

    def test_non_numeric_duration_raises(self):
        with pytest.raises(TypeError, match="max_backfill_duration_s"):
            _coord(max_backfill_duration_s="long")


# =============================================================================
# get_state()
# =============================================================================

class TestGetState:
    def test_returns_coordinator_state(self):
        c = _coord()
        s = c.get_state()
        assert isinstance(s, CoordinatorState)

    def test_initial_state(self):
        c = _coord()
        s = c.get_state()
        assert s.phase == HybridPhase.BACKFILL
        assert s.sync_point is None
        assert s.backfill_start == 1000.0
        assert s.backfill_end == 2000.0
        assert s.elapsed_backfill_s == 0.0
        assert s.candles_processed == 0
        assert s.sync_attempts == 0
        assert s.version == 1

    def test_state_reflects_updates(self):
        c = _coord()
        c.process_backfill_candle(1.0)
        s = c.get_state()
        assert s.candles_processed == 1
        assert s.elapsed_backfill_s == 1.0
        assert s.version == 2


# =============================================================================
# Backfill processing
# =============================================================================

class TestBackfillProcessing:
    def test_increments_candle_count(self):
        c = _coord()
        c.process_backfill_candle(0.1)
        c.process_backfill_candle(0.1)
        assert c.get_state().candles_processed == 2

    def test_accumulates_duration(self):
        c = _coord()
        c.process_backfill_candle(1.5)
        c.process_backfill_candle(2.5)
        assert c.get_state().elapsed_backfill_s == 4.0

    def test_returns_state(self):
        c = _coord()
        s = c.process_backfill_candle(0.1)
        assert isinstance(s, CoordinatorState)

    def test_zero_duration_valid(self):
        c = _coord()
        c.process_backfill_candle(0.0)
        assert c.get_state().elapsed_backfill_s == 0.0

    def test_negative_duration_raises(self):
        c = _coord()
        with pytest.raises(ValueError, match="duration_s"):
            c.process_backfill_candle(-1.0)

    def test_non_numeric_duration_raises(self):
        c = _coord()
        with pytest.raises(TypeError, match="duration_s"):
            c.process_backfill_candle("fast")

    def test_not_in_backfill_raises(self):
        c = _synced_coord()
        with pytest.raises(ValueError, match="BACKFILL"):
            c.process_backfill_candle(0.1)

    def test_backfill_budget_decreases(self):
        c = _coord(max_backfill_duration_s=10.0)
        c.process_backfill_candle(3.0)
        assert c.backfill_budget_remaining_s == 7.0

    def test_budget_remaining_never_negative(self):
        c = _coord(max_backfill_duration_s=10.0)
        try:
            for _ in range(20):
                c.process_backfill_candle(1.0)
        except OverflowError:
            pass
        assert c.backfill_budget_remaining_s == 0.0


# =============================================================================
# Backfill duration limit (CONSTRAINT 8)
# =============================================================================

class TestBackfillDurationLimit:
    def test_exceeds_limit_raises_overflow(self):
        c = _coord(max_backfill_duration_s=5.0)
        c.process_backfill_candle(3.0)
        c.process_backfill_candle(2.0)
        with pytest.raises(OverflowError, match="CONSTRAINT 8"):
            c.process_backfill_candle(1.0)

    def test_exceeds_transitions_to_failed(self):
        c = _coord(max_backfill_duration_s=5.0)
        try:
            for _ in range(10):
                c.process_backfill_candle(1.0)
        except OverflowError:
            pass
        assert c.phase == HybridPhase.FAILED
        assert c.is_terminal is True

    def test_at_exact_limit_does_not_raise(self):
        c = _coord(max_backfill_duration_s=5.0)
        c.process_backfill_candle(5.0)
        assert c.phase == HybridPhase.BACKFILL


# =============================================================================
# Sync point detection
# =============================================================================

class TestAttemptSync:
    def test_sync_detected(self):
        c = _coord()
        r = c.attempt_sync(2001.0, True)
        assert r.sync_detected is True
        assert r.sync_timestamp == 2001.0
        assert r.integrity_passed is True
        assert c.phase == HybridPhase.LIVE
        assert c.sync_point == 2001.0

    def test_integrity_failed(self):
        c = _coord()
        r = c.attempt_sync(2001.0, False)
        assert r.sync_detected is False
        assert r.sync_timestamp is None
        assert r.integrity_passed is False
        assert c.phase == HybridPhase.BACKFILL
        assert c.sync_point is None

    def test_timestamp_before_backfill_end(self):
        c = _coord()
        r = c.attempt_sync(1500.0, True)
        assert r.sync_detected is False
        assert r.integrity_passed is True
        assert c.phase == HybridPhase.BACKFILL

    def test_timestamp_at_backfill_end(self):
        c = _coord()
        r = c.attempt_sync(2000.0, True)
        assert r.sync_detected is False
        assert "backfill_end" in r.reason

    def test_sync_attempts_count(self):
        c = _coord()
        c.attempt_sync(1500.0, True)
        c.attempt_sync(1800.0, False)
        c.attempt_sync(2001.0, True)
        assert c.get_state().sync_attempts == 3

    def test_non_numeric_timestamp_raises(self):
        c = _coord()
        with pytest.raises(TypeError, match="live_candle_timestamp"):
            c.attempt_sync("now", True)

    def test_non_bool_integrity_raises(self):
        c = _coord()
        with pytest.raises(TypeError, match="integrity_passed"):
            c.attempt_sync(2001.0, 1)

    def test_not_in_backfill_raises(self):
        c = _synced_coord()
        with pytest.raises(ValueError, match="BACKFILL"):
            c.attempt_sync(3000.0, True)

    def test_int_timestamp_accepted(self):
        c = _coord()
        r = c.attempt_sync(2001, True)
        assert r.sync_detected is True
        assert r.sync_timestamp == 2001.0


# =============================================================================
# Sync point immutability
# =============================================================================

class TestSyncPointImmutability:
    def test_sync_point_set_once(self):
        c = _coord()
        c.attempt_sync(2001.0, True)
        assert c.sync_point == 2001.0

    def test_cannot_attempt_sync_after_set(self):
        c = _coord()
        c.attempt_sync(2001.0, True)
        # Now in LIVE phase, attempt_sync should raise
        with pytest.raises(ValueError, match="BACKFILL"):
            c.attempt_sync(3000.0, True)

    def test_sync_point_immutable_across_lifecycle(self):
        c = _synced_coord()
        c.process_live_candle()
        c.process_live_candle()
        assert c.sync_point == 2001.0


# =============================================================================
# Live processing
# =============================================================================

class TestLiveProcessing:
    def test_increments_candle_count(self):
        c = _synced_coord()
        initial = c.get_state().candles_processed
        c.process_live_candle()
        assert c.get_state().candles_processed == initial + 1

    def test_returns_state(self):
        c = _synced_coord()
        s = c.process_live_candle()
        assert isinstance(s, CoordinatorState)

    def test_not_in_live_raises(self):
        c = _coord()
        with pytest.raises(ValueError, match="LIVE"):
            c.process_live_candle()

    def test_multiple_live_candles(self):
        c = _synced_coord()
        for _ in range(10):
            c.process_live_candle()
        # 1 backfill + 10 live = 11
        assert c.get_state().candles_processed == 11


# =============================================================================
# Session completion
# =============================================================================

class TestComplete:
    def test_transitions_to_completed(self):
        c = _synced_coord()
        s = c.complete()
        assert s.phase == HybridPhase.COMPLETED
        assert c.is_terminal is True

    def test_not_in_live_raises(self):
        c = _coord()
        with pytest.raises(ValueError, match="LIVE"):
            c.complete()

    def test_completed_is_terminal(self):
        c = _synced_coord()
        c.complete()
        with pytest.raises(ValueError):
            c.process_live_candle()


# =============================================================================
# Failure
# =============================================================================

class TestFail:
    def test_fail_from_backfill(self):
        c = _coord()
        s = c.fail("data corruption")
        assert s.phase == HybridPhase.FAILED
        assert c.is_terminal is True

    def test_fail_from_live(self):
        c = _synced_coord()
        s = c.fail("connection lost")
        assert s.phase == HybridPhase.FAILED

    def test_fail_from_completed_raises(self):
        c = _synced_coord()
        c.complete()
        with pytest.raises(ValueError):
            c.fail("too late")

    def test_fail_from_failed_raises(self):
        c = _coord()
        c.fail("first failure")
        with pytest.raises(ValueError):
            c.fail("second failure")

    def test_empty_reason_raises(self):
        c = _coord()
        with pytest.raises(ValueError, match="reason"):
            c.fail("")

    def test_non_string_reason_raises(self):
        c = _coord()
        with pytest.raises(TypeError, match="reason"):
            c.fail(42)


# =============================================================================
# Phase transition enforcement
# =============================================================================

class TestPhaseTransitions:
    def test_backfill_to_live_via_sync(self):
        c = _coord()
        assert c.phase == HybridPhase.BACKFILL
        c.attempt_sync(2001.0, True)
        assert c.phase == HybridPhase.LIVE

    def test_live_to_completed(self):
        c = _synced_coord()
        c.complete()
        assert c.phase == HybridPhase.COMPLETED

    def test_backfill_to_failed(self):
        c = _coord()
        c.fail("error")
        assert c.phase == HybridPhase.FAILED

    def test_live_to_failed(self):
        c = _synced_coord()
        c.fail("error")
        assert c.phase == HybridPhase.FAILED

    def test_completed_is_terminal_no_transitions(self):
        c = _synced_coord()
        c.complete()
        with pytest.raises(ValueError):
            c.fail("cannot")

    def test_failed_is_terminal_no_transitions(self):
        c = _coord()
        c.fail("done")
        with pytest.raises(ValueError):
            c.fail("again")


# =============================================================================
# Properties
# =============================================================================

class TestProperties:
    def test_phase_property(self):
        c = _coord()
        assert c.phase == HybridPhase.BACKFILL

    def test_sync_point_none_initially(self):
        c = _coord()
        assert c.sync_point is None

    def test_sync_point_after_sync(self):
        c = _coord()
        c.attempt_sync(2001.0, True)
        assert c.sync_point == 2001.0

    def test_is_terminal_false(self):
        c = _coord()
        assert c.is_terminal is False

    def test_is_terminal_completed(self):
        c = _synced_coord()
        c.complete()
        assert c.is_terminal is True

    def test_is_terminal_failed(self):
        c = _coord()
        c.fail("error")
        assert c.is_terminal is True

    def test_backfill_budget_remaining(self):
        c = _coord(max_backfill_duration_s=100.0)
        assert c.backfill_budget_remaining_s == 100.0
        c.process_backfill_candle(30.0)
        assert c.backfill_budget_remaining_s == 70.0


# =============================================================================
# Version tracking
# =============================================================================

class TestVersionTracking:
    def test_initial_version(self):
        c = _coord()
        assert c.get_state().version == 1

    def test_version_increments_on_backfill(self):
        c = _coord()
        c.process_backfill_candle(0.1)
        assert c.get_state().version == 2

    def test_version_increments_on_sync(self):
        c = _coord()
        c.attempt_sync(2001.0, True)
        # attempt_sync increments version, then transitions increment more
        assert c.get_state().version >= 2

    def test_version_increments_on_live_candle(self):
        c = _synced_coord()
        v_before = c.get_state().version
        c.process_live_candle()
        assert c.get_state().version == v_before + 1


# =============================================================================
# Full lifecycle
# =============================================================================

class TestFullLifecycle:
    def test_complete_lifecycle(self):
        c = _coord(max_backfill_duration_s=60.0)

        # Phase 1: Backfill
        assert c.phase == HybridPhase.BACKFILL
        for _ in range(5):
            c.process_backfill_candle(0.5)
        assert c.get_state().candles_processed == 5
        assert c.get_state().elapsed_backfill_s == 2.5

        # Phase 2: Failed sync attempts
        r1 = c.attempt_sync(1500.0, True)
        assert r1.sync_detected is False
        r2 = c.attempt_sync(2001.0, False)
        assert r2.sync_detected is False
        assert c.get_state().sync_attempts == 2

        # Phase 3: Successful sync
        r3 = c.attempt_sync(2001.0, True)
        assert r3.sync_detected is True
        assert c.phase == HybridPhase.LIVE

        # Phase 4: Live processing
        for _ in range(3):
            c.process_live_candle()
        assert c.get_state().candles_processed == 8

        # Phase 5: Complete
        s = c.complete()
        assert s.phase == HybridPhase.COMPLETED
        assert c.is_terminal is True
        assert c.sync_point == 2001.0

    def test_lifecycle_with_failure(self):
        c = _coord()
        c.process_backfill_candle(1.0)
        c.fail("data provider disconnected")
        assert c.phase == HybridPhase.FAILED
        assert c.is_terminal is True


# =============================================================================
# Determinism
# =============================================================================

class TestDeterminism:
    def test_same_sequence_same_state(self):
        c1 = _coord()
        c2 = _coord()

        for c in [c1, c2]:
            c.process_backfill_candle(1.0)
            c.process_backfill_candle(2.0)
            c.attempt_sync(2001.0, True)
            c.process_live_candle()

        s1 = c1.get_state()
        s2 = c2.get_state()
        assert s1.phase == s2.phase
        assert s1.sync_point == s2.sync_point
        assert s1.candles_processed == s2.candles_processed
        assert s1.elapsed_backfill_s == s2.elapsed_backfill_s
        assert s1.version == s2.version

    def test_different_sequence_different_state(self):
        c1 = _coord()
        c2 = _coord()

        c1.attempt_sync(2001.0, True)
        c2.process_backfill_candle(1.0)

        assert c1.phase != c2.phase
