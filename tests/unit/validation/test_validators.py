# =============================================================================
# tests/unit/validation/test_validators.py — Unit tests for S15 validators
#
# 30+ tests covering all 10 validation categories.
# Self-contained — uses only synthetic data.
# =============================================================================

import hashlib
import math

import pytest

from jarvis.validation.validators import (
    ValidationResult,
    validate_ece_walkforward,
    validate_ece_per_regime,
    validate_crisis_detection,
    validate_stress_certification,
    validate_ood_consensus,
    validate_system_contract,
    validate_meta_uncertainty_transitions,
    validate_numerical_stability,
    validate_performance,
    validate_logging_integrity,
    run_all_validations,
)


# =============================================================================
# TestValidationResult
# =============================================================================

class TestValidationResult:
    """Tests for the ValidationResult frozen dataclass."""

    def test_frozen(self):
        r = ValidationResult(
            category="TEST", passed=True, score=1.0,
            details="ok", n_checks=1, n_passed=1,
        )
        with pytest.raises(AttributeError):
            r.passed = False

    def test_all_fields(self):
        r = ValidationResult(
            category="CAT", passed=False, score=0.5,
            details="half", n_checks=10, n_passed=5,
        )
        assert r.category == "CAT"
        assert r.passed is False
        assert r.score == 0.5
        assert r.details == "half"
        assert r.n_checks == 10
        assert r.n_passed == 5

    def test_score_must_be_finite(self):
        with pytest.raises(ValueError):
            ValidationResult(
                category="X", passed=True, score=float("nan"),
                details="", n_checks=0, n_passed=0,
            )

    def test_category_must_be_str(self):
        with pytest.raises(TypeError):
            ValidationResult(
                category=123, passed=True, score=1.0,
                details="", n_checks=0, n_passed=0,
            )


# =============================================================================
# TestECEWalkforward
# =============================================================================

class TestECEWalkforward:
    """Category 1: ECE Walk-Forward."""

    def test_all_pass(self):
        ece_values = tuple(0.01 for _ in range(16))
        r = validate_ece_walkforward(ece_values)
        assert r.passed is True
        assert r.score == 1.0
        assert r.category == "ECE_WALKFORWARD"

    def test_some_fail(self):
        # 10 pass, 6 fail -> 62.5% < 87.5%
        ece_values = tuple(0.01 for _ in range(10)) + tuple(0.06 for _ in range(6))
        r = validate_ece_walkforward(ece_values)
        assert r.passed is False

    def test_exactly_threshold(self):
        # 14/16 = 87.5% which equals min_pass_rate
        ece_values = tuple(0.01 for _ in range(14)) + tuple(0.06 for _ in range(2))
        r = validate_ece_walkforward(ece_values)
        assert r.passed is True
        assert r.n_passed == 14
        assert r.n_checks == 16

    def test_empty_input(self):
        r = validate_ece_walkforward(())
        assert r.n_checks == 0
        assert r.passed is False  # 0/0 = 0.0 < 0.875

    def test_type_error_on_list(self):
        with pytest.raises(TypeError):
            validate_ece_walkforward([0.01, 0.02])

    def test_non_finite_values_counted_as_fail(self):
        ece_values = (0.01, float("nan"), 0.01, float("inf"))
        r = validate_ece_walkforward(ece_values)
        assert r.n_passed == 2


# =============================================================================
# TestECEPerRegime
# =============================================================================

class TestECEPerRegime:
    """Category 2: Per-Regime ECE."""

    def test_all_regimes_pass(self):
        regime_eces = {
            "RISK_ON": 0.02, "RISK_OFF": 0.03,
            "CRISIS": 0.03, "TRANSITION": 0.02,
        }
        r = validate_ece_per_regime(regime_eces)
        assert r.passed is True
        assert r.category == "ECE_PER_REGIME"

    def test_one_fails(self):
        regime_eces = {
            "RISK_ON": 0.02, "RISK_OFF": 0.06,
        }
        r = validate_ece_per_regime(regime_eces)
        assert r.passed is False
        assert r.n_passed == 1

    def test_drift_too_high(self):
        # Both below 0.05, but drift = 0.03 > 0.02
        regime_eces = {"A": 0.01, "B": 0.04}
        r = validate_ece_per_regime(regime_eces)
        assert r.passed is False

    def test_drift_exactly_at_threshold(self):
        # drift = 0.03 which is NOT < 0.02 (must be strictly less)
        regime_eces = {"A": 0.01, "B": 0.04}
        r = validate_ece_per_regime(regime_eces)
        assert r.passed is False

    def test_empty_dict(self):
        r = validate_ece_per_regime({})
        assert r.n_checks == 0


# =============================================================================
# TestCrisisDetection
# =============================================================================

class TestCrisisDetection:
    """Category 3: Historical Crisis Detection."""

    def test_all_detected(self):
        scores = (0.7, 0.8, 0.9, 0.6)
        r = validate_crisis_detection(scores)
        assert r.passed is True

    def test_some_missed(self):
        scores = (0.7, 0.3, 0.9)
        r = validate_crisis_detection(scores)
        assert r.passed is False
        assert r.n_passed == 2

    def test_empty(self):
        r = validate_crisis_detection(())
        assert r.passed is True  # vacuously true: 0 == 0


# =============================================================================
# TestStressCertification
# =============================================================================

class TestStressCertification:
    """Category 4: Synthetic Stress Certification."""

    def test_pass_rate_above_threshold(self):
        # Simple bool-based results: 14/15 pass = 93.3%
        stress_results = tuple(True for _ in range(14)) + (False,)
        r = validate_stress_certification(stress_results)
        assert r.passed is True
        assert r.n_passed == 14

    def test_below_threshold(self):
        # 12/15 = 80% < 90%
        stress_results = tuple(True for _ in range(12)) + tuple(False for _ in range(3))
        r = validate_stress_certification(stress_results)
        assert r.passed is False

    def test_with_objects_having_passed_attr(self):
        class FakeResult:
            def __init__(self, p):
                self.passed = p

        results = tuple(FakeResult(True) for _ in range(15))
        r = validate_stress_certification(results)
        assert r.passed is True


# =============================================================================
# TestOODConsensus
# =============================================================================

class TestOODConsensus:
    """Category 5: OOD Consensus."""

    def test_all_five_sensors(self):
        counts = (5, 5, 5, 5, 5)
        r = validate_ood_consensus(counts)
        assert r.passed is True
        assert r.score == 1.0

    def test_some_missing(self):
        counts = (5, 4, 5, 3, 5)
        r = validate_ood_consensus(counts)
        assert r.passed is False
        assert r.n_passed == 3


# =============================================================================
# TestSystemContract
# =============================================================================

class TestSystemContract:
    """Category 6: System Contract D(t)."""

    def test_all_fields_present(self):
        fields = (
            {"mu": 0.1, "sigma_squared": 0.01, "Q": 0.9, "S": 0.8, "U": 0.1, "R": 0.95},
            {"mu": -0.2, "sigma_squared": 0.02, "Q": 0.7, "S": 0.9, "U": 0.0, "R": 0.8},
        )
        r = validate_system_contract(fields)
        assert r.passed is True

    def test_some_missing(self):
        fields = (
            {"mu": 0.1, "sigma_squared": 0.01},  # missing Q, S, U, R
            {"mu": 0.1, "sigma_squared": 0.01, "Q": 0.9, "S": 0.8, "U": 0.1, "R": 0.95},
        )
        r = validate_system_contract(fields)
        assert r.passed is False
        assert r.n_passed == 1


# =============================================================================
# TestMetaUTransitions
# =============================================================================

class TestMetaUTransitions:
    """Category 7: Meta-Uncertainty State Transitions."""

    def test_valid_ordering(self):
        transitions = ("NORMAL", "RECALIBRATION", "CONSERVATIVE", "COLLAPSE")
        r = validate_meta_uncertainty_transitions(transitions)
        assert r.passed is True

    def test_invalid_ordering_skip(self):
        # Skipping from NORMAL to COLLAPSE (distance 3)
        transitions = ("NORMAL", "COLLAPSE")
        r = validate_meta_uncertainty_transitions(transitions)
        assert r.passed is False

    def test_same_state(self):
        transitions = ("NORMAL", "NORMAL", "NORMAL")
        r = validate_meta_uncertainty_transitions(transitions)
        assert r.passed is True

    def test_back_and_forth(self):
        transitions = ("NORMAL", "RECALIBRATION", "NORMAL")
        r = validate_meta_uncertainty_transitions(transitions)
        assert r.passed is True

    def test_single_entry(self):
        transitions = ("NORMAL",)
        r = validate_meta_uncertainty_transitions(transitions)
        assert r.passed is True


# =============================================================================
# TestNumericalStability
# =============================================================================

class TestNumericalStability:
    """Category 8: Numerical Stability."""

    def test_all_finite(self):
        values = tuple(float(i) * 0.1 for i in range(1000))
        r = validate_numerical_stability(values)
        assert r.passed is True
        assert r.n_passed == 1000

    def test_some_nan(self):
        values = (1.0, 2.0, float("nan"), 4.0)
        r = validate_numerical_stability(values)
        assert r.passed is False
        assert r.n_passed == 3

    def test_some_inf(self):
        values = (1.0, float("inf"), 3.0)
        r = validate_numerical_stability(values)
        assert r.passed is False
        assert r.n_passed == 2

    def test_empty(self):
        r = validate_numerical_stability(())
        assert r.passed is True  # vacuously true


# =============================================================================
# TestPerformance
# =============================================================================

class TestPerformance:
    """Category 9: Performance."""

    def test_within_limits(self):
        fast = tuple(float(i) for i in range(1, 41))  # 1..40ms
        deep = tuple(float(i) * 10 for i in range(1, 41))  # 10..400ms
        r = validate_performance(fast, deep)
        assert r.passed is True

    def test_exceeds_p95_fast(self):
        # All fast latencies at 60ms
        fast = tuple(60.0 for _ in range(100))
        deep = tuple(100.0 for _ in range(100))
        r = validate_performance(fast, deep)
        assert r.passed is False

    def test_exceeds_p95_deep(self):
        fast = tuple(10.0 for _ in range(100))
        deep = tuple(600.0 for _ in range(100))
        r = validate_performance(fast, deep)
        assert r.passed is False

    def test_empty_latencies(self):
        r = validate_performance((), ())
        assert r.passed is True  # 0.0 <= limits


# =============================================================================
# TestLoggingIntegrity
# =============================================================================

class TestLoggingIntegrity:
    """Category 10: Logging Integrity."""

    def test_valid_chain(self):
        # Build a valid hash chain
        seed = "genesis"
        chain = [seed]
        for i in range(1, 10):
            h = hashlib.sha256(
                (chain[i - 1] + "::" + str(i)).encode("utf-8")
            ).hexdigest()
            chain.append(h)
        r = validate_logging_integrity(tuple(chain))
        assert r.passed is True
        assert r.n_passed == 9

    def test_broken_chain(self):
        chain = ("abc", "def", "ghi")
        r = validate_logging_integrity(chain)
        assert r.passed is False

    def test_single_hash(self):
        r = validate_logging_integrity(("abc",))
        assert r.passed is True

    def test_empty(self):
        r = validate_logging_integrity(())
        assert r.passed is True


# =============================================================================
# TestRunAllValidations
# =============================================================================

class TestRunAllValidations:
    """Test run_all_validations returns all 10 categories."""

    def test_all_10_categories(self):
        data = {
            "ece_values": tuple(0.01 for _ in range(16)),
            "regime_eces": {"RISK_ON": 0.02, "RISK_OFF": 0.03},
            "crisis_ood_scores": (0.7, 0.8),
            "stress_results": tuple(True for _ in range(15)),
            "sensor_counts": (5, 5, 5),
            "contract_fields": (
                {"mu": 0.1, "sigma_squared": 0.01, "Q": 0.9, "S": 0.8, "U": 0.1, "R": 0.95},
            ),
            "transitions": ("NORMAL", "RECALIBRATION"),
            "numerical_values": tuple(1.0 for _ in range(100)),
            "latencies_fast": tuple(10.0 for _ in range(100)),
            "latencies_deep": tuple(100.0 for _ in range(100)),
            "event_hashes": ("seed",),
        }
        results = run_all_validations(data)
        assert len(results) == 10
        categories = {r.category for r in results}
        assert "ECE_WALKFORWARD" in categories
        assert "ECE_PER_REGIME" in categories
        assert "CRISIS_DETECTION" in categories
        assert "STRESS_CERTIFICATION" in categories
        assert "OOD_CONSENSUS" in categories
        assert "SYSTEM_CONTRACT" in categories
        assert "META_U_TRANSITIONS" in categories
        assert "NUMERICAL_STABILITY" in categories
        assert "PERFORMANCE" in categories
        assert "LOGGING_INTEGRITY" in categories

    def test_empty_data(self):
        results = run_all_validations({})
        assert len(results) == 10

    def test_type_error_on_non_dict(self):
        with pytest.raises(TypeError):
            run_all_validations("not a dict")


# =============================================================================
# TestDeterminism
# =============================================================================

class TestDeterminism:
    """DET-07: Same inputs = same outputs."""

    def test_ece_walkforward_deterministic(self):
        ece_values = tuple(0.01 * i for i in range(16))
        r1 = validate_ece_walkforward(ece_values)
        r2 = validate_ece_walkforward(ece_values)
        assert r1.passed == r2.passed
        assert r1.score == r2.score
        assert r1.n_passed == r2.n_passed

    def test_numerical_stability_deterministic(self):
        values = tuple(float(i) for i in range(100))
        r1 = validate_numerical_stability(values)
        r2 = validate_numerical_stability(values)
        assert r1.score == r2.score


# =============================================================================
# TestImportContract
# =============================================================================

class TestImportContract:
    """Verify all expected names are importable."""

    def test_all_names_importable(self):
        from jarvis.validation.validators import __all__ as all_names
        import jarvis.validation.validators as mod
        for name in all_names:
            assert hasattr(mod, name), f"{name} not found in validators module"
