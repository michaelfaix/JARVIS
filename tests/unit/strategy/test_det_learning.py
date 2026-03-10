# =============================================================================
# Tests for jarvis/learning/deterministic_learning.py (S27)
# =============================================================================

import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from jarvis.learning.deterministic_learning import (
    DeterministicLearningOrchestrator,
    LearningCycleResult,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

@pytest.fixture
def log_layer():
    mock = MagicMock()
    mock.log_event = MagicMock()
    return mock


@pytest.fixture
def orchestrator(log_layer, tmp_path):
    return DeterministicLearningOrchestrator(
        model_registry_path=tmp_path,
        log_layer=log_layer,
    )


def _cal_fn(ece_active=0.06, ece_candidate=0.04):
    """Return a calibration_eval_fn that returns fixed ECE values."""
    def fn(*, model, data):
        if model == "active":
            return ece_active
        return ece_candidate
    return fn


def _stress_fn(passes=True):
    """Return a stress_test_fn that returns a fixed result."""
    def fn(*, model, data):
        return passes
    return fn


PARAMS_A = {"alpha": 0.1, "beta": 0.2}
PARAMS_B = {"beta": 0.2, "alpha": 0.1}  # Same keys, different insertion order
VALIDATION_DATA = {"returns": [0.01, -0.02, 0.03]}


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

class TestConstants:
    def test_min_improvement_threshold(self):
        assert DeterministicLearningOrchestrator.MIN_IMPROVEMENT_THRESHOLD == 0.005

    def test_max_ece_after_training(self):
        assert DeterministicLearningOrchestrator.MAX_ECE_AFTER_TRAINING == 0.05

    def test_required_stress_pass(self):
        assert DeterministicLearningOrchestrator.REQUIRED_STRESS_PASS is True


# ---------------------------------------------------------------------------
# CONSTRUCTOR
# ---------------------------------------------------------------------------

class TestConstructor:
    def test_init_attributes(self, orchestrator, tmp_path, log_layer):
        assert orchestrator.registry_path == tmp_path
        assert orchestrator.log is log_layer
        assert orchestrator._active_model_hash is None

    def test_no_rollback_initially(self, orchestrator):
        assert orchestrator._rollback_snapshot is None


# ---------------------------------------------------------------------------
# ECE GATE
# ---------------------------------------------------------------------------

class TestECEGate:
    def test_ece_gate_fail_above_hard_limit(self, orchestrator, log_layer):
        with pytest.raises(RuntimeError, match="LEARNING_GATE_FAIL"):
            orchestrator.run_cycle(
                new_model_params=PARAMS_A,
                validation_data=VALIDATION_DATA,
                stress_test_fn=_stress_fn(True),
                calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.06),
                chunk_id="chunk_1",
            )
        log_layer.log_event.assert_called()
        event_kwargs = log_layer.log_event.call_args
        assert event_kwargs[1]["type"] == "LEARNING_GATE_FAIL"
        assert event_kwargs[1]["reason"] == "ECE_ABOVE_HARD_LIMIT"

    def test_ece_gate_fail_includes_value(self, orchestrator):
        with pytest.raises(RuntimeError, match="0.0700"):
            orchestrator.run_cycle(
                new_model_params=PARAMS_A,
                validation_data=VALIDATION_DATA,
                stress_test_fn=_stress_fn(True),
                calibration_eval_fn=_cal_fn(ece_candidate=0.07),
                chunk_id="chunk_1",
            )

    def test_ece_gate_fail_includes_hard_limit(self, orchestrator):
        with pytest.raises(RuntimeError, match="Hard Limit"):
            orchestrator.run_cycle(
                new_model_params=PARAMS_A,
                validation_data=VALIDATION_DATA,
                stress_test_fn=_stress_fn(True),
                calibration_eval_fn=_cal_fn(ece_candidate=0.051),
                chunk_id="chunk_1",
            )

    def test_ece_exactly_at_limit_passes(self, orchestrator):
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.05),
            chunk_id="chunk_1",
        )
        assert isinstance(result, LearningCycleResult)

    def test_ece_gate_checked_before_stress(self, orchestrator):
        """ECE gate must be evaluated before stress_test_fn is called."""
        stress_called = []

        def stress_fn(*, model, data):
            stress_called.append(True)
            return True

        with pytest.raises(RuntimeError, match="LEARNING_GATE_FAIL"):
            orchestrator.run_cycle(
                new_model_params=PARAMS_A,
                validation_data=VALIDATION_DATA,
                stress_test_fn=stress_fn,
                calibration_eval_fn=_cal_fn(ece_candidate=0.08),
                chunk_id="chunk_1",
            )
        assert len(stress_called) == 0


# ---------------------------------------------------------------------------
# STRESS TEST GATE
# ---------------------------------------------------------------------------

class TestStressTestGate:
    def test_stress_test_gate_fail(self, orchestrator, log_layer):
        with pytest.raises(RuntimeError, match="Stress-Test nicht bestanden"):
            orchestrator.run_cycle(
                new_model_params=PARAMS_A,
                validation_data=VALIDATION_DATA,
                stress_test_fn=_stress_fn(False),
                calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
                chunk_id="chunk_1",
            )
        event_kwargs = log_layer.log_event.call_args
        assert event_kwargs[1]["type"] == "LEARNING_GATE_FAIL"
        assert event_kwargs[1]["reason"] == "STRESS_TEST_FAILED"

    def test_stress_fn_receives_candidate(self, orchestrator):
        received_model = []

        def stress_fn(*, model, data):
            received_model.append(model)
            return True

        orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=stress_fn,
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert received_model == ["candidate"]

    def test_stress_fn_receives_validation_data(self, orchestrator):
        received_data = []

        def stress_fn(*, model, data):
            received_data.append(data)
            return True

        orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=stress_fn,
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert received_data[0] is VALIDATION_DATA


# ---------------------------------------------------------------------------
# INSUFFICIENT IMPROVEMENT
# ---------------------------------------------------------------------------

class TestInsufficientImprovement:
    def test_no_deploy_below_threshold(self, orchestrator, log_layer):
        # improvement = 0.049 - 0.046 = 0.003 < 0.005
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.049, ece_candidate=0.046),
            chunk_id="chunk_1",
        )
        assert result.deployed is False
        assert result.model_hash == "CANDIDATE_NOT_DEPLOYED"
        assert result.rollback_available is True

    def test_no_deploy_logs_event(self, orchestrator, log_layer):
        orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.049, ece_candidate=0.046),
            chunk_id="chunk_1",
        )
        event_kwargs = log_layer.log_event.call_args
        assert event_kwargs[1]["type"] == "LEARNING_NO_DEPLOY"
        assert event_kwargs[1]["reason"] == "INSUFFICIENT_IMPROVEMENT"

    def test_no_deploy_notes(self, orchestrator):
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.049, ece_candidate=0.046),
            chunk_id="chunk_1",
        )
        assert "Nicht deployt" in result.notes
        assert "0.0030" in result.notes

    def test_zero_improvement_no_deploy(self, orchestrator):
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.04, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert result.deployed is False
        assert result.improvement == pytest.approx(0.0)

    def test_negative_improvement_no_deploy(self, orchestrator):
        # Candidate worse than active
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.04, ece_candidate=0.045),
            chunk_id="chunk_1",
        )
        assert result.deployed is False
        assert result.improvement < 0

    def test_exactly_at_threshold_no_deploy(self, orchestrator):
        # improvement = 0.005 is NOT strictly less than 0.005 → should deploy? No: < means 0.005 is not < 0.005
        # Actually 0.005 is NOT < 0.005 → passes improvement check → deploys
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.05, ece_candidate=0.045),
            chunk_id="chunk_1",
        )
        assert result.deployed is True


# ---------------------------------------------------------------------------
# SUCCESSFUL DEPLOYMENT
# ---------------------------------------------------------------------------

class TestSuccessfulDeployment:
    def test_deployed_true(self, orchestrator):
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert result.deployed is True
        assert result.rollback_available is True

    def test_model_hash_not_candidate(self, orchestrator):
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert result.model_hash != "CANDIDATE_NOT_DEPLOYED"
        assert len(result.model_hash) == 16

    def test_model_hash_is_sha256_of_sorted_json(self, orchestrator):
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        expected = hashlib.sha256(
            json.dumps(PARAMS_A, sort_keys=True).encode()
        ).hexdigest()[:16]
        assert result.model_hash == expected

    def test_deployment_logs_event(self, orchestrator, log_layer):
        orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        event_kwargs = log_layer.log_event.call_args
        assert event_kwargs[1]["type"] == "LEARNING_DEPLOYED"
        assert "model_hash" in event_kwargs[1]
        assert "ece_improvement" in event_kwargs[1]
        assert "cycle_id" in event_kwargs[1]

    def test_deployment_notes(self, orchestrator):
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert "Deployt" in result.notes
        assert "0.0200" in result.notes

    def test_active_model_hash_updated(self, orchestrator):
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert orchestrator._active_model_hash == result.model_hash

    def test_ece_values_in_result(self, orchestrator):
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert result.ece_before == pytest.approx(0.06)
        assert result.ece_after == pytest.approx(0.04)
        assert result.improvement == pytest.approx(0.02)

    def test_stress_pass_in_result(self, orchestrator):
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert result.stress_pass is True


# ---------------------------------------------------------------------------
# ROLLBACK
# ---------------------------------------------------------------------------

class TestRollback:
    def test_rollback_no_snapshot(self, orchestrator, log_layer):
        result = orchestrator.rollback()
        assert result is False
        log_layer.log_event.assert_called_once()
        event_kwargs = log_layer.log_event.call_args
        assert event_kwargs[1]["type"] == "ROLLBACK_FAILED"
        assert event_kwargs[1]["reason"] == "NO_SNAPSHOT_AVAILABLE"

    def test_rollback_success_after_two_deploys(self, orchestrator, log_layer):
        # Deploy first model
        orchestrator.run_cycle(
            new_model_params={"v": 1},
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        first_hash = orchestrator._active_model_hash

        # Deploy second model (snapshot of first is saved)
        orchestrator.run_cycle(
            new_model_params={"v": 2},
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_2",
        )

        # Rollback to first
        result = orchestrator.rollback()
        assert result is True
        assert orchestrator._active_model_hash == first_hash

    def test_rollback_logs_success(self, orchestrator, log_layer):
        # Deploy then rollback
        orchestrator.run_cycle(
            new_model_params={"v": 1},
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        orchestrator.run_cycle(
            new_model_params={"v": 2},
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_2",
        )
        orchestrator.rollback()
        event_kwargs = log_layer.log_event.call_args
        assert event_kwargs[1]["type"] == "ROLLBACK_SUCCESS"
        assert "restored_hash" in event_kwargs[1]

    def test_first_deploy_no_snapshot_yet(self, orchestrator):
        """First deployment has no previous model, so snapshot is None."""
        orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        # _rollback_snapshot is None because _active_model_hash was None before first deploy
        assert orchestrator._rollback_snapshot is None


# ---------------------------------------------------------------------------
# CYCLE ID & HASHING
# ---------------------------------------------------------------------------

class TestCycleIdAndHashing:
    def test_cycle_id_is_12_chars(self, orchestrator):
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert len(result.cycle_id) == 12

    def test_cycle_id_is_hex(self, orchestrator):
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        int(result.cycle_id, 16)  # Should not raise

    def test_model_hash_from_sorted_json(self, orchestrator):
        """Same params with different insertion order produce same hash."""
        r1 = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_a",
        )
        r2 = orchestrator.run_cycle(
            new_model_params=PARAMS_B,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_b",
        )
        assert r1.model_hash == r2.model_hash

    def test_different_params_different_hash(self, orchestrator):
        r1 = orchestrator.run_cycle(
            new_model_params={"x": 1},
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_a",
        )
        r2 = orchestrator.run_cycle(
            new_model_params={"x": 2},
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_b",
        )
        assert r1.model_hash != r2.model_hash

    def test_timestamp_iso_format(self, orchestrator):
        result = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert "T" in result.timestamp


# ---------------------------------------------------------------------------
# GATE ORDER ENFORCEMENT
# ---------------------------------------------------------------------------

class TestGateOrder:
    def test_ece_checked_before_stress(self, orchestrator):
        """If ECE fails, stress_test_fn must NOT be called."""
        stress_calls = []

        def tracked_stress(*, model, data):
            stress_calls.append(True)
            return True

        with pytest.raises(RuntimeError, match="LEARNING_GATE_FAIL"):
            orchestrator.run_cycle(
                new_model_params=PARAMS_A,
                validation_data=VALIDATION_DATA,
                stress_test_fn=tracked_stress,
                calibration_eval_fn=_cal_fn(ece_candidate=0.08),
                chunk_id="chunk_1",
            )
        assert len(stress_calls) == 0

    def test_stress_checked_before_improvement(self, orchestrator, log_layer):
        """If stress fails, no LEARNING_NO_DEPLOY or LEARNING_DEPLOYED should appear."""
        with pytest.raises(RuntimeError, match="Stress-Test"):
            orchestrator.run_cycle(
                new_model_params=PARAMS_A,
                validation_data=VALIDATION_DATA,
                stress_test_fn=_stress_fn(False),
                calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
                chunk_id="chunk_1",
            )
        # Only LEARNING_GATE_FAIL should have been logged
        for c in log_layer.log_event.call_args_list:
            assert c[1]["type"] != "LEARNING_NO_DEPLOY"
            assert c[1]["type"] != "LEARNING_DEPLOYED"

    def test_calibration_eval_fn_called_with_both_models(self, orchestrator):
        models_called = []

        def tracking_cal(*, model, data):
            models_called.append(model)
            return 0.04

        orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=tracking_cal,
            chunk_id="chunk_1",
        )
        assert "active" in models_called
        assert "candidate" in models_called
        # Active evaluated before candidate
        assert models_called.index("active") < models_called.index("candidate")


# ---------------------------------------------------------------------------
# LOGGING EVENTS
# ---------------------------------------------------------------------------

class TestLoggingEvents:
    def test_gate_fail_ece_logs_exactly_once(self, orchestrator, log_layer):
        with pytest.raises(RuntimeError):
            orchestrator.run_cycle(
                new_model_params=PARAMS_A,
                validation_data=VALIDATION_DATA,
                stress_test_fn=_stress_fn(True),
                calibration_eval_fn=_cal_fn(ece_candidate=0.08),
                chunk_id="chunk_1",
            )
        assert log_layer.log_event.call_count == 1

    def test_gate_fail_stress_logs_exactly_once(self, orchestrator, log_layer):
        with pytest.raises(RuntimeError):
            orchestrator.run_cycle(
                new_model_params=PARAMS_A,
                validation_data=VALIDATION_DATA,
                stress_test_fn=_stress_fn(False),
                calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
                chunk_id="chunk_1",
            )
        assert log_layer.log_event.call_count == 1

    def test_no_deploy_logs_exactly_once(self, orchestrator, log_layer):
        orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.04, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert log_layer.log_event.call_count == 1

    def test_deploy_logs_exactly_once(self, orchestrator, log_layer):
        orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert log_layer.log_event.call_count == 1

    def test_all_events_contain_cycle_id(self, orchestrator, log_layer):
        # Successful deploy
        orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert "cycle_id" in log_layer.log_event.call_args[1]

    def test_event_contains_type_key(self, orchestrator, log_layer):
        orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        assert "type" in log_layer.log_event.call_args[1]


# ---------------------------------------------------------------------------
# LEARNING CYCLE RESULT DATACLASS
# ---------------------------------------------------------------------------

class TestLearningCycleResult:
    def test_all_fields(self):
        r = LearningCycleResult(
            cycle_id="abc123def456",
            timestamp="2026-01-01T00:00:00",
            ece_before=0.06,
            ece_after=0.04,
            stress_pass=True,
            improvement=0.02,
            deployed=True,
            rollback_available=True,
            model_hash="abcdef0123456789",
            notes="Test",
        )
        assert r.cycle_id == "abc123def456"
        assert r.timestamp == "2026-01-01T00:00:00"
        assert r.ece_before == 0.06
        assert r.ece_after == 0.04
        assert r.stress_pass is True
        assert r.improvement == 0.02
        assert r.deployed is True
        assert r.rollback_available is True
        assert r.model_hash == "abcdef0123456789"
        assert r.notes == "Test"


# ---------------------------------------------------------------------------
# FULL CYCLE INTEGRATION
# ---------------------------------------------------------------------------

class TestFullCycle:
    def test_two_successive_deploys(self, orchestrator):
        r1 = orchestrator.run_cycle(
            new_model_params={"v": 1},
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        r2 = orchestrator.run_cycle(
            new_model_params={"v": 2},
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_2",
        )
        assert r1.deployed is True
        assert r2.deployed is True
        assert r1.model_hash != r2.model_hash

    def test_deploy_then_no_deploy(self, orchestrator):
        r1 = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        r2 = orchestrator.run_cycle(
            new_model_params=PARAMS_A,
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.04, ece_candidate=0.04),
            chunk_id="chunk_2",
        )
        assert r1.deployed is True
        assert r2.deployed is False

    def test_deploy_rollback_deploy(self, orchestrator):
        r1 = orchestrator.run_cycle(
            new_model_params={"v": 1},
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_1",
        )
        r2 = orchestrator.run_cycle(
            new_model_params={"v": 2},
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_2",
        )
        assert orchestrator.rollback() is True
        assert orchestrator._active_model_hash == r1.model_hash

        r3 = orchestrator.run_cycle(
            new_model_params={"v": 3},
            validation_data=VALIDATION_DATA,
            stress_test_fn=_stress_fn(True),
            calibration_eval_fn=_cal_fn(ece_active=0.06, ece_candidate=0.04),
            chunk_id="chunk_3",
        )
        assert r3.deployed is True
