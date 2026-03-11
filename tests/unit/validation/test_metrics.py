# =============================================================================
# tests/unit/validation/test_metrics.py — Unit tests for S15 validation metrics
#
# 20+ tests for ValidationMetrics, VetoResult, and check_veto_criteria.
# Self-contained — uses only synthetic data.
# =============================================================================

import math

import pytest

from jarvis.validation.metrics import (
    ValidationMetrics,
    VetoResult,
    VETO_ECE_THRESHOLD,
    VETO_ECE_DRIFT_THRESHOLD,
    VETO_CALIBRATION_STABILITY,
    VETO_OOD_RECALL,
    VETO_REGIME_DETECTION,
    VETO_FAST_P95_MS,
    VETO_DEEP_P95_MS,
    check_veto_criteria,
)


# =============================================================================
# Helper: build a default passing metrics
# =============================================================================

def _make_metrics(**overrides) -> ValidationMetrics:
    """Create a ValidationMetrics with all-passing defaults, then apply overrides."""
    defaults = dict(
        ece_mean=0.02,
        ece_max=0.04,
        ece_pass_rate=0.95,
        ece_regime_drift=0.01,
        calibration_stability_std=0.01,
        ood_recall=0.95,
        regime_detection_rate=0.98,
        numerical_stability=True,
        performance_fast_p95_ms=30.0,
        performance_deep_p95_ms=300.0,
    )
    defaults.update(overrides)
    return ValidationMetrics(**defaults)


# =============================================================================
# TestValidationMetrics
# =============================================================================

class TestValidationMetrics:
    """Tests for the ValidationMetrics frozen dataclass."""

    def test_frozen(self):
        m = _make_metrics()
        with pytest.raises(AttributeError):
            m.ece_mean = 0.1

    def test_all_fields(self):
        m = _make_metrics()
        assert m.ece_mean == 0.02
        assert m.ece_max == 0.04
        assert m.ece_pass_rate == 0.95
        assert m.ece_regime_drift == 0.01
        assert m.calibration_stability_std == 0.01
        assert m.ood_recall == 0.95
        assert m.regime_detection_rate == 0.98
        assert m.numerical_stability is True
        assert m.performance_fast_p95_ms == 30.0
        assert m.performance_deep_p95_ms == 300.0

    def test_nan_raises(self):
        with pytest.raises(ValueError):
            _make_metrics(ece_mean=float("nan"))

    def test_inf_raises(self):
        with pytest.raises(ValueError):
            _make_metrics(performance_fast_p95_ms=float("inf"))

    def test_non_numeric_raises(self):
        with pytest.raises(TypeError):
            _make_metrics(ece_mean="not_a_number")

    def test_numerical_stability_must_be_bool(self):
        with pytest.raises(TypeError):
            _make_metrics(numerical_stability=1)


# =============================================================================
# TestVetoResult
# =============================================================================

class TestVetoResult:
    """Tests for the VetoResult frozen dataclass."""

    def test_frozen(self):
        m = _make_metrics()
        v = VetoResult(passed=True, failures=(), metrics=m)
        with pytest.raises(AttributeError):
            v.passed = False

    def test_passed_and_failures(self):
        m = _make_metrics()
        v = VetoResult(passed=True, failures=(), metrics=m)
        assert v.passed is True
        assert v.failures == ()

    def test_failed_with_failures(self):
        m = _make_metrics(ece_mean=0.1)
        v = VetoResult(passed=False, failures=("ece_mean",), metrics=m)
        assert v.passed is False
        assert "ece_mean" in v.failures

    def test_type_errors(self):
        m = _make_metrics()
        with pytest.raises(TypeError):
            VetoResult(passed="yes", failures=(), metrics=m)
        with pytest.raises(TypeError):
            VetoResult(passed=True, failures=[], metrics=m)
        with pytest.raises(TypeError):
            VetoResult(passed=True, failures=(), metrics="not_metrics")


# =============================================================================
# TestVetoConstants
# =============================================================================

class TestVetoConstants:
    """Verify all threshold values match FAS specification."""

    def test_ece_threshold(self):
        assert VETO_ECE_THRESHOLD == 0.05

    def test_ece_drift_threshold(self):
        assert VETO_ECE_DRIFT_THRESHOLD == 0.02

    def test_calibration_stability(self):
        assert VETO_CALIBRATION_STABILITY == 0.02

    def test_ood_recall(self):
        assert VETO_OOD_RECALL == 0.90

    def test_regime_detection(self):
        assert VETO_REGIME_DETECTION == 0.95

    def test_fast_p95(self):
        assert VETO_FAST_P95_MS == 50.0

    def test_deep_p95(self):
        assert VETO_DEEP_P95_MS == 500.0


# =============================================================================
# TestCheckVetoCriteria
# =============================================================================

class TestCheckVetoCriteria:
    """Tests for check_veto_criteria()."""

    def test_all_pass(self):
        m = _make_metrics()
        v = check_veto_criteria(m)
        assert v.passed is True
        assert v.failures == ()
        assert v.metrics is m

    def test_ece_fails(self):
        m = _make_metrics(ece_mean=0.06)
        v = check_veto_criteria(m)
        assert v.passed is False
        assert "ece_mean" in v.failures

    def test_ece_drift_fails(self):
        m = _make_metrics(ece_regime_drift=0.03)
        v = check_veto_criteria(m)
        assert v.passed is False
        assert "ece_regime_drift" in v.failures

    def test_calibration_stability_fails(self):
        m = _make_metrics(calibration_stability_std=0.03)
        v = check_veto_criteria(m)
        assert v.passed is False
        assert "calibration_stability_std" in v.failures

    def test_ood_recall_fails(self):
        m = _make_metrics(ood_recall=0.80)
        v = check_veto_criteria(m)
        assert v.passed is False
        assert "ood_recall" in v.failures

    def test_regime_detection_fails(self):
        m = _make_metrics(regime_detection_rate=0.90)
        v = check_veto_criteria(m)
        assert v.passed is False
        assert "regime_detection_rate" in v.failures

    def test_numerical_stability_fails(self):
        m = _make_metrics(numerical_stability=False)
        v = check_veto_criteria(m)
        assert v.passed is False
        assert "numerical_stability" in v.failures

    def test_fast_performance_fails(self):
        m = _make_metrics(performance_fast_p95_ms=55.0)
        v = check_veto_criteria(m)
        assert v.passed is False
        assert "performance_fast_p95_ms" in v.failures

    def test_deep_performance_fails(self):
        m = _make_metrics(performance_deep_p95_ms=550.0)
        v = check_veto_criteria(m)
        assert v.passed is False
        assert "performance_deep_p95_ms" in v.failures

    def test_multiple_failures(self):
        m = _make_metrics(
            ece_mean=0.10,
            ood_recall=0.50,
            numerical_stability=False,
        )
        v = check_veto_criteria(m)
        assert v.passed is False
        assert len(v.failures) == 3
        assert "ece_mean" in v.failures
        assert "ood_recall" in v.failures
        assert "numerical_stability" in v.failures

    def test_boundary_ece_exact(self):
        # ece_mean == 0.05 is NOT < 0.05, so it fails
        m = _make_metrics(ece_mean=0.05)
        v = check_veto_criteria(m)
        assert v.passed is False
        assert "ece_mean" in v.failures

    def test_boundary_ece_just_below(self):
        m = _make_metrics(ece_mean=0.0499)
        v = check_veto_criteria(m)
        assert "ece_mean" not in v.failures

    def test_boundary_ood_recall_exact(self):
        # ood_recall == 0.90 is >= 0.90, so it passes
        m = _make_metrics(ood_recall=0.90)
        v = check_veto_criteria(m)
        assert "ood_recall" not in v.failures

    def test_boundary_drift_exact(self):
        # ece_regime_drift == 0.02 is <= 0.02, so it passes
        m = _make_metrics(ece_regime_drift=0.02)
        v = check_veto_criteria(m)
        assert "ece_regime_drift" not in v.failures

    def test_boundary_fast_p95_exact(self):
        # performance_fast_p95_ms == 50.0 is <= 50.0, so it passes
        m = _make_metrics(performance_fast_p95_ms=50.0)
        v = check_veto_criteria(m)
        assert "performance_fast_p95_ms" not in v.failures

    def test_type_error_on_non_metrics(self):
        with pytest.raises(TypeError):
            check_veto_criteria("not_metrics")


# =============================================================================
# TestDeterminism
# =============================================================================

class TestDeterminism:
    """DET-07: Same inputs = same outputs."""

    def test_veto_deterministic(self):
        m = _make_metrics(ece_mean=0.06, ood_recall=0.80)
        v1 = check_veto_criteria(m)
        v2 = check_veto_criteria(m)
        assert v1.passed == v2.passed
        assert v1.failures == v2.failures


# =============================================================================
# TestImportContract
# =============================================================================

class TestImportContract:
    """Verify all expected names are importable."""

    def test_all_names_importable(self):
        from jarvis.validation.metrics import __all__ as all_names
        import jarvis.validation.metrics as mod
        for name in all_names:
            assert hasattr(mod, name), f"{name} not found in metrics module"
