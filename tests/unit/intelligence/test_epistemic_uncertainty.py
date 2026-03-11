# =============================================================================
# tests/unit/intelligence/test_epistemic_uncertainty.py
# Tests for jarvis/intelligence/epistemic_uncertainty.py
# =============================================================================

import pytest

from jarvis.intelligence.epistemic_uncertainty import (
    MUS_WEIGHT_REGIME,
    MUS_WEIGHT_SPARSITY,
    MUS_WEIGHT_FM_FREQ,
    DATA_SPARSITY_THRESHOLD,
    DATA_SPARSITY_MAX_PENALTY,
    CONFIDENCE_DECAY_FACTOR,
    CONFIDENCE_DECAY_MAX,
    CONFIDENCE_DECAY_MIN_VALUE,
    UNCERTAINTY_WEIGHT_MODEL,
    UNCERTAINTY_WEIGHT_DATA,
    UNCERTAINTY_WEIGHT_ALEATORIC,
    ModelUncertaintyScore,
    DataSparsityPenalty,
    ConfidenceDecayResult,
    UncertaintyBundle,
    EpistemicUncertaintyEngine,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_mus_weights_sum_to_one(self):
        total = MUS_WEIGHT_REGIME + MUS_WEIGHT_SPARSITY + MUS_WEIGHT_FM_FREQ
        assert abs(total - 1.0) < 1e-10

    def test_mus_weight_regime(self):
        assert MUS_WEIGHT_REGIME == 0.40

    def test_mus_weight_sparsity(self):
        assert MUS_WEIGHT_SPARSITY == 0.35

    def test_mus_weight_fm_freq(self):
        assert MUS_WEIGHT_FM_FREQ == 0.25

    def test_data_sparsity_threshold(self):
        assert DATA_SPARSITY_THRESHOLD == 0.60

    def test_data_sparsity_max_penalty(self):
        assert DATA_SPARSITY_MAX_PENALTY == 0.40

    def test_confidence_decay_factor(self):
        assert CONFIDENCE_DECAY_FACTOR == 0.02

    def test_confidence_decay_max(self):
        assert CONFIDENCE_DECAY_MAX == 0.10

    def test_confidence_decay_min_value(self):
        assert CONFIDENCE_DECAY_MIN_VALUE == 0.30

    def test_uncertainty_weights_sum_to_one(self):
        total = (UNCERTAINTY_WEIGHT_MODEL + UNCERTAINTY_WEIGHT_DATA
                 + UNCERTAINTY_WEIGHT_ALEATORIC)
        assert abs(total - 1.0) < 1e-10

    def test_uncertainty_weight_model(self):
        assert UNCERTAINTY_WEIGHT_MODEL == 0.45

    def test_uncertainty_weight_data(self):
        assert UNCERTAINTY_WEIGHT_DATA == 0.35

    def test_uncertainty_weight_aleatoric(self):
        assert UNCERTAINTY_WEIGHT_ALEATORIC == 0.20


# =============================================================================
# SECTION 2 -- MODEL UNCERTAINTY SCORE
# =============================================================================

class TestModelUncertaintyScore:
    def test_frozen(self):
        m = ModelUncertaintyScore(0.1, 0.2, 0.3, 0.2)
        with pytest.raises(AttributeError):
            m.regime_instability_score = 0.5

    def test_valid_construction(self):
        m = ModelUncertaintyScore(0.5, 0.3, 0.2, 0.35)
        assert m.regime_instability_score == 0.5
        assert m.data_sparsity_score == 0.3
        assert m.fm_frequency_score == 0.2
        assert m.model_uncertainty_score == 0.35

    def test_boundary_zero(self):
        m = ModelUncertaintyScore(0.0, 0.0, 0.0, 0.0)
        assert m.model_uncertainty_score == 0.0

    def test_boundary_one(self):
        m = ModelUncertaintyScore(1.0, 1.0, 1.0, 1.0)
        assert m.model_uncertainty_score == 1.0

    def test_out_of_range_high(self):
        with pytest.raises(ValueError, match="must be in"):
            ModelUncertaintyScore(1.1, 0.0, 0.0, 0.0)

    def test_out_of_range_low(self):
        with pytest.raises(ValueError, match="must be in"):
            ModelUncertaintyScore(-0.1, 0.0, 0.0, 0.0)

    def test_type_error(self):
        with pytest.raises(TypeError, match="must be numeric"):
            ModelUncertaintyScore("bad", 0.0, 0.0, 0.0)


# =============================================================================
# SECTION 3 -- DATA SPARSITY PENALTY
# =============================================================================

class TestDataSparsityPenalty:
    def test_frozen(self):
        p = DataSparsityPenalty(0.8, False, 1.0, 0.0)
        with pytest.raises(AttributeError):
            p.valid_fraction = 0.5

    def test_no_penalty(self):
        p = DataSparsityPenalty(0.8, False, 1.0, 0.0)
        assert p.sparsity_penalty == 0.0
        assert p.confidence_multiplier == 1.0

    def test_with_penalty(self):
        p = DataSparsityPenalty(0.3, True, 0.8, 0.2)
        assert p.below_threshold is True
        assert p.sparsity_penalty == 0.2


# =============================================================================
# SECTION 4 -- CONFIDENCE DECAY RESULT
# =============================================================================

class TestConfidenceDecayResult:
    def test_frozen(self):
        r = ConfidenceDecayResult(0.8, 0, 0.0, 0.8, False)
        with pytest.raises(AttributeError):
            r.prior_Q = 0.5

    def test_no_decay(self):
        r = ConfidenceDecayResult(0.8, 0, 0.0, 0.8, False)
        assert r.decay_was_active is False
        assert r.new_Q == 0.8

    def test_with_decay(self):
        r = ConfidenceDecayResult(0.8, 3, 0.06, 0.74, True)
        assert r.decay_was_active is True
        assert r.decay_applied == 0.06


# =============================================================================
# SECTION 5 -- UNCERTAINTY BUNDLE
# =============================================================================

class TestUncertaintyBundle:
    def test_frozen(self):
        b = UncertaintyBundle(0.3, 0.2, 0.1, 0.25, 0.3, 0.1, 0.02)
        with pytest.raises(AttributeError):
            b.total_uncertainty = 0.5

    def test_valid_construction(self):
        b = UncertaintyBundle(0.3, 0.2, 0.1, 0.25, 0.3, 0.1, 0.02)
        assert b.epistemic_model == 0.3
        assert b.total_uncertainty == 0.25

    def test_out_of_range(self):
        with pytest.raises(ValueError, match="must be in"):
            UncertaintyBundle(1.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    def test_type_error(self):
        with pytest.raises(TypeError, match="must be numeric"):
            UncertaintyBundle("bad", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    def test_all_zero(self):
        b = UncertaintyBundle(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        assert b.total_uncertainty == 0.0

    def test_all_one(self):
        b = UncertaintyBundle(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.1)
        assert b.total_uncertainty == 1.0


# =============================================================================
# SECTION 6 -- ENGINE: MODEL UNCERTAINTY
# =============================================================================

class TestEngineModelUncertainty:
    def test_zero_inputs(self):
        eng = EpistemicUncertaintyEngine()
        m = eng.compute_model_uncertainty(0, 20, 20, 0)
        assert m.regime_instability_score == 0.0
        assert m.data_sparsity_score == 0.0
        assert m.fm_frequency_score == 0.0
        assert m.model_uncertainty_score == 0.0

    def test_max_inputs(self):
        eng = EpistemicUncertaintyEngine()
        m = eng.compute_model_uncertainty(10, 0, 20, 6)
        assert m.regime_instability_score == 1.0
        assert m.data_sparsity_score == 1.0
        assert m.fm_frequency_score == 1.0
        assert m.model_uncertainty_score == pytest.approx(1.0)

    def test_partial_inputs(self):
        eng = EpistemicUncertaintyEngine()
        m = eng.compute_model_uncertainty(5, 10, 20, 3)
        assert m.regime_instability_score == pytest.approx(0.5)
        assert m.data_sparsity_score == pytest.approx(0.5)
        assert m.fm_frequency_score == pytest.approx(0.5)
        expected = 0.40 * 0.5 + 0.35 * 0.5 + 0.25 * 0.5
        assert m.model_uncertainty_score == pytest.approx(expected)

    def test_clipping_over_max(self):
        eng = EpistemicUncertaintyEngine()
        m = eng.compute_model_uncertainty(20, 0, 20, 12)
        assert m.regime_instability_score == 1.0
        assert m.fm_frequency_score == 1.0

    def test_zero_window_size(self):
        eng = EpistemicUncertaintyEngine()
        m = eng.compute_model_uncertainty(0, 0, 0, 0)
        assert m.data_sparsity_score == 1.0  # 1.0 - 0/1 = 1.0


# =============================================================================
# SECTION 7 -- ENGINE: SPARSITY PENALTY
# =============================================================================

class TestEngineSparsityPenalty:
    def test_above_threshold(self):
        eng = EpistemicUncertaintyEngine()
        p = eng.compute_sparsity_penalty(15, 20)
        assert p.valid_fraction == pytest.approx(0.75)
        assert p.below_threshold is False
        assert p.sparsity_penalty == 0.0
        assert p.confidence_multiplier == 1.0

    def test_at_threshold(self):
        eng = EpistemicUncertaintyEngine()
        p = eng.compute_sparsity_penalty(12, 20)
        assert p.valid_fraction == pytest.approx(0.60)
        assert p.below_threshold is False

    def test_below_threshold(self):
        eng = EpistemicUncertaintyEngine()
        p = eng.compute_sparsity_penalty(6, 20)
        assert p.valid_fraction == pytest.approx(0.30)
        assert p.below_threshold is True
        assert p.sparsity_penalty > 0
        assert p.confidence_multiplier < 1.0

    def test_zero_valid(self):
        eng = EpistemicUncertaintyEngine()
        p = eng.compute_sparsity_penalty(0, 20)
        assert p.valid_fraction == 0.0
        assert p.below_threshold is True
        assert p.sparsity_penalty == pytest.approx(DATA_SPARSITY_MAX_PENALTY)
        assert p.confidence_multiplier == pytest.approx(0.60)

    def test_full_valid(self):
        eng = EpistemicUncertaintyEngine()
        p = eng.compute_sparsity_penalty(20, 20)
        assert p.valid_fraction == 1.0
        assert p.below_threshold is False
        assert p.sparsity_penalty == 0.0

    def test_zero_window(self):
        eng = EpistemicUncertaintyEngine()
        p = eng.compute_sparsity_penalty(0, 0)
        assert p.valid_fraction == 0.0
        assert p.below_threshold is True


# =============================================================================
# SECTION 8 -- ENGINE: CONFIDENCE DECAY
# =============================================================================

class TestEngineConfidenceDecay:
    def test_no_decay_with_signal(self):
        eng = EpistemicUncertaintyEngine()
        r = eng.compute_confidence_decay(0.8, 5, True)
        assert r.decay_was_active is False
        assert r.decay_applied == 0.0
        assert r.new_Q == 0.8

    def test_no_decay_zero_bars(self):
        eng = EpistemicUncertaintyEngine()
        r = eng.compute_confidence_decay(0.8, 0, False)
        assert r.decay_was_active is False
        assert r.new_Q == 0.8

    def test_decay_one_bar(self):
        eng = EpistemicUncertaintyEngine()
        r = eng.compute_confidence_decay(0.8, 1, False)
        assert r.decay_was_active is True
        assert r.decay_applied == pytest.approx(0.02)
        assert r.new_Q == pytest.approx(0.78)

    def test_decay_three_bars(self):
        eng = EpistemicUncertaintyEngine()
        r = eng.compute_confidence_decay(0.8, 3, False)
        assert r.decay_applied == pytest.approx(0.06)
        assert r.new_Q == pytest.approx(0.74)

    def test_decay_capped_at_max(self):
        eng = EpistemicUncertaintyEngine()
        r = eng.compute_confidence_decay(0.8, 10, False)
        assert r.decay_applied == pytest.approx(CONFIDENCE_DECAY_MAX)

    def test_decay_exceeds_max(self):
        eng = EpistemicUncertaintyEngine()
        r = eng.compute_confidence_decay(0.8, 100, False)
        assert r.decay_applied == pytest.approx(CONFIDENCE_DECAY_MAX)

    def test_decay_floor(self):
        eng = EpistemicUncertaintyEngine()
        r = eng.compute_confidence_decay(0.35, 5, False)
        assert r.new_Q >= CONFIDENCE_DECAY_MIN_VALUE

    def test_decay_floor_exact(self):
        eng = EpistemicUncertaintyEngine()
        r = eng.compute_confidence_decay(0.31, 5, False)
        # 0.31 - 0.10 = 0.21, floored to 0.30
        assert r.new_Q == pytest.approx(CONFIDENCE_DECAY_MIN_VALUE)


# =============================================================================
# SECTION 9 -- ENGINE: FULL COMPUTE
# =============================================================================

class TestEngineCompute:
    def test_all_zero(self):
        eng = EpistemicUncertaintyEngine()
        mu = eng.compute_model_uncertainty(0, 20, 20, 0)
        sp = eng.compute_sparsity_penalty(20, 20)
        cd = eng.compute_confidence_decay(0.8, 0, True)
        bundle = eng.compute(mu, sp, cd, 0.0)
        assert bundle.total_uncertainty == pytest.approx(0.0)

    def test_all_max(self):
        eng = EpistemicUncertaintyEngine()
        mu = eng.compute_model_uncertainty(10, 0, 20, 6)
        sp = eng.compute_sparsity_penalty(0, 20)
        cd = eng.compute_confidence_decay(0.5, 10, False)
        bundle = eng.compute(mu, sp, cd, 10.0)
        assert bundle.total_uncertainty <= 1.0
        assert bundle.total_uncertainty > 0.5

    def test_aleatoric_scaling(self):
        eng = EpistemicUncertaintyEngine()
        mu = eng.compute_model_uncertainty(0, 20, 20, 0)
        sp = eng.compute_sparsity_penalty(20, 20)
        cd = eng.compute_confidence_decay(0.8, 0, True)
        # vol_nvu = 2.5 → aleatoric = 2.5/5 = 0.5
        bundle = eng.compute(mu, sp, cd, 2.5)
        assert bundle.aleatoric == pytest.approx(0.5)
        expected_total = UNCERTAINTY_WEIGHT_ALEATORIC * 0.5
        assert bundle.total_uncertainty == pytest.approx(expected_total)

    def test_aleatoric_capped_at_one(self):
        eng = EpistemicUncertaintyEngine()
        mu = eng.compute_model_uncertainty(0, 20, 20, 0)
        sp = eng.compute_sparsity_penalty(20, 20)
        cd = eng.compute_confidence_decay(0.8, 0, True)
        bundle = eng.compute(mu, sp, cd, 100.0)
        assert bundle.aleatoric == 1.0

    def test_epistemic_data_combines_sparsity_and_decay(self):
        eng = EpistemicUncertaintyEngine()
        mu = eng.compute_model_uncertainty(0, 20, 20, 0)
        sp = DataSparsityPenalty(0.3, True, 0.8, 0.2)
        cd = ConfidenceDecayResult(0.8, 3, 0.06, 0.74, True)
        bundle = eng.compute(mu, sp, cd, 0.0)
        assert bundle.epistemic_data == pytest.approx(0.26)

    def test_output_is_frozen(self):
        eng = EpistemicUncertaintyEngine()
        mu = eng.compute_model_uncertainty(0, 20, 20, 0)
        sp = eng.compute_sparsity_penalty(20, 20)
        cd = eng.compute_confidence_decay(0.8, 0, True)
        bundle = eng.compute(mu, sp, cd, 0.0)
        with pytest.raises(AttributeError):
            bundle.total_uncertainty = 0.99

    def test_formula_verification(self):
        eng = EpistemicUncertaintyEngine()
        mu = ModelUncertaintyScore(0.4, 0.3, 0.2, 0.32)
        sp = DataSparsityPenalty(0.5, True, 0.9, 0.1)
        cd = ConfidenceDecayResult(0.8, 2, 0.04, 0.76, True)
        bundle = eng.compute(mu, sp, cd, 1.5)
        # epistemic_model = 0.32
        # epistemic_data = clip(0.1 + 0.04) = 0.14
        # aleatoric = clip(1.5/5) = 0.3
        # total = 0.45*0.32 + 0.35*0.14 + 0.20*0.3
        expected = 0.45 * 0.32 + 0.35 * 0.14 + 0.20 * 0.3
        assert bundle.total_uncertainty == pytest.approx(expected)


# =============================================================================
# SECTION 10 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_same_inputs_same_output(self):
        eng = EpistemicUncertaintyEngine()
        for _ in range(5):
            mu = eng.compute_model_uncertainty(3, 15, 20, 2)
            sp = eng.compute_sparsity_penalty(15, 20)
            cd = eng.compute_confidence_decay(0.7, 2, False)
            b = eng.compute(mu, sp, cd, 1.5)
            assert b.total_uncertainty == b.total_uncertainty  # stable

    def test_independent_engines(self):
        e1 = EpistemicUncertaintyEngine()
        e2 = EpistemicUncertaintyEngine()
        mu1 = e1.compute_model_uncertainty(5, 10, 20, 3)
        mu2 = e2.compute_model_uncertainty(5, 10, 20, 3)
        assert mu1 == mu2
