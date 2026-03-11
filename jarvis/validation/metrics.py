# =============================================================================
# jarvis/validation/metrics.py — S15 Validation Metrics & VETO Criteria
#
# Authority: FAS v6.0.1, S15
#
# Aggregate validation metrics and VETO gate enforcement.
#
# Entry point: check_veto_criteria()
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
#   stdlib:   dataclasses, math
#   internal: NONE
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "ValidationMetrics",
    "VetoResult",
    "VETO_ECE_THRESHOLD",
    "VETO_ECE_DRIFT_THRESHOLD",
    "VETO_CALIBRATION_STABILITY",
    "VETO_OOD_RECALL",
    "VETO_REGIME_DETECTION",
    "VETO_FAST_P95_MS",
    "VETO_DEEP_P95_MS",
    "check_veto_criteria",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals, not parametrisable)
# =============================================================================

VETO_ECE_THRESHOLD: float = 0.05
"""Mean ECE must be below this for VETO pass."""

VETO_ECE_DRIFT_THRESHOLD: float = 0.02
"""Max ECE drift between regimes must be at or below this."""

VETO_CALIBRATION_STABILITY: float = 0.02
"""Calibration stability std must be below this."""

VETO_OOD_RECALL: float = 0.90
"""OOD recall must be at or above this."""

VETO_REGIME_DETECTION: float = 0.95
"""Regime detection rate must be at or above this."""

VETO_FAST_P95_MS: float = 50.0
"""Fast path P95 latency must be at or below this (ms)."""

VETO_DEEP_P95_MS: float = 500.0
"""Deep path P95 latency must be at or below this (ms)."""


# =============================================================================
# SECTION 2 -- DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class ValidationMetrics:
    """Aggregate validation metrics."""
    ece_mean: float
    ece_max: float
    ece_pass_rate: float
    ece_regime_drift: float
    calibration_stability_std: float
    ood_recall: float
    regime_detection_rate: float
    numerical_stability: bool
    performance_fast_p95_ms: float
    performance_deep_p95_ms: float

    def __post_init__(self) -> None:
        for name, val in [
            ("ece_mean", self.ece_mean),
            ("ece_max", self.ece_max),
            ("ece_pass_rate", self.ece_pass_rate),
            ("ece_regime_drift", self.ece_regime_drift),
            ("calibration_stability_std", self.calibration_stability_std),
            ("ood_recall", self.ood_recall),
            ("regime_detection_rate", self.regime_detection_rate),
            ("performance_fast_p95_ms", self.performance_fast_p95_ms),
            ("performance_deep_p95_ms", self.performance_deep_p95_ms),
        ]:
            if not isinstance(val, (int, float)):
                raise TypeError(
                    f"ValidationMetrics.{name} must be numeric, "
                    f"got {type(val).__name__}"
                )
            if not math.isfinite(val):
                raise ValueError(
                    f"ValidationMetrics.{name} must be finite, got {val!r}"
                )
        if not isinstance(self.numerical_stability, bool):
            raise TypeError(
                f"ValidationMetrics.numerical_stability must be bool, "
                f"got {type(self.numerical_stability).__name__}"
            )


@dataclass(frozen=True)
class VetoResult:
    """Result of VETO criteria check."""
    passed: bool
    failures: tuple
    metrics: ValidationMetrics

    def __post_init__(self) -> None:
        if not isinstance(self.passed, bool):
            raise TypeError(
                f"VetoResult.passed must be bool, "
                f"got {type(self.passed).__name__}"
            )
        if not isinstance(self.failures, tuple):
            raise TypeError(
                f"VetoResult.failures must be tuple, "
                f"got {type(self.failures).__name__}"
            )
        if not isinstance(self.metrics, ValidationMetrics):
            raise TypeError(
                f"VetoResult.metrics must be ValidationMetrics, "
                f"got {type(self.metrics).__name__}"
            )


# =============================================================================
# SECTION 3 -- VETO CRITERIA CHECK
# =============================================================================

def check_veto_criteria(metrics: ValidationMetrics) -> VetoResult:
    """
    Check all VETO criteria against metrics.

    Criteria (ALL must pass):
    1. ece_mean < VETO_ECE_THRESHOLD
    2. ece_regime_drift <= VETO_ECE_DRIFT_THRESHOLD
    3. calibration_stability_std < VETO_CALIBRATION_STABILITY
    4. ood_recall >= VETO_OOD_RECALL
    5. regime_detection_rate >= VETO_REGIME_DETECTION
    6. numerical_stability == True
    7. performance_fast_p95_ms <= VETO_FAST_P95_MS
    8. performance_deep_p95_ms <= VETO_DEEP_P95_MS

    Returns VetoResult with passed=True only if ALL criteria pass.
    """
    if not isinstance(metrics, ValidationMetrics):
        raise TypeError(
            f"metrics must be ValidationMetrics, "
            f"got {type(metrics).__name__}"
        )

    failures = []

    if not (metrics.ece_mean < VETO_ECE_THRESHOLD):
        failures.append("ece_mean")

    if not (metrics.ece_regime_drift <= VETO_ECE_DRIFT_THRESHOLD):
        failures.append("ece_regime_drift")

    if not (metrics.calibration_stability_std < VETO_CALIBRATION_STABILITY):
        failures.append("calibration_stability_std")

    if not (metrics.ood_recall >= VETO_OOD_RECALL):
        failures.append("ood_recall")

    if not (metrics.regime_detection_rate >= VETO_REGIME_DETECTION):
        failures.append("regime_detection_rate")

    if not metrics.numerical_stability:
        failures.append("numerical_stability")

    if not (metrics.performance_fast_p95_ms <= VETO_FAST_P95_MS):
        failures.append("performance_fast_p95_ms")

    if not (metrics.performance_deep_p95_ms <= VETO_DEEP_P95_MS):
        failures.append("performance_deep_p95_ms")

    passed = len(failures) == 0

    return VetoResult(
        passed=passed,
        failures=tuple(failures),
        metrics=metrics,
    )
