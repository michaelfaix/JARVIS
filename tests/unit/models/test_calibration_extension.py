# =============================================================================
# tests/unit/models/test_calibration_extension.py
# Tests for S09 Calibration Extension (new classes added to calibration.py)
# =============================================================================

from __future__ import annotations

import math

import pytest

from jarvis.models.calibration import (
    CONFIDENCE_FLOOR,
    CONFIDENCE_CEILING,
    ECE_HARD_GATE,
    ECE_REGIME_DRIFT_GATE,
    ONLINE_WINDOW_SIZE,
    ONLINE_UPDATE_FREQUENCY,
    TEMPERATURE_SCALING_T,
    CalibrationMetrics,
    CalibrationResult,
    CalibrationHardGate,
    CalibrationLayer,
    OnlineCalibrator,
    temperature_scaling,
    platt_scaling,
    evaluate_calibration,
)
from jarvis.utils.exceptions import CalibrationGateViolation
from jarvis.metrics.ece_calculator import ECEResult


# =============================================================================
# HELPERS
# =============================================================================

def _well_calibrated_data():
    """Data where confidence ~= accuracy (already calibrated)."""
    confidences = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
    outcomes    = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    return confidences, outcomes


def _miscalibrated_data():
    """Data where confidence is overconfident."""
    confidences = [0.9, 0.85, 0.8, 0.75, 0.9, 0.95, 0.88, 0.92, 0.87, 0.91]
    outcomes    = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    return confidences, outcomes


def _large_dataset(n=200):
    """Deterministic dataset with known pattern."""
    confidences = []
    outcomes = []
    for i in range(n):
        c = (i + 1) / (n + 1)
        o = 1.0 if (i % 3 != 0) else 0.0
        confidences.append(c)
        outcomes.append(o)
    return confidences, outcomes


def _make_metrics(ece: float, is_calibrated: bool) -> CalibrationMetrics:
    """Create CalibrationMetrics with given ECE for testing gates."""
    confs, outs = _well_calibrated_data()
    result = platt_scaling(confs, outs)
    # We need a real ECEResult, so use the one from the result but override
    # fields via a new CalibrationMetrics
    return CalibrationMetrics(
        ece=ece,
        mce=result.metrics.mce,
        brier=result.metrics.brier,
        nll=result.metrics.nll,
        is_calibrated=is_calibrated,
        n_samples=result.metrics.n_samples,
        ece_result=result.metrics.ece_result,
    )


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestExtensionConstants:
    def test_online_window_size(self):
        assert ONLINE_WINDOW_SIZE == 500

    def test_online_update_frequency(self):
        assert ONLINE_UPDATE_FREQUENCY == 100

    def test_temperature_scaling_t(self):
        assert TEMPERATURE_SCALING_T == 2.5

    def test_constants_are_int_or_float(self):
        assert isinstance(ONLINE_WINDOW_SIZE, int)
        assert isinstance(ONLINE_UPDATE_FREQUENCY, int)
        assert isinstance(TEMPERATURE_SCALING_T, float)


# =============================================================================
# SECTION 2 -- CALIBRATION HARD GATE
# =============================================================================

class TestCalibrationHardGate:
    def test_enforce_passes_low_ece(self):
        gate = CalibrationHardGate()
        metrics = _make_metrics(ece=0.01, is_calibrated=True)
        assert gate.enforce(metrics) is True

    def test_enforce_passes_just_below_gate(self):
        gate = CalibrationHardGate()
        metrics = _make_metrics(ece=0.049, is_calibrated=True)
        assert gate.enforce(metrics) is True

    def test_enforce_raises_at_gate(self):
        gate = CalibrationHardGate()
        metrics = _make_metrics(ece=0.05, is_calibrated=False)
        with pytest.raises(CalibrationGateViolation, match="hard gate"):
            gate.enforce(metrics)

    def test_enforce_raises_above_gate(self):
        gate = CalibrationHardGate()
        metrics = _make_metrics(ece=0.10, is_calibrated=False)
        with pytest.raises(CalibrationGateViolation):
            gate.enforce(metrics)

    def test_enforce_raises_on_wrong_type(self):
        gate = CalibrationHardGate()
        with pytest.raises(TypeError, match="CalibrationMetrics"):
            gate.enforce("not_metrics")

    def test_check_drift_passes(self):
        gate = CalibrationHardGate()
        assert gate.check_drift(0.03, 0.02) is True

    def test_check_drift_passes_at_boundary(self):
        gate = CalibrationHardGate()
        # Exactly at drift gate is not exceeded (> not >=)
        assert gate.check_drift(0.03, 0.01) is True

    def test_check_drift_raises_exceeded(self):
        gate = CalibrationHardGate()
        with pytest.raises(CalibrationGateViolation, match="drift"):
            gate.check_drift(0.04, 0.01)

    def test_check_drift_raises_reverse_direction(self):
        gate = CalibrationHardGate()
        with pytest.raises(CalibrationGateViolation, match="drift"):
            gate.check_drift(0.01, 0.04)

    def test_check_drift_non_finite_raises(self):
        gate = CalibrationHardGate()
        with pytest.raises(CalibrationGateViolation):
            gate.check_drift(float("nan"), 0.01)

    def test_enforce_non_finite_ece_raises(self):
        gate = CalibrationHardGate()
        metrics = _make_metrics(ece=float("inf"), is_calibrated=False)
        with pytest.raises(CalibrationGateViolation, match="non-finite"):
            gate.enforce(metrics)


# =============================================================================
# SECTION 3 -- CALIBRATION LAYER
# =============================================================================

class TestCalibrationLayer:
    def test_dispatch_risk_on_platt(self):
        layer = CalibrationLayer()
        confs, outs = _well_calibrated_data()
        result = layer.calibrate(tuple(confs), tuple(outs), regime="RISK_ON")
        assert result.method == "platt"

    def test_dispatch_risk_off_isotonic(self):
        layer = CalibrationLayer()
        confs, outs = _well_calibrated_data()
        result = layer.calibrate(tuple(confs), tuple(outs), regime="RISK_OFF")
        assert result.method == "isotonic"

    def test_dispatch_transition_beta(self):
        layer = CalibrationLayer()
        confs, outs = _well_calibrated_data()
        result = layer.calibrate(tuple(confs), tuple(outs), regime="TRANSITION")
        assert result.method == "beta"

    def test_dispatch_crisis_temperature(self):
        layer = CalibrationLayer()
        confs, outs = _well_calibrated_data()
        result = layer.calibrate(tuple(confs), tuple(outs), regime="CRISIS")
        assert result.method == "temperature"

    def test_dispatch_unknown_platt(self):
        layer = CalibrationLayer()
        confs, outs = _well_calibrated_data()
        result = layer.calibrate(tuple(confs), tuple(outs), regime="UNKNOWN")
        assert result.method == "platt"

    def test_invalid_regime_raises(self):
        layer = CalibrationLayer()
        confs, outs = _well_calibrated_data()
        with pytest.raises(ValueError, match="Unknown regime"):
            layer.calibrate(tuple(confs), tuple(outs), regime="INVALID")

    def test_get_method_for_regime(self):
        layer = CalibrationLayer()
        assert layer.get_method_for_regime("RISK_ON") == "platt"
        assert layer.get_method_for_regime("RISK_OFF") == "isotonic"
        assert layer.get_method_for_regime("TRANSITION") == "beta"
        assert layer.get_method_for_regime("CRISIS") == "temperature"
        assert layer.get_method_for_regime("UNKNOWN") == "platt"

    def test_get_method_non_string_raises(self):
        layer = CalibrationLayer()
        with pytest.raises(TypeError, match="string"):
            layer.get_method_for_regime(42)

    def test_default_regime_is_risk_on(self):
        layer = CalibrationLayer()
        confs, outs = _well_calibrated_data()
        result = layer.calibrate(tuple(confs), tuple(outs))
        assert result.method == "platt"

    def test_all_regimes_return_calibration_result(self):
        layer = CalibrationLayer()
        confs, outs = _well_calibrated_data()
        for regime in ("RISK_ON", "RISK_OFF", "TRANSITION", "CRISIS", "UNKNOWN"):
            result = layer.calibrate(tuple(confs), tuple(outs), regime=regime)
            assert isinstance(result, CalibrationResult)
            assert len(result.calibrated_confidences) == len(confs)


# =============================================================================
# SECTION 4 -- TEMPERATURE SCALING
# =============================================================================

class TestTemperatureScaling:
    def test_returns_result(self):
        confs, outs = _well_calibrated_data()
        result = temperature_scaling(confs, outs)
        assert isinstance(result, CalibrationResult)
        assert result.method == "temperature"

    def test_output_length(self):
        confs, outs = _well_calibrated_data()
        result = temperature_scaling(confs, outs)
        assert len(result.calibrated_confidences) == len(confs)

    def test_output_in_range(self):
        confs, outs = _well_calibrated_data()
        result = temperature_scaling(confs, outs)
        for c in result.calibrated_confidences:
            assert CONFIDENCE_FLOOR <= c <= CONFIDENCE_CEILING

    def test_t1_approximately_identity(self):
        """T=1.0 should be close to identity (sigmoid(logit(x)) = x)."""
        confs, outs = _well_calibrated_data()
        result = temperature_scaling(confs, outs, T=1.0)
        for original, calibrated in zip(confs, result.calibrated_confidences):
            # Within numerical tolerance
            assert abs(calibrated - max(CONFIDENCE_FLOOR, min(CONFIDENCE_CEILING, original))) < 1e-6

    def test_t_gt_1_moves_toward_half(self):
        """T > 1 should push values closer to 0.5."""
        confs = [0.1, 0.9, 0.2, 0.8]
        outs = [0.0, 1.0, 0.0, 1.0]
        result = temperature_scaling(confs, outs, T=2.5)
        for original, calibrated in zip(confs, result.calibrated_confidences):
            # Calibrated should be closer to 0.5 than original
            assert abs(calibrated - 0.5) <= abs(original - 0.5) + 1e-10

    def test_parameter_T_in_result(self):
        confs, outs = _well_calibrated_data()
        result = temperature_scaling(confs, outs, T=3.0)
        assert "T" in result.parameters
        assert result.parameters["T"] == 3.0

    def test_metrics_finite(self):
        confs, outs = _well_calibrated_data()
        result = temperature_scaling(confs, outs)
        assert math.isfinite(result.metrics.ece)
        assert math.isfinite(result.metrics.brier)
        assert math.isfinite(result.metrics.nll)

    def test_empty_input_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            temperature_scaling([], [])

    def test_single_sample(self):
        result = temperature_scaling([0.8], [1.0])
        assert len(result.calibrated_confidences) == 1
        assert CONFIDENCE_FLOOR <= result.calibrated_confidences[0] <= CONFIDENCE_CEILING

    def test_negative_T_raises(self):
        confs, outs = _well_calibrated_data()
        with pytest.raises(ValueError, match="positive"):
            temperature_scaling(confs, outs, T=-1.0)

    def test_zero_T_raises(self):
        confs, outs = _well_calibrated_data()
        with pytest.raises(ValueError, match="positive"):
            temperature_scaling(confs, outs, T=0.0)

    def test_default_T_is_constant(self):
        confs, outs = _well_calibrated_data()
        r1 = temperature_scaling(confs, outs)
        assert r1.parameters["T"] == TEMPERATURE_SCALING_T


# =============================================================================
# SECTION 5 -- ONLINE CALIBRATOR
# =============================================================================

class TestOnlineCalibrator:
    def test_init_empty(self):
        oc = OnlineCalibrator()
        assert oc.get_current_ece() == 0.0
        assert oc.should_recalibrate() is False

    def test_add_sample(self):
        oc = OnlineCalibrator()
        oc.add_sample(0.8, 1.0)
        oc.add_sample(0.2, 0.0)
        # Still fewer than 2 samples that matter for should_recalibrate
        assert oc.should_recalibrate() is False

    def test_window_trimming_at_max(self):
        oc = OnlineCalibrator()
        for i in range(600):
            c = (i + 1) / 601.0
            o = 1.0 if i % 2 == 0 else 0.0
            oc.add_sample(c, o)
        # Window should be trimmed to ONLINE_WINDOW_SIZE
        assert len(oc._confidences) == ONLINE_WINDOW_SIZE
        assert len(oc._outcomes) == ONLINE_WINDOW_SIZE

    def test_should_recalibrate_at_frequency(self):
        oc = OnlineCalibrator()
        for i in range(ONLINE_UPDATE_FREQUENCY - 1):
            oc.add_sample(0.5, 1.0)
        assert oc.should_recalibrate() is False
        oc.add_sample(0.5, 1.0)
        assert oc.should_recalibrate() is True

    def test_recalibrate_returns_result(self):
        oc = OnlineCalibrator()
        for i in range(20):
            c = (i + 1) / 21.0
            o = 1.0 if i >= 10 else 0.0
            oc.add_sample(c, o)
        result = oc.recalibrate(regime="RISK_ON")
        assert isinstance(result, CalibrationResult)
        assert result.method == "platt"

    def test_recalibrate_resets_counter(self):
        oc = OnlineCalibrator()
        for i in range(ONLINE_UPDATE_FREQUENCY):
            oc.add_sample(0.5, 1.0)
        assert oc.should_recalibrate() is True
        oc.recalibrate()
        assert oc.should_recalibrate() is False

    def test_recalibrate_empty_raises(self):
        oc = OnlineCalibrator()
        with pytest.raises(ValueError, match="no samples"):
            oc.recalibrate()

    def test_get_current_ece_with_data(self):
        oc = OnlineCalibrator()
        for i in range(50):
            c = (i + 1) / 51.0
            o = 1.0 if i >= 25 else 0.0
            oc.add_sample(c, o)
        ece = oc.get_current_ece()
        assert isinstance(ece, float)
        assert math.isfinite(ece)
        assert 0.0 <= ece <= 1.0

    def test_add_sample_nan_guard(self):
        oc = OnlineCalibrator()
        oc.add_sample(float("nan"), float("inf"))
        # Should fall back to defaults (0.5, 0.0)
        assert len(oc._confidences) == 1
        assert oc._confidences[0] == 0.5
        assert oc._outcomes[0] == 0.0

    def test_recalibrate_with_different_regimes(self):
        oc = OnlineCalibrator()
        for i in range(20):
            c = (i + 1) / 21.0
            o = 1.0 if i >= 10 else 0.0
            oc.add_sample(c, o)
        for regime in ("RISK_ON", "RISK_OFF", "TRANSITION", "CRISIS", "UNKNOWN"):
            result = oc.recalibrate(regime=regime)
            assert isinstance(result, CalibrationResult)


# =============================================================================
# SECTION 6 -- DETERMINISM
# =============================================================================

class TestExtensionDeterminism:
    def test_temperature_scaling_deterministic(self):
        confs, outs = _well_calibrated_data()
        r1 = temperature_scaling(confs, outs)
        r2 = temperature_scaling(confs, outs)
        assert r1.calibrated_confidences == r2.calibrated_confidences
        assert r1.parameters == r2.parameters
        assert r1.metrics.ece == r2.metrics.ece

    def test_calibration_layer_deterministic(self):
        layer = CalibrationLayer()
        confs, outs = _well_calibrated_data()
        for regime in ("RISK_ON", "RISK_OFF", "TRANSITION", "CRISIS", "UNKNOWN"):
            r1 = layer.calibrate(tuple(confs), tuple(outs), regime=regime)
            r2 = layer.calibrate(tuple(confs), tuple(outs), regime=regime)
            assert r1.calibrated_confidences == r2.calibrated_confidences

    def test_hard_gate_deterministic(self):
        gate = CalibrationHardGate()
        metrics = _make_metrics(ece=0.01, is_calibrated=True)
        assert gate.enforce(metrics) == gate.enforce(metrics)


# =============================================================================
# SECTION 7 -- IMPORT CONTRACT
# =============================================================================

class TestExtensionImportContract:
    def test_import_new_symbols_from_module(self):
        from jarvis.models.calibration import (
            ONLINE_WINDOW_SIZE,
            ONLINE_UPDATE_FREQUENCY,
            TEMPERATURE_SCALING_T,
            CalibrationHardGate,
            CalibrationLayer,
            OnlineCalibrator,
            temperature_scaling,
        )
        assert callable(temperature_scaling)
        assert ONLINE_WINDOW_SIZE == 500

    def test_import_from_init(self):
        from jarvis.models import (
            ONLINE_WINDOW_SIZE,
            ONLINE_UPDATE_FREQUENCY,
            TEMPERATURE_SCALING_T,
            CalibrationHardGate,
            CalibrationLayer,
            OnlineCalibrator,
            temperature_scaling,
        )
        assert callable(temperature_scaling)

    def test_all_exports_present(self):
        from jarvis.models import calibration
        for name in calibration.__all__:
            assert hasattr(calibration, name), f"Missing export: {name}"
