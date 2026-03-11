# =============================================================================
# jarvis/systems/validation_gates.py
# Authority: FAS v6.0.1 -- S17.5, lines 14801-14863
# =============================================================================
#
# SCOPE
# -----
# Validation gates for pipeline stages.  Each gate checks a single metric
# against a fixed threshold and returns a pass/fail result with reason.
#
# Public symbols:
#   QUALITY_THRESHOLD          Layer 1 quality gate (0.50)
#   DRIFT_THRESHOLD            Layer 2 drift gate (0.80)
#   KALMAN_THRESHOLD           Layer 3 Kalman stability gate (1e5)
#   ECE_THRESHOLD              Layer 5 calibration gate (0.05)
#   RISK_VAR_THRESHOLD         Layer 8 risk VaR gate (-0.15)
#   GateResult                 Frozen dataclass for gate check result
#   ValidationGate             Abstract base gate
#   QualityGate                Layer 1: data quality
#   DriftGate                  Layer 2: feature drift
#   KalmanGate                 Layer 3: Kalman stability
#   ECEGate                    Layer 5: calibration ECE
#   OODGate                    Layer 7: OOD detection (boolean)
#   RiskGate                   Layer 8: risk VaR limit
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, enum
#   external:  NONE
#   internal:  NONE
#   PROHIBITED: logging, random, file IO, network IO, datetime.now(), numpy
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-06  Fixed literals (thresholds) not parametrisable.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "QUALITY_THRESHOLD",
    "DRIFT_THRESHOLD",
    "KALMAN_THRESHOLD",
    "ECE_THRESHOLD",
    "RISK_VAR_THRESHOLD",
    "GateResult",
    "ValidationGate",
    "QualityGate",
    "DriftGate",
    "KalmanGate",
    "ECEGate",
    "OODGate",
    "RiskGate",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

QUALITY_THRESHOLD: float = 0.50
"""Layer 1: hard stop if quality_score < this value."""

DRIFT_THRESHOLD: float = 0.80
"""Layer 2: hard stop if drift_severity >= this value."""

KALMAN_THRESHOLD: float = 1e5
"""Layer 3: hard stop if condition_number >= this value."""

ECE_THRESHOLD: float = 0.05
"""Layer 5: hard gate — deployment blocked if ECE >= this value."""

RISK_VAR_THRESHOLD: float = -0.15
"""Layer 8: hard stop if VaR < this value (more negative = worse)."""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class GateResult:
    """
    Result of a validation gate check.

    Fields:
        gate_name: Identifier of the gate.
        passed:    True if the metric satisfies the gate condition.
        value:     The metric value that was checked.
        threshold: The threshold used for comparison.
        reason:    Human-readable explanation of the result.
    """
    gate_name: str
    passed: bool
    value: float
    threshold: float
    reason: str


# =============================================================================
# SECTION 3 -- ABSTRACT BASE GATE
# =============================================================================

class ValidationGate:
    """
    Abstract base class for all validation gates.

    Subclasses must implement check() returning a GateResult.
    """

    def __init__(self, name: str, threshold: float) -> None:
        if not isinstance(name, str):
            raise TypeError(
                f"name must be a string, got {type(name).__name__}"
            )
        if not isinstance(threshold, (int, float)):
            raise TypeError(
                f"threshold must be numeric, got {type(threshold).__name__}"
            )
        self._name = name
        self._threshold = float(threshold)

    @property
    def name(self) -> str:
        return self._name

    @property
    def threshold(self) -> float:
        return self._threshold

    def check(self, value: float) -> GateResult:
        """Check gate condition. Must be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement check()")


# =============================================================================
# SECTION 4 -- CONCRETE GATES
# =============================================================================

class QualityGate(ValidationGate):
    """
    Layer 1: Data Quality Gate.

    Pass condition: quality_score >= threshold.
    """

    def __init__(self) -> None:
        super().__init__("QualityGate", QUALITY_THRESHOLD)

    def check(self, quality_score: float) -> GateResult:
        if not isinstance(quality_score, (int, float)):
            raise TypeError(
                f"quality_score must be numeric, "
                f"got {type(quality_score).__name__}"
            )
        passed = quality_score >= self._threshold
        op = ">=" if passed else "<"
        reason = f"Quality score {quality_score:.3f} {op} {self._threshold}"
        return GateResult(
            gate_name=self._name,
            passed=passed,
            value=float(quality_score),
            threshold=self._threshold,
            reason=reason,
        )


class DriftGate(ValidationGate):
    """
    Layer 2: Feature Drift Gate.

    Pass condition: drift_severity < threshold.
    """

    def __init__(self) -> None:
        super().__init__("DriftGate", DRIFT_THRESHOLD)

    def check(self, drift_severity: float) -> GateResult:
        if not isinstance(drift_severity, (int, float)):
            raise TypeError(
                f"drift_severity must be numeric, "
                f"got {type(drift_severity).__name__}"
            )
        passed = drift_severity < self._threshold
        op = "<" if passed else ">="
        reason = f"Drift severity {drift_severity:.3f} {op} {self._threshold}"
        return GateResult(
            gate_name=self._name,
            passed=passed,
            value=float(drift_severity),
            threshold=self._threshold,
            reason=reason,
        )


class KalmanGate(ValidationGate):
    """
    Layer 3: Kalman Stability Gate.

    Pass condition: condition_number < threshold.
    """

    def __init__(self) -> None:
        super().__init__("KalmanGate", KALMAN_THRESHOLD)

    def check(self, condition_number: float) -> GateResult:
        if not isinstance(condition_number, (int, float)):
            raise TypeError(
                f"condition_number must be numeric, "
                f"got {type(condition_number).__name__}"
            )
        passed = condition_number < self._threshold
        op = "<" if passed else ">="
        reason = (
            f"Condition number {condition_number:.2e} {op} "
            f"{self._threshold:.2e}"
        )
        return GateResult(
            gate_name=self._name,
            passed=passed,
            value=float(condition_number),
            threshold=self._threshold,
            reason=reason,
        )


class ECEGate(ValidationGate):
    """
    Layer 5: Calibration Gate (Expected Calibration Error).

    Pass condition: ece < threshold.  HARD GATE — deployment blocked on fail.
    """

    def __init__(self) -> None:
        super().__init__("ECEGate", ECE_THRESHOLD)

    def check(self, ece: float) -> GateResult:
        if not isinstance(ece, (int, float)):
            raise TypeError(
                f"ece must be numeric, got {type(ece).__name__}"
            )
        passed = ece < self._threshold
        op = "<" if passed else ">="
        reason = f"ECE {ece:.4f} {op} {self._threshold}"
        return GateResult(
            gate_name=self._name,
            passed=passed,
            value=float(ece),
            threshold=self._threshold,
            reason=reason,
        )


class OODGate(ValidationGate):
    """
    Layer 7: OOD Detection Gate.

    Pass condition: is_ood is False.  Boolean gate — no numeric threshold.
    """

    def __init__(self) -> None:
        super().__init__("OODGate", 0.0)

    def check(self, is_ood: bool) -> GateResult:
        if not isinstance(is_ood, bool):
            raise TypeError(
                f"is_ood must be bool, got {type(is_ood).__name__}"
            )
        passed = not is_ood
        reason = f"OOD {'not ' if passed else ''}detected"
        return GateResult(
            gate_name=self._name,
            passed=passed,
            value=1.0 if is_ood else 0.0,
            threshold=self._threshold,
            reason=reason,
        )


class RiskGate(ValidationGate):
    """
    Layer 8: Risk Limit Gate (Value at Risk).

    Pass condition: var >= threshold (VaR is negative; closer to 0 = better).
    """

    def __init__(self) -> None:
        super().__init__("RiskGate", RISK_VAR_THRESHOLD)

    def check(self, var: float) -> GateResult:
        if not isinstance(var, (int, float)):
            raise TypeError(
                f"var must be numeric, got {type(var).__name__}"
            )
        passed = var >= self._threshold
        op = ">=" if passed else "<"
        reason = f"VaR {var:.3f} {op} {self._threshold}"
        return GateResult(
            gate_name=self._name,
            passed=passed,
            value=float(var),
            threshold=self._threshold,
            reason=reason,
        )
