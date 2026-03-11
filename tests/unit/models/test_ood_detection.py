# =============================================================================
# tests/unit/models/test_ood_detection.py — S10 OOD Detection Tests
#
# Comprehensive test suite for jarvis/models/ood_detection.py.
# 40+ tests covering all classes, functions, enums, constants, and edge cases.
# =============================================================================

from __future__ import annotations

import math

import pytest

from jarvis.models.ood_detection import (
    # Constants
    N_SENSORS,
    SENSOR_NAMES,
    SENSOR_WEIGHTS,
    SENSOR_DETECTION_THRESHOLD,
    OOD_CONSENSUS_MINIMUM,
    OOD_RECALL_MINIMUM,
    DEFAULT_OOD_THRESHOLD,
    # Enums
    OODSchwere,
    OODAktion,
    # Dataclasses
    OODResult,
    OODMetrics,
    # Sensor functions
    detect_msp,
    detect_mahalanobis,
    detect_wasserstein,
    detect_ensemble_variance,
    detect_reconstruction,
    # Classification helpers
    classify_severity,
    determine_action,
    # Classes
    OODEnsemble,
    OODDriftTracker,
    FalsePositiveController,
    # Top-level functions
    aggregate_ood,
    evaluate_ood_detector,
    handle_unknown_unknown,
)
from jarvis.models.fast_path import Prediction


# =============================================================================
# TestOODSchwere
# =============================================================================

class TestOODSchwere:
    """Tests for OODSchwere enum."""

    def test_niedrig_value(self) -> None:
        assert OODSchwere.NIEDRIG.value == "NIEDRIG"

    def test_mittel_value(self) -> None:
        assert OODSchwere.MITTEL.value == "MITTEL"

    def test_hoch_value(self) -> None:
        assert OODSchwere.HOCH.value == "HOCH"

    def test_kritisch_value(self) -> None:
        assert OODSchwere.KRITISCH.value == "KRITISCH"

    def test_enum_count(self) -> None:
        assert len(OODSchwere) == 4


# =============================================================================
# TestOODAktion
# =============================================================================

class TestOODAktion:
    """Tests for OODAktion enum."""

    def test_keine_value(self) -> None:
        assert OODAktion.KEINE.value == "KEINE"

    def test_unsicherheit_erhoehen_value(self) -> None:
        assert OODAktion.UNSICHERHEIT_ERHOEHEN.value == "UNSICHERHEIT_ERHOEHEN"

    def test_max_unsicherheit_value(self) -> None:
        assert OODAktion.MAX_UNSICHERHEIT.value == "MAX_UNSICHERHEIT"

    def test_vorhersagen_deaktivieren_value(self) -> None:
        assert OODAktion.VORHERSAGEN_DEAKTIVIEREN.value == "VORHERSAGEN_DEAKTIVIEREN"

    def test_enum_count(self) -> None:
        assert len(OODAktion) == 4


# =============================================================================
# TestOODResult
# =============================================================================

class TestOODResult:
    """Tests for OODResult dataclass."""

    def test_frozen(self) -> None:
        result = OODResult(
            score=0.5, severity=OODSchwere.MITTEL, action=OODAktion.KEINE,
            sensor_scores={}, consensus_count=0, is_ood=False,
        )
        with pytest.raises(AttributeError):
            result.score = 0.9  # type: ignore

    def test_all_fields(self) -> None:
        scores = {"MSP": 0.1, "MAHALANOBIS": 0.2}
        result = OODResult(
            score=0.3, severity=OODSchwere.MITTEL,
            action=OODAktion.UNSICHERHEIT_ERHOEHEN,
            sensor_scores=scores, consensus_count=2, is_ood=False,
        )
        assert result.score == 0.3
        assert result.severity == OODSchwere.MITTEL
        assert result.action == OODAktion.UNSICHERHEIT_ERHOEHEN
        assert result.sensor_scores == scores
        assert result.consensus_count == 2
        assert result.is_ood is False

    def test_is_ood_true(self) -> None:
        result = OODResult(
            score=0.8, severity=OODSchwere.KRITISCH,
            action=OODAktion.VORHERSAGEN_DEAKTIVIEREN,
            sensor_scores={}, consensus_count=4, is_ood=True,
        )
        assert result.is_ood is True

    def test_nan_score_raises(self) -> None:
        with pytest.raises(ValueError, match="finite"):
            OODResult(
                score=float("nan"), severity=OODSchwere.NIEDRIG,
                action=OODAktion.KEINE, sensor_scores={},
                consensus_count=0, is_ood=False,
            )

    def test_inf_score_raises(self) -> None:
        with pytest.raises(ValueError, match="finite"):
            OODResult(
                score=float("inf"), severity=OODSchwere.NIEDRIG,
                action=OODAktion.KEINE, sensor_scores={},
                consensus_count=0, is_ood=False,
            )


# =============================================================================
# TestOODMetrics
# =============================================================================

class TestOODMetrics:
    """Tests for OODMetrics dataclass."""

    def test_frozen(self) -> None:
        m = OODMetrics(true_positives=1, false_positives=0,
                       true_negatives=1, false_negatives=0)
        with pytest.raises(AttributeError):
            m.true_positives = 5  # type: ignore

    def test_precision_perfect(self) -> None:
        m = OODMetrics(true_positives=10, false_positives=0,
                       true_negatives=5, false_negatives=0)
        assert m.precision == 1.0

    def test_recall_perfect(self) -> None:
        m = OODMetrics(true_positives=10, false_positives=0,
                       true_negatives=5, false_negatives=0)
        assert m.recall == 1.0

    def test_f1_perfect(self) -> None:
        m = OODMetrics(true_positives=10, false_positives=0,
                       true_negatives=5, false_negatives=0)
        assert abs(m.f1_score - 1.0) < 1e-9

    def test_precision_division_by_zero(self) -> None:
        m = OODMetrics(true_positives=0, false_positives=0,
                       true_negatives=5, false_negatives=3)
        assert m.precision == 0.0

    def test_recall_division_by_zero(self) -> None:
        m = OODMetrics(true_positives=0, false_positives=2,
                       true_negatives=5, false_negatives=0)
        assert m.recall == 0.0

    def test_f1_both_zero(self) -> None:
        m = OODMetrics(true_positives=0, false_positives=0,
                       true_negatives=5, false_negatives=0)
        assert m.f1_score == 0.0

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            OODMetrics(true_positives=-1, false_positives=0,
                       true_negatives=0, false_negatives=0)

    def test_non_int_raises(self) -> None:
        with pytest.raises(TypeError, match="int"):
            OODMetrics(true_positives=1.5, false_positives=0,  # type: ignore
                       true_negatives=0, false_negatives=0)


# =============================================================================
# TestConstants
# =============================================================================

class TestConstants:
    """Tests for module-level constants."""

    def test_n_sensors(self) -> None:
        assert N_SENSORS == 5

    def test_sensor_names_count(self) -> None:
        assert len(SENSOR_NAMES) == 5

    def test_sensor_names_values(self) -> None:
        expected = ("MSP", "MAHALANOBIS", "WASSERSTEIN",
                    "ENSEMBLE_VARIANCE", "RECONSTRUCTION")
        assert SENSOR_NAMES == expected

    def test_sensor_weights_count(self) -> None:
        assert len(SENSOR_WEIGHTS) == 5

    def test_sensor_weights_sum_to_one(self) -> None:
        assert abs(sum(SENSOR_WEIGHTS) - 1.0) < 1e-9

    def test_consensus_minimum(self) -> None:
        assert OOD_CONSENSUS_MINIMUM == 3

    def test_recall_minimum(self) -> None:
        assert OOD_RECALL_MINIMUM == 0.90

    def test_default_threshold(self) -> None:
        assert DEFAULT_OOD_THRESHOLD == 0.5

    def test_detection_threshold(self) -> None:
        assert SENSOR_DETECTION_THRESHOLD == 0.5


# =============================================================================
# TestDetectMSP
# =============================================================================

class TestDetectMSP:
    """Tests for detect_msp sensor."""

    def test_confidence_one_score_zero(self) -> None:
        assert detect_msp(1.0) == 0.0

    def test_confidence_zero_score_one(self) -> None:
        assert detect_msp(0.0) == 1.0

    def test_midpoint(self) -> None:
        assert abs(detect_msp(0.5) - 0.5) < 1e-9

    def test_nan_returns_one(self) -> None:
        assert detect_msp(float("nan")) == 1.0

    def test_inf_returns_one(self) -> None:
        assert detect_msp(float("inf")) == 1.0

    def test_non_numeric_returns_half(self) -> None:
        assert detect_msp("not_a_number") == 0.5  # type: ignore


# =============================================================================
# TestDetectMahalanobis
# =============================================================================

class TestDetectMahalanobis:
    """Tests for detect_mahalanobis sensor."""

    def test_identical_features_score_zero(self) -> None:
        features = {"a": 1.0, "b": 2.0}
        train_mean = {"a": 1.0, "b": 2.0}
        # Identity matrix as inverse covariance
        cov_inv = [[1.0, 0.0], [0.0, 1.0]]
        score = detect_mahalanobis(features, train_mean, cov_inv)
        assert score == 0.0

    def test_different_features_positive(self) -> None:
        features = {"a": 5.0, "b": 5.0}
        train_mean = {"a": 0.0, "b": 0.0}
        cov_inv = [[1.0, 0.0], [0.0, 1.0]]
        score = detect_mahalanobis(features, train_mean, cov_inv)
        assert score > 0.0

    def test_empty_features_zero(self) -> None:
        score = detect_mahalanobis({}, {}, [])
        assert score == 0.0

    def test_no_common_keys_zero(self) -> None:
        score = detect_mahalanobis({"a": 1.0}, {"b": 1.0}, [[1.0]])
        assert score == 0.0

    def test_nan_in_features(self) -> None:
        features = {"a": float("nan")}
        train_mean = {"a": 0.0}
        cov_inv = [[1.0]]
        score = detect_mahalanobis(features, train_mean, cov_inv)
        assert score == 0.0

    def test_score_capped_at_one(self) -> None:
        # Very large distance should be capped
        features = {"a": 1000.0}
        train_mean = {"a": 0.0}
        cov_inv = [[1.0]]
        score = detect_mahalanobis(features, train_mean, cov_inv)
        assert score <= 1.0


# =============================================================================
# TestDetectWasserstein
# =============================================================================

class TestDetectWasserstein:
    """Tests for detect_wasserstein sensor."""

    def test_identical_windows_zero(self) -> None:
        window = [1.0, 2.0, 3.0, 4.0, 5.0]
        score = detect_wasserstein(window, window)
        assert score == 0.0

    def test_different_windows_positive(self) -> None:
        w1 = [0.0, 0.0, 0.0]
        w2 = [1.0, 1.0, 1.0]
        score = detect_wasserstein(w1, w2)
        assert score > 0.0

    def test_empty_windows_zero(self) -> None:
        assert detect_wasserstein([], [1.0, 2.0]) == 0.0
        assert detect_wasserstein([1.0, 2.0], []) == 0.0

    def test_nan_in_window_filtered(self) -> None:
        w1 = [1.0, float("nan"), 2.0]
        w2 = [1.0, 2.0]
        # Should filter NaN and still compute
        score = detect_wasserstein(w1, w2)
        assert math.isfinite(score)

    def test_score_capped_at_one(self) -> None:
        w1 = [0.0, 0.0, 0.0]
        w2 = [100.0, 100.0, 100.0]
        score = detect_wasserstein(w1, w2, threshold=1.0)
        assert score <= 1.0


# =============================================================================
# TestDetectEnsembleVariance
# =============================================================================

class TestDetectEnsembleVariance:
    """Tests for detect_ensemble_variance sensor."""

    def test_identical_predictions_zero(self) -> None:
        preds = (
            Prediction(mu=0.5, sigma=0.1, confidence=0.8),
            Prediction(mu=0.5, sigma=0.1, confidence=0.8),
            Prediction(mu=0.5, sigma=0.1, confidence=0.8),
        )
        score = detect_ensemble_variance(preds)
        assert score == 0.0

    def test_varied_predictions_positive(self) -> None:
        preds = (
            Prediction(mu=-0.5, sigma=0.1, confidence=0.8),
            Prediction(mu=0.0, sigma=0.1, confidence=0.8),
            Prediction(mu=0.5, sigma=0.1, confidence=0.8),
        )
        score = detect_ensemble_variance(preds)
        assert score > 0.0

    def test_empty_predictions_zero(self) -> None:
        assert detect_ensemble_variance(()) == 0.0

    def test_single_prediction_zero(self) -> None:
        preds = (Prediction(mu=0.5, sigma=0.1, confidence=0.8),)
        score = detect_ensemble_variance(preds)
        assert score == 0.0


# =============================================================================
# TestDetectReconstruction
# =============================================================================

class TestDetectReconstruction:
    """Tests for detect_reconstruction sensor."""

    def test_identical_features_zero(self) -> None:
        f = {"a": 1.0, "b": 2.0}
        score = detect_reconstruction(f, f)
        assert score == 0.0

    def test_different_features_positive(self) -> None:
        f1 = {"a": 0.0, "b": 0.0}
        f2 = {"a": 1.0, "b": 1.0}
        score = detect_reconstruction(f1, f2)
        assert score > 0.0

    def test_no_common_keys_zero(self) -> None:
        score = detect_reconstruction({"a": 1.0}, {"b": 2.0})
        assert score == 0.0

    def test_nan_values_filtered(self) -> None:
        f1 = {"a": float("nan"), "b": 1.0}
        f2 = {"a": 0.0, "b": 1.0}
        score = detect_reconstruction(f1, f2)
        # Only "b" used, which is identical
        assert score == 0.0


# =============================================================================
# TestClassifySeverity
# =============================================================================

class TestClassifySeverity:
    """Tests for classify_severity function."""

    def test_niedrig_below_03(self) -> None:
        assert classify_severity(0.0) == OODSchwere.NIEDRIG
        assert classify_severity(0.29) == OODSchwere.NIEDRIG

    def test_mittel_03_to_06(self) -> None:
        assert classify_severity(0.3) == OODSchwere.MITTEL
        assert classify_severity(0.59) == OODSchwere.MITTEL

    def test_hoch_06_to_08(self) -> None:
        assert classify_severity(0.6) == OODSchwere.HOCH
        assert classify_severity(0.79) == OODSchwere.HOCH

    def test_kritisch_above_08(self) -> None:
        assert classify_severity(0.8) == OODSchwere.KRITISCH
        assert classify_severity(1.0) == OODSchwere.KRITISCH

    def test_boundary_030(self) -> None:
        assert classify_severity(0.3) == OODSchwere.MITTEL

    def test_boundary_060(self) -> None:
        assert classify_severity(0.6) == OODSchwere.HOCH

    def test_boundary_080(self) -> None:
        assert classify_severity(0.8) == OODSchwere.KRITISCH

    def test_nan_returns_kritisch(self) -> None:
        assert classify_severity(float("nan")) == OODSchwere.KRITISCH


# =============================================================================
# TestDetermineAction
# =============================================================================

class TestDetermineAction:
    """Tests for determine_action function."""

    def test_not_ood_returns_keine(self) -> None:
        for sev in OODSchwere:
            assert determine_action(sev, is_ood=False) == OODAktion.KEINE

    def test_ood_niedrig_returns_keine(self) -> None:
        assert determine_action(OODSchwere.NIEDRIG, is_ood=True) == OODAktion.KEINE

    def test_ood_mittel_returns_erhoehen(self) -> None:
        assert determine_action(OODSchwere.MITTEL, is_ood=True) == OODAktion.UNSICHERHEIT_ERHOEHEN

    def test_ood_hoch_returns_max(self) -> None:
        assert determine_action(OODSchwere.HOCH, is_ood=True) == OODAktion.MAX_UNSICHERHEIT

    def test_ood_kritisch_returns_deaktivieren(self) -> None:
        assert determine_action(OODSchwere.KRITISCH, is_ood=True) == OODAktion.VORHERSAGEN_DEAKTIVIEREN


# =============================================================================
# TestOODEnsemble
# =============================================================================

class TestOODEnsemble:
    """Tests for OODEnsemble class."""

    def _make_preds(self, mu: float = 0.0) -> tuple:
        return (
            Prediction(mu=mu, sigma=0.1, confidence=0.8),
            Prediction(mu=mu, sigma=0.1, confidence=0.8),
            Prediction(mu=mu, sigma=0.1, confidence=0.8),
        )

    def test_all_sensors_low_not_ood(self) -> None:
        ensemble = OODEnsemble()
        result = ensemble.detect(
            confidence=0.95,
            features={"a": 1.0},
            predictions=self._make_preds(),
            current_window=[1.0, 2.0, 3.0],
            reference_window=[1.0, 2.0, 3.0],
            train_mean={"a": 1.0},
            train_cov_inv=[[1.0]],
            reference_features={"a": 1.0},
        )
        assert result.is_ood is False
        assert result.consensus_count < OOD_CONSENSUS_MINIMUM

    def test_all_sensors_high_is_ood(self) -> None:
        ensemble = OODEnsemble()
        result = ensemble.detect(
            confidence=0.0,  # MSP = 1.0
            features={"a": 100.0},  # high distance
            predictions=(
                Prediction(mu=-1.0, sigma=0.1, confidence=0.8),
                Prediction(mu=0.0, sigma=0.1, confidence=0.8),
                Prediction(mu=1.0, sigma=0.1, confidence=0.8),
            ),
            current_window=[100.0, 200.0, 300.0],
            reference_window=[0.0, 0.0, 0.0],
            train_mean={"a": 0.0},
            train_cov_inv=[[1.0]],
            reference_features={"a": 0.0},
        )
        assert result.is_ood is True
        assert result.consensus_count >= OOD_CONSENSUS_MINIMUM

    def test_mixed_consensus_check(self) -> None:
        ensemble = OODEnsemble()
        # MSP high, others low
        result = ensemble.detect(
            confidence=0.0,  # MSP = 1.0
            features={"a": 1.0},
            predictions=self._make_preds(),
            current_window=[1.0, 2.0],
            reference_window=[1.0, 2.0],
            train_mean={"a": 1.0},
            train_cov_inv=[[1.0]],
            reference_features={"a": 1.0},
        )
        # Only MSP should be high, others low -> not enough consensus
        assert isinstance(result, OODResult)
        assert len(result.sensor_scores) == N_SENSORS

    def test_result_score_in_range(self) -> None:
        ensemble = OODEnsemble()
        result = ensemble.detect(
            confidence=0.5, features={"a": 2.0},
            predictions=self._make_preds(),
            current_window=[1.0], reference_window=[2.0],
            train_mean={"a": 0.0}, train_cov_inv=[[1.0]],
            reference_features={"a": 0.0},
        )
        assert 0.0 <= result.score <= 1.0


# =============================================================================
# TestAggregateOOD
# =============================================================================

class TestAggregateOOD:
    """Tests for aggregate_ood function."""

    def test_weighted_scoring_correct(self) -> None:
        scores = dict(zip(SENSOR_NAMES, [0.0, 0.0, 0.0, 0.0, 0.0]))
        result = aggregate_ood(scores)
        assert result.score == 0.0
        assert result.is_ood is False

    def test_all_ones(self) -> None:
        scores = dict(zip(SENSOR_NAMES, [1.0, 1.0, 1.0, 1.0, 1.0]))
        result = aggregate_ood(scores)
        assert abs(result.score - 1.0) < 1e-9
        assert result.consensus_count == 5
        assert result.is_ood is True

    def test_consensus_counting(self) -> None:
        # 3 sensors above threshold, 2 below
        scores = dict(zip(SENSOR_NAMES, [0.8, 0.8, 0.8, 0.1, 0.1]))
        result = aggregate_ood(scores)
        assert result.consensus_count == 3
        assert result.is_ood is True

    def test_missing_sensor_defaults_zero(self) -> None:
        scores = {"MSP": 0.5}
        result = aggregate_ood(scores)
        assert math.isfinite(result.score)

    def test_type_error_on_non_dict(self) -> None:
        with pytest.raises(TypeError):
            aggregate_ood("not a dict")  # type: ignore


# =============================================================================
# TestHandleUnknownUnknown
# =============================================================================

class TestHandleUnknownUnknown:
    """Tests for handle_unknown_unknown function."""

    def test_all_5_consensus_deactivates(self) -> None:
        result = OODResult(
            score=0.4, severity=OODSchwere.MITTEL,
            action=OODAktion.UNSICHERHEIT_ERHOEHEN,
            sensor_scores={}, consensus_count=5, is_ood=True,
        )
        assert handle_unknown_unknown(result) == OODAktion.VORHERSAGEN_DEAKTIVIEREN

    def test_partial_consensus_returns_normal(self) -> None:
        result = OODResult(
            score=0.7, severity=OODSchwere.HOCH,
            action=OODAktion.MAX_UNSICHERHEIT,
            sensor_scores={}, consensus_count=3, is_ood=True,
        )
        assert handle_unknown_unknown(result) == OODAktion.MAX_UNSICHERHEIT

    def test_not_ood_returns_action(self) -> None:
        result = OODResult(
            score=0.1, severity=OODSchwere.NIEDRIG,
            action=OODAktion.KEINE,
            sensor_scores={}, consensus_count=1, is_ood=False,
        )
        assert handle_unknown_unknown(result) == OODAktion.KEINE

    def test_type_error_on_wrong_input(self) -> None:
        with pytest.raises(TypeError):
            handle_unknown_unknown("not_result")  # type: ignore


# =============================================================================
# TestOODDriftTracker
# =============================================================================

class TestOODDriftTracker:
    """Tests for OODDriftTracker class."""

    def test_empty_mean_zero(self) -> None:
        tracker = OODDriftTracker()
        assert tracker.get_mean_score() == 0.0

    def test_add_scores_and_mean(self) -> None:
        tracker = OODDriftTracker()
        tracker.add_score(0.4)
        tracker.add_score(0.6)
        assert abs(tracker.get_mean_score() - 0.5) < 1e-9

    def test_window_trimming(self) -> None:
        tracker = OODDriftTracker()
        for _ in range(150):
            tracker.add_score(0.5)
        assert len(tracker._scores) == OODDriftTracker.WINDOW_SIZE

    def test_drift_detection_positive(self) -> None:
        tracker = OODDriftTracker()
        # First half: low scores
        for _ in range(20):
            tracker.add_score(0.1)
        # Second half: high scores
        for _ in range(20):
            tracker.add_score(0.5)
        assert tracker.is_drifting() is True

    def test_drift_detection_negative(self) -> None:
        tracker = OODDriftTracker()
        for _ in range(20):
            tracker.add_score(0.3)
        assert tracker.is_drifting() is False

    def test_too_few_scores_no_drift(self) -> None:
        tracker = OODDriftTracker()
        tracker.add_score(0.1)
        tracker.add_score(0.9)
        assert tracker.is_drifting() is False

    def test_nan_replaced_with_half(self) -> None:
        tracker = OODDriftTracker()
        tracker.add_score(float("nan"))
        assert abs(tracker.get_mean_score() - 0.5) < 1e-9


# =============================================================================
# TestFalsePositiveController
# =============================================================================

class TestFalsePositiveController:
    """Tests for FalsePositiveController class."""

    def test_empty_fp_rate_zero(self) -> None:
        ctrl = FalsePositiveController()
        assert ctrl.get_fp_rate() == 0.0

    def test_record_and_fp_rate(self) -> None:
        ctrl = FalsePositiveController()
        # 1 FP out of 10 negatives
        ctrl.record(predicted_ood=True, actual_ood=False)  # FP
        for _ in range(9):
            ctrl.record(predicted_ood=False, actual_ood=False)  # TN
        assert abs(ctrl.get_fp_rate() - 0.1) < 1e-9

    def test_should_raise_threshold_true(self) -> None:
        ctrl = FalsePositiveController()
        # 10 FP out of 100 negatives = 10% > 5%
        for _ in range(10):
            ctrl.record(predicted_ood=True, actual_ood=False)
        for _ in range(90):
            ctrl.record(predicted_ood=False, actual_ood=False)
        assert ctrl.should_raise_threshold() is True

    def test_should_raise_threshold_false(self) -> None:
        ctrl = FalsePositiveController()
        # 1 FP out of 100 negatives = 1% < 5%
        ctrl.record(predicted_ood=True, actual_ood=False)
        for _ in range(99):
            ctrl.record(predicted_ood=False, actual_ood=False)
        assert ctrl.should_raise_threshold() is False

    def test_no_negatives_fp_rate_zero(self) -> None:
        ctrl = FalsePositiveController()
        ctrl.record(predicted_ood=True, actual_ood=True)  # TP
        assert ctrl.get_fp_rate() == 0.0


# =============================================================================
# TestEvaluateOODDetector
# =============================================================================

class TestEvaluateOODDetector:
    """Tests for evaluate_ood_detector function."""

    def _make_result(self, is_ood: bool) -> OODResult:
        return OODResult(
            score=0.5 if is_ood else 0.1,
            severity=OODSchwere.MITTEL if is_ood else OODSchwere.NIEDRIG,
            action=OODAktion.UNSICHERHEIT_ERHOEHEN if is_ood else OODAktion.KEINE,
            sensor_scores={}, consensus_count=3 if is_ood else 1,
            is_ood=is_ood,
        )

    def test_perfect_detection(self) -> None:
        results = [self._make_result(True), self._make_result(True),
                   self._make_result(False), self._make_result(False)]
        labels = [True, True, False, False]
        metrics = evaluate_ood_detector(results, labels)
        assert metrics.true_positives == 2
        assert metrics.true_negatives == 2
        assert metrics.false_positives == 0
        assert metrics.false_negatives == 0
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0

    def test_mixed_detection(self) -> None:
        results = [self._make_result(True), self._make_result(False),
                   self._make_result(True), self._make_result(False)]
        labels = [True, True, False, False]
        metrics = evaluate_ood_detector(results, labels)
        assert metrics.true_positives == 1
        assert metrics.false_negatives == 1
        assert metrics.false_positives == 1
        assert metrics.true_negatives == 1

    def test_all_wrong(self) -> None:
        results = [self._make_result(False), self._make_result(True)]
        labels = [True, False]
        metrics = evaluate_ood_detector(results, labels)
        assert metrics.true_positives == 0
        assert metrics.false_negatives == 1
        assert metrics.false_positives == 1
        assert metrics.true_negatives == 0

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="equal length"):
            evaluate_ood_detector([self._make_result(True)], [True, False])


# =============================================================================
# TestDeterminism
# =============================================================================

class TestDeterminism:
    """Tests for determinism guarantee (DET-07)."""

    def test_same_inputs_identical_msp(self) -> None:
        assert detect_msp(0.73) == detect_msp(0.73)

    def test_same_inputs_identical_ensemble(self) -> None:
        preds = (
            Prediction(mu=0.3, sigma=0.1, confidence=0.8),
            Prediction(mu=-0.1, sigma=0.2, confidence=0.6),
        )
        e1 = OODEnsemble()
        e2 = OODEnsemble()
        kwargs = dict(
            confidence=0.7, features={"a": 1.0, "b": 2.0},
            predictions=preds,
            current_window=[1.0, 2.0, 3.0],
            reference_window=[1.5, 2.5, 3.5],
            train_mean={"a": 0.0, "b": 0.0},
            train_cov_inv=[[1.0, 0.0], [0.0, 1.0]],
            reference_features={"a": 0.5, "b": 1.0},
        )
        r1 = e1.detect(**kwargs)
        r2 = e2.detect(**kwargs)
        assert r1.score == r2.score
        assert r1.consensus_count == r2.consensus_count
        assert r1.is_ood == r2.is_ood
        assert r1.sensor_scores == r2.sensor_scores


# =============================================================================
# TestImportContract
# =============================================================================

class TestImportContract:
    """Tests that all __all__ symbols are importable."""

    def test_all_symbols_importable(self) -> None:
        import jarvis.models.ood_detection as mod
        for name in mod.__all__:
            assert hasattr(mod, name), f"Missing export: {name}"

    def test_all_list_not_empty(self) -> None:
        import jarvis.models.ood_detection as mod
        assert len(mod.__all__) > 0


# =============================================================================
# TestNumericalSafety
# =============================================================================

class TestNumericalSafety:
    """Tests for NaN/Inf handling across all functions."""

    def test_msp_nan(self) -> None:
        score = detect_msp(float("nan"))
        assert math.isfinite(score)

    def test_mahalanobis_nan_in_cov(self) -> None:
        score = detect_mahalanobis(
            {"a": 1.0}, {"a": 0.0}, [[float("nan")]]
        )
        assert math.isfinite(score)

    def test_wasserstein_all_nan(self) -> None:
        score = detect_wasserstein(
            [float("nan"), float("nan")],
            [float("nan"), float("nan")],
        )
        assert math.isfinite(score)
        assert score == 0.0

    def test_reconstruction_inf(self) -> None:
        score = detect_reconstruction(
            {"a": float("inf")}, {"a": 0.0}
        )
        assert math.isfinite(score)

    def test_aggregate_ood_nan_values(self) -> None:
        scores = dict(zip(SENSOR_NAMES, [float("nan")] * 5))
        result = aggregate_ood(scores)
        assert math.isfinite(result.score)

    def test_ensemble_variance_inf(self) -> None:
        # Even with extreme values, output should be finite
        preds = (
            Prediction(mu=1.0, sigma=0.1, confidence=0.8),
            Prediction(mu=-1.0, sigma=0.1, confidence=0.8),
        )
        score = detect_ensemble_variance(preds, threshold=1e-15)
        assert math.isfinite(score)
        assert 0.0 <= score <= 1.0
