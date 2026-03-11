# =============================================================================
# tests/unit/systems/test_validation_gates.py
# Tests for jarvis/systems/validation_gates.py
# =============================================================================

import pytest

from jarvis.systems.validation_gates import (
    QUALITY_THRESHOLD,
    DRIFT_THRESHOLD,
    KALMAN_THRESHOLD,
    ECE_THRESHOLD,
    RISK_VAR_THRESHOLD,
    GateResult,
    ValidationGate,
    QualityGate,
    DriftGate,
    KalmanGate,
    ECEGate,
    OODGate,
    RiskGate,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_quality_threshold(self):
        assert QUALITY_THRESHOLD == 0.50

    def test_drift_threshold(self):
        assert DRIFT_THRESHOLD == 0.80

    def test_kalman_threshold(self):
        assert KALMAN_THRESHOLD == 1e5

    def test_ece_threshold(self):
        assert ECE_THRESHOLD == 0.05

    def test_risk_var_threshold(self):
        assert RISK_VAR_THRESHOLD == -0.15


# =============================================================================
# SECTION 2 -- GATE RESULT DATACLASS
# =============================================================================

class TestGateResult:
    def test_frozen(self):
        r = GateResult("test", True, 0.6, 0.5, "ok")
        with pytest.raises(AttributeError):
            r.passed = False

    def test_fields(self):
        r = GateResult(
            gate_name="QualityGate",
            passed=True,
            value=0.7,
            threshold=0.5,
            reason="Quality score 0.700 >= 0.5",
        )
        assert r.gate_name == "QualityGate"
        assert r.passed is True
        assert r.value == 0.7
        assert r.threshold == 0.5

    def test_equality(self):
        r1 = GateResult("test", True, 0.6, 0.5, "ok")
        r2 = GateResult("test", True, 0.6, 0.5, "ok")
        assert r1 == r2


# =============================================================================
# SECTION 3 -- ABSTRACT BASE GATE
# =============================================================================

class TestValidationGateBase:
    def test_name_property(self):
        g = QualityGate()
        assert g.name == "QualityGate"

    def test_threshold_property(self):
        g = QualityGate()
        assert g.threshold == QUALITY_THRESHOLD

    def test_base_check_raises(self):
        g = ValidationGate("test", 0.5)
        with pytest.raises(NotImplementedError):
            g.check(0.5)

    def test_name_type_error(self):
        with pytest.raises(TypeError, match="name must be a string"):
            ValidationGate(123, 0.5)

    def test_threshold_type_error(self):
        with pytest.raises(TypeError, match="threshold must be numeric"):
            ValidationGate("test", "bad")


# =============================================================================
# SECTION 4 -- QUALITY GATE
# =============================================================================

class TestQualityGate:
    def test_pass_above(self):
        r = QualityGate().check(0.7)
        assert r.passed is True
        assert r.gate_name == "QualityGate"

    def test_pass_at_threshold(self):
        r = QualityGate().check(0.5)
        assert r.passed is True

    def test_fail_below(self):
        r = QualityGate().check(0.49)
        assert r.passed is False

    def test_fail_zero(self):
        r = QualityGate().check(0.0)
        assert r.passed is False

    def test_pass_one(self):
        r = QualityGate().check(1.0)
        assert r.passed is True

    def test_reason_format_pass(self):
        r = QualityGate().check(0.7)
        assert ">=" in r.reason

    def test_reason_format_fail(self):
        r = QualityGate().check(0.3)
        assert "<" in r.reason

    def test_type_error(self):
        with pytest.raises(TypeError, match="quality_score must be numeric"):
            QualityGate().check("bad")

    def test_int_accepted(self):
        r = QualityGate().check(1)
        assert r.passed is True


# =============================================================================
# SECTION 5 -- DRIFT GATE
# =============================================================================

class TestDriftGate:
    def test_pass_below(self):
        r = DriftGate().check(0.5)
        assert r.passed is True

    def test_fail_at_threshold(self):
        r = DriftGate().check(0.8)
        assert r.passed is False

    def test_fail_above(self):
        r = DriftGate().check(0.9)
        assert r.passed is False

    def test_pass_zero(self):
        r = DriftGate().check(0.0)
        assert r.passed is True

    def test_reason_format_pass(self):
        r = DriftGate().check(0.5)
        assert "<" in r.reason

    def test_reason_format_fail(self):
        r = DriftGate().check(0.9)
        assert ">=" in r.reason

    def test_type_error(self):
        with pytest.raises(TypeError, match="drift_severity must be numeric"):
            DriftGate().check("bad")

    def test_gate_name(self):
        assert DriftGate().name == "DriftGate"


# =============================================================================
# SECTION 6 -- KALMAN GATE
# =============================================================================

class TestKalmanGate:
    def test_pass_below(self):
        r = KalmanGate().check(1e4)
        assert r.passed is True

    def test_fail_at_threshold(self):
        r = KalmanGate().check(1e5)
        assert r.passed is False

    def test_fail_above(self):
        r = KalmanGate().check(1e6)
        assert r.passed is False

    def test_pass_zero(self):
        r = KalmanGate().check(0.0)
        assert r.passed is True

    def test_scientific_notation_in_reason(self):
        r = KalmanGate().check(1e4)
        assert "e" in r.reason.lower()

    def test_type_error(self):
        with pytest.raises(TypeError, match="condition_number must be numeric"):
            KalmanGate().check("bad")

    def test_gate_name(self):
        assert KalmanGate().name == "KalmanGate"


# =============================================================================
# SECTION 7 -- ECE GATE
# =============================================================================

class TestECEGate:
    def test_pass_below(self):
        r = ECEGate().check(0.03)
        assert r.passed is True

    def test_fail_at_threshold(self):
        r = ECEGate().check(0.05)
        assert r.passed is False

    def test_fail_above(self):
        r = ECEGate().check(0.10)
        assert r.passed is False

    def test_pass_zero(self):
        r = ECEGate().check(0.0)
        assert r.passed is True

    def test_four_decimal_reason(self):
        r = ECEGate().check(0.0312)
        assert "0.0312" in r.reason

    def test_type_error(self):
        with pytest.raises(TypeError, match="ece must be numeric"):
            ECEGate().check("bad")

    def test_gate_name(self):
        assert ECEGate().name == "ECEGate"


# =============================================================================
# SECTION 8 -- OOD GATE
# =============================================================================

class TestOODGate:
    def test_pass_not_ood(self):
        r = OODGate().check(False)
        assert r.passed is True

    def test_fail_ood(self):
        r = OODGate().check(True)
        assert r.passed is False

    def test_reason_not_detected(self):
        r = OODGate().check(False)
        assert "not detected" in r.reason

    def test_reason_detected(self):
        r = OODGate().check(True)
        assert "detected" in r.reason
        assert "not" not in r.reason

    def test_value_encoding(self):
        r_ood = OODGate().check(True)
        r_ok = OODGate().check(False)
        assert r_ood.value == 1.0
        assert r_ok.value == 0.0

    def test_type_error(self):
        with pytest.raises(TypeError, match="is_ood must be bool"):
            OODGate().check(1)

    def test_gate_name(self):
        assert OODGate().name == "OODGate"


# =============================================================================
# SECTION 9 -- RISK GATE
# =============================================================================

class TestRiskGate:
    def test_pass_above_threshold(self):
        r = RiskGate().check(-0.10)
        assert r.passed is True

    def test_pass_at_threshold(self):
        r = RiskGate().check(-0.15)
        assert r.passed is True

    def test_fail_below_threshold(self):
        r = RiskGate().check(-0.20)
        assert r.passed is False

    def test_pass_zero(self):
        r = RiskGate().check(0.0)
        assert r.passed is True

    def test_reason_format_pass(self):
        r = RiskGate().check(-0.10)
        assert ">=" in r.reason

    def test_reason_format_fail(self):
        r = RiskGate().check(-0.20)
        assert "<" in r.reason

    def test_type_error(self):
        with pytest.raises(TypeError, match="var must be numeric"):
            RiskGate().check("bad")

    def test_gate_name(self):
        assert RiskGate().name == "RiskGate"


# =============================================================================
# SECTION 10 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_quality_gate_deterministic(self):
        results = [QualityGate().check(0.6) for _ in range(10)]
        assert all(r == results[0] for r in results)

    def test_ood_gate_deterministic(self):
        results = [OODGate().check(True) for _ in range(10)]
        assert all(r == results[0] for r in results)

    def test_risk_gate_deterministic(self):
        results = [RiskGate().check(-0.12) for _ in range(10)]
        assert all(r == results[0] for r in results)
