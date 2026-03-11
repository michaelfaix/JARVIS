# =============================================================================
# jarvis/models/ood_detection.py — S10 OOD Detection
#
# Authority: FAS v6.0.1, S10 (Lines 3250-3620)
#
# 5-sensor OOD detection ensemble with consensus voting:
#   1. MSP (Maximum Softmax Probability)
#   2. Mahalanobis distance
#   3. Wasserstein distance
#   4. Ensemble variance
#   5. Reconstruction error
#
# Entry points:
#   OODEnsemble.detect()         -> OODResult
#   aggregate_ood()              -> OODResult
#   evaluate_ood_detector()      -> OODMetrics
#   handle_unknown_unknown()     -> OODAktion
#
# CLASSIFICATION: Tier 6 — ANALYSIS AND STRATEGY RESEARCH TOOL.
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  Deterministic arithmetic only.
# DET-05  All branching is deterministic.
# DET-06  Fixed literals are not parametrised.
# DET-07  Same inputs = bit-identical outputs.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No numpy / scipy / sklearn / torch
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
#
# DEPENDENCIES
# ------------
#   stdlib:   dataclasses, enum, math
#   internal: jarvis.utils.helpers (wasserstein_distance)
#             jarvis.utils.numeric_safety (safe_divide)
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple

from jarvis.utils.helpers import wasserstein_distance
from jarvis.utils.numeric_safety import safe_divide

__all__ = [
    # Constants
    "N_SENSORS",
    "SENSOR_NAMES",
    "SENSOR_WEIGHTS",
    "SENSOR_DETECTION_THRESHOLD",
    "OOD_CONSENSUS_MINIMUM",
    "OOD_RECALL_MINIMUM",
    "DEFAULT_OOD_THRESHOLD",
    # Enums
    "OODSchwere",
    "OODAktion",
    # Dataclasses
    "OODResult",
    "OODMetrics",
    # Sensor functions
    "detect_msp",
    "detect_mahalanobis",
    "detect_wasserstein",
    "detect_ensemble_variance",
    "detect_reconstruction",
    # Classification helpers
    "classify_severity",
    "determine_action",
    # Classes
    "OODEnsemble",
    "OODDriftTracker",
    "FalsePositiveController",
    # Top-level functions
    "aggregate_ood",
    "evaluate_ood_detector",
    "handle_unknown_unknown",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals, not parametrisable)
# =============================================================================

N_SENSORS: int = 5
"""Number of OOD sensors in the ensemble."""

SENSOR_NAMES: Tuple[str, ...] = (
    "MSP",
    "MAHALANOBIS",
    "WASSERSTEIN",
    "ENSEMBLE_VARIANCE",
    "RECONSTRUCTION",
)
"""Names of the 5 OOD sensors."""

SENSOR_WEIGHTS: Tuple[float, ...] = (0.25, 0.20, 0.20, 0.20, 0.15)
"""Weights for each sensor in the ensemble aggregation."""

SENSOR_DETECTION_THRESHOLD: float = 0.5
"""Per-sensor threshold above which a sensor detects OOD."""

OOD_CONSENSUS_MINIMUM: int = 3
"""At least 3/5 sensors must agree for OOD declaration."""

OOD_RECALL_MINIMUM: float = 0.90
"""Minimum recall target for OOD detection."""

DEFAULT_OOD_THRESHOLD: float = 0.5
"""Default threshold for OOD score."""

#: Epsilon for safe operations.
_EPS: float = 1e-10


# =============================================================================
# SECTION 2 -- ENUMS
# =============================================================================

class OODSchwere(Enum):
    """OOD severity classification."""
    NIEDRIG = "NIEDRIG"
    MITTEL = "MITTEL"
    HOCH = "HOCH"
    KRITISCH = "KRITISCH"


class OODAktion(Enum):
    """Recommended action based on OOD detection."""
    KEINE = "KEINE"
    UNSICHERHEIT_ERHOEHEN = "UNSICHERHEIT_ERHOEHEN"
    MAX_UNSICHERHEIT = "MAX_UNSICHERHEIT"
    VORHERSAGEN_DEAKTIVIEREN = "VORHERSAGEN_DEAKTIVIEREN"


# =============================================================================
# SECTION 3 -- DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class OODResult:
    """
    Aggregated OOD detection result from 5-sensor ensemble.

    Fields:
        score:           Weighted aggregate OOD score in [0, 1].
        severity:        Severity classification (OODSchwere).
        action:          Recommended action (OODAktion).
        sensor_scores:   Dict mapping sensor name to individual score.
        consensus_count: Number of sensors detecting OOD (score > threshold).
        is_ood:          True if consensus_count >= OOD_CONSENSUS_MINIMUM.
    """
    score: float
    severity: OODSchwere
    action: OODAktion
    sensor_scores: dict
    consensus_count: int
    is_ood: bool

    def __post_init__(self) -> None:
        if not isinstance(self.score, (int, float)):
            raise TypeError(
                f"OODResult.score must be numeric, got {type(self.score).__name__}"
            )
        if not math.isfinite(self.score):
            raise ValueError(
                f"OODResult.score must be finite, got {self.score!r}"
            )
        if not isinstance(self.severity, OODSchwere):
            raise TypeError(
                f"OODResult.severity must be OODSchwere, "
                f"got {type(self.severity).__name__}"
            )
        if not isinstance(self.action, OODAktion):
            raise TypeError(
                f"OODResult.action must be OODAktion, "
                f"got {type(self.action).__name__}"
            )
        if not isinstance(self.sensor_scores, dict):
            raise TypeError(
                f"OODResult.sensor_scores must be dict, "
                f"got {type(self.sensor_scores).__name__}"
            )
        if not isinstance(self.consensus_count, int):
            raise TypeError(
                f"OODResult.consensus_count must be int, "
                f"got {type(self.consensus_count).__name__}"
            )
        if not isinstance(self.is_ood, bool):
            raise TypeError(
                f"OODResult.is_ood must be bool, "
                f"got {type(self.is_ood).__name__}"
            )


@dataclass(frozen=True)
class OODMetrics:
    """
    Evaluation metrics for OOD detection.

    Fields:
        true_positives:  Count of correctly detected OOD samples.
        false_positives: Count of incorrectly flagged in-distribution samples.
        true_negatives:  Count of correctly identified in-distribution samples.
        false_negatives: Count of missed OOD samples.
    """
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int

    def __post_init__(self) -> None:
        for name, val in [
            ("true_positives", self.true_positives),
            ("false_positives", self.false_positives),
            ("true_negatives", self.true_negatives),
            ("false_negatives", self.false_negatives),
        ]:
            if not isinstance(val, int):
                raise TypeError(
                    f"OODMetrics.{name} must be int, "
                    f"got {type(val).__name__}"
                )
            if val < 0:
                raise ValueError(
                    f"OODMetrics.{name} must be non-negative, got {val}"
                )

    @property
    def precision(self) -> float:
        """Precision = TP / (TP + FP). Returns 0.0 if denominator is zero."""
        denom = self.true_positives + self.false_positives
        if denom == 0:
            return 0.0
        return self.true_positives / denom

    @property
    def recall(self) -> float:
        """Recall = TP / (TP + FN). Returns 0.0 if denominator is zero."""
        denom = self.true_positives + self.false_negatives
        if denom == 0:
            return 0.0
        return self.true_positives / denom

    @property
    def f1_score(self) -> float:
        """F1 = 2 * precision * recall / (precision + recall). Returns 0.0 if zero."""
        p = self.precision
        r = self.recall
        denom = p + r
        if denom < _EPS:
            return 0.0
        return 2.0 * p * r / denom


# =============================================================================
# SECTION 4 -- SENSOR FUNCTIONS (all return float in [0, 1])
# =============================================================================

def detect_msp(confidence: float) -> float:
    """
    Maximum Softmax Probability sensor.

    score = 1 - confidence. Lower confidence means higher OOD score.

    Args:
        confidence: Model confidence in [0, 1].

    Returns:
        OOD score in [0, 1].
    """
    if not isinstance(confidence, (int, float)):
        return 0.5
    if not math.isfinite(confidence):
        return 1.0
    confidence = max(0.0, min(1.0, float(confidence)))
    return 1.0 - confidence


def detect_mahalanobis(
    features: dict,
    train_mean: dict,
    train_cov_inv: list,
) -> float:
    """
    Mahalanobis distance sensor.

    d^2 = (x - mu)^T Sigma^{-1} (x - mu)
    score = min(d / normalization_factor, 1.0)

    Pure Python matrix-vector multiplication.

    Args:
        features:      Dict of feature name -> float value.
        train_mean:    Dict of feature name -> mean value from training.
        train_cov_inv: Inverse covariance matrix as list of lists.

    Returns:
        OOD score in [0, 1].
    """
    if not isinstance(features, dict) or not isinstance(train_mean, dict):
        return 0.0
    if not isinstance(train_cov_inv, list):
        return 0.0

    # Get common keys in sorted order for determinism
    common_keys = sorted(set(features.keys()) & set(train_mean.keys()))
    if not common_keys:
        return 0.0

    n = len(common_keys)

    # Build difference vector (x - mu)
    diff = []
    for k in common_keys:
        fv = features[k]
        mv = train_mean[k]
        if not isinstance(fv, (int, float)) or not math.isfinite(fv):
            fv = 0.0
        if not isinstance(mv, (int, float)) or not math.isfinite(mv):
            mv = 0.0
        diff.append(float(fv) - float(mv))

    # Validate covariance inverse dimensions
    if len(train_cov_inv) < n:
        return 0.0
    for row in train_cov_inv[:n]:
        if not isinstance(row, list) or len(row) < n:
            return 0.0

    # Compute (x - mu)^T * cov_inv * (x - mu)
    # First: cov_inv * diff
    cov_inv_diff = []
    for i in range(n):
        val = 0.0
        for j in range(n):
            entry = train_cov_inv[i][j]
            if not isinstance(entry, (int, float)) or not math.isfinite(entry):
                entry = 0.0
            val += float(entry) * diff[j]
        cov_inv_diff.append(val)

    # Then: diff^T * (cov_inv * diff)
    d_squared = 0.0
    for i in range(n):
        d_squared += diff[i] * cov_inv_diff[i]

    # Guard against negative values from numerical issues
    if not math.isfinite(d_squared) or d_squared < 0.0:
        d_squared = 0.0

    d = math.sqrt(d_squared)

    # Normalization factor: sqrt(n) to scale with dimensionality
    normalization_factor = math.sqrt(float(n)) if n > 0 else 1.0

    score = d / normalization_factor if normalization_factor > _EPS else 0.0

    # NaN/Inf guard
    if not math.isfinite(score):
        return 1.0

    return min(score, 1.0)


def detect_wasserstein(
    current_window: list,
    reference_window: list,
    threshold: float = 1.0,
) -> float:
    """
    Wasserstein distance sensor.

    Uses wasserstein_distance from jarvis.utils.helpers.
    score = min(wd / threshold, 1.0)

    Args:
        current_window:   Current data window as list of floats.
        reference_window: Reference data window as list of floats.
        threshold:        Normalization threshold. Default 1.0.

    Returns:
        OOD score in [0, 1].
    """
    if not isinstance(current_window, (list, tuple)):
        return 0.0
    if not isinstance(reference_window, (list, tuple)):
        return 0.0
    if not current_window or not reference_window:
        return 0.0

    # Filter to finite values
    cw = [float(v) for v in current_window
          if isinstance(v, (int, float)) and math.isfinite(v)]
    rw = [float(v) for v in reference_window
          if isinstance(v, (int, float)) and math.isfinite(v)]

    if not cw or not rw:
        return 0.0

    wd = wasserstein_distance(cw, rw)

    # NaN/Inf guard
    if not math.isfinite(wd):
        return 1.0

    if not isinstance(threshold, (int, float)) or not math.isfinite(threshold):
        threshold = 1.0
    if threshold < _EPS:
        threshold = _EPS

    score = wd / threshold

    if not math.isfinite(score):
        return 1.0

    return min(max(0.0, score), 1.0)


def detect_ensemble_variance(
    predictions: tuple,
    threshold: float = 0.1,
) -> float:
    """
    Ensemble variance sensor.

    variance = var(prediction.mu for p in predictions)
    score = min(variance / threshold, 1.0)

    Args:
        predictions: Tuple of Prediction objects (must have .mu attribute).
        threshold:   Normalization threshold. Default 0.1.

    Returns:
        OOD score in [0, 1].
    """
    if not isinstance(predictions, (tuple, list)) or not predictions:
        return 0.0

    # Extract mu values
    mus = []
    for p in predictions:
        mu = getattr(p, "mu", None)
        if mu is not None and isinstance(mu, (int, float)) and math.isfinite(mu):
            mus.append(float(mu))

    if not mus:
        return 0.0

    n = len(mus)
    mean_mu = sum(mus) / n
    variance = sum((m - mean_mu) ** 2 for m in mus) / n

    # NaN/Inf guard
    if not math.isfinite(variance):
        return 1.0

    if not isinstance(threshold, (int, float)) or not math.isfinite(threshold):
        threshold = 0.1
    if threshold < _EPS:
        threshold = _EPS

    score = variance / threshold

    if not math.isfinite(score):
        return 1.0

    return min(max(0.0, score), 1.0)


def detect_reconstruction(
    features: dict,
    reference_features: dict,
    threshold: float = 1.0,
) -> float:
    """
    Reconstruction error sensor (simplified -- no autoencoder, uses MSE).

    mse = mean((features[k] - reference[k])^2 for common keys)
    score = min(mse / threshold, 1.0)

    Args:
        features:           Current feature dict.
        reference_features: Reference feature dict.
        threshold:          Normalization threshold. Default 1.0.

    Returns:
        OOD score in [0, 1].
    """
    if not isinstance(features, dict) or not isinstance(reference_features, dict):
        return 0.0

    common_keys = sorted(set(features.keys()) & set(reference_features.keys()))
    if not common_keys:
        return 0.0

    sum_sq = 0.0
    count = 0
    for k in common_keys:
        fv = features[k]
        rv = reference_features[k]
        if (not isinstance(fv, (int, float)) or not math.isfinite(fv)):
            continue
        if (not isinstance(rv, (int, float)) or not math.isfinite(rv)):
            continue
        diff = float(fv) - float(rv)
        sum_sq += diff * diff
        count += 1

    if count == 0:
        return 0.0

    mse = sum_sq / count

    # NaN/Inf guard
    if not math.isfinite(mse):
        return 1.0

    if not isinstance(threshold, (int, float)) or not math.isfinite(threshold):
        threshold = 1.0
    if threshold < _EPS:
        threshold = _EPS

    score = mse / threshold

    if not math.isfinite(score):
        return 1.0

    return min(max(0.0, score), 1.0)


# =============================================================================
# SECTION 5 -- SEVERITY AND ACTION CLASSIFICATION
# =============================================================================

def classify_severity(score: float) -> OODSchwere:
    """
    Classify OOD score into severity level.

    Args:
        score: Aggregated OOD score in [0, 1].

    Returns:
        OODSchwere enum value.
    """
    if not isinstance(score, (int, float)) or not math.isfinite(score):
        return OODSchwere.KRITISCH
    if score < 0.3:
        return OODSchwere.NIEDRIG
    if score < 0.6:
        return OODSchwere.MITTEL
    if score < 0.8:
        return OODSchwere.HOCH
    return OODSchwere.KRITISCH


def determine_action(severity: OODSchwere, is_ood: bool) -> OODAktion:
    """
    Determine recommended action from severity and OOD status.

    Args:
        severity: OODSchwere classification.
        is_ood:   Whether consensus was reached.

    Returns:
        OODAktion enum value.
    """
    if not is_ood:
        return OODAktion.KEINE
    _SEVERITY_ACTION_MAP = {
        OODSchwere.NIEDRIG: OODAktion.KEINE,
        OODSchwere.MITTEL: OODAktion.UNSICHERHEIT_ERHOEHEN,
        OODSchwere.HOCH: OODAktion.MAX_UNSICHERHEIT,
        OODSchwere.KRITISCH: OODAktion.VORHERSAGEN_DEAKTIVIEREN,
    }
    return _SEVERITY_ACTION_MAP.get(severity, OODAktion.KEINE)


# =============================================================================
# SECTION 6 -- OOD ENSEMBLE
# =============================================================================

class OODEnsemble:
    """
    5-sensor OOD detection ensemble with consensus voting.

    Runs all 5 sensors, aggregates with SENSOR_WEIGHTS, determines consensus.

    Usage:
        ensemble = OODEnsemble()
        result = ensemble.detect(
            confidence=0.9, features={...}, predictions=(...),
            current_window=[...], reference_window=[...],
            train_mean={...}, train_cov_inv=[[...]], reference_features={...},
        )
    """

    def detect(
        self,
        confidence: float,
        features: dict,
        predictions: tuple,
        current_window: list,
        reference_window: list,
        train_mean: dict,
        train_cov_inv: list,
        reference_features: dict,
    ) -> OODResult:
        """
        Run all 5 sensors, aggregate with SENSOR_WEIGHTS, determine consensus.

        1. Run each sensor to get 5 scores.
        2. Weighted aggregate: score = sum(w * s for w, s in zip(SENSOR_WEIGHTS, scores)).
        3. Consensus: count sensors where score > SENSOR_DETECTION_THRESHOLD.
        4. is_ood = consensus_count >= OOD_CONSENSUS_MINIMUM.
        5. Determine severity and action from score.

        Args:
            confidence:         Model confidence for MSP sensor.
            features:           Feature dict for Mahalanobis and reconstruction.
            predictions:        Tuple of Prediction objects for ensemble variance.
            current_window:     Current data window for Wasserstein sensor.
            reference_window:   Reference data window for Wasserstein sensor.
            train_mean:         Training mean dict for Mahalanobis sensor.
            train_cov_inv:      Inverse covariance matrix for Mahalanobis sensor.
            reference_features: Reference features for reconstruction sensor.

        Returns:
            OODResult with aggregated scores and consensus.
        """
        # Run all 5 sensors
        s_msp = detect_msp(confidence)
        s_maha = detect_mahalanobis(features, train_mean, train_cov_inv)
        s_wass = detect_wasserstein(current_window, reference_window)
        s_evar = detect_ensemble_variance(predictions)
        s_recon = detect_reconstruction(features, reference_features)

        scores = (s_msp, s_maha, s_wass, s_evar, s_recon)

        sensor_scores = dict(zip(SENSOR_NAMES, scores))

        # Weighted aggregate
        agg_score = 0.0
        for w, s in zip(SENSOR_WEIGHTS, scores):
            agg_score += w * s

        # NaN/Inf guard
        if not math.isfinite(agg_score):
            agg_score = 1.0
        agg_score = max(0.0, min(1.0, agg_score))

        # Consensus count
        consensus_count = sum(
            1 for s in scores if s > SENSOR_DETECTION_THRESHOLD
        )

        is_ood = consensus_count >= OOD_CONSENSUS_MINIMUM

        severity = classify_severity(agg_score)
        action = determine_action(severity, is_ood)

        return OODResult(
            score=agg_score,
            severity=severity,
            action=action,
            sensor_scores=sensor_scores,
            consensus_count=consensus_count,
            is_ood=is_ood,
        )


# =============================================================================
# SECTION 7 -- AGGREGATE OOD (standalone function)
# =============================================================================

def aggregate_ood(sensor_scores: dict) -> OODResult:
    """
    Aggregate sensor scores into OODResult.

    Weighted score, consensus count, severity, action.

    Args:
        sensor_scores: Dict mapping sensor name to score float.

    Returns:
        OODResult with aggregated scores and consensus.
    """
    if not isinstance(sensor_scores, dict):
        raise TypeError(
            f"sensor_scores must be a dict, got {type(sensor_scores).__name__}"
        )

    # Build scores tuple in canonical order
    scores = []
    for name in SENSOR_NAMES:
        val = sensor_scores.get(name, 0.0)
        if not isinstance(val, (int, float)) or not math.isfinite(val):
            val = 0.0
        scores.append(max(0.0, min(1.0, float(val))))

    # Weighted aggregate
    agg_score = 0.0
    for w, s in zip(SENSOR_WEIGHTS, scores):
        agg_score += w * s

    if not math.isfinite(agg_score):
        agg_score = 1.0
    agg_score = max(0.0, min(1.0, agg_score))

    consensus_count = sum(
        1 for s in scores if s > SENSOR_DETECTION_THRESHOLD
    )

    is_ood = consensus_count >= OOD_CONSENSUS_MINIMUM

    severity = classify_severity(agg_score)
    action = determine_action(severity, is_ood)

    # Rebuild sensor_scores dict in canonical order
    canonical_scores = dict(zip(SENSOR_NAMES, scores))

    return OODResult(
        score=agg_score,
        severity=severity,
        action=action,
        sensor_scores=canonical_scores,
        consensus_count=consensus_count,
        is_ood=is_ood,
    )


# =============================================================================
# SECTION 8 -- HANDLE UNKNOWN-UNKNOWN
# =============================================================================

def handle_unknown_unknown(ood_result: OODResult) -> OODAktion:
    """
    Handle unknown-unknowns.

    If is_ood and consensus == 5 (all sensors agree), always return
    VORHERSAGEN_DEAKTIVIEREN regardless of severity.
    Otherwise return ood_result.action.

    Args:
        ood_result: OODResult from detection.

    Returns:
        OODAktion recommendation.
    """
    if not isinstance(ood_result, OODResult):
        raise TypeError(
            f"ood_result must be OODResult, got {type(ood_result).__name__}"
        )
    if ood_result.is_ood and ood_result.consensus_count == N_SENSORS:
        return OODAktion.VORHERSAGEN_DEAKTIVIEREN
    return ood_result.action


# =============================================================================
# SECTION 9 -- OOD DRIFT TRACKER
# =============================================================================

class OODDriftTracker:
    """
    Tracks OOD score drift over a sliding window.

    Instance state is per-object (no global mutable state).
    A fresh OODDriftTracker should be created per session (DET-02).
    """

    WINDOW_SIZE: int = 100
    """Maximum window size for score tracking."""

    DRIFT_THRESHOLD: float = 0.1
    """Threshold for drift detection: recent mean must exceed historical mean by this."""

    def __init__(self) -> None:
        self._scores: List[float] = []

    def add_score(self, score: float) -> None:
        """
        Add a score to the tracking window.

        Non-finite values are silently replaced with 0.5.

        Args:
            score: OOD score to track.
        """
        if not isinstance(score, (int, float)) or not math.isfinite(score):
            score = 0.5
        score = max(0.0, min(1.0, float(score)))
        self._scores.append(score)
        if len(self._scores) > self.WINDOW_SIZE:
            self._scores = self._scores[-self.WINDOW_SIZE:]

    def get_mean_score(self) -> float:
        """
        Get the mean score over the current window.

        Returns:
            Mean score, or 0.0 if window is empty.
        """
        if not self._scores:
            return 0.0
        result = sum(self._scores) / len(self._scores)
        if not math.isfinite(result):
            return 0.0
        return result

    def is_drifting(self) -> bool:
        """
        Check whether recent scores are drifting upward.

        True if the mean of the recent half exceeds the mean of the
        historical (first) half by more than DRIFT_THRESHOLD.

        Returns:
            True if drift is detected.
        """
        n = len(self._scores)
        if n < 4:
            return False

        mid = n // 2
        historical = self._scores[:mid]
        recent = self._scores[mid:]

        hist_mean = sum(historical) / len(historical)
        recent_mean = sum(recent) / len(recent)

        if not math.isfinite(hist_mean) or not math.isfinite(recent_mean):
            return False

        return (recent_mean - hist_mean) > self.DRIFT_THRESHOLD


# =============================================================================
# SECTION 10 -- FALSE POSITIVE CONTROLLER
# =============================================================================

class FalsePositiveController:
    """
    Controls false positive rate by adjusting detection threshold.

    Instance state is per-object (no global mutable state).
    A fresh FalsePositiveController should be created per session (DET-02).
    """

    FP_TOLERANCE: float = 0.05
    """Maximum acceptable false positive rate (5%)."""

    def __init__(self) -> None:
        self._predictions: List[Tuple[bool, bool]] = []

    def record(self, predicted_ood: bool, actual_ood: bool) -> None:
        """
        Record a single prediction-outcome pair.

        Args:
            predicted_ood: Whether OOD was predicted.
            actual_ood:    Whether the sample was actually OOD.
        """
        self._predictions.append((bool(predicted_ood), bool(actual_ood)))

    def get_fp_rate(self) -> float:
        """
        Compute the false positive rate.

        FP rate = FP / (FP + TN).
        Returns 0.0 if no negative samples.

        Returns:
            False positive rate in [0, 1].
        """
        fp = 0
        tn = 0
        for predicted, actual in self._predictions:
            if not actual:  # actual negative
                if predicted:
                    fp += 1
                else:
                    tn += 1

        denom = fp + tn
        if denom == 0:
            return 0.0
        return fp / denom

    def should_raise_threshold(self) -> bool:
        """
        Check whether FP rate exceeds FP_TOLERANCE.

        Returns:
            True if threshold should be raised.
        """
        return self.get_fp_rate() > self.FP_TOLERANCE


# =============================================================================
# SECTION 11 -- EVALUATE OOD DETECTOR
# =============================================================================

def evaluate_ood_detector(
    results: list,
    labels: list,
) -> OODMetrics:
    """
    Compute TP/FP/TN/FN from OOD results and ground truth labels.

    Args:
        results: List of OODResult objects.
        labels:  List of bool (True = OOD, False = in-distribution).

    Returns:
        OODMetrics with confusion matrix counts.

    Raises:
        ValueError: If results and labels have different lengths.
    """
    if len(results) != len(labels):
        raise ValueError(
            f"results and labels must have equal length. "
            f"Got {len(results)} vs {len(labels)}"
        )

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for result, label in zip(results, labels):
        predicted = result.is_ood if isinstance(result, OODResult) else bool(result)
        actual = bool(label)

        if actual and predicted:
            tp += 1
        elif not actual and predicted:
            fp += 1
        elif not actual and not predicted:
            tn += 1
        else:  # actual and not predicted
            fn += 1

    return OODMetrics(
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
    )
