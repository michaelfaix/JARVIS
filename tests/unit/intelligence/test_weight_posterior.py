# =============================================================================
# tests/unit/intelligence/test_weight_posterior.py
# Tests for jarvis/intelligence/weight_posterior.py
# =============================================================================

import pytest

from jarvis.intelligence.weight_posterior import (
    HISTORY_WINDOW,
    FM_DEFENSIVE_CAP,
    WeightPosteriorModel,
    WeightPosteriorEstimator,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_history_window(self):
        assert HISTORY_WINDOW == 20

    def test_fm_defensive_cap(self):
        assert FM_DEFENSIVE_CAP == 0.5


# =============================================================================
# SECTION 2 -- WEIGHT POSTERIOR MODEL
# =============================================================================

class TestWeightPosteriorModel:
    def test_frozen(self):
        m = WeightPosteriorModel("S1", 0.5, 0.4, 0.1, 10, 0.8, 0.9)
        with pytest.raises(AttributeError):
            m.posterior_mean = 0.99

    def test_fields(self):
        m = WeightPosteriorModel(
            strategy_id="S1",
            prior_weight=0.5,
            posterior_mean=0.4,
            posterior_std=0.1,
            evidence_count=10,
            regime_alignment=0.8,
            confidence_factor=0.9,
        )
        assert m.strategy_id == "S1"
        assert m.prior_weight == 0.5
        assert m.posterior_mean == 0.4
        assert m.posterior_std == 0.1
        assert m.evidence_count == 10
        assert m.regime_alignment == 0.8
        assert m.confidence_factor == 0.9

    def test_equality(self):
        m1 = WeightPosteriorModel("S1", 0.5, 0.4, 0.1, 10, 0.8, 0.9)
        m2 = WeightPosteriorModel("S1", 0.5, 0.4, 0.1, 10, 0.8, 0.9)
        assert m1 == m2


# =============================================================================
# SECTION 3 -- ESTIMATOR: FEW OBSERVATIONS
# =============================================================================

class TestEstimatorFewObservations:
    def test_empty_history(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 0.8, [], 0.9, 0.7, False)
        assert result.posterior_mean == pytest.approx(0.8 * 0.9 * 0.7)
        assert result.posterior_std == pytest.approx(0.5)
        assert result.evidence_count == 0

    def test_single_observation(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 0.8, [0.6], 0.9, 0.7, False)
        assert result.posterior_mean == pytest.approx(0.8 * 0.9 * 0.7)
        assert result.posterior_std == pytest.approx(0.5)
        assert result.evidence_count == 1

    def test_zero_alignment(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 0.8, [], 0.0, 0.7, False)
        assert result.posterior_mean == 0.0

    def test_zero_confidence(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 0.8, [], 0.9, 0.0, False)
        assert result.posterior_mean == 0.0


# =============================================================================
# SECTION 4 -- ESTIMATOR: SUFFICIENT OBSERVATIONS
# =============================================================================

class TestEstimatorSufficientObservations:
    def test_two_observations(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 0.6, [0.5, 0.7], 1.0, 1.0, False)
        # posterior_mean = (0.5*0.6 + 0.5*mean([0.5,0.7])) * 1.0 * 1.0
        obs_mean = 0.6
        expected = (0.5 * 0.6 + 0.5 * obs_mean) * 1.0 * 1.0
        assert result.posterior_mean == pytest.approx(expected)
        assert result.evidence_count == 2

    def test_many_observations(self):
        est = WeightPosteriorEstimator()
        hist = [0.5] * 30
        result = est.estimate("S1", 0.5, hist, 1.0, 1.0, False)
        # obs_mean = 0.5, prior = 0.5
        # posterior_mean = (0.5*0.5 + 0.5*0.5) * 1 * 1 = 0.5
        assert result.posterior_mean == pytest.approx(0.5)
        # Uses last 20
        assert result.evidence_count == 30

    def test_history_window_respected(self):
        """Only last HISTORY_WINDOW observations used for mean/std."""
        est = WeightPosteriorEstimator()
        # 10 old values of 0.0, then 20 values of 1.0
        hist = [0.0] * 10 + [1.0] * 20
        result = est.estimate("S1", 0.5, hist, 1.0, 1.0, False)
        # Last 20 are all 1.0, obs_mean = 1.0
        expected = (0.5 * 0.5 + 0.5 * 1.0) * 1.0 * 1.0
        assert result.posterior_mean == pytest.approx(expected)

    def test_regime_alignment_scaling(self):
        est = WeightPosteriorEstimator()
        r1 = est.estimate("S1", 0.5, [0.5, 0.5], 1.0, 1.0, False)
        r2 = est.estimate("S1", 0.5, [0.5, 0.5], 0.5, 1.0, False)
        assert r2.posterior_mean == pytest.approx(r1.posterior_mean * 0.5)

    def test_confidence_scaling(self):
        est = WeightPosteriorEstimator()
        r1 = est.estimate("S1", 0.5, [0.5, 0.5], 1.0, 1.0, False)
        r2 = est.estimate("S1", 0.5, [0.5, 0.5], 1.0, 0.5, False)
        assert r2.posterior_mean == pytest.approx(r1.posterior_mean * 0.5)

    def test_posterior_std_decreases_with_observations(self):
        est = WeightPosteriorEstimator()
        r_few = est.estimate("S1", 0.5, [0.5, 0.6], 1.0, 1.0, False)
        r_many = est.estimate("S1", 0.5, [0.5, 0.6] * 10, 1.0, 1.0, False)
        assert r_many.posterior_std <= r_few.posterior_std


# =============================================================================
# SECTION 5 -- FM DEFENSIVE CAP
# =============================================================================

class TestFmDefensiveCap:
    def test_fm_caps_posterior(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 0.8, [0.8, 0.8], 1.0, 1.0, True)
        assert result.posterior_mean <= 0.8 * FM_DEFENSIVE_CAP

    def test_fm_cap_with_zero_prior(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 0.0, [0.5, 0.5], 1.0, 1.0, True)
        assert result.posterior_mean == 0.0

    def test_fm_no_cap_when_false(self):
        est = WeightPosteriorEstimator()
        r_no_fm = est.estimate("S1", 0.8, [0.8, 0.8], 1.0, 1.0, False)
        r_fm = est.estimate("S1", 0.8, [0.8, 0.8], 1.0, 1.0, True)
        assert r_fm.posterior_mean <= r_no_fm.posterior_mean

    def test_fm_cap_value(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 0.6, [], 1.0, 1.0, True)
        # Without FM: 0.6*1*1 = 0.6; with FM: min(0.6, 0.6*0.5) = 0.3
        assert result.posterior_mean == pytest.approx(0.3)

    def test_fm_cap_few_obs(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 1.0, [], 1.0, 1.0, True)
        assert result.posterior_mean <= 1.0 * FM_DEFENSIVE_CAP


# =============================================================================
# SECTION 6 -- CLIPPING
# =============================================================================

class TestClipping:
    def test_posterior_mean_clipped_to_one(self):
        est = WeightPosteriorEstimator()
        # High values everywhere
        result = est.estimate("S1", 1.0, [1.0, 1.0], 1.0, 1.0, False)
        assert result.posterior_mean <= 1.0

    def test_posterior_mean_clipped_to_zero(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 0.0, [0.0, 0.0], 0.0, 0.0, False)
        assert result.posterior_mean >= 0.0

    def test_posterior_std_clipped_to_half(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 0.5, [], 1.0, 1.0, False)
        assert result.posterior_std <= 0.5

    def test_prior_weight_clipped(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 1.5, [0.5, 0.5], 1.0, 1.0, False)
        assert result.prior_weight == 1.0

    def test_regime_alignment_clipped(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 0.5, [0.5, 0.5], 1.5, 1.0, False)
        assert result.regime_alignment == 1.0

    def test_confidence_clipped(self):
        est = WeightPosteriorEstimator()
        result = est.estimate("S1", 0.5, [0.5, 0.5], 1.0, 1.5, False)
        assert result.confidence_factor == 1.0


# =============================================================================
# SECTION 7 -- VALIDATION
# =============================================================================

class TestValidation:
    def test_strategy_id_type_error(self):
        est = WeightPosteriorEstimator()
        with pytest.raises(TypeError, match="strategy_id must be a string"):
            est.estimate(123, 0.5, [], 1.0, 1.0, False)

    def test_strategy_id_empty(self):
        est = WeightPosteriorEstimator()
        with pytest.raises(ValueError, match="strategy_id must not be empty"):
            est.estimate("", 0.5, [], 1.0, 1.0, False)

    def test_prior_weight_type_error(self):
        est = WeightPosteriorEstimator()
        with pytest.raises(TypeError, match="prior_weight must be numeric"):
            est.estimate("S1", "bad", [], 1.0, 1.0, False)

    def test_historical_weights_type_error(self):
        est = WeightPosteriorEstimator()
        with pytest.raises(TypeError, match="historical_weights must be a list"):
            est.estimate("S1", 0.5, (0.5, 0.6), 1.0, 1.0, False)

    def test_regime_alignment_type_error(self):
        est = WeightPosteriorEstimator()
        with pytest.raises(TypeError, match="regime_alignment must be numeric"):
            est.estimate("S1", 0.5, [], "bad", 1.0, False)

    def test_confidence_q_type_error(self):
        est = WeightPosteriorEstimator()
        with pytest.raises(TypeError, match="confidence_q must be numeric"):
            est.estimate("S1", 0.5, [], 1.0, "bad", False)

    def test_fm_active_type_error(self):
        est = WeightPosteriorEstimator()
        with pytest.raises(TypeError, match="fm_active must be bool"):
            est.estimate("S1", 0.5, [], 1.0, 1.0, 1)


# =============================================================================
# SECTION 8 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_same_inputs_same_output(self):
        est = WeightPosteriorEstimator()
        hist = [0.5, 0.6, 0.4, 0.55, 0.45]
        results = [
            est.estimate("S1", 0.5, hist, 0.8, 0.7, False)
            for _ in range(10)
        ]
        means = [r.posterior_mean for r in results]
        assert len(set(means)) == 1

    def test_independent_estimators(self):
        hist = [0.5, 0.6, 0.4]
        r1 = WeightPosteriorEstimator().estimate("S1", 0.5, hist, 0.8, 0.9, False)
        r2 = WeightPosteriorEstimator().estimate("S1", 0.5, hist, 0.8, 0.9, False)
        assert r1 == r2

    def test_fm_deterministic(self):
        est = WeightPosteriorEstimator()
        hist = [0.5, 0.6]
        r1 = est.estimate("S1", 0.8, hist, 1.0, 1.0, True)
        r2 = est.estimate("S1", 0.8, hist, 1.0, 1.0, True)
        assert r1.posterior_mean == r2.posterior_mean
