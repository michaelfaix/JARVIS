# =============================================================================
# tests/unit/models/test_calibration.py
# Tests for jarvis/models/calibration.py
# =============================================================================

from __future__ import annotations

import math

import pytest

from jarvis.metrics.ece_calculator import ECEResult
from jarvis.models.calibration import (
    CONFIDENCE_FLOOR,
    CONFIDENCE_CEILING,
    ECE_HARD_GATE,
    ECE_REGIME_DRIFT_GATE,
    PLATT_MAX_ITER,
    PLATT_LR,
    ISOTONIC_MIN_SAMPLES,
    BETA_MAX_ITER,
    BETA_LR,
    CalibrationMetrics,
    CalibrationResult,
    platt_scaling,
    isotonic_regression,
    beta_calibration,
    evaluate_calibration,
    _clamp,
    _sigmoid,
    _logit,
    _brier_score,
    _nll,
    _VALID_METHODS,
)


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


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_confidence_floor(self):
        assert CONFIDENCE_FLOOR == 1e-6

    def test_confidence_ceiling(self):
        assert CONFIDENCE_CEILING == 1.0 - 1e-6

    def test_ece_hard_gate(self):
        assert ECE_HARD_GATE == 0.05

    def test_ece_regime_drift_gate(self):
        assert ECE_REGIME_DRIFT_GATE == 0.02

    def test_platt_max_iter(self):
        assert PLATT_MAX_ITER == 100

    def test_platt_lr(self):
        assert PLATT_LR == 0.01

    def test_isotonic_min_samples(self):
        assert ISOTONIC_MIN_SAMPLES == 2

    def test_beta_max_iter(self):
        assert BETA_MAX_ITER == 100

    def test_beta_lr(self):
        assert BETA_LR == 0.01

    def test_valid_methods(self):
        assert _VALID_METHODS == ("platt", "isotonic", "beta")


# =============================================================================
# SECTION 2 -- HELPERS
# =============================================================================

class TestClamp:
    def test_within_range(self):
        assert _clamp(0.5) == 0.5

    def test_floor(self):
        assert _clamp(0.0) == CONFIDENCE_FLOOR

    def test_ceiling(self):
        assert _clamp(1.0) == CONFIDENCE_CEILING

    def test_negative(self):
        assert _clamp(-1.0) == CONFIDENCE_FLOOR

    def test_above_one(self):
        assert _clamp(2.0) == CONFIDENCE_CEILING

    def test_at_floor(self):
        assert _clamp(CONFIDENCE_FLOOR) == CONFIDENCE_FLOOR

    def test_at_ceiling(self):
        assert _clamp(CONFIDENCE_CEILING) == CONFIDENCE_CEILING


class TestSigmoid:
    def test_zero(self):
        assert _sigmoid(0.0) == 0.5

    def test_large_positive(self):
        assert abs(_sigmoid(100.0) - 1.0) < 1e-10

    def test_large_negative(self):
        assert abs(_sigmoid(-100.0)) < 1e-10

    def test_symmetry(self):
        x = 2.5
        assert abs(_sigmoid(x) + _sigmoid(-x) - 1.0) < 1e-14

    def test_finite(self):
        for x in [-1000, -10, 0, 10, 1000]:
            assert math.isfinite(_sigmoid(x))


class TestLogit:
    def test_half(self):
        assert abs(_logit(0.5)) < 1e-14

    def test_roundtrip(self):
        for p in [0.1, 0.3, 0.5, 0.7, 0.9]:
            assert abs(_sigmoid(_logit(p)) - p) < 1e-10

    def test_floor_clamp(self):
        result = _logit(0.0)
        assert math.isfinite(result)

    def test_ceiling_clamp(self):
        result = _logit(1.0)
        assert math.isfinite(result)


class TestBrierScore:
    def test_perfect(self):
        assert _brier_score([1.0, 0.0], [1.0, 0.0]) == 0.0

    def test_worst(self):
        assert _brier_score([1.0, 0.0], [0.0, 1.0]) == 1.0

    def test_known_value(self):
        result = _brier_score([0.5, 0.5], [1.0, 0.0])
        assert abs(result - 0.25) < 1e-14


class TestNLL:
    def test_perfect_low_nll(self):
        result = _nll([0.99, 0.01], [1.0, 0.0])
        assert result < 0.05

    def test_wrong_high_nll(self):
        result = _nll([0.01, 0.99], [1.0, 0.0])
        assert result > 2.0

    def test_finite(self):
        result = _nll([0.5, 0.5], [1.0, 0.0])
        assert math.isfinite(result)


# =============================================================================
# SECTION 3 -- DATACLASS INVARIANTS
# =============================================================================

class TestCalibrationMetricsFrozen:
    def test_frozen(self):
        confs, outs = _well_calibrated_data()
        result = evaluate_calibration(confs, outs, method="platt")
        with pytest.raises(AttributeError):
            result.metrics.ece = 0.0

    def test_fields_present(self):
        confs, outs = _well_calibrated_data()
        result = evaluate_calibration(confs, outs, method="platt")
        m = result.metrics
        assert isinstance(m.ece, float)
        assert isinstance(m.mce, float)
        assert isinstance(m.brier, float)
        assert isinstance(m.nll, float)
        assert isinstance(m.is_calibrated, bool)
        assert isinstance(m.n_samples, int)
        assert isinstance(m.ece_result, ECEResult)


class TestCalibrationResultFrozen:
    def test_frozen(self):
        confs, outs = _well_calibrated_data()
        result = evaluate_calibration(confs, outs, method="platt")
        with pytest.raises(AttributeError):
            result.method = "other"

    def test_fields_present(self):
        confs, outs = _well_calibrated_data()
        result = evaluate_calibration(confs, outs, method="platt")
        assert isinstance(result.method, str)
        assert isinstance(result.calibrated_confidences, tuple)
        assert isinstance(result.metrics, CalibrationMetrics)
        assert isinstance(result.parameters, dict)


# =============================================================================
# SECTION 4 -- INPUT VALIDATION
# =============================================================================

class TestInputValidation:
    def test_empty_confidences(self):
        with pytest.raises(ValueError, match="must not be empty"):
            evaluate_calibration([], [], method="platt")

    def test_length_mismatch(self):
        with pytest.raises(ValueError, match="equal length"):
            evaluate_calibration([0.5, 0.6], [1.0], method="platt")

    def test_confidences_not_list(self):
        with pytest.raises(TypeError, match="list or tuple"):
            evaluate_calibration("abc", [1.0], method="platt")

    def test_outcomes_not_list(self):
        with pytest.raises(TypeError, match="list or tuple"):
            evaluate_calibration([0.5], "abc", method="platt")

    def test_confidence_non_numeric(self):
        with pytest.raises(TypeError, match="must be numeric"):
            evaluate_calibration(["a"], [1.0], method="platt")

    def test_outcome_non_numeric(self):
        with pytest.raises(TypeError, match="must be numeric"):
            evaluate_calibration([0.5], ["a"], method="platt")

    def test_confidence_nan(self):
        with pytest.raises(ValueError, match="must be finite"):
            evaluate_calibration([float("nan")], [1.0], method="platt")

    def test_confidence_inf(self):
        with pytest.raises(ValueError, match="must be finite"):
            evaluate_calibration([float("inf")], [1.0], method="platt")

    def test_confidence_negative(self):
        with pytest.raises(ValueError, match="must be in"):
            evaluate_calibration([-0.1], [1.0], method="platt")

    def test_confidence_above_one(self):
        with pytest.raises(ValueError, match="must be in"):
            evaluate_calibration([1.1], [1.0], method="platt")

    def test_outcome_negative(self):
        with pytest.raises(ValueError, match="must be in"):
            evaluate_calibration([0.5], [-0.1], method="platt")

    def test_outcome_above_one(self):
        with pytest.raises(ValueError, match="must be in"):
            evaluate_calibration([0.5], [1.1], method="platt")

    def test_invalid_method(self):
        with pytest.raises(ValueError, match="must be one of"):
            evaluate_calibration([0.5], [1.0], method="unknown")

    def test_method_not_string(self):
        with pytest.raises(TypeError, match="must be a string"):
            evaluate_calibration([0.5], [1.0], method=42)

    def test_validation_applies_to_all_methods(self):
        for method in ("platt", "isotonic", "beta"):
            with pytest.raises(ValueError, match="must not be empty"):
                evaluate_calibration([], [], method=method)


# =============================================================================
# SECTION 5 -- PLATT SCALING
# =============================================================================

class TestPlattScaling:
    def test_returns_result(self):
        confs, outs = _well_calibrated_data()
        result = platt_scaling(confs, outs)
        assert isinstance(result, CalibrationResult)
        assert result.method == "platt"

    def test_output_length(self):
        confs, outs = _well_calibrated_data()
        result = platt_scaling(confs, outs)
        assert len(result.calibrated_confidences) == len(confs)

    def test_output_in_range(self):
        confs, outs = _well_calibrated_data()
        result = platt_scaling(confs, outs)
        for c in result.calibrated_confidences:
            assert CONFIDENCE_FLOOR <= c <= CONFIDENCE_CEILING

    def test_parameters_a_b(self):
        confs, outs = _well_calibrated_data()
        result = platt_scaling(confs, outs)
        assert "a" in result.parameters
        assert "b" in result.parameters
        assert math.isfinite(result.parameters["a"])
        assert math.isfinite(result.parameters["b"])

    def test_metrics_finite(self):
        confs, outs = _well_calibrated_data()
        result = platt_scaling(confs, outs)
        assert math.isfinite(result.metrics.ece)
        assert math.isfinite(result.metrics.mce)
        assert math.isfinite(result.metrics.brier)
        assert math.isfinite(result.metrics.nll)

    def test_ece_nonneg(self):
        confs, outs = _well_calibrated_data()
        result = platt_scaling(confs, outs)
        assert result.metrics.ece >= 0.0

    def test_brier_nonneg(self):
        confs, outs = _well_calibrated_data()
        result = platt_scaling(confs, outs)
        assert result.metrics.brier >= 0.0

    def test_n_samples(self):
        confs, outs = _well_calibrated_data()
        result = platt_scaling(confs, outs)
        assert result.metrics.n_samples == len(confs)

    def test_ece_result_present(self):
        confs, outs = _well_calibrated_data()
        result = platt_scaling(confs, outs)
        assert isinstance(result.metrics.ece_result, ECEResult)
        assert result.metrics.ece == result.metrics.ece_result.ece

    def test_miscalibrated_improves(self):
        confs, outs = _miscalibrated_data()
        from jarvis.metrics.ece_calculator import compute_ece as _ece
        ece_before = _ece(confs, outs).ece
        result = platt_scaling(confs, outs)
        # Platt scaling should reduce ECE on miscalibrated data
        assert result.metrics.ece <= ece_before + 0.01

    def test_single_sample(self):
        result = platt_scaling([0.8], [1.0])
        assert len(result.calibrated_confidences) == 1
        assert CONFIDENCE_FLOOR <= result.calibrated_confidences[0] <= CONFIDENCE_CEILING

    def test_large_dataset(self):
        confs, outs = _large_dataset(200)
        result = platt_scaling(confs, outs)
        assert result.metrics.n_samples == 200
        assert all(math.isfinite(c) for c in result.calibrated_confidences)


# =============================================================================
# SECTION 6 -- ISOTONIC REGRESSION
# =============================================================================

class TestIsotonicRegression:
    def test_returns_result(self):
        confs, outs = _well_calibrated_data()
        result = isotonic_regression(confs, outs)
        assert isinstance(result, CalibrationResult)
        assert result.method == "isotonic"

    def test_output_length(self):
        confs, outs = _well_calibrated_data()
        result = isotonic_regression(confs, outs)
        assert len(result.calibrated_confidences) == len(confs)

    def test_output_in_range(self):
        confs, outs = _well_calibrated_data()
        result = isotonic_regression(confs, outs)
        for c in result.calibrated_confidences:
            assert CONFIDENCE_FLOOR <= c <= CONFIDENCE_CEILING

    def test_parameters_n_blocks(self):
        confs, outs = _well_calibrated_data()
        result = isotonic_regression(confs, outs)
        assert "n_blocks" in result.parameters
        assert "n_levels" in result.parameters
        assert result.parameters["n_blocks"] >= 1.0

    def test_monotonicity_when_sorted(self):
        """Isotonic output, when sorted by input confidence, is non-decreasing."""
        confs, outs = _large_dataset(100)
        result = isotonic_regression(confs, outs)
        # Pair (confidence, calibrated) sorted by confidence
        pairs = sorted(
            zip(confs, result.calibrated_confidences), key=lambda x: x[0]
        )
        cal_sorted = [p[1] for p in pairs]
        for i in range(1, len(cal_sorted)):
            assert cal_sorted[i] >= cal_sorted[i - 1] - 1e-14

    def test_perfect_calibration_preserved(self):
        """Already monotonic outcomes should not degrade much."""
        confs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        outs  = [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        result = isotonic_regression(confs, outs)
        assert result.metrics.brier <= 0.3

    def test_metrics_finite(self):
        confs, outs = _well_calibrated_data()
        result = isotonic_regression(confs, outs)
        assert math.isfinite(result.metrics.ece)
        assert math.isfinite(result.metrics.brier)
        assert math.isfinite(result.metrics.nll)

    def test_single_sample(self):
        result = isotonic_regression([0.7], [1.0])
        assert len(result.calibrated_confidences) == 1

    def test_all_same_confidence(self):
        confs = [0.5] * 10
        outs = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
        result = isotonic_regression(confs, outs)
        assert len(result.calibrated_confidences) == 10
        # All outputs must be in valid range
        for c in result.calibrated_confidences:
            assert CONFIDENCE_FLOOR <= c <= CONFIDENCE_CEILING
        # Average calibrated confidence should be near 0.5 (50% positive rate)
        avg = sum(result.calibrated_confidences) / len(result.calibrated_confidences)
        assert abs(avg - 0.5) < 0.2

    def test_two_samples(self):
        result = isotonic_regression([0.3, 0.8], [0.0, 1.0])
        assert len(result.calibrated_confidences) == 2

    def test_large_dataset(self):
        confs, outs = _large_dataset(200)
        result = isotonic_regression(confs, outs)
        assert result.metrics.n_samples == 200


# =============================================================================
# SECTION 7 -- BETA CALIBRATION
# =============================================================================

class TestBetaCalibration:
    def test_returns_result(self):
        confs, outs = _well_calibrated_data()
        result = beta_calibration(confs, outs)
        assert isinstance(result, CalibrationResult)
        assert result.method == "beta"

    def test_output_length(self):
        confs, outs = _well_calibrated_data()
        result = beta_calibration(confs, outs)
        assert len(result.calibrated_confidences) == len(confs)

    def test_output_in_range(self):
        confs, outs = _well_calibrated_data()
        result = beta_calibration(confs, outs)
        for c in result.calibrated_confidences:
            assert CONFIDENCE_FLOOR <= c <= CONFIDENCE_CEILING

    def test_parameters_a_b_c(self):
        confs, outs = _well_calibrated_data()
        result = beta_calibration(confs, outs)
        assert "a" in result.parameters
        assert "b" in result.parameters
        assert "c" in result.parameters
        assert math.isfinite(result.parameters["a"])
        assert math.isfinite(result.parameters["b"])
        assert math.isfinite(result.parameters["c"])

    def test_metrics_finite(self):
        confs, outs = _well_calibrated_data()
        result = beta_calibration(confs, outs)
        assert math.isfinite(result.metrics.ece)
        assert math.isfinite(result.metrics.mce)
        assert math.isfinite(result.metrics.brier)
        assert math.isfinite(result.metrics.nll)

    def test_single_sample(self):
        result = beta_calibration([0.6], [1.0])
        assert len(result.calibrated_confidences) == 1
        assert CONFIDENCE_FLOOR <= result.calibrated_confidences[0] <= CONFIDENCE_CEILING

    def test_miscalibrated_improves(self):
        confs, outs = _miscalibrated_data()
        from jarvis.metrics.ece_calculator import compute_ece as _ece
        ece_before = _ece(confs, outs).ece
        result = beta_calibration(confs, outs)
        assert result.metrics.ece <= ece_before + 0.01

    def test_large_dataset(self):
        confs, outs = _large_dataset(200)
        result = beta_calibration(confs, outs)
        assert result.metrics.n_samples == 200
        assert all(math.isfinite(c) for c in result.calibrated_confidences)


# =============================================================================
# SECTION 8 -- EVALUATE CALIBRATION (ENTRY POINT)
# =============================================================================

class TestEvaluateCalibration:
    def test_dispatches_platt(self):
        confs, outs = _well_calibrated_data()
        result = evaluate_calibration(confs, outs, method="platt")
        assert result.method == "platt"

    def test_dispatches_isotonic(self):
        confs, outs = _well_calibrated_data()
        result = evaluate_calibration(confs, outs, method="isotonic")
        assert result.method == "isotonic"

    def test_dispatches_beta(self):
        confs, outs = _well_calibrated_data()
        result = evaluate_calibration(confs, outs, method="beta")
        assert result.method == "beta"

    def test_default_is_platt(self):
        confs, outs = _well_calibrated_data()
        result = evaluate_calibration(confs, outs)
        assert result.method == "platt"

    def test_returns_calibration_result(self):
        confs, outs = _well_calibrated_data()
        for method in ("platt", "isotonic", "beta"):
            result = evaluate_calibration(confs, outs, method=method)
            assert isinstance(result, CalibrationResult)

    def test_all_methods_produce_valid_output(self):
        confs, outs = _large_dataset(100)
        for method in ("platt", "isotonic", "beta"):
            result = evaluate_calibration(confs, outs, method=method)
            assert len(result.calibrated_confidences) == len(confs)
            assert all(
                CONFIDENCE_FLOOR <= c <= CONFIDENCE_CEILING
                for c in result.calibrated_confidences
            )
            assert result.metrics.ece >= 0.0
            assert result.metrics.brier >= 0.0
            assert math.isfinite(result.metrics.nll)

    def test_consumes_compute_ece(self):
        """Verify metrics.ece_result is from compute_ece()."""
        confs, outs = _well_calibrated_data()
        result = evaluate_calibration(confs, outs, method="platt")
        ece_r = result.metrics.ece_result
        assert isinstance(ece_r, ECEResult)
        assert ece_r.n_samples == len(confs)
        assert len(ece_r.bin_statistics) > 0

    def test_is_calibrated_flag(self):
        confs, outs = _well_calibrated_data()
        result = evaluate_calibration(confs, outs, method="platt")
        if result.metrics.ece < ECE_HARD_GATE:
            assert result.metrics.is_calibrated is True
        else:
            assert result.metrics.is_calibrated is False


# =============================================================================
# SECTION 9 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_platt_deterministic(self):
        confs, outs = _well_calibrated_data()
        r1 = platt_scaling(confs, outs)
        r2 = platt_scaling(confs, outs)
        assert r1.calibrated_confidences == r2.calibrated_confidences
        assert r1.parameters == r2.parameters
        assert r1.metrics.ece == r2.metrics.ece

    def test_isotonic_deterministic(self):
        confs, outs = _well_calibrated_data()
        r1 = isotonic_regression(confs, outs)
        r2 = isotonic_regression(confs, outs)
        assert r1.calibrated_confidences == r2.calibrated_confidences
        assert r1.metrics.ece == r2.metrics.ece

    def test_beta_deterministic(self):
        confs, outs = _well_calibrated_data()
        r1 = beta_calibration(confs, outs)
        r2 = beta_calibration(confs, outs)
        assert r1.calibrated_confidences == r2.calibrated_confidences
        assert r1.parameters == r2.parameters
        assert r1.metrics.ece == r2.metrics.ece

    def test_evaluate_calibration_deterministic(self):
        confs, outs = _large_dataset(50)
        for method in ("platt", "isotonic", "beta"):
            r1 = evaluate_calibration(confs, outs, method=method)
            r2 = evaluate_calibration(confs, outs, method=method)
            assert r1.calibrated_confidences == r2.calibrated_confidences


# =============================================================================
# SECTION 10 -- EDGE CASES
# =============================================================================

class TestEdgeCases:
    def test_all_positive_outcomes(self):
        confs = [0.5, 0.6, 0.7, 0.8, 0.9]
        outs = [1.0, 1.0, 1.0, 1.0, 1.0]
        for method in ("platt", "isotonic", "beta"):
            result = evaluate_calibration(confs, outs, method=method)
            assert len(result.calibrated_confidences) == 5
            assert all(math.isfinite(c) for c in result.calibrated_confidences)

    def test_all_negative_outcomes(self):
        confs = [0.1, 0.2, 0.3, 0.4, 0.5]
        outs = [0.0, 0.0, 0.0, 0.0, 0.0]
        for method in ("platt", "isotonic", "beta"):
            result = evaluate_calibration(confs, outs, method=method)
            assert len(result.calibrated_confidences) == 5
            assert all(math.isfinite(c) for c in result.calibrated_confidences)

    def test_extreme_confidences(self):
        confs = [0.001, 0.999, 0.5]
        outs = [0.0, 1.0, 1.0]
        for method in ("platt", "isotonic", "beta"):
            result = evaluate_calibration(confs, outs, method=method)
            for c in result.calibrated_confidences:
                assert CONFIDENCE_FLOOR <= c <= CONFIDENCE_CEILING

    def test_all_same_outcome(self):
        confs = [0.3, 0.5, 0.7, 0.9]
        outs = [1.0, 1.0, 1.0, 1.0]
        result = isotonic_regression(confs, outs)
        # All isotonic outputs should be 1.0 (clamped to ceiling)
        for c in result.calibrated_confidences:
            assert c >= CONFIDENCE_CEILING - 1e-10 or c == CONFIDENCE_FLOOR

    def test_two_classes_well_separated(self):
        confs = [0.1, 0.15, 0.2, 0.85, 0.9, 0.95]
        outs = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
        result = platt_scaling(confs, outs)
        # Low-confidence samples should map lower than high-confidence
        low_avg = sum(result.calibrated_confidences[:3]) / 3
        high_avg = sum(result.calibrated_confidences[3:]) / 3
        assert low_avg < high_avg

    def test_integer_outcomes(self):
        confs = [0.3, 0.7, 0.5]
        outs = [0, 1, 1]
        result = evaluate_calibration(confs, outs, method="platt")
        assert len(result.calibrated_confidences) == 3

    def test_integer_confidences(self):
        confs = [0, 1, 0, 1]
        outs = [0.0, 1.0, 0.0, 1.0]
        result = evaluate_calibration(confs, outs, method="platt")
        assert len(result.calibrated_confidences) == 4


# =============================================================================
# SECTION 11 -- METRICS CONSISTENCY
# =============================================================================

class TestMetricsConsistency:
    def test_ece_matches_ece_result(self):
        confs, outs = _large_dataset(100)
        for method in ("platt", "isotonic", "beta"):
            result = evaluate_calibration(confs, outs, method=method)
            assert result.metrics.ece == result.metrics.ece_result.ece

    def test_mce_matches_ece_result(self):
        confs, outs = _large_dataset(100)
        for method in ("platt", "isotonic", "beta"):
            result = evaluate_calibration(confs, outs, method=method)
            assert result.metrics.mce == result.metrics.ece_result.max_bin_error

    def test_is_calibrated_matches_threshold(self):
        confs, outs = _large_dataset(100)
        for method in ("platt", "isotonic", "beta"):
            result = evaluate_calibration(confs, outs, method=method)
            assert result.metrics.is_calibrated == (
                result.metrics.ece < ECE_HARD_GATE
            )

    def test_brier_in_range(self):
        confs, outs = _large_dataset(100)
        for method in ("platt", "isotonic", "beta"):
            result = evaluate_calibration(confs, outs, method=method)
            assert 0.0 <= result.metrics.brier <= 1.0

    def test_ece_in_range(self):
        confs, outs = _large_dataset(100)
        for method in ("platt", "isotonic", "beta"):
            result = evaluate_calibration(confs, outs, method=method)
            assert 0.0 <= result.metrics.ece <= 1.0

    def test_mce_in_range(self):
        confs, outs = _large_dataset(100)
        for method in ("platt", "isotonic", "beta"):
            result = evaluate_calibration(confs, outs, method=method)
            assert 0.0 <= result.metrics.mce <= 1.0

    def test_nll_nonneg(self):
        confs, outs = _large_dataset(100)
        for method in ("platt", "isotonic", "beta"):
            result = evaluate_calibration(confs, outs, method=method)
            assert result.metrics.nll >= 0.0


# =============================================================================
# SECTION 12 -- IMPORT CONTRACT
# =============================================================================

class TestImportContract:
    def test_import_from_module(self):
        from jarvis.models.calibration import (
            CalibrationMetrics,
            CalibrationResult,
            platt_scaling,
            isotonic_regression,
            beta_calibration,
            evaluate_calibration,
        )
        assert callable(platt_scaling)
        assert callable(isotonic_regression)
        assert callable(beta_calibration)
        assert callable(evaluate_calibration)

    def test_import_from_init(self):
        from jarvis.models import (
            CalibrationMetrics,
            CalibrationResult,
            platt_scaling,
            isotonic_regression,
            beta_calibration,
            evaluate_calibration,
        )
        assert callable(evaluate_calibration)

    def test_all_exports(self):
        from jarvis.models import calibration
        for name in calibration.__all__:
            assert hasattr(calibration, name)
