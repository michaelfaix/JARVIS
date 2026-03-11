# =============================================================================
# tests/unit/systems/test_control_flow.py
# Tests for jarvis/systems/control_flow.py
# =============================================================================

import pytest

from jarvis.systems.control_flow import (
    ControlSignal,
    FlowState,
    LAYER_NAMES,
    SystemControlFlow,
)


# =============================================================================
# SECTION 1 -- CONTROL SIGNAL ENUM
# =============================================================================

class TestControlSignal:
    def test_four_signals(self):
        assert len(ControlSignal) == 4

    def test_continue(self):
        assert ControlSignal.CONTINUE.value == "continue"

    def test_degrade(self):
        assert ControlSignal.DEGRADE.value == "degrade"

    def test_stop(self):
        assert ControlSignal.STOP.value == "stop"

    def test_emergency(self):
        assert ControlSignal.EMERGENCY.value == "emergency"


# =============================================================================
# SECTION 2 -- FLOW STATE DATACLASS
# =============================================================================

class TestFlowState:
    def test_frozen(self):
        fs = FlowState(1, "data_ingestion", ControlSignal.CONTINUE, True, "ok")
        with pytest.raises(AttributeError):
            fs.signal = ControlSignal.STOP

    def test_fields(self):
        fs = FlowState(
            layer=1,
            layer_name="data_ingestion",
            signal=ControlSignal.CONTINUE,
            gate_passed=True,
            reason="ok",
        )
        assert fs.layer == 1
        assert fs.layer_name == "data_ingestion"
        assert fs.signal == ControlSignal.CONTINUE
        assert fs.gate_passed is True

    def test_equality(self):
        fs1 = FlowState(1, "data_ingestion", ControlSignal.CONTINUE, True, "ok")
        fs2 = FlowState(1, "data_ingestion", ControlSignal.CONTINUE, True, "ok")
        assert fs1 == fs2


# =============================================================================
# SECTION 3 -- LAYER NAMES
# =============================================================================

class TestLayerNames:
    def test_eleven_layers(self):
        assert len(LAYER_NAMES) == 11

    def test_sequential_keys(self):
        assert set(LAYER_NAMES.keys()) == set(range(1, 12))

    def test_layer_1(self):
        assert LAYER_NAMES[1] == "data_ingestion"

    def test_layer_7(self):
        assert LAYER_NAMES[7] == "ood_detection"

    def test_layer_8(self):
        assert LAYER_NAMES[8] == "risk_engine"

    def test_layer_11(self):
        assert LAYER_NAMES[11] == "output_interface"


# =============================================================================
# SECTION 4 -- FULL PIPELINE (ALL GATES PASS)
# =============================================================================

class TestFullPipeline:
    """All metrics within safe range — all 11 layers should be traversed."""

    def _good_inputs(self):
        return dict(
            quality_score=0.8,
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.02,
            is_ood=False,
            var=-0.10,
        )

    def test_eleven_states(self):
        flow = SystemControlFlow()
        states = flow.execute(**self._good_inputs())
        assert len(states) == 11

    def test_all_continue(self):
        flow = SystemControlFlow()
        states = flow.execute(**self._good_inputs())
        assert all(s.signal == ControlSignal.CONTINUE for s in states)

    def test_all_gates_passed(self):
        flow = SystemControlFlow()
        states = flow.execute(**self._good_inputs())
        assert all(s.gate_passed for s in states)

    def test_layer_numbers_sequential(self):
        flow = SystemControlFlow()
        states = flow.execute(**self._good_inputs())
        layers = [s.layer for s in states]
        assert layers == list(range(1, 12))

    def test_layer_names_match(self):
        flow = SystemControlFlow()
        states = flow.execute(**self._good_inputs())
        for s in states:
            assert s.layer_name == LAYER_NAMES[s.layer]

    def test_non_gated_layers_passthrough(self):
        flow = SystemControlFlow()
        states = flow.execute(**self._good_inputs())
        non_gated = [s for s in states if s.layer in {4, 6, 9, 10, 11}]
        for s in non_gated:
            assert s.gate_passed is True
            assert "passthrough" in s.reason.lower()


# =============================================================================
# SECTION 5 -- LAYER 1 HARD STOP (QUALITY)
# =============================================================================

class TestLayer1Stop:
    def test_low_quality_stops(self):
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.3,
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.02,
            is_ood=False,
            var=-0.10,
        )
        assert len(states) == 1
        assert states[0].layer == 1
        assert states[0].signal == ControlSignal.STOP
        assert states[0].gate_passed is False

    def test_quality_at_threshold_passes(self):
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.5,
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.02,
            is_ood=False,
            var=-0.10,
        )
        assert len(states) > 1
        assert states[0].signal == ControlSignal.CONTINUE


# =============================================================================
# SECTION 6 -- LAYER 2 DEGRADE (DRIFT)
# =============================================================================

class TestLayer2Degrade:
    def test_high_drift_degrades(self):
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.8,
            drift_severity=0.9,
            condition_number=1e3,
            ece=0.02,
            is_ood=False,
            var=-0.10,
        )
        assert len(states) == 2
        assert states[1].layer == 2
        assert states[1].signal == ControlSignal.DEGRADE
        assert states[1].gate_passed is False

    def test_drift_at_threshold_degrades(self):
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.8,
            drift_severity=0.8,
            condition_number=1e3,
            ece=0.02,
            is_ood=False,
            var=-0.10,
        )
        assert states[1].signal == ControlSignal.DEGRADE


# =============================================================================
# SECTION 7 -- LAYER 3 DEGRADE (KALMAN)
# =============================================================================

class TestLayer3Degrade:
    def test_high_condition_number_degrades(self):
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.8,
            drift_severity=0.3,
            condition_number=1e6,
            ece=0.02,
            is_ood=False,
            var=-0.10,
        )
        assert len(states) == 3
        assert states[2].layer == 3
        assert states[2].signal == ControlSignal.DEGRADE

    def test_condition_below_passes(self):
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.8,
            drift_severity=0.3,
            condition_number=9e4,
            ece=0.02,
            is_ood=False,
            var=-0.10,
        )
        assert states[2].signal == ControlSignal.CONTINUE


# =============================================================================
# SECTION 8 -- LAYER 5 STOP (ECE)
# =============================================================================

class TestLayer5Stop:
    def test_high_ece_stops(self):
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.8,
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.10,
            is_ood=False,
            var=-0.10,
        )
        # Layers 1-4 pass, layer 5 stops
        assert len(states) == 5
        assert states[4].layer == 5
        assert states[4].signal == ControlSignal.STOP
        assert states[4].gate_passed is False

    def test_ece_at_threshold_stops(self):
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.8,
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.05,
            is_ood=False,
            var=-0.10,
        )
        assert states[4].signal == ControlSignal.STOP


# =============================================================================
# SECTION 9 -- LAYER 7 DEGRADE (OOD)
# =============================================================================

class TestLayer7Degrade:
    def test_ood_detected_degrades(self):
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.8,
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.02,
            is_ood=True,
            var=-0.10,
        )
        # Layers 1-6 pass, layer 7 degrades
        assert len(states) == 7
        assert states[6].layer == 7
        assert states[6].signal == ControlSignal.DEGRADE
        assert states[6].gate_passed is False

    def test_no_ood_passes(self):
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.8,
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.02,
            is_ood=False,
            var=-0.10,
        )
        assert states[6].signal == ControlSignal.CONTINUE


# =============================================================================
# SECTION 10 -- LAYER 8 EMERGENCY (RISK)
# =============================================================================

class TestLayer8Emergency:
    def test_high_drawdown_emergency(self):
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.8,
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.02,
            is_ood=False,
            var=-0.20,
        )
        # Layers 1-7 pass, layer 8 emergency
        assert len(states) == 8
        assert states[7].layer == 8
        assert states[7].signal == ControlSignal.EMERGENCY
        assert states[7].gate_passed is False

    def test_var_at_threshold_passes(self):
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.8,
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.02,
            is_ood=False,
            var=-0.15,
        )
        assert states[7].signal == ControlSignal.CONTINUE


# =============================================================================
# SECTION 11 -- EARLY EXIT ENFORCEMENT
# =============================================================================

class TestEarlyExit:
    def test_first_failure_stops(self):
        """Only layers up to first failure are in result."""
        flow = SystemControlFlow()
        # Quality fails at layer 1 — no further layers
        states = flow.execute(
            quality_score=0.1,
            drift_severity=0.9,  # would fail layer 2
            condition_number=1e6,  # would fail layer 3
            ece=0.10,  # would fail layer 5
            is_ood=True,  # would fail layer 7
            var=-0.20,  # would fail layer 8
        )
        assert len(states) == 1
        assert states[0].layer == 1

    def test_multiple_failures_earliest_wins(self):
        """If layers 2 and 7 would fail, only layer 2 is reached."""
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.8,
            drift_severity=0.9,  # fails layer 2
            condition_number=1e3,
            ece=0.02,
            is_ood=True,  # would fail layer 7
            var=-0.10,
        )
        assert len(states) == 2
        assert states[-1].layer == 2
        assert states[-1].signal == ControlSignal.DEGRADE


# =============================================================================
# SECTION 12 -- VALIDATION
# =============================================================================

class TestValidation:
    def test_quality_score_type_error(self):
        flow = SystemControlFlow()
        with pytest.raises(TypeError, match="quality_score must be numeric"):
            flow.execute("bad", 0.3, 1e3, 0.02, False, -0.10)

    def test_drift_severity_type_error(self):
        flow = SystemControlFlow()
        with pytest.raises(TypeError, match="drift_severity must be numeric"):
            flow.execute(0.8, "bad", 1e3, 0.02, False, -0.10)

    def test_condition_number_type_error(self):
        flow = SystemControlFlow()
        with pytest.raises(TypeError, match="condition_number must be numeric"):
            flow.execute(0.8, 0.3, "bad", 0.02, False, -0.10)

    def test_ece_type_error(self):
        flow = SystemControlFlow()
        with pytest.raises(TypeError, match="ece must be numeric"):
            flow.execute(0.8, 0.3, 1e3, "bad", False, -0.10)

    def test_is_ood_type_error(self):
        flow = SystemControlFlow()
        with pytest.raises(TypeError, match="is_ood must be bool"):
            flow.execute(0.8, 0.3, 1e3, 0.02, 1, -0.10)

    def test_var_type_error(self):
        flow = SystemControlFlow()
        with pytest.raises(TypeError, match="var must be numeric"):
            flow.execute(0.8, 0.3, 1e3, 0.02, False, "bad")


# =============================================================================
# SECTION 13 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_same_inputs_same_output(self):
        flow = SystemControlFlow()
        kwargs = dict(
            quality_score=0.8,
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.02,
            is_ood=False,
            var=-0.10,
        )
        results = [flow.execute(**kwargs) for _ in range(10)]
        for r in results[1:]:
            assert r == results[0]

    def test_independent_flows(self):
        kwargs = dict(
            quality_score=0.8,
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.02,
            is_ood=False,
            var=-0.10,
        )
        r1 = SystemControlFlow().execute(**kwargs)
        r2 = SystemControlFlow().execute(**kwargs)
        assert r1 == r2

    def test_failure_path_deterministic(self):
        flow = SystemControlFlow()
        kwargs = dict(
            quality_score=0.8,
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.02,
            is_ood=True,
            var=-0.10,
        )
        r1 = flow.execute(**kwargs)
        r2 = flow.execute(**kwargs)
        assert r1 == r2
        assert r1[-1].signal == ControlSignal.DEGRADE


# =============================================================================
# SECTION 14 -- EVENT LOG INTEGRATION
# =============================================================================

from jarvis.core.event_log import EventLog, EventLogEntry, EventType


def _make_event_log() -> EventLog:
    """Create a fresh EventLog for testing."""
    return EventLog(
        session_id="test-session",
        operating_mode="historical",
        start_time=0.0,
    )


def _good_inputs():
    return dict(
        quality_score=0.8,
        drift_severity=0.3,
        condition_number=1e3,
        ece=0.02,
        is_ood=False,
        var=-0.10,
    )


class TestEventLogIntegration:
    """Tests for EventLog wiring in SystemControlFlow.execute()."""

    def test_no_event_log_backward_compatible(self):
        """Without event_log, execute() works exactly as before."""
        flow = SystemControlFlow()
        states = flow.execute(**_good_inputs())
        assert len(states) == 11

    def test_event_log_receives_entries(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        flow.execute(**_good_inputs(), event_log=log, timestamp=1.0)
        assert log.entry_count == 11

    def test_event_log_entry_count_matches_states(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        states = flow.execute(**_good_inputs(), event_log=log, timestamp=1.0)
        assert log.entry_count == len(states)

    def test_event_type_is_layer_transition(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        flow.execute(**_good_inputs(), event_log=log, timestamp=1.0)
        for entry in log.get_entries():
            assert entry.event_type == EventType.LAYER_TRANSITION.value

    def test_entries_have_correct_timestamp(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        flow.execute(**_good_inputs(), event_log=log, timestamp=42.5)
        for entry in log.get_entries():
            assert entry.timestamp == 42.5

    def test_payload_contains_layer_info(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        flow.execute(**_good_inputs(), event_log=log, timestamp=1.0)
        entries = log.get_entries()
        for i, entry in enumerate(entries):
            assert entry.event_payload["layer"] == i + 1
            assert entry.event_payload["layer_name"] == LAYER_NAMES[i + 1]
            assert "signal" in entry.event_payload
            assert "gate_passed" in entry.event_payload
            assert "reason" in entry.event_payload

    def test_payload_signal_values(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        flow.execute(**_good_inputs(), event_log=log, timestamp=1.0)
        for entry in log.get_entries():
            assert entry.event_payload["signal"] == "continue"
            assert entry.event_payload["gate_passed"] is True

    def test_sequence_ids_monotonic(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        flow.execute(**_good_inputs(), event_log=log, timestamp=1.0)
        entries = log.get_entries()
        for i in range(1, len(entries)):
            assert entries[i].sequence_id > entries[i - 1].sequence_id

    def test_state_hashes_are_sha256(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        flow.execute(**_good_inputs(), event_log=log, timestamp=1.0)
        for entry in log.get_entries():
            assert len(entry.state_hash_before) == 64
            assert len(entry.state_hash_after) == 64
            # Valid hex
            int(entry.state_hash_before, 16)
            int(entry.state_hash_after, 16)

    def test_hash_chain_linked(self):
        """state_hash_after of entry N == state_hash_before of entry N+1."""
        log = _make_event_log()
        flow = SystemControlFlow()
        flow.execute(**_good_inputs(), event_log=log, timestamp=1.0)
        entries = log.get_entries()
        for i in range(1, len(entries)):
            assert entries[i].state_hash_before == entries[i - 1].state_hash_after

    def test_hashes_distinct_per_layer(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        flow.execute(**_good_inputs(), event_log=log, timestamp=1.0)
        after_hashes = [e.state_hash_after for e in log.get_entries()]
        assert len(set(after_hashes)) == 11

    def test_early_exit_logs_only_traversed_layers(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.3,  # fails layer 1
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.02,
            is_ood=False,
            var=-0.10,
            event_log=log,
            timestamp=1.0,
        )
        assert len(states) == 1
        assert log.entry_count == 1
        entry = log.get_entries()[0]
        assert entry.event_payload["layer"] == 1
        assert entry.event_payload["signal"] == "stop"
        assert entry.event_payload["gate_passed"] is False

    def test_layer_2_failure_logs_two_entries(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.8,
            drift_severity=0.9,  # fails layer 2
            condition_number=1e3,
            ece=0.02,
            is_ood=False,
            var=-0.10,
            event_log=log,
            timestamp=1.0,
        )
        assert len(states) == 2
        assert log.entry_count == 2
        assert log.get_entries()[1].event_payload["signal"] == "degrade"

    def test_layer_8_emergency_logs_eight_entries(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        states = flow.execute(
            quality_score=0.8,
            drift_severity=0.3,
            condition_number=1e3,
            ece=0.02,
            is_ood=False,
            var=-0.20,  # fails layer 8
            event_log=log,
            timestamp=1.0,
        )
        assert len(states) == 8
        assert log.entry_count == 8
        assert log.get_entries()[-1].event_payload["signal"] == "emergency"

    def test_deterministic_event_log(self):
        """Same inputs produce identical event log entries."""
        kwargs = _good_inputs()
        log1 = _make_event_log()
        log2 = _make_event_log()
        SystemControlFlow().execute(**kwargs, event_log=log1, timestamp=1.0)
        SystemControlFlow().execute(**kwargs, event_log=log2, timestamp=1.0)
        entries1 = log1.get_entries()
        entries2 = log2.get_entries()
        assert len(entries1) == len(entries2)
        for e1, e2 in zip(entries1, entries2):
            assert e1.sequence_id == e2.sequence_id
            assert e1.event_payload == e2.event_payload
            assert e1.state_hash_before == e2.state_hash_before
            assert e1.state_hash_after == e2.state_hash_after

    def test_event_log_integrity_after_close(self):
        log = _make_event_log()
        log.set_genesis_state_hash("a" * 64)
        flow = SystemControlFlow()
        flow.execute(**_good_inputs(), event_log=log, timestamp=1.0)
        last_hash = log.get_entries()[-1].state_hash_after
        log.close(end_time=2.0, final_state_hash=last_hash)
        assert log.is_closed
        assert log.validate_integrity()

    def test_multiple_executions_append_to_same_log(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        flow.execute(**_good_inputs(), event_log=log, timestamp=1.0)
        assert log.entry_count == 11
        # Second execution appends more entries
        flow.execute(**_good_inputs(), event_log=log, timestamp=2.0)
        assert log.entry_count == 22

    def test_multiple_executions_sequence_ids_monotonic(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        flow.execute(**_good_inputs(), event_log=log, timestamp=1.0)
        flow.execute(**_good_inputs(), event_log=log, timestamp=2.0)
        entries = log.get_entries()
        for i in range(1, len(entries)):
            assert entries[i].sequence_id > entries[i - 1].sequence_id

    def test_filter_by_layer_transition_type(self):
        log = _make_event_log()
        flow = SystemControlFlow()
        flow.execute(**_good_inputs(), event_log=log, timestamp=1.0)
        transitions = log.get_entries_by_type(EventType.LAYER_TRANSITION.value)
        assert len(transitions) == 11
