# =============================================================================
# tests/unit/systems/test_reproducibility.py
# Tests for jarvis/systems/reproducibility.py
# =============================================================================

import math

import numpy as np
import pytest

from jarvis.systems.reproducibility import (
    FLOAT_PRECISION,
    TOLERANCE_FLOAT_COMPARE,
    ReproducibilityResult,
    ReproducibilityController,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_float_precision(self):
        assert FLOAT_PRECISION == 15

    def test_tolerance(self):
        assert TOLERANCE_FLOAT_COMPARE == 1e-14


# =============================================================================
# SECTION 2 -- RESULT DATACLASS
# =============================================================================

class TestReproducibilityResult:
    def test_frozen(self):
        r = ReproducibilityResult(True, (), "abc123")
        with pytest.raises(AttributeError):
            r.reproducible = False

    def test_fields(self):
        r = ReproducibilityResult(
            reproducible=True,
            mismatches=(),
            fingerprint="abc123",
        )
        assert r.reproducible is True
        assert r.mismatches == ()
        assert r.fingerprint == "abc123"

    def test_equality(self):
        r1 = ReproducibilityResult(True, (), "abc")
        r2 = ReproducibilityResult(True, (), "abc")
        assert r1 == r2


# =============================================================================
# SECTION 3 -- ENSURE_REPRODUCIBLE (SCALAR)
# =============================================================================

class TestEnsureReproducible:
    def test_basic_float(self):
        ctrl = ReproducibilityController()
        result = ctrl.ensure_reproducible(0.123456789012345)
        assert isinstance(result, float)

    def test_round_precision(self):
        ctrl = ReproducibilityController()
        # 16+ digit float should be rounded to 15 digits
        val = 1.1234567890123456789
        result = ctrl.ensure_reproducible(val)
        assert result == round(val, 15)

    def test_integer_input(self):
        ctrl = ReproducibilityController()
        result = ctrl.ensure_reproducible(5)
        assert result == 5.0

    def test_zero(self):
        ctrl = ReproducibilityController()
        assert ctrl.ensure_reproducible(0.0) == 0.0

    def test_negative(self):
        ctrl = ReproducibilityController()
        result = ctrl.ensure_reproducible(-0.123456789012345)
        assert result == round(-0.123456789012345, 15)

    def test_nan_raises(self):
        ctrl = ReproducibilityController()
        with pytest.raises(ValueError, match="NaN"):
            ctrl.ensure_reproducible(float("nan"))

    def test_inf_raises(self):
        ctrl = ReproducibilityController()
        with pytest.raises(ValueError, match="Inf"):
            ctrl.ensure_reproducible(float("inf"))

    def test_neg_inf_raises(self):
        ctrl = ReproducibilityController()
        with pytest.raises(ValueError, match="Inf"):
            ctrl.ensure_reproducible(float("-inf"))

    def test_type_error(self):
        ctrl = ReproducibilityController()
        with pytest.raises(TypeError, match="value must be numeric"):
            ctrl.ensure_reproducible("bad")


# =============================================================================
# SECTION 4 -- ENSURE_REPRODUCIBLE_ARRAY
# =============================================================================

class TestEnsureReproducibleArray:
    def test_basic_array(self):
        ctrl = ReproducibilityController()
        arr = np.array([0.1234567890123456, 0.9876543210987654])
        result = ctrl.ensure_reproducible_array(arr)
        assert isinstance(result, np.ndarray)
        expected = np.around(arr, FLOAT_PRECISION)
        np.testing.assert_array_equal(result, expected)

    def test_empty_array(self):
        ctrl = ReproducibilityController()
        arr = np.array([])
        result = ctrl.ensure_reproducible_array(arr)
        assert len(result) == 0

    def test_2d_array(self):
        ctrl = ReproducibilityController()
        arr = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = ctrl.ensure_reproducible_array(arr)
        np.testing.assert_array_equal(result, arr)

    def test_nan_raises(self):
        ctrl = ReproducibilityController()
        with pytest.raises(ValueError, match="NaN"):
            ctrl.ensure_reproducible_array(np.array([1.0, float("nan")]))

    def test_inf_raises(self):
        ctrl = ReproducibilityController()
        with pytest.raises(ValueError, match="Inf"):
            ctrl.ensure_reproducible_array(np.array([1.0, float("inf")]))

    def test_type_error(self):
        ctrl = ReproducibilityController()
        with pytest.raises(TypeError, match="arr must be a numpy ndarray"):
            ctrl.ensure_reproducible_array([1.0, 2.0])


# =============================================================================
# SECTION 5 -- VERIFY_REPRODUCIBILITY (FLOAT)
# =============================================================================

class TestVerifyFloat:
    def test_identical_floats(self):
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility(0.5, 0.5)
        assert result.reproducible is True
        assert len(result.mismatches) == 0

    def test_different_floats(self):
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility(0.5, 0.6)
        assert result.reproducible is False
        assert len(result.mismatches) == 1

    def test_within_tolerance(self):
        ctrl = ReproducibilityController()
        a = 0.5
        b = 0.5 + 1e-15  # within tolerance
        result = ctrl.verify_reproducibility(a, b)
        assert result.reproducible is True

    def test_outside_tolerance(self):
        ctrl = ReproducibilityController()
        a = 0.5
        b = 0.5 + 1e-13  # outside tolerance
        result = ctrl.verify_reproducibility(a, b)
        assert result.reproducible is False

    def test_both_nan(self):
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility(float("nan"), float("nan"))
        assert result.reproducible is True

    def test_one_nan(self):
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility(float("nan"), 0.5)
        assert result.reproducible is False


# =============================================================================
# SECTION 6 -- VERIFY_REPRODUCIBILITY (ARRAY)
# =============================================================================

class TestVerifyArray:
    def test_identical_arrays(self):
        ctrl = ReproducibilityController()
        arr = np.array([1.0, 2.0, 3.0])
        result = ctrl.verify_reproducibility(arr, arr.copy())
        assert result.reproducible is True

    def test_different_arrays(self):
        ctrl = ReproducibilityController()
        a = np.array([1.0, 2.0])
        b = np.array([1.0, 3.0])
        result = ctrl.verify_reproducibility(a, b)
        assert result.reproducible is False

    def test_shape_mismatch(self):
        ctrl = ReproducibilityController()
        a = np.array([1.0, 2.0])
        b = np.array([1.0, 2.0, 3.0])
        result = ctrl.verify_reproducibility(a, b)
        assert result.reproducible is False
        assert "shape" in result.mismatches[0]


# =============================================================================
# SECTION 7 -- VERIFY_REPRODUCIBILITY (DICT)
# =============================================================================

class TestVerifyDict:
    def test_identical_dicts(self):
        ctrl = ReproducibilityController()
        d = {"a": 1.0, "b": 2.0}
        result = ctrl.verify_reproducibility(d, d.copy())
        assert result.reproducible is True

    def test_different_dicts(self):
        ctrl = ReproducibilityController()
        d1 = {"a": 1.0, "b": 2.0}
        d2 = {"a": 1.0, "b": 3.0}
        result = ctrl.verify_reproducibility(d1, d2)
        assert result.reproducible is False

    def test_key_mismatch(self):
        ctrl = ReproducibilityController()
        d1 = {"a": 1.0}
        d2 = {"b": 1.0}
        result = ctrl.verify_reproducibility(d1, d2)
        assert result.reproducible is False
        assert "key" in result.mismatches[0]

    def test_nested_dicts(self):
        ctrl = ReproducibilityController()
        d1 = {"a": {"x": 1.0}}
        d2 = {"a": {"x": 1.0}}
        result = ctrl.verify_reproducibility(d1, d2)
        assert result.reproducible is True

    def test_nested_dict_mismatch(self):
        ctrl = ReproducibilityController()
        d1 = {"a": {"x": 1.0}}
        d2 = {"a": {"x": 2.0}}
        result = ctrl.verify_reproducibility(d1, d2)
        assert result.reproducible is False


# =============================================================================
# SECTION 8 -- VERIFY_REPRODUCIBILITY (LIST, OTHER)
# =============================================================================

class TestVerifyOther:
    def test_identical_lists(self):
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility([1.0, 2.0], [1.0, 2.0])
        assert result.reproducible is True

    def test_list_length_mismatch(self):
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility([1.0], [1.0, 2.0])
        assert result.reproducible is False

    def test_identical_strings(self):
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility("hello", "hello")
        assert result.reproducible is True

    def test_different_strings(self):
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility("hello", "world")
        assert result.reproducible is False

    def test_type_mismatch(self):
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility(1.0, "1.0")
        assert result.reproducible is False
        assert "type" in result.mismatches[0]

    def test_identical_ints(self):
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility(42, 42)
        assert result.reproducible is True

    def test_identical_bools(self):
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility(True, True)
        assert result.reproducible is True


# =============================================================================
# SECTION 9 -- SYSTEM FINGERPRINT
# =============================================================================

class TestSystemFingerprint:
    def test_returns_string(self):
        ctrl = ReproducibilityController()
        fp = ctrl.get_system_fingerprint()
        assert isinstance(fp, str)

    def test_length_16(self):
        ctrl = ReproducibilityController()
        fp = ctrl.get_system_fingerprint()
        assert len(fp) == 16

    def test_hex_chars(self):
        ctrl = ReproducibilityController()
        fp = ctrl.get_system_fingerprint()
        assert all(c in "0123456789abcdef" for c in fp)

    def test_deterministic(self):
        ctrl = ReproducibilityController()
        fp1 = ctrl.get_system_fingerprint()
        fp2 = ctrl.get_system_fingerprint()
        assert fp1 == fp2

    def test_result_includes_fingerprint(self):
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility(1.0, 1.0)
        assert len(result.fingerprint) == 16


# =============================================================================
# SECTION 10 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_ensure_reproducible_deterministic(self):
        ctrl = ReproducibilityController()
        results = [ctrl.ensure_reproducible(0.123456789) for _ in range(10)]
        assert len(set(results)) == 1

    def test_verify_deterministic(self):
        ctrl = ReproducibilityController()
        results = [
            ctrl.verify_reproducibility({"x": 0.5}, {"x": 0.5})
            for _ in range(10)
        ]
        assert all(r == results[0] for r in results)

    def test_independent_controllers(self):
        r1 = ReproducibilityController().verify_reproducibility(0.5, 0.5)
        r2 = ReproducibilityController().verify_reproducibility(0.5, 0.5)
        assert r1.reproducible == r2.reproducible


# =============================================================================
# SECTION 11 -- MISMATCH MESSAGE CONTENT (mutant killers)
# =============================================================================

class TestMismatchMessageContent:
    """Assert on mismatch string content to kill display-text mutants."""

    def test_float_mismatch_contains_neq_operator(self):
        """Kills L195: != -> == in f-string."""
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility(1.0, 2.0)
        assert result.reproducible is False
        msg = result.mismatches[0]
        assert "!=" in msg
        assert "==" not in msg  # must NOT contain == (kills the mutant)

    def test_float_mismatch_diff_value_is_correct(self):
        """Kills L195: - -> + in abs(a - b)."""
        ctrl = ReproducibilityController()
        a, b = 1.0, 3.0
        result = ctrl.verify_reproducibility(a, b)
        assert result.reproducible is False
        msg = result.mismatches[0]
        # diff should be abs(1.0 - 3.0) = 2.0, not abs(1.0 + 3.0) = 4.0
        assert "2.00e+00" in msg

    def test_array_mismatch_max_diff_correct(self):
        """Kills L203: a - b -> a + b in np.abs(...)."""
        ctrl = ReproducibilityController()
        a = np.array([0.0, 1.0])
        b = np.array([0.0, 2.0])
        result = ctrl.verify_reproducibility(a, b)
        assert result.reproducible is False
        msg = result.mismatches[0]
        # max_diff = max(abs([0-0, 1-2])) = 1.0
        # mutant:   max(abs([0+0, 1+2])) = 3.0
        assert "1.00e+00" in msg

    def test_generic_mismatch_contains_neq(self):
        """Kills L229: != -> == in f-string for non-float/array/dict/list."""
        ctrl = ReproducibilityController()
        result = ctrl.verify_reproducibility("hello", "world")
        assert result.reproducible is False
        msg = result.mismatches[0]
        assert "!=" in msg
        assert "==" not in msg
