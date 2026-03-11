# =============================================================================
# tests/unit/models/test_deep_path.py
# Tests for jarvis/models/deep_path.py — S07 Deep Path Ensemble
# =============================================================================

from __future__ import annotations

import math

import pytest

from jarvis.core.state_layer import LatentState
from jarvis.models.fast_path import (
    FastPathEnsemble,
    FastResult,
    Prediction,
    UNCERTAINTY_TRIGGER_DEEP_PATH,
)
from jarvis.models.deep_path import (
    TRANSFORMER_LAYERS,
    TRANSFORMER_D_MODEL,
    TRANSFORMER_HEADS,
    TRANSFORMER_D_FF,
    TRANSFORMER_DROPOUT,
    TRANSFORMER_MAX_SEQ,
    PARTICLE_COUNT,
    PARTICLE_RESAMPLING,
    PARTICLE_MIN_EFFECTIVE,
    BMA_WEIGHTS,
    OOD_THRESHOLD_MEDIUM,
    Peak,
    DeepResult,
    should_activate_deep_path,
    aggregate_deep,
    TransformerPredictor,
    ParticleFilter,
    DeepPathEnsemble,
)


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


def _default_fast_result() -> FastResult:
    """Standard FastResult for tests."""
    return FastResult(
        mu=0.15,
        sigma=0.12,
        deep_triggered=False,
        latency_ms=2.0,
        ensemble_seeds=(42, 1042, 2042),
    )


def _high_sigma_fast_result() -> FastResult:
    """FastResult with high sigma (triggers deep path)."""
    return FastResult(
        mu=0.05,
        sigma=0.25,
        deep_triggered=True,
        latency_ms=3.0,
        ensemble_seeds=(42, 1042, 2042),
    )


def _low_sigma_fast_result() -> FastResult:
    """FastResult with very low sigma."""
    return FastResult(
        mu=0.1,
        sigma=0.02,
        deep_triggered=False,
        latency_ms=1.0,
        ensemble_seeds=(42, 1042, 2042),
    )


# =============================================================================
# SECTION 1 -- TestPeak
# =============================================================================

class TestPeak:
    def test_frozen(self):
        p = Peak(mu=0.5, weight=0.3)
        with pytest.raises(AttributeError):
            p.mu = 0.1

    def test_positive_weight(self):
        p = Peak(mu=0.0, weight=0.5)
        assert p.weight > 0

    def test_field_values(self):
        p = Peak(mu=-0.3, weight=0.7)
        assert p.mu == -0.3
        assert p.weight == 0.7

    def test_zero_weight_rejected(self):
        with pytest.raises(ValueError, match="must be > 0"):
            Peak(mu=0.0, weight=0.0)

    def test_negative_weight_rejected(self):
        with pytest.raises(ValueError, match="must be > 0"):
            Peak(mu=0.0, weight=-0.1)

    def test_nan_mu_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            Peak(mu=float("nan"), weight=0.5)

    def test_inf_weight_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            Peak(mu=0.0, weight=float("inf"))


# =============================================================================
# SECTION 2 -- TestDeepResult
# =============================================================================

class TestDeepResult:
    def test_frozen(self):
        r = DeepResult(
            mu=0.1, sigma_squared=0.03,
            sigma_sq_aleatoric=0.01, sigma_sq_epistemic_model=0.01,
            sigma_sq_epistemic_data=0.01,
            Q=0.5, S=0.7, U=0.0, R=0.8, latency_ms=5.0,
        )
        with pytest.raises(AttributeError):
            r.mu = 0.5

    def test_sigma_sq_invariant_pass(self):
        r = DeepResult(
            mu=0.1, sigma_squared=0.03,
            sigma_sq_aleatoric=0.01, sigma_sq_epistemic_model=0.01,
            sigma_sq_epistemic_data=0.01,
            Q=0.5, S=0.7, U=0.0, R=0.8, latency_ms=0.0,
        )
        assert abs(r.sigma_squared - (r.sigma_sq_aleatoric + r.sigma_sq_epistemic_model + r.sigma_sq_epistemic_data)) < 1e-6

    def test_sigma_sq_invariant_fail(self):
        with pytest.raises(ValueError, match="decomposition inconsistent"):
            DeepResult(
                mu=0.1, sigma_squared=0.10,
                sigma_sq_aleatoric=0.01, sigma_sq_epistemic_model=0.01,
                sigma_sq_epistemic_data=0.01,
                Q=0.5, S=0.7, U=0.0, R=0.8, latency_ms=0.0,
            )

    def test_nan_mu_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            DeepResult(
                mu=float("nan"), sigma_squared=0.03,
                sigma_sq_aleatoric=0.01, sigma_sq_epistemic_model=0.01,
                sigma_sq_epistemic_data=0.01,
                Q=0.5, S=0.7, U=0.0, R=0.8, latency_ms=0.0,
            )

    def test_inf_sigma_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            DeepResult(
                mu=0.1, sigma_squared=float("inf"),
                sigma_sq_aleatoric=0.01, sigma_sq_epistemic_model=0.01,
                sigma_sq_epistemic_data=0.01,
                Q=0.5, S=0.7, U=0.0, R=0.8, latency_ms=0.0,
            )

    def test_nan_Q_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            DeepResult(
                mu=0.1, sigma_squared=0.03,
                sigma_sq_aleatoric=0.01, sigma_sq_epistemic_model=0.01,
                sigma_sq_epistemic_data=0.01,
                Q=float("nan"), S=0.7, U=0.0, R=0.8, latency_ms=0.0,
            )

    def test_all_dt_fields_present(self):
        r = DeepResult(
            mu=0.1, sigma_squared=0.03,
            sigma_sq_aleatoric=0.01, sigma_sq_epistemic_model=0.01,
            sigma_sq_epistemic_data=0.01,
            Q=0.5, S=0.7, U=0.0, R=0.8, latency_ms=0.0,
        )
        assert hasattr(r, "mu")
        assert hasattr(r, "sigma_squared")
        assert hasattr(r, "sigma_sq_aleatoric")
        assert hasattr(r, "sigma_sq_epistemic_model")
        assert hasattr(r, "sigma_sq_epistemic_data")
        assert hasattr(r, "Q")
        assert hasattr(r, "S")
        assert hasattr(r, "U")
        assert hasattr(r, "R")
        assert hasattr(r, "latency_ms")

    def test_nan_latency_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            DeepResult(
                mu=0.1, sigma_squared=0.03,
                sigma_sq_aleatoric=0.01, sigma_sq_epistemic_model=0.01,
                sigma_sq_epistemic_data=0.01,
                Q=0.5, S=0.7, U=0.0, R=0.8, latency_ms=float("nan"),
            )


# =============================================================================
# SECTION 3 -- TestConstants
# =============================================================================

class TestConstants:
    def test_bma_weights_sum(self):
        assert abs(sum(BMA_WEIGHTS) - 1.0) < 1e-10

    def test_bma_weights_tuple(self):
        assert isinstance(BMA_WEIGHTS, tuple)
        assert len(BMA_WEIGHTS) == 3

    def test_bma_weights_values(self):
        assert BMA_WEIGHTS == (0.3, 0.5, 0.2)

    def test_particle_count(self):
        assert PARTICLE_COUNT == 1000

    def test_particle_resampling(self):
        assert PARTICLE_RESAMPLING == "systematic"

    def test_particle_min_effective(self):
        assert PARTICLE_MIN_EFFECTIVE == 500

    def test_transformer_layers(self):
        assert TRANSFORMER_LAYERS == 4

    def test_transformer_d_model(self):
        assert TRANSFORMER_D_MODEL == 128

    def test_transformer_heads(self):
        assert TRANSFORMER_HEADS == 8

    def test_transformer_d_ff(self):
        assert TRANSFORMER_D_FF == 512

    def test_transformer_dropout(self):
        assert TRANSFORMER_DROPOUT == 0.1

    def test_transformer_max_seq(self):
        assert TRANSFORMER_MAX_SEQ == 200

    def test_ood_threshold_medium(self):
        assert OOD_THRESHOLD_MEDIUM == 0.6


# =============================================================================
# SECTION 4 -- TestShouldActivateDeepPath
# =============================================================================

class TestShouldActivateDeepPath:
    def test_high_sigma_triggers(self):
        assert should_activate_deep_path(fast_sigma=0.20) is True

    def test_low_sigma_no_trigger(self):
        assert should_activate_deep_path(fast_sigma=0.05) is False

    def test_at_threshold_no_trigger(self):
        # Exactly at threshold, not > threshold
        assert should_activate_deep_path(fast_sigma=UNCERTAINTY_TRIGGER_DEEP_PATH) is False

    def test_ood_risk_triggers(self):
        assert should_activate_deep_path(fast_sigma=0.05, ood_risk_score=0.7) is True

    def test_ood_at_threshold_no_trigger(self):
        assert should_activate_deep_path(fast_sigma=0.05, ood_risk_score=0.6) is False

    def test_regime_transition_triggers(self):
        assert should_activate_deep_path(
            fast_sigma=0.05, regime_transition_detected=True
        ) is True

    def test_user_request_triggers(self):
        assert should_activate_deep_path(
            fast_sigma=0.05, user_request_deep=True
        ) is True

    def test_no_triggers_false(self):
        assert should_activate_deep_path(
            fast_sigma=0.05,
            ood_risk_score=0.3,
            regime_transition_detected=False,
            user_request_deep=False,
        ) is False

    def test_combined_triggers(self):
        assert should_activate_deep_path(
            fast_sigma=0.20,
            ood_risk_score=0.7,
            regime_transition_detected=True,
            user_request_deep=True,
        ) is True


# =============================================================================
# SECTION 5 -- TestTransformerPredictor
# =============================================================================

class TestTransformerPredictor:
    def test_init_with_seed(self):
        t = TransformerPredictor(seed=42)
        assert t._seed == 42

    def test_init_seed_type_error(self):
        with pytest.raises(TypeError, match="must be an int"):
            TransformerPredictor(seed=3.14)

    def test_predict_returns_prediction(self):
        t = TransformerPredictor(seed=42)
        p = t.predict([{"momentum": 0.3, "volatility": 0.1}])
        assert isinstance(p, Prediction)

    def test_predict_mu_in_range(self):
        t = TransformerPredictor(seed=42)
        p = t.predict([{"momentum": 0.5}])
        assert -1.0 <= p.mu <= 1.0

    def test_predict_sigma_positive(self):
        t = TransformerPredictor(seed=42)
        p = t.predict([{"momentum": 0.3}])
        assert p.sigma > 0

    def test_deterministic(self):
        t1 = TransformerPredictor(seed=42)
        t2 = TransformerPredictor(seed=42)
        seq = [{"momentum": 0.3, "volatility": 0.15}]
        p1 = t1.predict(seq)
        p2 = t2.predict(seq)
        assert p1.mu == p2.mu
        assert p1.sigma == p2.sigma
        assert p1.confidence == p2.confidence

    def test_different_seeds_different_results(self):
        t1 = TransformerPredictor(seed=42)
        t2 = TransformerPredictor(seed=99)
        seq = [{"momentum": 0.3, "volatility": 0.15}]
        p1 = t1.predict(seq)
        p2 = t2.predict(seq)
        # Different seeds should produce different weights and thus different results
        # (at least one field should differ)
        assert p1.mu != p2.mu or p1.sigma != p2.sigma

    def test_predict_empty_sequence(self):
        t = TransformerPredictor(seed=42)
        p = t.predict([])
        assert isinstance(p, Prediction)
        assert math.isfinite(p.mu)

    def test_predict_list_of_floats(self):
        t = TransformerPredictor(seed=42)
        p = t.predict([0.1, 0.2, 0.3])
        assert isinstance(p, Prediction)


# =============================================================================
# SECTION 6 -- TestParticleFilter
# =============================================================================

class TestParticleFilter:
    def test_init_particles_count(self):
        pf = ParticleFilter(seed=42)
        assert len(pf._particles) == PARTICLE_COUNT
        assert len(pf._weights) == PARTICLE_COUNT

    def test_init_custom_count(self):
        pf = ParticleFilter(seed=42, n_particles=50)
        assert len(pf._particles) == 50

    def test_init_seed_type_error(self):
        with pytest.raises(TypeError, match="must be an int"):
            ParticleFilter(seed=3.14)

    def test_init_invalid_n_particles(self):
        with pytest.raises(ValueError, match="positive int"):
            ParticleFilter(seed=42, n_particles=0)

    def test_predict_returns_valid(self):
        pf = ParticleFilter(seed=42)
        mu, var = pf.predict(_default_features())
        assert math.isfinite(mu)
        assert math.isfinite(var)
        assert var >= 0.0

    def test_predict_mu_in_range(self):
        pf = ParticleFilter(seed=42)
        mu, _ = pf.predict(_default_features())
        assert -1.0 <= mu <= 1.0

    def test_systematic_resample_deterministic(self):
        pf1 = ParticleFilter(seed=42, n_particles=100)
        pf2 = ParticleFilter(seed=42, n_particles=100)
        pf1.predict(_default_features())
        pf2.predict(_default_features())
        assert pf1._particles == pf2._particles
        assert pf1._weights == pf2._weights

    def test_effective_sample_size(self):
        pf = ParticleFilter(seed=42, n_particles=100)
        # Initially equal weights: ESS = n
        ess = pf._effective_sample_size()
        assert abs(ess - 100.0) < 1.0

    def test_get_multimodal_peaks_returns_peaks(self):
        pf = ParticleFilter(seed=42)
        pf.predict(_default_features())
        peaks = pf.get_multimodal_peaks()
        assert isinstance(peaks, tuple)
        assert len(peaks) >= 1
        assert all(isinstance(p, Peak) for p in peaks)

    def test_weights_sum_to_one(self):
        pf = ParticleFilter(seed=42)
        pf.predict(_default_features())
        total = sum(pf._weights)
        assert abs(total - 1.0) < 1e-6


# =============================================================================
# SECTION 7 -- TestDeepPathEnsemble
# =============================================================================

class TestDeepPathEnsemble:
    def test_init(self):
        ens = DeepPathEnsemble(base_seed=42)
        assert ens._base_seed == 42

    def test_init_seed_type_error(self):
        with pytest.raises(TypeError, match="must be an int"):
            DeepPathEnsemble(base_seed=3.14)

    def test_predict_returns_deep_result(self):
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(_default_features(), _default_fast_result())
        assert isinstance(result, DeepResult)

    def test_predict_with_state(self):
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(
            _default_features(), _default_fast_result(), state=_default_state()
        )
        assert isinstance(result, DeepResult)
        # With state, Q should be stability * regime_confidence
        expected_Q = 0.7 * 0.8
        assert abs(result.Q - expected_Q) < 1e-6
        assert abs(result.S - 0.7) < 1e-6
        assert abs(result.R - 0.8) < 1e-6

    def test_predict_without_state_defaults(self):
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(_default_features(), _default_fast_result(), state=None)
        assert isinstance(result, DeepResult)
        assert result.Q == 0.5
        assert result.S == 0.5
        assert result.R == 0.5

    def test_sigma_sq_decomposition_correctness(self):
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(_default_features(), _default_fast_result())
        expected = (
            result.sigma_sq_aleatoric
            + result.sigma_sq_epistemic_model
            + result.sigma_sq_epistemic_data
        )
        assert abs(result.sigma_squared - expected) < 1e-6

    def test_sigma_components_nonneg(self):
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(_default_features(), _default_fast_result())
        assert result.sigma_sq_aleatoric >= 0.0
        assert result.sigma_sq_epistemic_model >= 0.0
        assert result.sigma_sq_epistemic_data >= 0.0
        assert result.sigma_squared >= 0.0

    def test_U_placeholder_zero(self):
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(_default_features(), _default_fast_result())
        assert result.U == 0.0

    def test_latency_ms_passthrough(self):
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(
            _default_features(), _default_fast_result(), latency_ms=42.5
        )
        assert result.latency_ms == 42.5

    def test_features_type_error(self):
        ens = DeepPathEnsemble(base_seed=42)
        with pytest.raises(TypeError, match="must be a dict"):
            ens.predict("not a dict", _default_fast_result())

    def test_fast_result_type_error(self):
        ens = DeepPathEnsemble(base_seed=42)
        with pytest.raises(TypeError, match="must be a FastResult"):
            ens.predict(_default_features(), "not a FastResult")

    def test_latency_nan_rejected(self):
        ens = DeepPathEnsemble(base_seed=42)
        with pytest.raises(ValueError, match="must be finite"):
            ens.predict(_default_features(), _default_fast_result(),
                        latency_ms=float("nan"))


# =============================================================================
# SECTION 8 -- TestAggregateDeep
# =============================================================================

class TestAggregateDeep:
    def test_bma_weights_applied(self):
        pred = Prediction(mu=0.0, sigma=0.1, confidence=0.5)
        result = aggregate_deep(
            fast_mu=1.0, fast_sigma=0.1,
            transformer_pred=pred,
            particle_mu=0.0, particle_sigma=0.1,
        )
        # mu = 0.3*1.0 + 0.5*0.0 + 0.2*0.0 = 0.3
        assert abs(result["mu"] - 0.3) < 1e-10

    def test_sigma_sq_components_sum(self):
        pred = Prediction(mu=0.2, sigma=0.15, confidence=0.6)
        result = aggregate_deep(
            fast_mu=0.1, fast_sigma=0.1,
            transformer_pred=pred,
            particle_mu=0.3, particle_sigma=0.2,
        )
        expected = (
            result["sigma_sq_aleatoric"]
            + result["sigma_sq_epistemic_model"]
            + result["sigma_sq_epistemic_data"]
        )
        assert abs(result["sigma_squared"] - expected) < 1e-10

    def test_system_contract_fields_with_state(self):
        state = _default_state()
        pred = Prediction(mu=0.0, sigma=0.1, confidence=0.5)
        result = aggregate_deep(
            fast_mu=0.1, fast_sigma=0.1,
            transformer_pred=pred,
            particle_mu=0.0, particle_sigma=0.1,
            state=state,
        )
        assert abs(result["Q"] - state.stability * state.regime_confidence) < 1e-10
        assert abs(result["S"] - state.stability) < 1e-10
        assert abs(result["R"] - state.regime_confidence) < 1e-10
        assert result["U"] == 0.0

    def test_system_contract_fields_without_state(self):
        pred = Prediction(mu=0.0, sigma=0.1, confidence=0.5)
        result = aggregate_deep(
            fast_mu=0.1, fast_sigma=0.1,
            transformer_pred=pred,
            particle_mu=0.0, particle_sigma=0.1,
            state=None,
        )
        assert result["Q"] == 0.5
        assert result["S"] == 0.5
        assert result["R"] == 0.5
        assert result["U"] == 0.0

    def test_epistemic_data_from_state(self):
        state = _default_state()  # prediction_uncertainty = 0.1
        pred = Prediction(mu=0.0, sigma=0.1, confidence=0.5)
        result = aggregate_deep(
            fast_mu=0.1, fast_sigma=0.1,
            transformer_pred=pred,
            particle_mu=0.0, particle_sigma=0.1,
            state=state,
        )
        assert abs(result["sigma_sq_epistemic_data"] - 0.01) < 1e-10

    def test_epistemic_data_zero_without_state(self):
        pred = Prediction(mu=0.0, sigma=0.1, confidence=0.5)
        result = aggregate_deep(
            fast_mu=0.1, fast_sigma=0.1,
            transformer_pred=pred,
            particle_mu=0.0, particle_sigma=0.1,
            state=None,
        )
        assert result["sigma_sq_epistemic_data"] == 0.0


# =============================================================================
# SECTION 9 -- TestNumericalSafety
# =============================================================================

class TestNumericalSafety:
    def test_nan_features_handled(self):
        features = {"volatility": float("nan"), "momentum": float("nan")}
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(features, _default_fast_result())
        assert math.isfinite(result.mu)
        assert math.isfinite(result.sigma_squared)

    def test_extreme_values(self):
        features = {"volatility": 1e6, "momentum": 1e6, "trend_strength": 1e6}
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(features, _default_fast_result())
        assert math.isfinite(result.mu)
        assert math.isfinite(result.sigma_squared)

    def test_zero_features(self):
        features = {"volatility": 0.0, "momentum": 0.0, "trend_strength": 0.0}
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(features, _default_fast_result())
        assert math.isfinite(result.mu)
        assert result.sigma_squared >= 0.0

    def test_very_large_values(self):
        features = {"volatility": 1e10, "momentum": -1e10}
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(features, _default_fast_result())
        assert math.isfinite(result.mu)
        assert math.isfinite(result.sigma_squared)

    def test_negative_features(self):
        features = {"volatility": -1.0, "momentum": -1.0, "trend_strength": -1.0}
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(features, _default_fast_result())
        assert math.isfinite(result.mu)
        assert math.isfinite(result.sigma_squared)


# =============================================================================
# SECTION 10 -- TestDeterminism
# =============================================================================

class TestDeterminism:
    def test_same_inputs_identical_outputs(self):
        features = _default_features()
        fast_result = _default_fast_result()
        state = _default_state()

        ens1 = DeepPathEnsemble(base_seed=42)
        ens2 = DeepPathEnsemble(base_seed=42)
        r1 = ens1.predict(features, fast_result, state=state, latency_ms=1.0)
        r2 = ens2.predict(features, fast_result, state=state, latency_ms=1.0)

        assert r1.mu == r2.mu
        assert r1.sigma_squared == r2.sigma_squared
        assert r1.sigma_sq_aleatoric == r2.sigma_sq_aleatoric
        assert r1.sigma_sq_epistemic_model == r2.sigma_sq_epistemic_model
        assert r1.sigma_sq_epistemic_data == r2.sigma_sq_epistemic_data
        assert r1.Q == r2.Q
        assert r1.S == r2.S
        assert r1.U == r2.U
        assert r1.R == r2.R

    def test_fresh_instances_same_result(self):
        features = _default_features()
        fast_result = _default_fast_result()
        results = []
        for _ in range(3):
            ens = DeepPathEnsemble(base_seed=42)
            results.append(ens.predict(features, fast_result))
        assert all(r.mu == results[0].mu for r in results)
        assert all(r.sigma_squared == results[0].sigma_squared for r in results)

    def test_seeds_preserved(self):
        ens1 = DeepPathEnsemble(base_seed=42)
        ens2 = DeepPathEnsemble(base_seed=42)
        assert ens1._transformer._seed == ens2._transformer._seed
        assert ens1._particle_filter._seed == ens2._particle_filter._seed

    def test_transformer_deterministic_across_calls(self):
        t = TransformerPredictor(seed=42)
        seq = [{"momentum": 0.3, "volatility": 0.15}]
        p1 = t.predict(seq)
        # Fresh instance
        t2 = TransformerPredictor(seed=42)
        p2 = t2.predict(seq)
        assert p1.mu == p2.mu
        assert p1.sigma == p2.sigma

    def test_particle_filter_deterministic(self):
        pf1 = ParticleFilter(seed=42, n_particles=100)
        pf2 = ParticleFilter(seed=42, n_particles=100)
        r1 = pf1.predict(_default_features())
        r2 = pf2.predict(_default_features())
        assert r1[0] == r2[0]
        assert r1[1] == r2[1]


# =============================================================================
# SECTION 11 -- TestImportContract
# =============================================================================

class TestImportContract:
    def test_all_symbols_importable(self):
        import jarvis.models.deep_path as mod
        for name in mod.__all__:
            assert hasattr(mod, name), f"Missing __all__ export: {name}"

    def test_import_from_module(self):
        from jarvis.models.deep_path import (
            Peak,
            DeepResult,
            DeepPathEnsemble,
            TransformerPredictor,
            ParticleFilter,
            should_activate_deep_path,
            aggregate_deep,
        )
        assert callable(should_activate_deep_path)
        assert callable(aggregate_deep)

    def test_import_from_init(self):
        from jarvis.models import (
            Peak,
            DeepResult,
            DeepPathEnsemble,
            should_activate_deep_path,
            aggregate_deep,
        )
        assert callable(should_activate_deep_path)
        assert callable(aggregate_deep)

    def test_all_exports_complete(self):
        import jarvis.models.deep_path as mod
        expected = [
            "TRANSFORMER_LAYERS",
            "TRANSFORMER_D_MODEL",
            "TRANSFORMER_HEADS",
            "TRANSFORMER_D_FF",
            "TRANSFORMER_DROPOUT",
            "TRANSFORMER_MAX_SEQ",
            "PARTICLE_COUNT",
            "PARTICLE_RESAMPLING",
            "PARTICLE_MIN_EFFECTIVE",
            "BMA_WEIGHTS",
            "OOD_THRESHOLD_MEDIUM",
            "Peak",
            "DeepResult",
            "should_activate_deep_path",
            "aggregate_deep",
            "TransformerPredictor",
            "ParticleFilter",
            "DeepPathEnsemble",
        ]
        for name in expected:
            assert name in mod.__all__, f"{name} not in __all__"


# =============================================================================
# SECTION 12 -- TestEdgeCases
# =============================================================================

class TestEdgeCases:
    def test_empty_features(self):
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict({}, _default_fast_result())
        assert isinstance(result, DeepResult)
        assert math.isfinite(result.mu)

    def test_single_feature(self):
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict({"momentum": 0.5}, _default_fast_result())
        assert isinstance(result, DeepResult)

    def test_fast_result_high_sigma(self):
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(_default_features(), _high_sigma_fast_result())
        assert isinstance(result, DeepResult)
        assert math.isfinite(result.mu)

    def test_fast_result_low_sigma(self):
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(_default_features(), _low_sigma_fast_result())
        assert isinstance(result, DeepResult)

    def test_mu_clipped_to_range(self):
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(_default_features(), _default_fast_result())
        assert -1.0 <= result.mu <= 1.0

    def test_default_state_works(self):
        ens = DeepPathEnsemble(base_seed=42)
        state = LatentState.default()
        result = ens.predict(_default_features(), _default_fast_result(), state=state)
        assert isinstance(result, DeepResult)
        assert math.isfinite(result.mu)

    def test_extra_features_ignored(self):
        features = _default_features()
        features["unknown_feature"] = 999.0
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(features, _default_fast_result())
        assert isinstance(result, DeepResult)

    def test_latency_zero(self):
        ens = DeepPathEnsemble(base_seed=42)
        result = ens.predict(_default_features(), _default_fast_result(), latency_ms=0.0)
        assert result.latency_ms == 0.0

    def test_different_seeds_different_ensemble(self):
        ens1 = DeepPathEnsemble(base_seed=1)
        ens2 = DeepPathEnsemble(base_seed=2)
        r1 = ens1.predict(_default_features(), _default_fast_result())
        r2 = ens2.predict(_default_features(), _default_fast_result())
        # Different seeds should produce different results
        assert r1.mu != r2.mu or r1.sigma_squared != r2.sigma_squared


# =============================================================================
# SECTION 13 -- TestIntegration
# =============================================================================

class TestIntegration:
    def test_fast_to_deep_pipeline(self):
        """FastPathEnsemble -> DeepPathEnsemble end-to-end."""
        features = _default_features()
        state = _default_state()

        # Step 1: Fast path
        fast_ens = FastPathEnsemble(base_seed=42)
        fast_result = fast_ens.predict(features, state=state, latency_ms=2.0)
        assert isinstance(fast_result, FastResult)

        # Step 2: Check activation
        activated = should_activate_deep_path(fast_sigma=fast_result.sigma)

        # Step 3: Deep path (run regardless for test)
        deep_ens = DeepPathEnsemble(base_seed=42)
        deep_result = deep_ens.predict(
            features, fast_result, state=state, latency_ms=50.0
        )
        assert isinstance(deep_result, DeepResult)

        # Verify system contract fields
        assert math.isfinite(deep_result.mu)
        assert deep_result.sigma_squared >= 0.0
        assert deep_result.sigma_sq_aleatoric >= 0.0
        assert deep_result.sigma_sq_epistemic_model >= 0.0
        assert deep_result.sigma_sq_epistemic_data >= 0.0
        assert 0.0 <= deep_result.Q
        assert 0.0 <= deep_result.S
        assert 0.0 <= deep_result.R

    def test_pipeline_with_high_uncertainty(self):
        """Pipeline with high uncertainty triggering deep path."""
        features = {"volatility": 0.5, "momentum": 0.1, "trend_strength": -0.3}
        state = _default_state()

        fast_ens = FastPathEnsemble(base_seed=42)
        fast_result = fast_ens.predict(features, state=state)

        # High volatility should trigger deep path
        activated = should_activate_deep_path(fast_sigma=fast_result.sigma)

        deep_ens = DeepPathEnsemble(base_seed=42)
        deep_result = deep_ens.predict(features, fast_result, state=state)
        assert isinstance(deep_result, DeepResult)
        assert math.isfinite(deep_result.sigma_squared)

    def test_pipeline_without_state(self):
        """Pipeline without LatentState uses defaults."""
        features = _default_features()

        fast_ens = FastPathEnsemble(base_seed=42)
        fast_result = fast_ens.predict(features)

        deep_ens = DeepPathEnsemble(base_seed=42)
        deep_result = deep_ens.predict(features, fast_result)

        assert deep_result.Q == 0.5
        assert deep_result.S == 0.5
        assert deep_result.R == 0.5
        assert deep_result.sigma_sq_epistemic_data == 0.0
