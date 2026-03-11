# =============================================================================
# tests/unit/models/test_uncertainty.py
# Tests for jarvis/models/uncertainty.py (S08 Uncertainty Layer)
# =============================================================================

from __future__ import annotations

import math

import pytest

from jarvis.models.fast_path import Prediction
from jarvis.models.uncertainty import (
    # Constants
    META_U_RECALIBRATION,
    META_U_CONSERVATIVE,
    META_U_COLLAPSE,
    CI_Z_50,
    CI_Z_90,
    CI_Z_95,
    UNCERTAINTY_MAX,
    # Dataclasses
    UncertaintyBreakdown,
    Intervals,
    MetaUncertaintyState,
    # Classes
    UncertaintyLayer,
    MetaUncertaintyEstimator,
    InformationQualityEstimator,
    # Helper functions
    compute_aleatoric,
    compute_epistemic,
)


# =============================================================================
# HELPERS
# =============================================================================

def _make_prediction(mu: float = 0.1, sigma: float = 0.2,
                     confidence: float = 0.7) -> Prediction:
    """Create a Prediction with given values."""
    return Prediction(mu=mu, sigma=sigma, confidence=confidence)


def _make_predictions_varied() -> tuple:
    """Create a tuple of varied predictions for testing."""
    return (
        _make_prediction(mu=0.1, sigma=0.2, confidence=0.7),
        _make_prediction(mu=0.3, sigma=0.1, confidence=0.8),
        _make_prediction(mu=-0.1, sigma=0.3, confidence=0.6),
    )


def _make_predictions_identical() -> tuple:
    """Create a tuple of identical predictions."""
    return (
        _make_prediction(mu=0.5, sigma=0.2, confidence=0.7),
        _make_prediction(mu=0.5, sigma=0.2, confidence=0.7),
        _make_prediction(mu=0.5, sigma=0.2, confidence=0.7),
    )


# =============================================================================
# SECTION 1 -- TestConstants
# =============================================================================

class TestConstants:
    def test_meta_u_recalibration_value(self):
        assert META_U_RECALIBRATION == 0.3

    def test_meta_u_conservative_value(self):
        assert META_U_CONSERVATIVE == 0.5

    def test_meta_u_collapse_value(self):
        assert META_U_COLLAPSE == 0.7

    def test_ci_z_50_value(self):
        assert CI_Z_50 == 0.6745

    def test_ci_z_90_value(self):
        assert CI_Z_90 == 1.6449

    def test_ci_z_95_value(self):
        assert CI_Z_95 == 1.9600

    def test_uncertainty_max_value(self):
        assert UNCERTAINTY_MAX == 0.95

    def test_threshold_ordering(self):
        """Thresholds must be strictly increasing."""
        assert META_U_RECALIBRATION < META_U_CONSERVATIVE < META_U_COLLAPSE

    def test_z_score_ordering(self):
        """Z-scores must be strictly increasing."""
        assert CI_Z_50 < CI_Z_90 < CI_Z_95


# =============================================================================
# SECTION 2 -- TestUncertaintyBreakdown
# =============================================================================

class TestUncertaintyBreakdown:
    def test_frozen(self):
        ub = UncertaintyBreakdown(
            aleatoric=0.1, epistemic_model=0.2, epistemic_data=0.1,
            distributional=0.05, meta=0.0, total=0.3,
        )
        with pytest.raises(AttributeError):
            ub.aleatoric = 0.5

    def test_all_fields_non_negative(self):
        ub = UncertaintyBreakdown(
            aleatoric=0.0, epistemic_model=0.0, epistemic_data=0.0,
            distributional=0.0, meta=0.0, total=0.0,
        )
        assert ub.aleatoric >= 0.0
        assert ub.epistemic_model >= 0.0
        assert ub.epistemic_data >= 0.0
        assert ub.distributional >= 0.0
        assert ub.meta >= 0.0
        assert ub.total >= 0.0

    def test_total_capped_at_uncertainty_max(self):
        with pytest.raises(ValueError, match="total must be <="):
            UncertaintyBreakdown(
                aleatoric=0.1, epistemic_model=0.1, epistemic_data=0.1,
                distributional=0.1, meta=0.1, total=0.96,
            )

    def test_nan_guard_aleatoric(self):
        with pytest.raises(ValueError, match="must be finite"):
            UncertaintyBreakdown(
                aleatoric=float("nan"), epistemic_model=0.1,
                epistemic_data=0.1, distributional=0.0, meta=0.0, total=0.2,
            )

    def test_inf_guard_epistemic(self):
        with pytest.raises(ValueError, match="must be finite"):
            UncertaintyBreakdown(
                aleatoric=0.1, epistemic_model=float("inf"),
                epistemic_data=0.1, distributional=0.0, meta=0.0, total=0.2,
            )

    def test_negative_guard(self):
        with pytest.raises(ValueError, match="must be non-negative"):
            UncertaintyBreakdown(
                aleatoric=-0.1, epistemic_model=0.1,
                epistemic_data=0.1, distributional=0.0, meta=0.0, total=0.2,
            )

    def test_valid_construction(self):
        ub = UncertaintyBreakdown(
            aleatoric=0.2, epistemic_model=0.15, epistemic_data=0.1,
            distributional=0.05, meta=0.1, total=0.5,
        )
        assert ub.aleatoric == 0.2
        assert ub.epistemic_model == 0.15
        assert ub.epistemic_data == 0.1
        assert ub.distributional == 0.05
        assert ub.meta == 0.1
        assert ub.total == 0.5


# =============================================================================
# SECTION 3 -- TestIntervals
# =============================================================================

class TestIntervals:
    def test_frozen(self):
        iv = Intervals(
            ci_50=(0.3, 0.7), ci_90=(0.1, 0.9), ci_95=(0.0, 1.0),
        )
        with pytest.raises(AttributeError):
            iv.ci_50 = (0.0, 1.0)

    def test_ci_50_narrower_than_ci_90(self):
        iv = Intervals(
            ci_50=(0.3, 0.7), ci_90=(0.1, 0.9), ci_95=(0.0, 1.0),
        )
        width_50 = iv.ci_50[1] - iv.ci_50[0]
        width_90 = iv.ci_90[1] - iv.ci_90[0]
        assert width_50 < width_90

    def test_ci_90_narrower_than_ci_95(self):
        iv = Intervals(
            ci_50=(0.3, 0.7), ci_90=(0.1, 0.9), ci_95=(0.0, 1.0),
        )
        width_90 = iv.ci_90[1] - iv.ci_90[0]
        width_95 = iv.ci_95[1] - iv.ci_95[0]
        assert width_90 < width_95

    def test_symmetric_around_mu(self):
        mu = 0.5
        sigma = 0.2
        layer = UncertaintyLayer()
        iv = layer.compute_intervals(mu, sigma)
        # Check symmetry: mu - lower == upper - mu
        for ci in [iv.ci_50, iv.ci_90, iv.ci_95]:
            assert abs((mu - ci[0]) - (ci[1] - mu)) < 1e-10

    def test_invalid_ci_lower_greater_than_upper(self):
        with pytest.raises(ValueError, match="lower must be <= upper"):
            Intervals(
                ci_50=(0.7, 0.3), ci_90=(0.1, 0.9), ci_95=(0.0, 1.0),
            )

    def test_nan_in_ci(self):
        with pytest.raises(ValueError, match="must be finite"):
            Intervals(
                ci_50=(float("nan"), 0.7), ci_90=(0.1, 0.9),
                ci_95=(0.0, 1.0),
            )

    def test_invalid_type_ci(self):
        with pytest.raises(TypeError, match="must be a 2-tuple"):
            Intervals(
                ci_50=[0.3, 0.7], ci_90=(0.1, 0.9), ci_95=(0.0, 1.0),
            )


# =============================================================================
# SECTION 4 -- TestMetaUncertaintyState
# =============================================================================

class TestMetaUncertaintyState:
    def test_frozen(self):
        ms = MetaUncertaintyState(U=0.1, state="NORMAL",
                                   triggered_threshold=0.0)
        with pytest.raises(AttributeError):
            ms.U = 0.5

    def test_valid_states(self):
        for state in ("NORMAL", "RECALIBRATION", "CONSERVATIVE", "COLLAPSE"):
            ms = MetaUncertaintyState(U=0.1, state=state,
                                       triggered_threshold=0.0)
            assert ms.state == state

    def test_invalid_state(self):
        with pytest.raises(ValueError, match="must be one of"):
            MetaUncertaintyState(U=0.1, state="INVALID",
                                  triggered_threshold=0.0)

    def test_u_out_of_range(self):
        with pytest.raises(ValueError, match="must be in \\[0, 1\\]"):
            MetaUncertaintyState(U=1.5, state="NORMAL",
                                  triggered_threshold=0.0)

    def test_threshold_tracking(self):
        ms = MetaUncertaintyState(U=0.6, state="CONSERVATIVE",
                                   triggered_threshold=META_U_CONSERVATIVE)
        assert ms.triggered_threshold == META_U_CONSERVATIVE


# =============================================================================
# SECTION 5 -- TestComputeAleatoric
# =============================================================================

class TestComputeAleatoric:
    def test_mean_of_sigmas(self):
        preds = (
            _make_prediction(sigma=0.2),
            _make_prediction(sigma=0.4),
            _make_prediction(sigma=0.6),
        )
        result = compute_aleatoric(preds)
        expected = (0.2 + 0.4 + 0.6) / 3.0
        assert abs(result - expected) < 1e-10

    def test_empty_input_returns_zero(self):
        assert compute_aleatoric(()) == 0.0

    def test_single_prediction(self):
        preds = (_make_prediction(sigma=0.3),)
        assert abs(compute_aleatoric(preds) - 0.3) < 1e-10


# =============================================================================
# SECTION 6 -- TestComputeEpistemic
# =============================================================================

class TestComputeEpistemic:
    def test_std_of_mus(self):
        preds = (
            _make_prediction(mu=0.1),
            _make_prediction(mu=0.3),
            _make_prediction(mu=0.5),
        )
        result = compute_epistemic(preds)
        mean_mu = (0.1 + 0.3 + 0.5) / 3.0
        var = ((0.1 - mean_mu) ** 2 + (0.3 - mean_mu) ** 2
               + (0.5 - mean_mu) ** 2) / 3.0
        expected = math.sqrt(var)
        assert abs(result - expected) < 1e-10

    def test_empty_returns_zero(self):
        assert compute_epistemic(()) == 0.0

    def test_single_returns_zero(self):
        preds = (_make_prediction(mu=0.5),)
        assert compute_epistemic(preds) == 0.0

    def test_identical_predictions_returns_zero(self):
        preds = _make_predictions_identical()
        assert compute_epistemic(preds) == 0.0


# =============================================================================
# SECTION 7 -- TestUncertaintyLayer
# =============================================================================

class TestUncertaintyLayer:
    def test_decompose_basic(self):
        layer = UncertaintyLayer()
        preds = _make_predictions_varied()
        bd = layer.decompose(preds)
        assert bd.aleatoric >= 0.0
        assert bd.epistemic_model >= 0.0
        assert bd.epistemic_data == 0.0  # default
        assert bd.distributional == 0.0  # default
        assert bd.meta == 0.0
        assert 0.0 <= bd.total <= UNCERTAINTY_MAX

    def test_decompose_with_drift(self):
        layer = UncertaintyLayer()
        preds = _make_predictions_varied()
        bd = layer.decompose(preds, data_drift=0.3)
        assert bd.epistemic_data == 0.3

    def test_decompose_with_shift(self):
        layer = UncertaintyLayer()
        preds = _make_predictions_varied()
        bd = layer.decompose(preds, distributional_shift=0.4)
        assert bd.distributional == 0.4

    def test_total_capped(self):
        layer = UncertaintyLayer()
        # Create predictions with high sigma spread to push total high
        preds = (
            _make_prediction(mu=-1.0, sigma=0.9),
            _make_prediction(mu=1.0, sigma=0.9),
        )
        bd = layer.decompose(preds, data_drift=0.9, distributional_shift=0.9)
        assert bd.total <= UNCERTAINTY_MAX

    def test_compute_intervals_symmetric(self):
        layer = UncertaintyLayer()
        iv = layer.compute_intervals(mu=0.5, sigma=0.1)
        # Each interval should be symmetric around mu
        for ci in [iv.ci_50, iv.ci_90, iv.ci_95]:
            center = (ci[0] + ci[1]) / 2.0
            assert abs(center - 0.5) < 1e-10

    def test_intervals_ordering(self):
        layer = UncertaintyLayer()
        iv = layer.compute_intervals(mu=0.0, sigma=0.3)
        w50 = iv.ci_50[1] - iv.ci_50[0]
        w90 = iv.ci_90[1] - iv.ci_90[0]
        w95 = iv.ci_95[1] - iv.ci_95[0]
        assert w50 < w90 < w95

    def test_intervals_zero_sigma(self):
        layer = UncertaintyLayer()
        iv = layer.compute_intervals(mu=1.0, sigma=0.0)
        assert iv.ci_50 == (1.0, 1.0)
        assert iv.ci_90 == (1.0, 1.0)
        assert iv.ci_95 == (1.0, 1.0)

    def test_intervals_values(self):
        layer = UncertaintyLayer()
        mu, sigma = 0.0, 1.0
        iv = layer.compute_intervals(mu, sigma)
        assert abs(iv.ci_50[0] - (-CI_Z_50)) < 1e-10
        assert abs(iv.ci_50[1] - CI_Z_50) < 1e-10
        assert abs(iv.ci_90[0] - (-CI_Z_90)) < 1e-10
        assert abs(iv.ci_90[1] - CI_Z_90) < 1e-10
        assert abs(iv.ci_95[0] - (-CI_Z_95)) < 1e-10
        assert abs(iv.ci_95[1] - CI_Z_95) < 1e-10

    def test_decompose_empty_predictions(self):
        layer = UncertaintyLayer()
        bd = layer.decompose(())
        assert bd.aleatoric == 0.0
        assert bd.epistemic_model == 0.0
        assert bd.total == 0.0

    def test_decompose_single_prediction(self):
        layer = UncertaintyLayer()
        preds = (_make_prediction(mu=0.5, sigma=0.2),)
        bd = layer.decompose(preds)
        assert bd.aleatoric == pytest.approx(0.2, abs=1e-10)
        assert bd.epistemic_model == 0.0  # single prediction, no disagreement

    def test_decompose_type_error_not_tuple(self):
        layer = UncertaintyLayer()
        with pytest.raises(TypeError, match="predictions must be a tuple"):
            layer.decompose([_make_prediction()])

    def test_intervals_nan_mu(self):
        layer = UncertaintyLayer()
        with pytest.raises(ValueError, match="mu must be finite"):
            layer.compute_intervals(mu=float("nan"), sigma=0.1)

    def test_intervals_negative_sigma(self):
        layer = UncertaintyLayer()
        with pytest.raises(ValueError, match="sigma must be non-negative"):
            layer.compute_intervals(mu=0.0, sigma=-0.1)


# =============================================================================
# SECTION 8 -- TestMetaUncertaintyEstimator
# =============================================================================

class TestMetaUncertaintyEstimator:
    def test_normal_state(self):
        est = MetaUncertaintyEstimator()
        result = est.estimate(calibration_error=0.05, stability=0.95)
        assert result.state == "NORMAL"
        assert result.triggered_threshold == 0.0

    def test_recalibration_state(self):
        est = MetaUncertaintyEstimator()
        # U = sqrt(0.3^2 + (1-0.95)^2) = sqrt(0.09 + 0.0025) ~ 0.304
        result = est.estimate(calibration_error=0.3, stability=0.95)
        assert result.state == "RECALIBRATION"
        assert result.triggered_threshold == META_U_RECALIBRATION

    def test_conservative_state(self):
        est = MetaUncertaintyEstimator()
        # U = sqrt(0.4^2 + (1-0.7)^2) = sqrt(0.16+0.09) = 0.5
        # 0.5 <= 0.5, so boundary => still at CONSERVATIVE? No, > 0.3 and <= 0.5
        # Actually 0.5 is NOT > 0.5 so it's RECALIBRATION.
        # Use higher values:
        # U = sqrt(0.5^2 + (1-0.8)^2) = sqrt(0.25+0.04) = sqrt(0.29) ~ 0.539
        result = est.estimate(calibration_error=0.5, stability=0.8)
        assert result.state == "CONSERVATIVE"
        assert result.triggered_threshold == META_U_CONSERVATIVE

    def test_collapse_state(self):
        est = MetaUncertaintyEstimator()
        # U = sqrt(0.7^2 + (1-0.3)^2) = sqrt(0.49+0.49) = sqrt(0.98) ~ 0.99
        result = est.estimate(calibration_error=0.7, stability=0.3)
        assert result.state == "COLLAPSE"
        assert result.triggered_threshold == META_U_COLLAPSE

    def test_boundary_at_recalibration(self):
        est = MetaUncertaintyEstimator()
        # U exactly at META_U_RECALIBRATION = 0.3 should be NORMAL
        # U = sqrt(0.3^2 + 0^2) = 0.3, need stability = 1.0
        result = est.estimate(calibration_error=0.3, stability=1.0)
        assert result.U == pytest.approx(0.3)
        assert result.state == "NORMAL"

    def test_just_above_recalibration(self):
        est = MetaUncertaintyEstimator()
        # U = sqrt(0.3^2 + 0.05^2) = sqrt(0.09 + 0.0025) ~ 0.3035
        result = est.estimate(calibration_error=0.3, stability=0.95)
        assert result.U > META_U_RECALIBRATION
        assert result.state == "RECALIBRATION"

    def test_u_clamped_to_01(self):
        est = MetaUncertaintyEstimator()
        # Maximum: calibration_error=1.0, stability=0.0
        # U = sqrt(1 + 1) = sqrt(2) ~ 1.414, clamped to 1.0
        result = est.estimate(calibration_error=1.0, stability=0.0)
        assert result.U == 1.0

    def test_zero_inputs_normal(self):
        est = MetaUncertaintyEstimator()
        # U = sqrt(0 + 1) = 1.0 → COLLAPSE
        # Actually stability=0 means instability=1
        result = est.estimate(calibration_error=0.0, stability=0.0)
        assert result.U == 1.0
        assert result.state == "COLLAPSE"

    def test_perfect_inputs_normal(self):
        est = MetaUncertaintyEstimator()
        result = est.estimate(calibration_error=0.0, stability=1.0)
        assert result.U == 0.0
        assert result.state == "NORMAL"

    def test_nan_calibration_error(self):
        est = MetaUncertaintyEstimator()
        with pytest.raises(ValueError, match="calibration_error must be finite"):
            est.estimate(calibration_error=float("nan"), stability=0.9)

    def test_inf_stability(self):
        est = MetaUncertaintyEstimator()
        with pytest.raises(ValueError, match="stability must be finite"):
            est.estimate(calibration_error=0.1, stability=float("inf"))


# =============================================================================
# SECTION 9 -- TestInformationQualityEstimator
# =============================================================================

class TestInformationQualityEstimator:
    def test_perfect_quality(self):
        est = InformationQualityEstimator()
        assert est.compute_quality(1.0, 1.0, 1.0) == 1.0

    def test_zero_quality(self):
        est = InformationQualityEstimator()
        assert est.compute_quality(0.0, 0.0, 0.0) == 0.0

    def test_mixed_quality(self):
        est = InformationQualityEstimator()
        result = est.compute_quality(0.6, 0.8, 0.4)
        expected = (0.6 + 0.8 + 0.4) / 3.0
        assert abs(result - expected) < 1e-10

    def test_clipping_above_one(self):
        est = InformationQualityEstimator()
        # Values > 1 should be clipped to 1.0
        result = est.compute_quality(1.5, 2.0, 1.0)
        assert result == 1.0

    def test_clipping_below_zero(self):
        est = InformationQualityEstimator()
        # Negative values clipped to 0.0
        result = est.compute_quality(-0.5, -1.0, 0.0)
        assert result == 0.0

    def test_nan_input(self):
        est = InformationQualityEstimator()
        with pytest.raises(ValueError, match="must be finite"):
            est.compute_quality(float("nan"), 0.5, 0.5)

    def test_feature_weights_normalization(self):
        est = InformationQualityEstimator()
        weights = est.compute_feature_weights(
            {"momentum": 0.3, "vol": 0.7}
        )
        total = sum(weights.values())
        assert abs(total - 1.0) < 1e-10

    def test_feature_weights_proportional(self):
        est = InformationQualityEstimator()
        weights = est.compute_feature_weights(
            {"a": 1.0, "b": 3.0}
        )
        assert abs(weights["a"] - 0.25) < 1e-10
        assert abs(weights["b"] - 0.75) < 1e-10

    def test_feature_weights_crisis_uniform(self):
        est = InformationQualityEstimator()
        weights = est.compute_feature_weights(
            {"a": 0.1, "b": 0.9, "c": 0.5}, regime="CRISIS"
        )
        expected = 1.0 / 3.0
        for v in weights.values():
            assert abs(v - expected) < 1e-10

    def test_feature_weights_empty_dict(self):
        est = InformationQualityEstimator()
        weights = est.compute_feature_weights({})
        assert weights == {}

    def test_feature_weights_all_zero(self):
        est = InformationQualityEstimator()
        weights = est.compute_feature_weights({"a": 0.0, "b": 0.0})
        # Uniform fallback
        assert abs(weights["a"] - 0.5) < 1e-10
        assert abs(weights["b"] - 0.5) < 1e-10

    def test_feature_weights_type_error(self):
        est = InformationQualityEstimator()
        with pytest.raises(TypeError, match="must be a dict"):
            est.compute_feature_weights([1, 2, 3])


# =============================================================================
# SECTION 10 -- TestNumericalSafety
# =============================================================================

class TestNumericalSafety:
    def test_decompose_nan_drift(self):
        layer = UncertaintyLayer()
        with pytest.raises(ValueError, match="data_drift must be finite"):
            layer.decompose((), data_drift=float("nan"))

    def test_decompose_inf_shift(self):
        layer = UncertaintyLayer()
        with pytest.raises(ValueError, match="distributional_shift must be finite"):
            layer.decompose((), distributional_shift=float("inf"))

    def test_intervals_inf_sigma(self):
        layer = UncertaintyLayer()
        with pytest.raises(ValueError, match="sigma must be finite"):
            layer.compute_intervals(mu=0.0, sigma=float("inf"))

    def test_breakdown_negative_inf(self):
        with pytest.raises(ValueError, match="must be finite"):
            UncertaintyBreakdown(
                aleatoric=float("-inf"), epistemic_model=0.0,
                epistemic_data=0.0, distributional=0.0, meta=0.0, total=0.0,
            )

    def test_extreme_values_clamped(self):
        """Large drift/shift values clamped to [0,1]."""
        layer = UncertaintyLayer()
        bd = layer.decompose((), data_drift=5.0, distributional_shift=10.0)
        assert bd.epistemic_data == 1.0
        assert bd.distributional == 1.0

    def test_negative_drift_clamped(self):
        layer = UncertaintyLayer()
        bd = layer.decompose((), data_drift=-0.5)
        assert bd.epistemic_data == 0.0


# =============================================================================
# SECTION 11 -- TestDeterminism
# =============================================================================

class TestDeterminism:
    def test_same_inputs_identical_decompose(self):
        layer1 = UncertaintyLayer()
        layer2 = UncertaintyLayer()
        preds = _make_predictions_varied()
        bd1 = layer1.decompose(preds, data_drift=0.2,
                               distributional_shift=0.1)
        bd2 = layer2.decompose(preds, data_drift=0.2,
                               distributional_shift=0.1)
        assert bd1.aleatoric == bd2.aleatoric
        assert bd1.epistemic_model == bd2.epistemic_model
        assert bd1.total == bd2.total

    def test_same_inputs_identical_intervals(self):
        layer1 = UncertaintyLayer()
        layer2 = UncertaintyLayer()
        iv1 = layer1.compute_intervals(mu=0.5, sigma=0.3)
        iv2 = layer2.compute_intervals(mu=0.5, sigma=0.3)
        assert iv1.ci_50 == iv2.ci_50
        assert iv1.ci_90 == iv2.ci_90
        assert iv1.ci_95 == iv2.ci_95

    def test_fresh_instances_same_result(self):
        preds = _make_predictions_varied()
        results = []
        for _ in range(3):
            layer = UncertaintyLayer()
            bd = layer.decompose(preds, data_drift=0.1)
            results.append(bd.total)
        assert results[0] == results[1] == results[2]

    def test_meta_estimator_deterministic(self):
        est1 = MetaUncertaintyEstimator()
        est2 = MetaUncertaintyEstimator()
        r1 = est1.estimate(calibration_error=0.2, stability=0.8)
        r2 = est2.estimate(calibration_error=0.2, stability=0.8)
        assert r1.U == r2.U
        assert r1.state == r2.state


# =============================================================================
# SECTION 12 -- TestImportContract
# =============================================================================

class TestImportContract:
    def test_all_symbols_importable(self):
        import jarvis.models.uncertainty as mod
        for name in mod.__all__:
            assert hasattr(mod, name), f"Missing __all__ symbol: {name}"

    def test_all_list_complete(self):
        """All public classes and functions should be in __all__."""
        import jarvis.models.uncertainty as mod
        expected = {
            "META_U_RECALIBRATION", "META_U_CONSERVATIVE", "META_U_COLLAPSE",
            "CI_Z_50", "CI_Z_90", "CI_Z_95", "UNCERTAINTY_MAX",
            "UncertaintyBreakdown", "Intervals", "MetaUncertaintyState",
            "UncertaintyLayer", "MetaUncertaintyEstimator",
            "InformationQualityEstimator",
            "compute_aleatoric", "compute_epistemic",
        }
        assert set(mod.__all__) == expected


# =============================================================================
# SECTION 13 -- TestEdgeCases
# =============================================================================

class TestEdgeCases:
    def test_empty_predictions_decompose(self):
        layer = UncertaintyLayer()
        bd = layer.decompose(())
        assert bd.aleatoric == 0.0
        assert bd.epistemic_model == 0.0
        assert bd.total == 0.0

    def test_single_prediction_no_epistemic(self):
        layer = UncertaintyLayer()
        preds = (_make_prediction(mu=0.5, sigma=0.1),)
        bd = layer.decompose(preds)
        assert bd.epistemic_model == 0.0
        # Aleatoric should equal single sigma
        assert bd.aleatoric == pytest.approx(0.1, abs=1e-10)

    def test_all_same_predictions(self):
        layer = UncertaintyLayer()
        preds = _make_predictions_identical()
        bd = layer.decompose(preds)
        assert bd.epistemic_model == 0.0
        # All same sigma=0.2, so aleatoric=0.2
        assert bd.aleatoric == pytest.approx(0.2, abs=1e-10)

    def test_zero_sigma_intervals(self):
        layer = UncertaintyLayer()
        iv = layer.compute_intervals(mu=0.0, sigma=0.0)
        assert iv.ci_50 == (0.0, 0.0)
        assert iv.ci_90 == (0.0, 0.0)
        assert iv.ci_95 == (0.0, 0.0)

    def test_large_sigma_intervals(self):
        layer = UncertaintyLayer()
        iv = layer.compute_intervals(mu=0.0, sigma=100.0)
        # Intervals should be very wide
        assert iv.ci_95[1] - iv.ci_95[0] > 100.0

    def test_negative_mu_intervals(self):
        layer = UncertaintyLayer()
        iv = layer.compute_intervals(mu=-5.0, sigma=1.0)
        # Center should be at -5
        center = (iv.ci_50[0] + iv.ci_50[1]) / 2.0
        assert abs(center - (-5.0)) < 1e-10

    def test_information_quality_negative_inputs_clamped(self):
        est = InformationQualityEstimator()
        result = est.compute_quality(-1.0, -1.0, -1.0)
        assert result == 0.0

    def test_meta_uncertainty_negative_calibration_clamped(self):
        est = MetaUncertaintyEstimator()
        result = est.estimate(calibration_error=-0.5, stability=1.0)
        # Clamped to 0.0, so U = sqrt(0 + 0) = 0.0
        assert result.U == 0.0
        assert result.state == "NORMAL"

    def test_meta_uncertainty_stability_above_one_clamped(self):
        est = MetaUncertaintyEstimator()
        result = est.estimate(calibration_error=0.0, stability=1.5)
        # stability clamped to 1.0, U = sqrt(0 + 0) = 0.0
        assert result.U == 0.0
        assert result.state == "NORMAL"

    def test_feature_weights_non_finite_importance(self):
        est = InformationQualityEstimator()
        weights = est.compute_feature_weights(
            {"a": float("nan"), "b": 1.0}
        )
        # NaN treated as 0.0, so a=0.0, b=1.0 → a=0.0, b=1.0
        assert weights["a"] == 0.0
        assert weights["b"] == 1.0

    def test_feature_weights_negative_importance(self):
        est = InformationQualityEstimator()
        weights = est.compute_feature_weights(
            {"a": -0.5, "b": 1.0}
        )
        # Negative clamped to 0.0
        assert weights["a"] == 0.0
        assert weights["b"] == 1.0
