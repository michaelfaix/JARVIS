# =============================================================================
# tests/unit/intelligence/test_bayesian_confidence.py
# Tests for jarvis/intelligence/bayesian_confidence.py
# =============================================================================

import pytest

from jarvis.intelligence.bayesian_confidence import (
    LIKELIHOOD_TABLE,
    SPIKE_UP_MIN_QUALITY,
    BayesianConfidenceUpdate,
    data_quality_band,
    BayesianConfidenceEngine,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_likelihood_table_regime_count(self):
        assert len(LIKELIHOOD_TABLE) == 5

    def test_likelihood_table_regimes(self):
        expected = {"TRENDING", "RANGING", "HIGH_VOL", "SHOCK", "UNKNOWN"}
        assert set(LIKELIHOOD_TABLE.keys()) == expected

    def test_likelihood_table_bands(self):
        for regime, bands in LIKELIHOOD_TABLE.items():
            assert set(bands.keys()) == {"high", "medium", "low"}

    def test_likelihood_table_values_in_range(self):
        for regime, bands in LIKELIHOOD_TABLE.items():
            for band, val in bands.items():
                assert 0.0 <= val <= 1.0, f"{regime}/{band} = {val}"

    def test_trending_high(self):
        assert LIKELIHOOD_TABLE["TRENDING"]["high"] == 0.85

    def test_unknown_low(self):
        assert LIKELIHOOD_TABLE["UNKNOWN"]["low"] == 0.08

    def test_shock_medium(self):
        assert LIKELIHOOD_TABLE["SHOCK"]["medium"] == 0.20

    def test_spike_up_min_quality(self):
        assert SPIKE_UP_MIN_QUALITY == 0.70

    def test_likelihood_monotonic_per_regime(self):
        """Within each regime, high > medium > low."""
        for regime, bands in LIKELIHOOD_TABLE.items():
            assert bands["high"] > bands["medium"] > bands["low"], regime

    def test_likelihood_monotonic_per_band(self):
        """For high band: TRENDING > RANGING > HIGH_VOL > SHOCK > UNKNOWN."""
        for band in ["high", "medium", "low"]:
            vals = [LIKELIHOOD_TABLE[r][band] for r in
                    ["TRENDING", "RANGING", "HIGH_VOL", "SHOCK", "UNKNOWN"]]
            for i in range(len(vals) - 1):
                assert vals[i] > vals[i + 1], f"band={band}"


# =============================================================================
# SECTION 2 -- DATA QUALITY BAND
# =============================================================================

class TestDataQualityBand:
    def test_high(self):
        assert data_quality_band(0.75) == "high"

    def test_high_above(self):
        assert data_quality_band(0.90) == "high"

    def test_medium(self):
        assert data_quality_band(0.50) == "medium"

    def test_medium_above(self):
        assert data_quality_band(0.74) == "medium"

    def test_low(self):
        assert data_quality_band(0.49) == "low"

    def test_low_zero(self):
        assert data_quality_band(0.0) == "low"

    def test_type_error(self):
        with pytest.raises(TypeError, match="must be numeric"):
            data_quality_band("high")

    def test_int_accepted(self):
        assert data_quality_band(1) == "high"
        assert data_quality_band(0) == "low"


# =============================================================================
# SECTION 3 -- BAYESIAN CONFIDENCE UPDATE DATACLASS
# =============================================================================

class TestBayesianConfidenceUpdate:
    def test_frozen(self):
        u = BayesianConfidenceUpdate(0.5, 0.6, 0.4, 0.75, True, False, True)
        with pytest.raises(AttributeError):
            u.posterior_confidence = 0.9

    def test_fields(self):
        u = BayesianConfidenceUpdate(
            prior_confidence=0.5,
            likelihood=0.6,
            evidence=0.4,
            posterior_confidence=0.75,
            regime_stable=True,
            fm_active=False,
            update_permitted=True,
        )
        assert u.prior_confidence == 0.5
        assert u.likelihood == 0.6
        assert u.evidence == 0.4
        assert u.posterior_confidence == 0.75


# =============================================================================
# SECTION 4 -- ENGINE BASIC
# =============================================================================

class TestEngineBasic:
    def test_basic_update(self):
        eng = BayesianConfidenceEngine()
        result = eng.update(
            prior_confidence=0.5,
            regime="TRENDING",
            quality_score=0.80,
            fm_active=False,
            regime_stable=True,
        )
        assert isinstance(result, BayesianConfidenceUpdate)
        assert 0.0 <= result.posterior_confidence <= 1.0

    def test_trending_high_quality_increases(self):
        """TRENDING with high quality should generally increase confidence."""
        eng = BayesianConfidenceEngine()
        result = eng.update(0.5, "TRENDING", 0.80, False, True)
        # With TRENDING/high, likelihood=0.85 which is highest
        assert result.posterior_confidence >= result.prior_confidence

    def test_shock_low_quality_decreases(self):
        """SHOCK with low quality should decrease confidence."""
        eng = BayesianConfidenceEngine()
        result = eng.update(0.5, "SHOCK", 0.30, False, True)
        assert result.posterior_confidence <= result.prior_confidence

    def test_unknown_regime_fallback(self):
        """Unrecognised regime falls back to UNKNOWN."""
        eng = BayesianConfidenceEngine()
        result = eng.update(0.5, "NONEXISTENT", 0.80, False, True)
        # Should use UNKNOWN likelihood
        result_unk = eng.update(0.5, "UNKNOWN", 0.80, False, True)
        assert result.likelihood == result_unk.likelihood

    def test_all_regimes_valid(self):
        eng = BayesianConfidenceEngine()
        for regime in LIKELIHOOD_TABLE:
            result = eng.update(0.5, regime, 0.80, False, True)
            assert 0.0 <= result.posterior_confidence <= 1.0


# =============================================================================
# SECTION 5 -- SPIKE-UP CONSTRAINT
# =============================================================================

class TestSpikeUpConstraint:
    def test_spike_up_permitted(self):
        eng = BayesianConfidenceEngine()
        result = eng.update(0.3, "TRENDING", 0.80, False, True)
        assert result.update_permitted is True
        # With TRENDING/high quality, posterior should increase
        assert result.posterior_confidence >= 0.3

    def test_spike_up_blocked_fm_active(self):
        eng = BayesianConfidenceEngine()
        result = eng.update(0.3, "TRENDING", 0.80, True, True)
        assert result.update_permitted is False
        assert result.posterior_confidence <= 0.3

    def test_spike_up_blocked_regime_unstable(self):
        eng = BayesianConfidenceEngine()
        result = eng.update(0.3, "TRENDING", 0.80, False, False)
        assert result.update_permitted is False
        assert result.posterior_confidence <= 0.3

    def test_spike_up_blocked_low_quality(self):
        eng = BayesianConfidenceEngine()
        result = eng.update(0.3, "TRENDING", 0.69, False, True)
        assert result.update_permitted is False
        assert result.posterior_confidence <= 0.3

    def test_spike_up_at_exact_threshold(self):
        eng = BayesianConfidenceEngine()
        result = eng.update(0.3, "TRENDING", 0.70, False, True)
        assert result.update_permitted is True

    def test_can_always_decrease(self):
        """Even without spike-up, posterior can decrease."""
        eng = BayesianConfidenceEngine()
        result = eng.update(0.8, "SHOCK", 0.30, True, False)
        assert result.posterior_confidence <= 0.8


# =============================================================================
# SECTION 6 -- JOINT MULTIPLIER
# =============================================================================

class TestJointMultiplier:
    def test_default_is_one(self):
        eng = BayesianConfidenceEngine()
        r1 = eng.update(0.5, "TRENDING", 0.80, False, True)
        r2 = eng.update(0.5, "TRENDING", 0.80, False, True, 1.0)
        assert r1.likelihood == r2.likelihood

    def test_multiplier_reduces_likelihood(self):
        eng = BayesianConfidenceEngine()
        r1 = eng.update(0.5, "TRENDING", 0.80, False, True, 1.0)
        r2 = eng.update(0.5, "TRENDING", 0.80, False, True, 2.0)
        assert r2.likelihood < r1.likelihood

    def test_high_multiplier(self):
        eng = BayesianConfidenceEngine()
        result = eng.update(0.5, "TRENDING", 0.80, False, True, 10.0)
        assert result.likelihood < 0.1

    def test_multiplier_clipped_to_zero_one(self):
        eng = BayesianConfidenceEngine()
        result = eng.update(0.5, "TRENDING", 0.80, False, True, 0.5)
        assert result.likelihood <= 1.0


# =============================================================================
# SECTION 7 -- VALIDATION
# =============================================================================

class TestValidation:
    def test_prior_type_error(self):
        eng = BayesianConfidenceEngine()
        with pytest.raises(TypeError, match="prior_confidence must be numeric"):
            eng.update("bad", "TRENDING", 0.80, False, True)

    def test_prior_out_of_range(self):
        eng = BayesianConfidenceEngine()
        with pytest.raises(ValueError, match="prior_confidence must be in"):
            eng.update(1.5, "TRENDING", 0.80, False, True)

    def test_quality_type_error(self):
        eng = BayesianConfidenceEngine()
        with pytest.raises(TypeError, match="quality_score must be numeric"):
            eng.update(0.5, "TRENDING", "bad", False, True)

    def test_fm_active_type_error(self):
        eng = BayesianConfidenceEngine()
        with pytest.raises(TypeError, match="fm_active must be bool"):
            eng.update(0.5, "TRENDING", 0.80, 1, True)

    def test_regime_stable_type_error(self):
        eng = BayesianConfidenceEngine()
        with pytest.raises(TypeError, match="regime_stable must be bool"):
            eng.update(0.5, "TRENDING", 0.80, False, 1)

    def test_joint_multiplier_type_error(self):
        eng = BayesianConfidenceEngine()
        with pytest.raises(TypeError, match="joint_multiplier must be numeric"):
            eng.update(0.5, "TRENDING", 0.80, False, True, "bad")

    def test_joint_multiplier_zero(self):
        eng = BayesianConfidenceEngine()
        with pytest.raises(ValueError, match="joint_multiplier must be > 0"):
            eng.update(0.5, "TRENDING", 0.80, False, True, 0.0)

    def test_joint_multiplier_negative(self):
        eng = BayesianConfidenceEngine()
        with pytest.raises(ValueError, match="joint_multiplier must be > 0"):
            eng.update(0.5, "TRENDING", 0.80, False, True, -1.0)


# =============================================================================
# SECTION 8 -- EDGE CASES
# =============================================================================

class TestEdgeCases:
    def test_prior_zero(self):
        eng = BayesianConfidenceEngine()
        result = eng.update(0.0, "TRENDING", 0.80, False, True)
        # 0 * anything = 0
        assert result.posterior_confidence == 0.0

    def test_prior_one(self):
        eng = BayesianConfidenceEngine()
        result = eng.update(1.0, "TRENDING", 0.80, False, True)
        assert result.posterior_confidence <= 1.0

    def test_quality_zero(self):
        eng = BayesianConfidenceEngine()
        result = eng.update(0.5, "TRENDING", 0.0, False, True)
        assert data_quality_band(0.0) == "low"
        assert 0.0 <= result.posterior_confidence <= 1.0

    def test_quality_one(self):
        eng = BayesianConfidenceEngine()
        result = eng.update(0.5, "TRENDING", 1.0, False, True)
        assert data_quality_band(1.0) == "high"

    def test_evidence_positive(self):
        eng = BayesianConfidenceEngine()
        result = eng.update(0.5, "TRENDING", 0.80, False, True)
        assert result.evidence > 0


# =============================================================================
# SECTION 9 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_same_inputs_same_output(self):
        eng = BayesianConfidenceEngine()
        results = [
            eng.update(0.5, "TRENDING", 0.80, False, True)
            for _ in range(10)
        ]
        posteriors = [r.posterior_confidence for r in results]
        assert len(set(posteriors)) == 1

    def test_independent_engines(self):
        r1 = BayesianConfidenceEngine().update(0.5, "RANGING", 0.60, True, False)
        r2 = BayesianConfidenceEngine().update(0.5, "RANGING", 0.60, True, False)
        assert r1 == r2
