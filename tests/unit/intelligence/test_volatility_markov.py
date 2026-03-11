# =============================================================================
# tests/unit/intelligence/test_volatility_markov.py
# Tests for jarvis/intelligence/volatility_markov.py
# =============================================================================

import numpy as np
import pytest

from jarvis.core.schema_versions import GLOBAL_STATE_VERSION
from jarvis.intelligence.volatility_markov import (
    VOL_STATES,
    N_VOL_STATES,
    classify_vol_state,
    VolatilityTransitionMatrix,
    VolatilityTransitionEstimator,
)


# =============================================================================
# HELPERS
# =============================================================================

def _uniform_vol_matrix() -> VolatilityTransitionMatrix:
    """Build a 4x4 uniform transition matrix."""
    val = 0.25
    matrix = tuple(tuple(val for _ in range(4)) for _ in range(4))
    return VolatilityTransitionMatrix(
        states=VOL_STATES, matrix=matrix,
        n_obs=0, version=GLOBAL_STATE_VERSION,
    )


def _identity_vol_matrix() -> VolatilityTransitionMatrix:
    """Build 4x4 identity transition matrix."""
    matrix = tuple(
        tuple(1.0 if i == j else 0.0 for j in range(4))
        for i in range(4)
    )
    return VolatilityTransitionMatrix(
        states=VOL_STATES, matrix=matrix,
        n_obs=0, version=GLOBAL_STATE_VERSION,
    )


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_vol_states(self):
        assert VOL_STATES == ("LOW", "MEDIUM", "HIGH", "EXTREME")

    def test_n_vol_states(self):
        assert N_VOL_STATES == 4

    def test_n_matches_tuple(self):
        assert N_VOL_STATES == len(VOL_STATES)

    def test_vol_states_is_tuple(self):
        assert isinstance(VOL_STATES, tuple)


# =============================================================================
# SECTION 2 -- classify_vol_state
# =============================================================================

class TestClassifyVolState:
    """Test threshold classification (DET-06 fixed literals)."""

    def test_low_zero(self):
        assert classify_vol_state(0.0) == "LOW"

    def test_low_below_one(self):
        assert classify_vol_state(0.99) == "LOW"

    def test_medium_at_one(self):
        assert classify_vol_state(1.0) == "MEDIUM"

    def test_medium_below_two(self):
        assert classify_vol_state(1.99) == "MEDIUM"

    def test_high_at_two(self):
        assert classify_vol_state(2.0) == "HIGH"

    def test_high_below_three(self):
        assert classify_vol_state(2.99) == "HIGH"

    def test_extreme_at_three(self):
        assert classify_vol_state(3.0) == "EXTREME"

    def test_extreme_above_three(self):
        assert classify_vol_state(10.0) == "EXTREME"

    def test_extreme_large(self):
        assert classify_vol_state(100.0) == "EXTREME"

    def test_type_error_string(self):
        with pytest.raises(TypeError, match="must be numeric"):
            classify_vol_state("1.0")

    def test_type_error_none(self):
        with pytest.raises(TypeError, match="must be numeric"):
            classify_vol_state(None)

    def test_negative_value_error(self):
        with pytest.raises(ValueError, match="must be >= 0"):
            classify_vol_state(-0.1)

    def test_int_accepted(self):
        assert classify_vol_state(0) == "LOW"
        assert classify_vol_state(1) == "MEDIUM"
        assert classify_vol_state(2) == "HIGH"
        assert classify_vol_state(3) == "EXTREME"

    def test_boundary_precision(self):
        """Exact boundaries at 1.0, 2.0, 3.0."""
        assert classify_vol_state(0.999999999) == "LOW"
        assert classify_vol_state(1.000000001) == "MEDIUM"
        assert classify_vol_state(1.999999999) == "MEDIUM"
        assert classify_vol_state(2.000000001) == "HIGH"
        assert classify_vol_state(2.999999999) == "HIGH"
        assert classify_vol_state(3.000000001) == "EXTREME"


# =============================================================================
# SECTION 3 -- VOLATILITY TRANSITION MATRIX
# =============================================================================

class TestVolatilityTransitionMatrix:
    def test_frozen(self):
        m = _uniform_vol_matrix()
        with pytest.raises(AttributeError):
            m.n_obs = 99

    def test_construction_valid(self):
        m = _uniform_vol_matrix()
        assert m.states == VOL_STATES
        assert m.n_obs == 0
        assert m.version == GLOBAL_STATE_VERSION

    def test_row_count_mismatch(self):
        with pytest.raises(ValueError, match="row count"):
            VolatilityTransitionMatrix(
                states=("LOW", "HIGH"),
                matrix=((0.5, 0.5),),
                n_obs=0, version="1.0.0",
            )

    def test_col_count_mismatch(self):
        with pytest.raises(ValueError, match="row .* length"):
            VolatilityTransitionMatrix(
                states=("LOW", "HIGH"),
                matrix=((0.5, 0.3, 0.2), (0.4, 0.6, 0.0)),
                n_obs=0, version="1.0.0",
            )

    def test_row_sum_not_one(self):
        with pytest.raises(ValueError, match="rows must sum to 1.0"):
            VolatilityTransitionMatrix(
                states=("LOW", "HIGH"),
                matrix=((0.5, 0.3), (0.4, 0.6)),
                n_obs=0, version="1.0.0",
            )

    def test_identity_valid(self):
        m = _identity_vol_matrix()
        assert m.transition_probability("LOW", "LOW") == 1.0

    def test_equality(self):
        m1 = _uniform_vol_matrix()
        m2 = _uniform_vol_matrix()
        assert m1 == m2


# =============================================================================
# SECTION 4 -- TRANSITION PROBABILITY LOOKUP
# =============================================================================

class TestTransitionProbability:
    def test_identity(self):
        m = _identity_vol_matrix()
        for s in VOL_STATES:
            assert m.transition_probability(s, s) == 1.0
            for other in VOL_STATES:
                if other != s:
                    assert m.transition_probability(s, other) == 0.0

    def test_custom(self):
        m = VolatilityTransitionMatrix(
            states=("A", "B"),
            matrix=((0.7, 0.3), (0.4, 0.6)),
            n_obs=10, version="1.0.0",
        )
        assert m.transition_probability("A", "B") == pytest.approx(0.3)

    def test_unknown_from_state(self):
        m = _uniform_vol_matrix()
        with pytest.raises(ValueError, match="from_state.*not in states"):
            m.transition_probability("INVALID", "LOW")

    def test_unknown_to_state(self):
        m = _uniform_vol_matrix()
        with pytest.raises(ValueError, match="to_state.*not in states"):
            m.transition_probability("LOW", "INVALID")


# =============================================================================
# SECTION 5 -- FM-02 TRIGGER PROBABILITY
# =============================================================================

class TestProbFm02Trigger:
    def test_from_low(self):
        m = _uniform_vol_matrix()
        assert m.prob_fm02_trigger("LOW") == pytest.approx(0.25)

    def test_from_extreme_identity(self):
        m = _identity_vol_matrix()
        assert m.prob_fm02_trigger("EXTREME") == 1.0

    def test_from_low_identity(self):
        m = _identity_vol_matrix()
        assert m.prob_fm02_trigger("LOW") == 0.0

    def test_unknown_state(self):
        m = _uniform_vol_matrix()
        with pytest.raises(ValueError, match="from_state.*not in states"):
            m.prob_fm02_trigger("INVALID")

    def test_delegates_to_transition_probability(self):
        m = VolatilityTransitionMatrix(
            states=VOL_STATES,
            matrix=(
                (0.7, 0.1, 0.1, 0.1),
                (0.1, 0.6, 0.2, 0.1),
                (0.05, 0.05, 0.5, 0.4),
                (0.0, 0.0, 0.1, 0.9),
            ),
            n_obs=100, version="1.0.0",
        )
        assert m.prob_fm02_trigger("LOW") == pytest.approx(0.1)
        assert m.prob_fm02_trigger("HIGH") == pytest.approx(0.4)
        assert m.prob_fm02_trigger("EXTREME") == pytest.approx(0.9)


# =============================================================================
# SECTION 6 -- ESTIMATOR FROM STATES
# =============================================================================

class TestEstimatorFromStates:
    def test_basic(self):
        est = VolatilityTransitionEstimator()
        seq = ["LOW", "LOW", "MEDIUM", "HIGH", "EXTREME"]
        result = est.estimate_from_states(seq)
        assert isinstance(result, VolatilityTransitionMatrix)
        assert result.states == VOL_STATES
        assert result.n_obs == 4
        assert result.version == GLOBAL_STATE_VERSION

    def test_row_sums(self):
        est = VolatilityTransitionEstimator()
        seq = ["LOW", "MEDIUM", "HIGH", "EXTREME", "LOW", "MEDIUM"]
        result = est.estimate_from_states(seq)
        arr = np.array(result.matrix)
        np.testing.assert_allclose(arr.sum(axis=1), 1.0, atol=1e-6)

    def test_all_same_state(self):
        est = VolatilityTransitionEstimator()
        seq = ["MEDIUM"] * 20
        result = est.estimate_from_states(seq)
        p = result.transition_probability("MEDIUM", "MEDIUM")
        assert p > 0.9

    def test_custom_states(self):
        est = VolatilityTransitionEstimator()
        result = est.estimate_from_states(
            ["X", "Y", "X"],
            states=("X", "Y"),
        )
        assert result.states == ("X", "Y")
        assert result.n_obs == 2

    def test_minimum_sequence(self):
        est = VolatilityTransitionEstimator()
        result = est.estimate_from_states(["LOW", "HIGH"])
        assert result.n_obs == 1

    def test_unrecognized_states_ignored(self):
        est = VolatilityTransitionEstimator()
        seq = ["LOW", "INVALID", "HIGH"]
        result = est.estimate_from_states(seq)
        assert result.n_obs == 0


# =============================================================================
# SECTION 7 -- ESTIMATOR VALIDATION
# =============================================================================

class TestEstimatorValidation:
    def test_too_short(self):
        est = VolatilityTransitionEstimator()
        with pytest.raises(ValueError, match=">= 2 elements"):
            est.estimate_from_states(["LOW"])

    def test_empty(self):
        est = VolatilityTransitionEstimator()
        with pytest.raises(ValueError, match=">= 2 elements"):
            est.estimate_from_states([])

    def test_not_list(self):
        est = VolatilityTransitionEstimator()
        with pytest.raises(TypeError, match="must be a list"):
            est.estimate_from_states(("LOW", "HIGH"))

    def test_empty_states(self):
        est = VolatilityTransitionEstimator()
        with pytest.raises(ValueError, match="must not be empty"):
            est.estimate_from_states(["A", "B"], states=())

    def test_smoothing_type_error(self):
        est = VolatilityTransitionEstimator()
        with pytest.raises(TypeError, match="laplace_smoothing must be numeric"):
            est.estimate_from_states(["LOW", "HIGH"], laplace_smoothing="x")

    def test_negative_smoothing(self):
        est = VolatilityTransitionEstimator()
        with pytest.raises(ValueError, match="laplace_smoothing must be >= 0"):
            est.estimate_from_states(["LOW", "HIGH"], laplace_smoothing=-1)


# =============================================================================
# SECTION 8 -- ESTIMATOR FROM NVU
# =============================================================================

class TestEstimatorFromNvu:
    def test_basic(self):
        est = VolatilityTransitionEstimator()
        nvu = [0.5, 1.5, 2.5, 3.5]  # LOW -> MEDIUM -> HIGH -> EXTREME
        result = est.estimate_from_nvu(nvu)
        assert isinstance(result, VolatilityTransitionMatrix)
        assert result.n_obs == 3
        assert result.states == VOL_STATES

    def test_all_low(self):
        est = VolatilityTransitionEstimator()
        nvu = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = est.estimate_from_nvu(nvu)
        p = result.transition_probability("LOW", "LOW")
        assert p > 0.9

    def test_escalation_pattern(self):
        est = VolatilityTransitionEstimator()
        nvu = [0.5, 1.5, 2.5, 3.5]  # monotonic escalation
        result = est.estimate_from_nvu(nvu)
        # Each state transitions to next with high probability
        assert result.transition_probability("LOW", "MEDIUM") > 0.5
        assert result.transition_probability("MEDIUM", "HIGH") > 0.5
        assert result.transition_probability("HIGH", "EXTREME") > 0.5

    def test_too_short(self):
        est = VolatilityTransitionEstimator()
        with pytest.raises(ValueError, match=">= 2 elements"):
            est.estimate_from_nvu([0.5])

    def test_not_list(self):
        est = VolatilityTransitionEstimator()
        with pytest.raises(TypeError, match="must be a list"):
            est.estimate_from_nvu((0.5, 1.5))

    def test_negative_nvu_propagates(self):
        est = VolatilityTransitionEstimator()
        with pytest.raises(ValueError, match="must be >= 0"):
            est.estimate_from_nvu([-0.5, 1.0])

    def test_row_sums(self):
        est = VolatilityTransitionEstimator()
        nvu = [0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 0.5]
        result = est.estimate_from_nvu(nvu)
        arr = np.array(result.matrix)
        np.testing.assert_allclose(arr.sum(axis=1), 1.0, atol=1e-6)


# =============================================================================
# SECTION 9 -- SMOOTHING
# =============================================================================

class TestSmoothing:
    def test_laplace_prevents_zeros(self):
        est = VolatilityTransitionEstimator()
        seq = ["LOW"] * 20
        result = est.estimate_from_states(seq)
        # Even unobserved transitions should have > 0 probability
        assert result.transition_probability("HIGH", "EXTREME") > 0

    def test_zero_smoothing(self):
        est = VolatilityTransitionEstimator()
        seq = ["LOW", "MEDIUM", "LOW"]
        result = est.estimate_from_states(seq, states=("LOW", "MEDIUM"),
                                          laplace_smoothing=0.0)
        assert result.transition_probability("LOW", "MEDIUM") == pytest.approx(1.0)


# =============================================================================
# SECTION 10 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_same_input_same_output_states(self):
        est = VolatilityTransitionEstimator()
        seq = ["LOW", "MEDIUM", "HIGH", "EXTREME", "LOW"]
        r1 = est.estimate_from_states(seq)
        r2 = est.estimate_from_states(seq)
        assert r1 == r2

    def test_same_input_same_output_nvu(self):
        est = VolatilityTransitionEstimator()
        nvu = [0.5, 1.5, 2.5, 3.5, 0.5]
        r1 = est.estimate_from_nvu(nvu)
        r2 = est.estimate_from_nvu(nvu)
        assert r1 == r2

    def test_classify_deterministic(self):
        for _ in range(100):
            assert classify_vol_state(1.5) == "MEDIUM"
            assert classify_vol_state(2.5) == "HIGH"

    def test_independent_estimators(self):
        seq = ["LOW", "MEDIUM", "HIGH"]
        r1 = VolatilityTransitionEstimator().estimate_from_states(seq)
        r2 = VolatilityTransitionEstimator().estimate_from_states(seq)
        assert r1 == r2
