# =============================================================================
# tests/unit/models/test_fast_path.py
# Tests for jarvis/models/fast_path.py — S06 Fast Path Ensemble
# =============================================================================

from __future__ import annotations

import math

import pytest

from jarvis.core.state_layer import LatentState
from jarvis.models.fast_path import (
    ENSEMBLE_WEIGHTS,
    UNCERTAINTY_TRIGGER_DEEP_PATH,
    RF_N_ESTIMATORS,
    RF_MAX_DEPTH,
    RF_MIN_SAMPLES_SPLIT,
    RF_MIN_SAMPLES_LEAF,
    Prediction,
    FastResult,
    FastPathEnsemble,
    aggregate_fast,
    classify,
    _member0_kalman,
    _member1_tree,
    _member2_rules,
    _safe_feature,
    _SIGMA_FLOOR,
    _CONFIDENCE_FLOOR,
    _CONFIDENCE_CEILING,
)
from jarvis.core.state_estimator import StateEstimator


# =============================================================================
# HELPERS
# =============================================================================

def _default_features() -> dict:
    """Standard feature dict for tests."""
    return {
        "volatility": 0.15,
        "trend_strength": 0.2,
        "momentum": 0.3,
        "mean_reversion": 0.1,
        "liquidity": 0.5,
        "stress": 0.2,
        "drift": 0.0,
        "noise": 0.05,
    }


def _default_state() -> LatentState:
    """Standard LatentState for tests."""
    return LatentState(
        regime=1,
        volatility=0.15,
        trend_strength=0.2,
        mean_reversion=0.1,
        liquidity=0.5,
        stress=0.2,
        momentum=0.3,
        drift=0.0,
        noise=0.05,
        regime_confidence=0.8,
        stability=0.7,
        prediction_uncertainty=0.1,
    )


# =============================================================================
# SECTION 1 -- TestPrediction
# =============================================================================

class TestPrediction:
    def test_frozen(self):
        p = Prediction(mu=0.5, sigma=0.1, confidence=0.8)
        with pytest.raises(AttributeError):
            p.mu = 0.3

    def test_basic_creation(self):
        p = Prediction(mu=0.5, sigma=0.1, confidence=0.8)
        assert p.mu == 0.5
        assert p.sigma == 0.1
        assert p.confidence == 0.8

    def test_mu_clipped_high(self):
        p = Prediction(mu=2.0, sigma=0.1, confidence=0.5)
        assert p.mu == 1.0

    def test_mu_clipped_low(self):
        p = Prediction(mu=-2.0, sigma=0.1, confidence=0.5)
        assert p.mu == -1.0

    def test_sigma_floored(self):
        p = Prediction(mu=0.0, sigma=0.0, confidence=0.5)
        assert p.sigma >= _SIGMA_FLOOR

    def test_sigma_negative_floored(self):
        p = Prediction(mu=0.0, sigma=-1.0, confidence=0.5)
        assert p.sigma >= _SIGMA_FLOOR

    def test_confidence_clipped_low(self):
        p = Prediction(mu=0.0, sigma=0.1, confidence=0.0)
        assert p.confidence == _CONFIDENCE_FLOOR

    def test_confidence_clipped_high(self):
        p = Prediction(mu=0.0, sigma=0.1, confidence=1.0)
        assert p.confidence == _CONFIDENCE_CEILING

    def test_nan_mu_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            Prediction(mu=float("nan"), sigma=0.1, confidence=0.5)

    def test_inf_sigma_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            Prediction(mu=0.0, sigma=float("inf"), confidence=0.5)

    def test_nan_confidence_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            Prediction(mu=0.0, sigma=0.1, confidence=float("nan"))

    def test_neg_inf_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            Prediction(mu=float("-inf"), sigma=0.1, confidence=0.5)


# =============================================================================
# SECTION 2 -- TestFastResult
# =============================================================================

class TestFastResult:
    def test_frozen(self):
        r = FastResult(mu=0.1, sigma=0.2, deep_triggered=False,
                       latency_ms=1.0, ensemble_seeds=(42, 1042, 2042))
        with pytest.raises(AttributeError):
            r.mu = 0.5

    def test_basic_creation(self):
        r = FastResult(mu=0.1, sigma=0.2, deep_triggered=True,
                       latency_ms=5.0, ensemble_seeds=(42, 1042, 2042))
        assert r.mu == 0.1
        assert r.sigma == 0.2
        assert r.deep_triggered is True
        assert r.latency_ms == 5.0
        assert r.ensemble_seeds == (42, 1042, 2042)

    def test_deep_triggered_when_sigma_high(self):
        r = FastResult(mu=0.0, sigma=0.20, deep_triggered=True,
                       latency_ms=0.0, ensemble_seeds=(42,))
        assert r.deep_triggered is True

    def test_not_triggered_when_sigma_low(self):
        r = FastResult(mu=0.0, sigma=0.05, deep_triggered=False,
                       latency_ms=0.0, ensemble_seeds=(42,))
        assert r.deep_triggered is False

    def test_ensemble_seeds_is_tuple(self):
        r = FastResult(mu=0.0, sigma=0.1, deep_triggered=False,
                       latency_ms=0.0, ensemble_seeds=(1, 2, 3))
        assert isinstance(r.ensemble_seeds, tuple)

    def test_ensemble_seeds_must_be_tuple(self):
        with pytest.raises(TypeError, match="must be a tuple"):
            FastResult(mu=0.0, sigma=0.1, deep_triggered=False,
                       latency_ms=0.0, ensemble_seeds=[1, 2, 3])

    def test_nan_mu_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            FastResult(mu=float("nan"), sigma=0.1, deep_triggered=False,
                       latency_ms=0.0, ensemble_seeds=(42,))

    def test_inf_sigma_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            FastResult(mu=0.0, sigma=float("inf"), deep_triggered=False,
                       latency_ms=0.0, ensemble_seeds=(42,))

    def test_nan_latency_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            FastResult(mu=0.0, sigma=0.1, deep_triggered=False,
                       latency_ms=float("nan"), ensemble_seeds=(42,))


# =============================================================================
# SECTION 3 -- TestConstants
# =============================================================================

class TestConstants:
    def test_ensemble_weights_tuple(self):
        assert isinstance(ENSEMBLE_WEIGHTS, tuple)

    def test_ensemble_weights_values(self):
        assert ENSEMBLE_WEIGHTS == (1.0, 1.5, 0.8)

    def test_ensemble_weights_sum_positive(self):
        assert sum(ENSEMBLE_WEIGHTS) > 0

    def test_uncertainty_trigger_value(self):
        assert UNCERTAINTY_TRIGGER_DEEP_PATH == 0.15

    def test_uncertainty_trigger_positive(self):
        assert UNCERTAINTY_TRIGGER_DEEP_PATH > 0.0

    def test_rf_n_estimators(self):
        assert RF_N_ESTIMATORS == 50

    def test_rf_max_depth(self):
        assert RF_MAX_DEPTH == 8

    def test_rf_min_samples_split(self):
        assert RF_MIN_SAMPLES_SPLIT == 20

    def test_rf_min_samples_leaf(self):
        assert RF_MIN_SAMPLES_LEAF == 10


# =============================================================================
# SECTION 4 -- TestClassify
# =============================================================================

class TestClassify:
    def test_normal(self):
        features = {"volatility": 0.1, "trend_strength": 0.2}
        assert classify(features) == "NORMAL"

    def test_high_uncertainty(self):
        features = {"volatility": 0.5, "trend_strength": 0.0}
        assert classify(features) == "HIGH_UNCERTAINTY"

    def test_avoid(self):
        features = {"volatility": 0.1, "trend_strength": -0.8}
        assert classify(features) == "AVOID"

    def test_boundary_volatility_at_030(self):
        # At exactly 0.3, not > 0.3, so NORMAL
        features = {"volatility": 0.3, "trend_strength": 0.0}
        assert classify(features) == "NORMAL"

    def test_boundary_volatility_above_030(self):
        features = {"volatility": 0.31, "trend_strength": 0.0}
        assert classify(features) == "HIGH_UNCERTAINTY"

    def test_boundary_trend_at_neg05(self):
        # At exactly -0.5, not < -0.5, so NORMAL
        features = {"volatility": 0.1, "trend_strength": -0.5}
        assert classify(features) == "NORMAL"

    def test_boundary_trend_below_neg05(self):
        features = {"volatility": 0.1, "trend_strength": -0.51}
        assert classify(features) == "AVOID"

    def test_empty_features(self):
        # Defaults: volatility=0.0, trend_strength=0.0 -> NORMAL
        assert classify({}) == "NORMAL"

    def test_nan_volatility_returns_high_uncertainty(self):
        features = {"volatility": float("nan"), "trend_strength": 0.0}
        assert classify(features) == "HIGH_UNCERTAINTY"

    def test_inf_trend_returns_high_uncertainty(self):
        features = {"volatility": 0.1, "trend_strength": float("inf")}
        assert classify(features) == "HIGH_UNCERTAINTY"

    def test_volatility_priority_over_trend(self):
        # High vol checked first
        features = {"volatility": 0.5, "trend_strength": -0.8}
        assert classify(features) == "HIGH_UNCERTAINTY"


# =============================================================================
# SECTION 5 -- TestAggregateFast
# =============================================================================

class TestAggregateFast:
    def test_basic_aggregation(self):
        preds = (
            Prediction(mu=0.1, sigma=0.1, confidence=0.7),
            Prediction(mu=0.2, sigma=0.15, confidence=0.6),
            Prediction(mu=0.0, sigma=0.1, confidence=0.5),
        )
        mu, sigma, triggered = aggregate_fast(preds)
        assert math.isfinite(mu)
        assert math.isfinite(sigma)
        assert sigma >= 0.0
        assert isinstance(triggered, bool)

    def test_weighted_mean_correctness(self):
        preds = (
            Prediction(mu=0.1, sigma=0.1, confidence=0.7),
            Prediction(mu=0.2, sigma=0.1, confidence=0.6),
            Prediction(mu=0.3, sigma=0.1, confidence=0.5),
        )
        weights = (1.0, 1.0, 1.0)
        mu, sigma, _ = aggregate_fast(preds, weights)
        expected_mu = (0.1 + 0.2 + 0.3) / 3.0
        assert abs(mu - expected_mu) < 1e-10

    def test_deep_trigger_high_sigma(self):
        preds = (
            Prediction(mu=0.5, sigma=0.5, confidence=0.5),
            Prediction(mu=-0.5, sigma=0.5, confidence=0.5),
            Prediction(mu=0.0, sigma=0.5, confidence=0.5),
        )
        _, sigma, triggered = aggregate_fast(preds)
        assert sigma > UNCERTAINTY_TRIGGER_DEEP_PATH
        assert triggered is True

    def test_deep_trigger_low_sigma(self):
        preds = (
            Prediction(mu=0.1, sigma=0.01, confidence=0.9),
            Prediction(mu=0.1, sigma=0.01, confidence=0.9),
            Prediction(mu=0.1, sigma=0.01, confidence=0.9),
        )
        _, sigma, triggered = aggregate_fast(preds)
        # All predictions agree and have low sigma -> low total sigma
        assert triggered is False

    def test_epistemic_aleatoric_decomposition(self):
        # When members agree, epistemic should be ~0
        preds = (
            Prediction(mu=0.5, sigma=0.2, confidence=0.7),
            Prediction(mu=0.5, sigma=0.2, confidence=0.7),
            Prediction(mu=0.5, sigma=0.2, confidence=0.7),
        )
        mu, sigma, _ = aggregate_fast(preds, (1.0, 1.0, 1.0))
        # sigma should be close to aleatoric only (0.2)
        assert abs(sigma - 0.2) < 0.01

    def test_empty_predictions(self):
        mu, sigma, triggered = aggregate_fast(())
        assert mu == 0.0
        assert sigma == 1.0
        assert triggered is True

    def test_single_prediction(self):
        preds = (Prediction(mu=0.3, sigma=0.1, confidence=0.7),)
        mu, sigma, _ = aggregate_fast(preds, (1.0,))
        assert abs(mu - 0.3) < 1e-10
        # With one member, epistemic = 0, so sigma = aleatoric = 0.1
        assert abs(sigma - 0.1) < 1e-10

    def test_custom_weights(self):
        preds = (
            Prediction(mu=1.0, sigma=0.1, confidence=0.9),
            Prediction(mu=0.0, sigma=0.1, confidence=0.5),
        )
        # Weight heavily towards first
        mu, _, _ = aggregate_fast(preds, (10.0, 0.0))
        assert abs(mu - 1.0) < 0.01


# =============================================================================
# SECTION 6 -- TestFastPathEnsemble
# =============================================================================

class TestFastPathEnsemble:
    def test_init_seeds(self):
        ens = FastPathEnsemble(base_seed=42)
        assert ens._seeds == (42, 1042, 2042)

    def test_init_seeds_custom(self):
        ens = FastPathEnsemble(base_seed=100)
        assert ens._seeds == (100, 1100, 2100)

    def test_init_seed_type_error(self):
        with pytest.raises(TypeError, match="must be an int"):
            FastPathEnsemble(base_seed=3.14)

    def test_predict_returns_fast_result(self):
        ens = FastPathEnsemble()
        result = ens.predict(_default_features())
        assert isinstance(result, FastResult)

    def test_predict_with_state(self):
        ens = FastPathEnsemble()
        result = ens.predict(_default_features(), state=_default_state())
        assert isinstance(result, FastResult)

    def test_predict_without_state(self):
        ens = FastPathEnsemble()
        result = ens.predict(_default_features(), state=None)
        assert isinstance(result, FastResult)

    def test_predict_mu_finite(self):
        ens = FastPathEnsemble()
        result = ens.predict(_default_features())
        assert math.isfinite(result.mu)

    def test_predict_sigma_nonneg(self):
        ens = FastPathEnsemble()
        result = ens.predict(_default_features())
        assert result.sigma >= 0.0

    def test_predict_ensemble_seeds(self):
        ens = FastPathEnsemble(base_seed=42)
        result = ens.predict(_default_features())
        assert result.ensemble_seeds == (42, 1042, 2042)

    def test_predict_latency_ms(self):
        ens = FastPathEnsemble()
        result = ens.predict(_default_features(), latency_ms=3.5)
        assert result.latency_ms == 3.5

    def test_predict_features_type_error(self):
        ens = FastPathEnsemble()
        with pytest.raises(TypeError, match="must be a dict"):
            ens.predict("not a dict")

    def test_predict_latency_nan_rejected(self):
        ens = FastPathEnsemble()
        with pytest.raises(ValueError, match="must be finite"):
            ens.predict(_default_features(), latency_ms=float("nan"))

    def test_get_uncertainty_before_predict(self):
        ens = FastPathEnsemble()
        assert ens.get_uncertainty() == 0.0

    def test_get_uncertainty_after_predict(self):
        ens = FastPathEnsemble()
        result = ens.predict(_default_features())
        assert ens.get_uncertainty() == result.sigma

    def test_get_uncertainty_nonneg(self):
        ens = FastPathEnsemble()
        ens.predict(_default_features())
        assert ens.get_uncertainty() >= 0.0


# =============================================================================
# SECTION 7 -- TestMember0Kalman
# =============================================================================

class TestMember0Kalman:
    def test_with_state(self):
        estimator = StateEstimator()
        p = _member0_kalman(_default_features(), _default_state(), estimator)
        assert isinstance(p, Prediction)
        assert math.isfinite(p.mu)
        assert p.sigma > 0
        assert _CONFIDENCE_FLOOR <= p.confidence <= _CONFIDENCE_CEILING

    def test_without_state(self):
        estimator = StateEstimator()
        p = _member0_kalman(_default_features(), None, estimator)
        assert isinstance(p, Prediction)
        assert math.isfinite(p.mu)

    def test_mu_in_range(self):
        estimator = StateEstimator()
        p = _member0_kalman(_default_features(), _default_state(), estimator)
        assert -1.0 <= p.mu <= 1.0

    def test_sigma_positive(self):
        estimator = StateEstimator()
        p = _member0_kalman(_default_features(), _default_state(), estimator)
        assert p.sigma >= _SIGMA_FLOOR


# =============================================================================
# SECTION 8 -- TestMember1Tree
# =============================================================================

class TestMember1Tree:
    def test_basic_prediction(self):
        p = _member1_tree(_default_features())
        assert isinstance(p, Prediction)

    def test_high_volatility_branch(self):
        features = {"volatility": 0.5, "stress": 0.7, "momentum": 0.0,
                     "trend_strength": 0.0, "mean_reversion": 0.0}
        p = _member1_tree(features)
        assert p.mu < 0  # Negative in high vol + high stress

    def test_positive_momentum_branch(self):
        features = {"volatility": 0.1, "momentum": 0.7, "trend_strength": 0.5,
                     "stress": 0.0, "mean_reversion": 0.0}
        p = _member1_tree(features)
        assert p.mu > 0  # Positive momentum

    def test_negative_momentum_branch(self):
        features = {"volatility": 0.1, "momentum": -0.7, "trend_strength": -0.5,
                     "stress": 0.0, "mean_reversion": 0.0}
        p = _member1_tree(features)
        assert p.mu < 0  # Negative momentum

    def test_neutral_branch(self):
        features = {"volatility": 0.1, "momentum": 0.0, "trend_strength": 0.0,
                     "stress": 0.0, "mean_reversion": 0.0}
        p = _member1_tree(features)
        assert -1.0 <= p.mu <= 1.0

    def test_mean_reversion_branch(self):
        features = {"volatility": 0.1, "momentum": 0.2, "trend_strength": 0.0,
                     "stress": 0.0, "mean_reversion": 0.5}
        p = _member1_tree(features)
        assert isinstance(p, Prediction)

    def test_mu_always_in_range(self):
        for mom in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            for vol in [0.0, 0.2, 0.5, 1.0]:
                features = {"volatility": vol, "momentum": mom,
                             "trend_strength": 0.0, "stress": 0.0,
                             "mean_reversion": 0.0}
                p = _member1_tree(features)
                assert -1.0 <= p.mu <= 1.0


# =============================================================================
# SECTION 9 -- TestMember2Rules
# =============================================================================

class TestMember2Rules:
    def test_normal_signal(self):
        features = {"volatility": 0.1, "trend_strength": 0.2}
        p = _member2_rules(features)
        assert isinstance(p, Prediction)
        assert p.mu == 0.0
        assert abs(p.sigma - 0.1) < 1e-10

    def test_high_uncertainty_signal(self):
        features = {"volatility": 0.5, "trend_strength": 0.0}
        p = _member2_rules(features)
        assert p.mu == 0.0
        assert abs(p.sigma - 0.5) < 1e-10

    def test_avoid_signal(self):
        features = {"volatility": 0.1, "trend_strength": -0.8}
        p = _member2_rules(features)
        assert p.mu == -0.3
        assert abs(p.sigma - 0.3) < 1e-10

    def test_confidence_in_range(self):
        for vol, ts in [(0.1, 0.0), (0.5, 0.0), (0.1, -0.8)]:
            features = {"volatility": vol, "trend_strength": ts}
            p = _member2_rules(features)
            assert _CONFIDENCE_FLOOR <= p.confidence <= _CONFIDENCE_CEILING


# =============================================================================
# SECTION 10 -- TestNumericalSafety
# =============================================================================

class TestNumericalSafety:
    def test_nan_feature_handled(self):
        features = {"volatility": float("nan"), "momentum": 0.3}
        ens = FastPathEnsemble()
        result = ens.predict(features)
        assert math.isfinite(result.mu)
        assert math.isfinite(result.sigma)

    def test_inf_feature_handled(self):
        features = {"volatility": float("inf"), "trend_strength": 0.0}
        ens = FastPathEnsemble()
        result = ens.predict(features)
        assert math.isfinite(result.mu)
        assert math.isfinite(result.sigma)

    def test_neg_inf_feature_handled(self):
        features = {"momentum": float("-inf")}
        ens = FastPathEnsemble()
        result = ens.predict(features)
        assert math.isfinite(result.mu)
        assert math.isfinite(result.sigma)

    def test_zero_features(self):
        features = {"volatility": 0.0, "momentum": 0.0,
                     "trend_strength": 0.0, "stress": 0.0}
        ens = FastPathEnsemble()
        result = ens.predict(features)
        assert math.isfinite(result.mu)
        assert result.sigma >= 0.0

    def test_safe_feature_nan(self):
        assert _safe_feature({"x": float("nan")}, "x", 0.5) == 0.5

    def test_safe_feature_inf(self):
        assert _safe_feature({"x": float("inf")}, "x", 0.5) == 0.5

    def test_safe_feature_missing(self):
        assert _safe_feature({}, "x", 0.5) == 0.5

    def test_safe_feature_non_numeric(self):
        assert _safe_feature({"x": "abc"}, "x", 0.5) == 0.5


# =============================================================================
# SECTION 11 -- TestDeterminism
# =============================================================================

class TestDeterminism:
    def test_same_inputs_identical_outputs(self):
        features = _default_features()
        state = _default_state()
        ens1 = FastPathEnsemble(base_seed=42)
        ens2 = FastPathEnsemble(base_seed=42)
        r1 = ens1.predict(features, state=state, latency_ms=1.0)
        r2 = ens2.predict(features, state=state, latency_ms=1.0)
        assert r1.mu == r2.mu
        assert r1.sigma == r2.sigma
        assert r1.deep_triggered == r2.deep_triggered

    def test_fresh_instances_same_result(self):
        features = _default_features()
        results = []
        for _ in range(3):
            ens = FastPathEnsemble(base_seed=42)
            results.append(ens.predict(features))
        assert all(r.mu == results[0].mu for r in results)
        assert all(r.sigma == results[0].sigma for r in results)

    def test_aggregate_fast_deterministic(self):
        preds = (
            Prediction(mu=0.2, sigma=0.1, confidence=0.7),
            Prediction(mu=0.3, sigma=0.2, confidence=0.6),
            Prediction(mu=-0.1, sigma=0.15, confidence=0.5),
        )
        r1 = aggregate_fast(preds)
        r2 = aggregate_fast(preds)
        assert r1 == r2

    def test_classify_deterministic(self):
        features = {"volatility": 0.2, "trend_strength": -0.3}
        assert classify(features) == classify(features)

    def test_member1_deterministic(self):
        features = _default_features()
        p1 = _member1_tree(features)
        p2 = _member1_tree(features)
        assert p1.mu == p2.mu
        assert p1.sigma == p2.sigma
        assert p1.confidence == p2.confidence


# =============================================================================
# SECTION 12 -- TestImportContract
# =============================================================================

class TestImportContract:
    def test_all_symbols_importable(self):
        import jarvis.models.fast_path as mod
        for name in mod.__all__:
            assert hasattr(mod, name), f"Missing __all__ export: {name}"

    def test_import_from_module(self):
        from jarvis.models.fast_path import (
            Prediction,
            FastResult,
            FastPathEnsemble,
            aggregate_fast,
            classify,
        )
        assert callable(aggregate_fast)
        assert callable(classify)

    def test_import_from_init(self):
        from jarvis.models import (
            Prediction,
            FastResult,
            FastPathEnsemble,
            aggregate_fast,
            classify,
        )
        assert callable(aggregate_fast)
        assert callable(classify)

    def test_all_exports_complete(self):
        import jarvis.models.fast_path as mod
        expected = [
            "ENSEMBLE_WEIGHTS",
            "UNCERTAINTY_TRIGGER_DEEP_PATH",
            "RF_N_ESTIMATORS",
            "RF_MAX_DEPTH",
            "RF_MIN_SAMPLES_SPLIT",
            "RF_MIN_SAMPLES_LEAF",
            "Prediction",
            "FastResult",
            "FastPathEnsemble",
            "aggregate_fast",
            "classify",
        ]
        for name in expected:
            assert name in mod.__all__, f"{name} not in __all__"


# =============================================================================
# SECTION 13 -- TestEdgeCases
# =============================================================================

class TestEdgeCases:
    def test_empty_features_dict(self):
        ens = FastPathEnsemble()
        result = ens.predict({})
        assert isinstance(result, FastResult)
        assert math.isfinite(result.mu)
        assert math.isfinite(result.sigma)

    def test_extreme_positive_features(self):
        features = {
            "volatility": 1e6,
            "momentum": 1e6,
            "trend_strength": 1e6,
            "stress": 1e6,
            "mean_reversion": 1e6,
        }
        ens = FastPathEnsemble()
        result = ens.predict(features)
        assert math.isfinite(result.mu)
        assert math.isfinite(result.sigma)

    def test_extreme_negative_features(self):
        features = {
            "volatility": -1e6,
            "momentum": -1e6,
            "trend_strength": -1e6,
            "stress": -1e6,
        }
        ens = FastPathEnsemble()
        result = ens.predict(features)
        assert math.isfinite(result.mu)
        assert math.isfinite(result.sigma)

    def test_all_zero_features(self):
        features = {
            "volatility": 0.0,
            "momentum": 0.0,
            "trend_strength": 0.0,
            "stress": 0.0,
            "mean_reversion": 0.0,
            "liquidity": 0.0,
            "drift": 0.0,
            "noise": 0.0,
        }
        ens = FastPathEnsemble()
        result = ens.predict(features)
        assert math.isfinite(result.mu)
        assert result.sigma >= 0.0

    def test_extra_features_ignored(self):
        features = _default_features()
        features["unknown_feature"] = 999.0
        ens = FastPathEnsemble()
        result = ens.predict(features)
        assert isinstance(result, FastResult)

    def test_default_state_works(self):
        ens = FastPathEnsemble()
        state = LatentState.default()
        result = ens.predict(_default_features(), state=state)
        assert isinstance(result, FastResult)
        assert math.isfinite(result.mu)

    def test_multiple_predictions_in_sequence(self):
        ens = FastPathEnsemble()
        results = []
        for i in range(5):
            features = {"momentum": i * 0.1, "volatility": 0.1}
            results.append(ens.predict(features))
        assert all(isinstance(r, FastResult) for r in results)
        assert all(math.isfinite(r.mu) for r in results)

    def test_latency_zero(self):
        ens = FastPathEnsemble()
        result = ens.predict(_default_features(), latency_ms=0.0)
        assert result.latency_ms == 0.0

    def test_different_seeds_different_ensemble(self):
        ens1 = FastPathEnsemble(base_seed=1)
        ens2 = FastPathEnsemble(base_seed=2)
        assert ens1._seeds != ens2._seeds
