# tests/unit/utils/test_numeric_safety.py
# Unit tests for jarvis/utils/numeric_safety.py

import math

import pytest

from jarvis.utils.exceptions import NumericalInstabilityError
from jarvis.utils.numeric_safety import (
    clip_probability,
    safe_divide,
    enforce_psd,
    safe_matrix_inverse,
    check_nan_inf,
)


# ---------------------------------------------------------------------------
# clip_probability
# ---------------------------------------------------------------------------

class TestClipProbability:

    def test_normal_value_unchanged(self):
        """Values within [1e-6, 1-1e-6] pass through unchanged."""
        assert clip_probability(0.5) == 0.5
        assert clip_probability(0.1) == 0.1
        assert clip_probability(0.99) == 0.99

    def test_clips_low_to_floor(self):
        """Values below 1e-6 are clipped to 1e-6."""
        result = clip_probability(0.0)
        assert result == 1e-6

    def test_clips_negative_to_floor(self):
        result = clip_probability(-0.5)
        assert result == 1e-6

    def test_clips_high_to_ceil(self):
        """Values above 1-1e-6 are clipped."""
        result = clip_probability(1.0)
        assert result == 1.0 - 1e-6

    def test_nan_raises(self):
        with pytest.raises(NumericalInstabilityError):
            clip_probability(float("nan"))

    def test_inf_raises(self):
        with pytest.raises(NumericalInstabilityError):
            clip_probability(float("inf"))

    def test_neg_inf_raises(self):
        with pytest.raises(NumericalInstabilityError):
            clip_probability(float("-inf"))

    def test_boundary_floor(self):
        """Exactly 1e-6 is not clipped."""
        assert clip_probability(1e-6) == 1e-6

    def test_boundary_ceil(self):
        """Exactly 1-1e-6 is not clipped."""
        val = 1.0 - 1e-6
        assert clip_probability(val) == val


# ---------------------------------------------------------------------------
# safe_divide
# ---------------------------------------------------------------------------

class TestSafeDivide:

    def test_normal_division(self):
        assert safe_divide(10.0, 2.0) == 5.0
        assert safe_divide(1.0, 4.0) == 0.25

    def test_denominator_near_zero(self):
        """When denominator is near zero, uses epsilon floor."""
        result = safe_divide(1.0, 0.0)
        assert math.isfinite(result)
        assert result > 0

    def test_both_near_zero_returns_zero(self):
        """When both numerator and denominator are near zero, returns 0.0."""
        assert safe_divide(0.0, 0.0) == 0.0
        assert safe_divide(1e-20, 1e-20) == 0.0

    def test_negative_denominator_near_zero(self):
        result = safe_divide(1.0, -1e-20)
        assert math.isfinite(result)

    def test_nan_numerator_raises(self):
        with pytest.raises(NumericalInstabilityError):
            safe_divide(float("nan"), 1.0)

    def test_nan_denominator_raises(self):
        with pytest.raises(NumericalInstabilityError):
            safe_divide(1.0, float("nan"))


# ---------------------------------------------------------------------------
# enforce_psd
# ---------------------------------------------------------------------------

class TestEnforcePSD:

    def test_symmetric_matrix_stays_symmetric(self):
        mat = [[1.0, 0.5], [0.5, 1.0]]
        result = enforce_psd(mat)
        assert result[0][1] == result[1][0]

    def test_non_symmetric_matrix_becomes_symmetric(self):
        mat = [[1.0, 0.3], [0.7, 1.0]]
        result = enforce_psd(mat)
        assert result[0][1] == result[1][0]
        assert result[0][1] == pytest.approx(0.5)

    def test_negative_diagonal_floored(self):
        """Negative diagonal entries are floored to _DIAG_FLOOR."""
        mat = [[-1.0, 0.0], [0.0, -2.0]]
        result = enforce_psd(mat)
        assert result[0][0] > 0
        assert result[1][1] > 0

    def test_empty_matrix(self):
        assert enforce_psd([]) == []

    def test_nan_raises(self):
        mat = [[float("nan"), 0.0], [0.0, 1.0]]
        with pytest.raises(NumericalInstabilityError):
            enforce_psd(mat)

    def test_non_square_raises(self):
        mat = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        with pytest.raises(ValueError):
            enforce_psd(mat)

    def test_identity_unchanged(self):
        mat = [[1.0, 0.0], [0.0, 1.0]]
        result = enforce_psd(mat)
        assert result[0][0] == 1.0
        assert result[1][1] == 1.0
        assert result[0][1] == 0.0
        assert result[1][0] == 0.0


# ---------------------------------------------------------------------------
# safe_matrix_inverse
# ---------------------------------------------------------------------------

class TestSafeMatrixInverse:

    def test_identity_inverse_is_near_identity(self):
        """Inverse of identity (with small lambda) should be near identity."""
        mat = [[1.0, 0.0], [0.0, 1.0]]
        inv = safe_matrix_inverse(mat, lambda_=1e-6)
        # (I + 1e-6*I)^{-1} ≈ I
        assert inv[0][0] == pytest.approx(1.0, abs=1e-4)
        assert inv[1][1] == pytest.approx(1.0, abs=1e-4)
        assert abs(inv[0][1]) < 1e-4
        assert abs(inv[1][0]) < 1e-4

    def test_regularization_prevents_singular(self):
        """A singular matrix can be inverted with regularization."""
        mat = [[0.0, 0.0], [0.0, 0.0]]
        inv = safe_matrix_inverse(mat, lambda_=0.1)
        # (0 + 0.1*I)^{-1} = 10*I
        assert inv[0][0] == pytest.approx(10.0, abs=0.1)
        assert inv[1][1] == pytest.approx(10.0, abs=0.1)

    def test_known_2x2_inverse(self):
        """Test with a known 2x2 matrix."""
        # [[2, 0], [0, 4]] with lambda=0 effectively
        mat = [[2.0, 0.0], [0.0, 4.0]]
        inv = safe_matrix_inverse(mat, lambda_=0.0)
        assert inv[0][0] == pytest.approx(0.5, abs=1e-6)
        assert inv[1][1] == pytest.approx(0.25, abs=1e-6)

    def test_empty_matrix(self):
        assert safe_matrix_inverse([]) == []

    def test_non_square_raises(self):
        mat = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        with pytest.raises(ValueError):
            safe_matrix_inverse(mat)

    def test_3x3_inverse_times_original_near_identity(self):
        """A * A^{-1} should be near identity."""
        mat = [[4.0, 2.0, 1.0], [2.0, 5.0, 3.0], [1.0, 3.0, 6.0]]
        inv = safe_matrix_inverse(mat, lambda_=1e-10)
        # Multiply mat * inv
        n = 3
        product = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    product[i][j] += mat[i][k] * inv[k][j]
        for i in range(n):
            for j in range(n):
                expected = 1.0 if i == j else 0.0
                assert product[i][j] == pytest.approx(expected, abs=1e-3)


# ---------------------------------------------------------------------------
# check_nan_inf
# ---------------------------------------------------------------------------

class TestCheckNanInf:

    def test_valid_float_passes(self):
        check_nan_inf(1.0, "test")
        check_nan_inf(0.0, "test")
        check_nan_inf(-999.9, "test")

    def test_nan_raises(self):
        with pytest.raises(NumericalInstabilityError):
            check_nan_inf(float("nan"), "test")

    def test_inf_raises(self):
        with pytest.raises(NumericalInstabilityError):
            check_nan_inf(float("inf"), "test")

    def test_neg_inf_raises(self):
        with pytest.raises(NumericalInstabilityError):
            check_nan_inf(float("-inf"), "test")

    def test_list_valid_passes(self):
        check_nan_inf([1.0, 2.0, 3.0], "test")

    def test_list_with_nan_raises(self):
        with pytest.raises(NumericalInstabilityError):
            check_nan_inf([1.0, float("nan"), 3.0], "test")

    def test_list_with_inf_raises(self):
        with pytest.raises(NumericalInstabilityError):
            check_nan_inf([1.0, float("inf")], "test")

    def test_empty_list_passes(self):
        check_nan_inf([], "test")


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:

    def test_clip_probability_deterministic(self):
        for _ in range(100):
            assert clip_probability(0.5) == 0.5
            assert clip_probability(0.0) == 1e-6

    def test_safe_divide_deterministic(self):
        for _ in range(100):
            assert safe_divide(10.0, 3.0) == safe_divide(10.0, 3.0)

    def test_enforce_psd_deterministic(self):
        mat = [[1.0, 0.3], [0.7, 1.0]]
        r1 = enforce_psd(mat)
        r2 = enforce_psd(mat)
        assert r1 == r2

    def test_safe_matrix_inverse_deterministic(self):
        mat = [[2.0, 1.0], [1.0, 3.0]]
        r1 = safe_matrix_inverse(mat)
        r2 = safe_matrix_inverse(mat)
        assert r1 == r2
