# tests/unit/core/test_regime_detector.py
# Coverage target: jarvis/core/regime_detector.py -> 95%+
# Missing lines: 147, 155-160, 175, 207, 212, 217, 222, 276, 287-292, 324,
#                376, 390, 398, 410-417, 429-440

import math

import pytest

from jarvis.core.regime import GlobalRegimeState
from jarvis.core.regime_detector import (
    RegimeDetector,
    RegimeResult,
    _gaussian_log_prob,
    _emission_log_prob,
    _log_sum_exp,
    _normalise,
    _N_STATES,
    _STATE_TO_REGIME,
)


# =============================================================================
# Helper functions
# =============================================================================

class TestGaussianLogProb:
    def test_at_mean(self):
        lp = _gaussian_log_prob(0.0, 0.0, 1.0)
        assert abs(lp - (-0.5 * math.log(2 * math.pi))) < 1e-10

    def test_away_from_mean(self):
        lp = _gaussian_log_prob(1.0, 0.0, 1.0)
        assert lp < _gaussian_log_prob(0.0, 0.0, 1.0)


class TestEmissionLogProb:
    def test_with_known_features(self):
        features = {"volatility": 0.3, "stress": 0.1}
        lp = _emission_log_prob(features, 0)  # RISK_ON
        assert isinstance(lp, float)
        assert math.isfinite(lp)

    def test_with_non_finite_feature(self):
        # line 147: non-finite replaced with 0.0
        features = {"volatility": float("nan"), "stress": float("inf")}
        lp = _emission_log_prob(features, 0)
        assert math.isfinite(lp)

    def test_missing_features(self):
        lp = _emission_log_prob({}, 0)
        assert math.isfinite(lp)


class TestLogSumExp:
    def test_normal(self):
        result = _log_sum_exp([0.0, 0.0])
        assert abs(result - math.log(2.0)) < 1e-10

    def test_empty_list(self):
        # line 155-156
        assert _log_sum_exp([]) == -math.inf

    def test_all_neg_inf(self):
        # line 158-159
        assert _log_sum_exp([-math.inf, -math.inf]) == -math.inf

    def test_single_value(self):
        result = _log_sum_exp([5.0])
        assert abs(result - 5.0) < 1e-10


class TestNormalise:
    def test_normal(self):
        result = _normalise([1.0, 1.0, 1.0, 1.0, 1.0])
        assert abs(sum(result) - 1.0) < 1e-10
        assert all(abs(v - 0.2) < 1e-10 for v in result)

    def test_all_zeros_returns_uniform(self):
        # line 175
        result = _normalise([0.0, 0.0, 0.0, 0.0, 0.0])
        assert abs(sum(result) - 1.0) < 1e-10

    def test_non_finite_replaced(self):
        result = _normalise([1.0, float("nan"), float("inf"), 1.0, 1.0])
        assert abs(sum(result) - 1.0) < 1e-10
        assert all(v > 0 for v in result)


# =============================================================================
# RegimeResult dataclass (lines 207-222)
# =============================================================================

class TestRegimeResult:
    def test_valid_construction(self):
        r = RegimeResult(
            hmm_index=0,
            regime=GlobalRegimeState.RISK_ON,
            confidence=0.7,
            posterior=(0.7, 0.1, 0.1, 0.05, 0.05),
        )
        assert r.hmm_index == 0
        assert r.regime == GlobalRegimeState.RISK_ON

    def test_invalid_hmm_index_raises(self):
        # line 207
        with pytest.raises(ValueError, match="hmm_index"):
            RegimeResult(hmm_index=5, regime=GlobalRegimeState.RISK_ON,
                         confidence=0.5, posterior=(0.2,)*5)

    def test_invalid_regime_type_raises(self):
        # line 212
        with pytest.raises(TypeError, match="GlobalRegimeState"):
            RegimeResult(hmm_index=0, regime="RISK_ON",
                         confidence=0.5, posterior=(0.2,)*5)

    def test_confidence_out_of_range_raises(self):
        # line 217
        with pytest.raises(ValueError, match="confidence"):
            RegimeResult(hmm_index=0, regime=GlobalRegimeState.RISK_ON,
                         confidence=1.5, posterior=(0.2,)*5)

    def test_wrong_posterior_length_raises(self):
        # line 222
        with pytest.raises(ValueError, match="posterior"):
            RegimeResult(hmm_index=0, regime=GlobalRegimeState.RISK_ON,
                         confidence=0.5, posterior=(0.5, 0.5))


# =============================================================================
# RegimeDetector.__init__ (lines 276, 287-292)
# =============================================================================

class TestRegimeDetectorInit:
    def test_default_construction(self):
        d = RegimeDetector()
        assert len(d._posterior) == 5
        assert abs(sum(d._posterior) - 1.0) < 1e-10

    def test_custom_transition_matrix(self):
        # line 276
        custom = [[0.2]*5 for _ in range(5)]
        d = RegimeDetector(transition_matrix=custom)
        tm = d.transition_probability()
        assert len(tm) == 5
        for row in tm:
            assert abs(sum(row) - 1.0) < 1e-10

    def test_custom_initial_prior(self):
        d = RegimeDetector(initial_prior=[1.0, 0.0, 0.0, 0.0, 0.0])
        assert d._posterior[0] > 0.5

    def test_wrong_prior_length_raises(self):
        # lines 287-292
        with pytest.raises(ValueError, match="length"):
            RegimeDetector(initial_prior=[0.5, 0.5])

    def test_wrong_transition_rows_raises(self):
        with pytest.raises(ValueError, match="rows"):
            RegimeDetector(transition_matrix=[[0.5]*5 for _ in range(3)])

    def test_wrong_transition_cols_raises(self):
        matrix = [[0.2]*5 for _ in range(5)]
        matrix[2] = [0.25, 0.25, 0.25]  # wrong length
        with pytest.raises(ValueError, match="columns"):
            RegimeDetector(transition_matrix=matrix)


# =============================================================================
# RegimeDetector.detect_regime (line 324)
# =============================================================================

class TestDetectRegime:
    def test_basic_detection(self):
        d = RegimeDetector()
        features = {"volatility": 0.3, "trend_strength": 0.7, "stress": 0.1}
        result = d.detect_regime(features)
        assert isinstance(result, RegimeResult)
        assert isinstance(result.regime, GlobalRegimeState)
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.posterior) == 5

    def test_none_features_raises(self):
        # line 324
        d = RegimeDetector()
        with pytest.raises(TypeError, match="None"):
            d.detect_regime(None)

    def test_crisis_features(self):
        d = RegimeDetector()
        crisis_features = {"volatility": 2.0, "stress": 1.5, "momentum": -0.2}
        for _ in range(10):
            result = d.detect_regime(crisis_features)
        assert result.regime in (GlobalRegimeState.CRISIS, GlobalRegimeState.RISK_OFF)

    def test_sequential_updates_change_posterior(self):
        d = RegimeDetector()
        r1 = d.detect_regime({"volatility": 0.3})
        r2 = d.detect_regime({"volatility": 2.0})
        assert r1.posterior != r2.posterior

    def test_deterministic(self):
        d1 = RegimeDetector()
        d2 = RegimeDetector()
        features = {"volatility": 0.5, "stress": 0.3}
        r1 = d1.detect_regime(features)
        r2 = d2.detect_regime(features)
        assert r1.posterior == r2.posterior
        assert r1.hmm_index == r2.hmm_index


# =============================================================================
# RegimeDetector.transition_probability (line 376)
# =============================================================================

class TestTransitionProbability:
    def test_returns_5x5(self):
        d = RegimeDetector()
        tm = d.transition_probability()
        assert len(tm) == 5
        for row in tm:
            assert len(row) == 5
            assert abs(sum(row) - 1.0) < 1e-10

    def test_deep_copy(self):
        # line 376
        d = RegimeDetector()
        tm = d.transition_probability()
        tm[0][0] = 999.0
        assert d.transition_probability()[0][0] != 999.0


# =============================================================================
# RegimeDetector.regime_confidence (line 390)
# =============================================================================

class TestRegimeConfidence:
    def test_initial_confidence(self):
        d = RegimeDetector()
        conf = d.regime_confidence()
        assert 0.0 <= conf <= 1.0

    def test_after_detection(self):
        # line 390
        d = RegimeDetector()
        d.detect_regime({"volatility": 0.3})
        conf = d.regime_confidence()
        assert 0.0 <= conf <= 1.0


# =============================================================================
# RegimeDetector.current_posterior (line 398)
# =============================================================================

class TestCurrentPosterior:
    def test_returns_copy(self):
        # line 398
        d = RegimeDetector()
        p = d.current_posterior()
        assert len(p) == 5
        p[0] = 999.0
        assert d.current_posterior()[0] != 999.0


# =============================================================================
# RegimeDetector.reset (lines 410-417)
# =============================================================================

class TestReset:
    def test_reset_to_uniform(self):
        d = RegimeDetector()
        d.detect_regime({"volatility": 2.0, "stress": 1.5})
        d.reset()
        p = d.current_posterior()
        assert all(abs(v - 0.2) < 1e-10 for v in p)

    def test_reset_with_custom_prior(self):
        d = RegimeDetector()
        d.reset(prior=[1.0, 0.0, 0.0, 0.0, 0.0])
        assert d.current_posterior()[0] > 0.5

    def test_reset_wrong_length_raises(self):
        # lines 413-416
        d = RegimeDetector()
        with pytest.raises(ValueError, match="length"):
            d.reset(prior=[0.5, 0.5])


# =============================================================================
# RegimeDetector._validate_transition (lines 429-440)
# =============================================================================

class TestValidateTransition:
    def test_valid_matrix(self):
        matrix = [[0.2]*5 for _ in range(5)]
        result = RegimeDetector._validate_transition(matrix)
        assert len(result) == 5

    def test_wrong_rows(self):
        # line 429-433
        with pytest.raises(ValueError, match="rows"):
            RegimeDetector._validate_transition([[0.2]*5])

    def test_wrong_cols(self):
        # line 435-439
        matrix = [[0.2]*5 for _ in range(5)]
        matrix[3] = [0.5, 0.5]
        with pytest.raises(ValueError, match="columns"):
            RegimeDetector._validate_transition(matrix)
