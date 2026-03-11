# =============================================================================
# tests/unit/models/test_auto_recalibrator.py
# Tests for S09.5 AutoRecalibrator (jarvis/models/auto_recalibrator.py)
# =============================================================================

from __future__ import annotations

import math

import pytest

from jarvis.models.auto_recalibrator import (
    RecalibrationTrigger,
    AutoRecalibrator,
)


# =============================================================================
# SECTION 1 -- RECALIBRATION TRIGGER DATACLASS
# =============================================================================

class TestRecalibrationTrigger:
    def test_frozen(self):
        trigger = RecalibrationTrigger(
            triggered=False, reason="NONE",
            current_ece=0.01, threshold=0.05, drift=0.0,
        )
        with pytest.raises(AttributeError):
            trigger.triggered = True

    def test_fields_present(self):
        trigger = RecalibrationTrigger(
            triggered=True, reason="ECE_EXCEEDED",
            current_ece=0.06, threshold=0.05, drift=0.01,
        )
        assert trigger.triggered is True
        assert trigger.reason == "ECE_EXCEEDED"
        assert trigger.current_ece == 0.06
        assert trigger.threshold == 0.05
        assert trigger.drift == 0.01

    def test_valid_reasons(self):
        for reason in ("ECE_EXCEEDED", "DRIFT_EXCEEDED", "SCHEDULED", "NONE"):
            trigger = RecalibrationTrigger(
                triggered=True, reason=reason,
                current_ece=0.01, threshold=0.05, drift=0.0,
            )
            assert trigger.reason == reason

    def test_invalid_reason_raises(self):
        with pytest.raises(ValueError, match="reason"):
            RecalibrationTrigger(
                triggered=True, reason="INVALID",
                current_ece=0.01, threshold=0.05, drift=0.0,
            )

    def test_non_finite_current_ece_raises(self):
        with pytest.raises(ValueError, match="finite"):
            RecalibrationTrigger(
                triggered=True, reason="NONE",
                current_ece=float("nan"), threshold=0.05, drift=0.0,
            )

    def test_non_finite_threshold_raises(self):
        with pytest.raises(ValueError, match="finite"):
            RecalibrationTrigger(
                triggered=True, reason="NONE",
                current_ece=0.01, threshold=float("inf"), drift=0.0,
            )

    def test_non_finite_drift_raises(self):
        with pytest.raises(ValueError, match="finite"):
            RecalibrationTrigger(
                triggered=True, reason="NONE",
                current_ece=0.01, threshold=0.05, drift=float("nan"),
            )


# =============================================================================
# SECTION 2 -- AUTO-RECALIBRATOR THRESHOLDS
# =============================================================================

class TestThresholds:
    def test_ece_threshold(self):
        assert AutoRecalibrator.ECE_THRESHOLD == 0.05

    def test_drift_threshold(self):
        assert AutoRecalibrator.DRIFT_THRESHOLD == 0.02

    def test_min_samples(self):
        assert AutoRecalibrator.MIN_SAMPLES == 100


# =============================================================================
# SECTION 3 -- AUTO-RECALIBRATOR CORE LOGIC
# =============================================================================

class TestAutoRecalibrator:
    def test_init_state(self):
        ar = AutoRecalibrator()
        assert ar._previous_ece == 0.0
        assert ar._sample_count == 0
        assert ar._last_check_count == 0

    def test_check_low_ece_not_triggered(self):
        ar = AutoRecalibrator()
        trigger = ar.check(0.01)
        assert trigger.triggered is False
        assert trigger.reason == "NONE"
        assert trigger.current_ece == 0.01

    def test_check_high_ece_triggered(self):
        ar = AutoRecalibrator()
        trigger = ar.check(0.06)
        assert trigger.triggered is True
        assert trigger.reason == "ECE_EXCEEDED"
        assert trigger.current_ece == 0.06
        assert trigger.threshold == 0.05

    def test_check_exactly_at_threshold_triggered(self):
        ar = AutoRecalibrator()
        trigger = ar.check(0.05)
        assert trigger.triggered is True
        assert trigger.reason == "ECE_EXCEEDED"

    def test_check_drift_exceeded(self):
        ar = AutoRecalibrator()
        # First check sets previous_ece to 0.0
        ar.check(0.0)
        # Now check with drift > 0.02
        trigger = ar.check(0.03)
        assert trigger.triggered is True
        assert trigger.reason == "DRIFT_EXCEEDED"
        assert trigger.drift > AutoRecalibrator.DRIFT_THRESHOLD

    def test_check_drift_within_limits(self):
        ar = AutoRecalibrator()
        ar.check(0.01)
        trigger = ar.check(0.02)
        # drift = 0.01 which is <= 0.02
        assert trigger.triggered is False
        assert trigger.reason == "NONE"

    def test_check_scheduled_trigger(self):
        ar = AutoRecalibrator()
        ar.add_samples(100)
        # First check: triggers scheduled because sample_count (100) >= MIN_SAMPLES
        # and sample_count - last_check_count (100 - 0) >= MIN_SAMPLES
        trigger = ar.check(0.01)
        assert trigger.triggered is True
        assert trigger.reason == "SCHEDULED"

    def test_add_samples(self):
        ar = AutoRecalibrator()
        ar.add_samples(50)
        assert ar._sample_count == 50
        ar.add_samples(25)
        assert ar._sample_count == 75

    def test_add_samples_default_one(self):
        ar = AutoRecalibrator()
        ar.add_samples()
        assert ar._sample_count == 1

    def test_add_samples_negative_raises(self):
        ar = AutoRecalibrator()
        with pytest.raises(ValueError, match="non-negative"):
            ar.add_samples(-1)

    def test_add_samples_non_int_raises(self):
        ar = AutoRecalibrator()
        with pytest.raises(TypeError, match="int"):
            ar.add_samples(1.5)

    def test_should_block_predictions_low_ece(self):
        ar = AutoRecalibrator()
        assert ar.should_block_predictions(0.03) is False

    def test_should_block_predictions_high_ece(self):
        ar = AutoRecalibrator()
        assert ar.should_block_predictions(0.10) is True

    def test_should_block_predictions_above_block(self):
        ar = AutoRecalibrator()
        assert ar.should_block_predictions(0.15) is True

    def test_should_block_predictions_nan(self):
        ar = AutoRecalibrator()
        assert ar.should_block_predictions(float("nan")) is True

    def test_reset(self):
        ar = AutoRecalibrator()
        ar.add_samples(200)
        ar.check(0.06)
        ar.reset()
        assert ar._previous_ece == 0.0
        assert ar._sample_count == 0
        assert ar._last_check_count == 0

    def test_check_updates_previous_ece(self):
        ar = AutoRecalibrator()
        ar.check(0.03)
        assert ar._previous_ece == 0.03
        ar.check(0.04)
        assert ar._previous_ece == 0.04


# =============================================================================
# SECTION 4 -- DETERMINISM
# =============================================================================

class TestAutoRecalibratorDeterminism:
    def test_same_sequence_same_result(self):
        ar1 = AutoRecalibrator()
        ar2 = AutoRecalibrator()

        ar1.add_samples(50)
        ar2.add_samples(50)

        t1 = ar1.check(0.03)
        t2 = ar2.check(0.03)

        assert t1.triggered == t2.triggered
        assert t1.reason == t2.reason
        assert t1.current_ece == t2.current_ece
        assert t1.drift == t2.drift

    def test_check_repeated_is_consistent(self):
        ar = AutoRecalibrator()
        # After first check, previous_ece is set, so second check has
        # different drift. We verify each call is deterministic given state.
        t1 = ar.check(0.01)
        # Now previous_ece = 0.01
        t2 = ar.check(0.01)
        # drift = 0.0, not triggered
        assert t2.triggered is False
        assert t2.reason == "NONE"
        assert t2.drift == 0.0


# =============================================================================
# SECTION 5 -- EDGE CASES
# =============================================================================

class TestEdgeCases:
    def test_zero_ece(self):
        ar = AutoRecalibrator()
        trigger = ar.check(0.0)
        assert trigger.triggered is False
        assert trigger.current_ece == 0.0

    def test_exactly_at_drift_boundary(self):
        ar = AutoRecalibrator()
        ar.check(0.01)
        # drift = |0.03 - 0.01| = 0.02, which is exactly at gate (not >)
        trigger = ar.check(0.03)
        assert trigger.triggered is False
        assert trigger.reason == "NONE"

    def test_negative_ece_clamped(self):
        ar = AutoRecalibrator()
        trigger = ar.check(-0.5)
        assert trigger.current_ece == 0.0
        assert trigger.triggered is False

    def test_nan_ece_treated_as_max(self):
        ar = AutoRecalibrator()
        trigger = ar.check(float("nan"))
        # NaN is replaced with 1.0 -> ECE_EXCEEDED
        assert trigger.triggered is True
        assert trigger.reason == "ECE_EXCEEDED"
        assert trigger.current_ece == 1.0

    def test_inf_ece_treated_as_max(self):
        ar = AutoRecalibrator()
        trigger = ar.check(float("inf"))
        assert trigger.triggered is True
        assert trigger.reason == "ECE_EXCEEDED"
        assert trigger.current_ece == 1.0

    def test_should_block_below_threshold(self):
        ar = AutoRecalibrator()
        assert ar.should_block_predictions(0.099) is False

    def test_should_block_at_threshold(self):
        ar = AutoRecalibrator()
        assert ar.should_block_predictions(0.10) is True


# =============================================================================
# SECTION 6 -- IMPORT CONTRACT
# =============================================================================

class TestImportContract:
    def test_import_from_module(self):
        from jarvis.models.auto_recalibrator import (
            RecalibrationTrigger,
            AutoRecalibrator,
        )
        assert RecalibrationTrigger is not None
        assert AutoRecalibrator is not None

    def test_import_from_init(self):
        from jarvis.models import (
            RecalibrationTrigger,
            AutoRecalibrator,
        )
        assert RecalibrationTrigger is not None
        assert AutoRecalibrator is not None

    def test_all_exports(self):
        from jarvis.models import auto_recalibrator
        for name in auto_recalibrator.__all__:
            assert hasattr(auto_recalibrator, name), f"Missing export: {name}"
