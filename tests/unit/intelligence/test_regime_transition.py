# =============================================================================
# tests/unit/intelligence/test_regime_transition.py
# Tests for jarvis/intelligence/regime_transition.py
# =============================================================================

import numpy as np
import pytest

from jarvis.core.schema_versions import GLOBAL_STATE_VERSION
from jarvis.intelligence.regime_transition import (
    CANONICAL_REGIMES,
    N_REGIMES,
    RegimeTransitionMatrix,
    RegimeTransitionEstimator,
)


# =============================================================================
# HELPERS
# =============================================================================

def _uniform_matrix(n: int) -> tuple:
    """Build an NxN uniform transition matrix (rows sum to 1)."""
    val = 1.0 / n
    return tuple(tuple(val for _ in range(n)) for _ in range(n))


def _identity_matrix(regimes: list) -> RegimeTransitionMatrix:
    """Build identity transition matrix (self-transition = 1.0)."""
    n = len(regimes)
    matrix = tuple(
        tuple(1.0 if i == j else 0.0 for j in range(n))
        for i in range(n)
    )
    return RegimeTransitionMatrix(
        regimes=tuple(regimes), matrix=matrix,
        n_obs=0, version=GLOBAL_STATE_VERSION,
    )


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_canonical_regimes_count(self):
        assert len(CANONICAL_REGIMES) == 5

    def test_canonical_regimes_contents(self):
        expected = ["TRENDING", "RANGING", "HIGH_VOL", "SHOCK", "UNKNOWN"]
        assert CANONICAL_REGIMES == expected

    def test_n_regimes(self):
        assert N_REGIMES == 5

    def test_n_regimes_matches_list(self):
        assert N_REGIMES == len(CANONICAL_REGIMES)


# =============================================================================
# SECTION 2 -- REGIME TRANSITION MATRIX DATACLASS
# =============================================================================

class TestRegimeTransitionMatrix:
    def test_frozen(self):
        m = _identity_matrix(CANONICAL_REGIMES)
        with pytest.raises(AttributeError):
            m.n_obs = 99

    def test_construction_valid(self):
        m = RegimeTransitionMatrix(
            regimes=("A", "B"),
            matrix=((0.7, 0.3), (0.4, 0.6)),
            n_obs=10,
            version="1.0.0",
        )
        assert m.regimes == ("A", "B")
        assert m.n_obs == 10

    def test_row_count_mismatch(self):
        with pytest.raises(ValueError, match="row count"):
            RegimeTransitionMatrix(
                regimes=("A", "B"),
                matrix=((0.5, 0.5),),  # 1 row for 2 regimes
                n_obs=0, version="1.0.0",
            )

    def test_col_count_mismatch(self):
        with pytest.raises(ValueError, match="row .* length"):
            RegimeTransitionMatrix(
                regimes=("A", "B"),
                matrix=((0.5, 0.3, 0.2), (0.4, 0.6, 0.0)),
                n_obs=0, version="1.0.0",
            )

    def test_row_sum_not_one(self):
        with pytest.raises(ValueError, match="rows must sum to 1.0"):
            RegimeTransitionMatrix(
                regimes=("A", "B"),
                matrix=((0.5, 0.3), (0.4, 0.6)),  # row 0 sums to 0.8
                n_obs=0, version="1.0.0",
            )

    def test_uniform_valid(self):
        m = RegimeTransitionMatrix(
            regimes=tuple(CANONICAL_REGIMES),
            matrix=_uniform_matrix(5),
            n_obs=100,
            version=GLOBAL_STATE_VERSION,
        )
        assert m.n_obs == 100

    def test_equality(self):
        m1 = _identity_matrix(["A", "B"])
        m2 = _identity_matrix(["A", "B"])
        assert m1 == m2


# =============================================================================
# SECTION 3 -- TRANSITION PROBABILITY LOOKUP
# =============================================================================

class TestTransitionProbability:
    def test_identity_self_transition(self):
        m = _identity_matrix(CANONICAL_REGIMES)
        for r in CANONICAL_REGIMES:
            assert m.transition_probability(r, r) == 1.0

    def test_identity_cross_transition(self):
        m = _identity_matrix(CANONICAL_REGIMES)
        assert m.transition_probability("TRENDING", "SHOCK") == 0.0

    def test_custom_matrix(self):
        m = RegimeTransitionMatrix(
            regimes=("A", "B"),
            matrix=((0.7, 0.3), (0.4, 0.6)),
            n_obs=10, version="1.0.0",
        )
        assert m.transition_probability("A", "B") == pytest.approx(0.3)
        assert m.transition_probability("B", "A") == pytest.approx(0.4)

    def test_unknown_from_regime(self):
        m = _identity_matrix(["A", "B"])
        with pytest.raises(ValueError, match="from_regime.*not in regimes"):
            m.transition_probability("X", "A")

    def test_unknown_to_regime(self):
        m = _identity_matrix(["A", "B"])
        with pytest.raises(ValueError, match="to_regime.*not in regimes"):
            m.transition_probability("A", "X")


# =============================================================================
# SECTION 4 -- MOST LIKELY NEXT
# =============================================================================

class TestMostLikelyNext:
    def test_identity_self(self):
        m = _identity_matrix(CANONICAL_REGIMES)
        for r in CANONICAL_REGIMES:
            assert m.most_likely_next(r) == r

    def test_custom(self):
        m = RegimeTransitionMatrix(
            regimes=("A", "B", "C"),
            matrix=(
                (0.1, 0.8, 0.1),
                (0.2, 0.3, 0.5),
                (0.6, 0.2, 0.2),
            ),
            n_obs=10, version="1.0.0",
        )
        assert m.most_likely_next("A") == "B"
        assert m.most_likely_next("B") == "C"
        assert m.most_likely_next("C") == "A"

    def test_tie_returns_first(self):
        """On tie, np.argmax returns first index."""
        m = RegimeTransitionMatrix(
            regimes=("A", "B"),
            matrix=((0.5, 0.5), (0.5, 0.5)),
            n_obs=0, version="1.0.0",
        )
        assert m.most_likely_next("A") == "A"

    def test_unknown_regime(self):
        m = _identity_matrix(["A", "B"])
        with pytest.raises(ValueError, match="current_regime.*not in regimes"):
            m.most_likely_next("X")


# =============================================================================
# SECTION 5 -- ESTIMATOR BASIC
# =============================================================================

class TestEstimatorBasic:
    def test_simple_sequence(self):
        est = RegimeTransitionEstimator()
        seq = ["TRENDING", "TRENDING", "RANGING", "RANGING", "TRENDING"]
        result = est.estimate(seq)
        assert isinstance(result, RegimeTransitionMatrix)
        assert result.regimes == tuple(CANONICAL_REGIMES)
        assert result.n_obs == 4
        assert result.version == GLOBAL_STATE_VERSION

    def test_all_same_regime(self):
        est = RegimeTransitionEstimator()
        seq = ["TRENDING"] * 10
        result = est.estimate(seq)
        # Self-transition should dominate
        p = result.transition_probability("TRENDING", "TRENDING")
        assert p > 0.9

    def test_alternating_regimes(self):
        est = RegimeTransitionEstimator()
        seq = ["TRENDING", "RANGING"] * 10
        result = est.estimate(seq)
        # TRENDING -> RANGING should dominate
        p_tr = result.transition_probability("TRENDING", "RANGING")
        p_rt = result.transition_probability("RANGING", "TRENDING")
        assert p_tr > 0.5
        assert p_rt > 0.5

    def test_row_sums(self):
        est = RegimeTransitionEstimator()
        seq = ["TRENDING", "RANGING", "HIGH_VOL", "SHOCK", "UNKNOWN", "TRENDING"]
        result = est.estimate(seq)
        arr = np.array(result.matrix)
        np.testing.assert_allclose(arr.sum(axis=1), 1.0, atol=1e-6)

    def test_uses_canonical_by_default(self):
        est = RegimeTransitionEstimator()
        result = est.estimate(["TRENDING", "RANGING"])
        assert result.regimes == tuple(CANONICAL_REGIMES)

    def test_custom_regimes(self):
        est = RegimeTransitionEstimator()
        result = est.estimate(
            ["X", "Y", "X"],
            regimes=["X", "Y"],
        )
        assert result.regimes == ("X", "Y")
        assert result.n_obs == 2

    def test_minimum_sequence(self):
        est = RegimeTransitionEstimator()
        result = est.estimate(["A", "B"], regimes=["A", "B"])
        assert result.n_obs == 1


# =============================================================================
# SECTION 6 -- ESTIMATOR LAPLACE SMOOTHING
# =============================================================================

class TestEstimatorSmoothing:
    def test_laplace_prevents_zeros(self):
        est = RegimeTransitionEstimator()
        # Only TRENDING observed — other regimes should still have > 0 prob
        seq = ["TRENDING"] * 20
        result = est.estimate(seq)
        p = result.transition_probability("RANGING", "HIGH_VOL")
        assert p > 0

    def test_zero_smoothing(self):
        est = RegimeTransitionEstimator()
        seq = ["TRENDING", "RANGING", "TRENDING"]
        result = est.estimate(seq, regimes=["TRENDING", "RANGING"],
                              laplace_smoothing=0.0)
        # TRENDING -> RANGING should be 1.0 (only observed transition from TRENDING)
        assert result.transition_probability("TRENDING", "RANGING") == pytest.approx(1.0)

    def test_high_smoothing(self):
        est = RegimeTransitionEstimator()
        seq = ["TRENDING", "RANGING"]
        result = est.estimate(seq, regimes=["TRENDING", "RANGING"],
                              laplace_smoothing=100.0)
        # With very high smoothing, matrix approaches uniform
        arr = np.array(result.matrix)
        assert np.allclose(arr, 0.5, atol=0.01)

    def test_negative_smoothing_error(self):
        est = RegimeTransitionEstimator()
        with pytest.raises(ValueError, match="laplace_smoothing must be >= 0"):
            est.estimate(["A", "B"], regimes=["A", "B"], laplace_smoothing=-1.0)


# =============================================================================
# SECTION 7 -- ESTIMATOR VALIDATION
# =============================================================================

class TestEstimatorValidation:
    def test_too_short(self):
        est = RegimeTransitionEstimator()
        with pytest.raises(ValueError, match=">= 2 elements"):
            est.estimate(["TRENDING"])

    def test_empty(self):
        est = RegimeTransitionEstimator()
        with pytest.raises(ValueError, match=">= 2 elements"):
            est.estimate([])

    def test_not_list(self):
        est = RegimeTransitionEstimator()
        with pytest.raises(TypeError, match="must be a list"):
            est.estimate(("TRENDING", "RANGING"))

    def test_empty_regimes(self):
        est = RegimeTransitionEstimator()
        with pytest.raises(ValueError, match="must not be empty"):
            est.estimate(["A", "B"], regimes=[])

    def test_smoothing_type_error(self):
        est = RegimeTransitionEstimator()
        with pytest.raises(TypeError, match="laplace_smoothing must be numeric"):
            est.estimate(["A", "B"], regimes=["A", "B"], laplace_smoothing="0.1")

    def test_unrecognized_regimes_ignored(self):
        est = RegimeTransitionEstimator()
        seq = ["TRENDING", "INVALID", "RANGING"]
        result = est.estimate(seq)
        # "INVALID" is not in CANONICAL_REGIMES, transitions involving it skipped
        assert result.n_obs == 0  # TRENDING->INVALID and INVALID->RANGING both skipped


# =============================================================================
# SECTION 8 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_same_input_same_output(self):
        est = RegimeTransitionEstimator()
        seq = ["TRENDING", "RANGING", "HIGH_VOL", "SHOCK", "UNKNOWN", "TRENDING"]
        r1 = est.estimate(seq)
        r2 = est.estimate(seq)
        assert r1 == r2

    def test_independent_estimators(self):
        seq = ["TRENDING", "RANGING", "HIGH_VOL"]
        r1 = RegimeTransitionEstimator().estimate(seq)
        r2 = RegimeTransitionEstimator().estimate(seq)
        assert r1 == r2

    def test_matrix_values_deterministic(self):
        est = RegimeTransitionEstimator()
        seq = ["TRENDING"] * 50 + ["RANGING"] * 50
        r1 = est.estimate(seq)
        r2 = est.estimate(seq)
        np.testing.assert_array_equal(
            np.array(r1.matrix), np.array(r2.matrix)
        )
