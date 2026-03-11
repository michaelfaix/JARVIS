# tests/unit/core/test_risk_layer_exceptions_cov.py
# Coverage target: jarvis/core/risk_layer/exceptions.py -> 95%+
# Missing lines: 81, 85, 94, 103-105, 141-152, 192, 196, 258-288, 291, 302-304
# These tests import from the REAL module (not the local copy).

import math

import pytest

from jarvis.core.risk_layer.exceptions import (
    RiskError,
    RiskNumericalError,
    RiskValidationError,
    RiskParameterConsistencyError,
)


# =============================================================================
# RiskError base (lines 80-110)
# =============================================================================

class TestRiskErrorBase:
    def test_construction(self):
        e = RiskError("test message", field_name="f", value=42)
        assert e.message == "test message"
        assert e.field_name == "f"
        assert e.value == 42
        assert str(e) == "test message"

    def test_empty_message_raises(self):
        with pytest.raises(ValueError, match="non-empty string"):
            RiskError("")

    def test_none_message_raises(self):
        with pytest.raises(ValueError, match="non-empty string"):
            RiskError(None)

    def test_non_string_field_name_raises(self):
        with pytest.raises(ValueError, match="field_name must be a string"):
            RiskError("msg", field_name=123)

    def test_repr(self):
        e = RiskError("msg", field_name="f", value=1)
        r = repr(e)
        assert "RiskError" in r
        assert "field_name='f'" in r
        assert "value=1" in r
        assert "message='msg'" in r

    def test_eq_same(self):
        a = RiskError("msg", "f", 1)
        b = RiskError("msg", "f", 1)
        assert a == b

    def test_eq_different_message(self):
        a = RiskError("a", "f", 1)
        b = RiskError("b", "f", 1)
        assert a != b

    def test_eq_not_implemented(self):
        e = RiskError("msg")
        assert e.__eq__("not an error") is NotImplemented

    def test_is_exception(self):
        assert issubclass(RiskError, Exception)


# =============================================================================
# RiskNumericalError (lines 141-152)
# =============================================================================

class TestRiskNumericalError:
    def test_nan_value(self):
        e = RiskNumericalError("vol", float("nan"))
        assert "vol" in e.message
        assert "nan" in e.message.lower()
        assert e.field_name == "vol"
        assert math.isnan(e.value)

    def test_inf_value(self):
        e = RiskNumericalError("price", float("inf"))
        assert "price" in e.message
        assert e.field_name == "price"

    def test_neg_inf_value(self):
        e = RiskNumericalError("ret", float("-inf"))
        assert e.field_name == "ret"

    def test_empty_field_name_raises(self):
        with pytest.raises(ValueError, match="non-empty string"):
            RiskNumericalError("", float("nan"))

    def test_inherits_risk_error(self):
        e = RiskNumericalError("f", float("nan"))
        assert isinstance(e, RiskError)


# =============================================================================
# RiskValidationError (lines 192, 196)
# =============================================================================

class TestRiskValidationError:
    def test_construction(self):
        e = RiskValidationError("pct", -0.5, "must be >= 0")
        assert "pct" in e.message
        assert "must be >= 0" in e.message
        assert e.field_name == "pct"
        assert e.value == -0.5
        assert e.constraint == "must be >= 0"

    def test_empty_field_name_raises(self):
        with pytest.raises(ValueError, match="field_name must be"):
            RiskValidationError("", 1, "c")

    def test_empty_constraint_raises(self):
        with pytest.raises(ValueError, match="constraint must be"):
            RiskValidationError("f", 1, "")

    def test_none_constraint_raises(self):
        with pytest.raises(ValueError, match="constraint must be"):
            RiskValidationError("f", 1, None)

    def test_inherits_risk_error(self):
        e = RiskValidationError("f", 1, "c")
        assert isinstance(e, RiskError)


# =============================================================================
# RiskParameterConsistencyError (lines 258-288, 291, 302-304)
# =============================================================================

class TestRiskParameterConsistencyError:
    def test_construction(self):
        e = RiskParameterConsistencyError(
            "soft_warn", 0.10, "hard_stop", 0.05, "soft must be < hard"
        )
        assert e.field_a == "soft_warn"
        assert e.value_a == 0.10
        assert e.field_b == "hard_stop"
        assert e.value_b == 0.05
        assert e.invariant_description == "soft must be < hard"
        assert "cross-field invariant" in e.message
        assert "soft_warn" in e.message
        assert "hard_stop" in e.message

    def test_empty_field_a_raises(self):
        with pytest.raises(ValueError, match="field_a must be non-empty"):
            RiskParameterConsistencyError("", 1, "b", 2, "inv")

    def test_empty_field_b_raises(self):
        with pytest.raises(ValueError, match="field_b must be non-empty"):
            RiskParameterConsistencyError("a", 1, "", 2, "inv")

    def test_empty_invariant_raises(self):
        with pytest.raises(ValueError, match="invariant_description must be non-empty"):
            RiskParameterConsistencyError("a", 1, "b", 2, "")

    def test_none_invariant_raises(self):
        with pytest.raises(ValueError, match="invariant_description must be non-empty"):
            RiskParameterConsistencyError("a", 1, "b", 2, None)

    def test_repr(self):
        e = RiskParameterConsistencyError("a", 1, "b", 2, "desc")
        r = repr(e)
        assert "RiskParameterConsistencyError" in r
        assert "field_a='a'" in r
        assert "field_b='b'" in r
        assert "invariant_description='desc'" in r

    def test_eq_same(self):
        a = RiskParameterConsistencyError("a", 1, "b", 2, "d")
        b = RiskParameterConsistencyError("a", 1, "b", 2, "d")
        assert a == b

    def test_eq_different(self):
        a = RiskParameterConsistencyError("a", 1, "b", 2, "d")
        b = RiskParameterConsistencyError("a", 1, "b", 3, "d")
        assert a != b

    def test_eq_not_implemented(self):
        e = RiskParameterConsistencyError("a", 1, "b", 2, "d")
        assert e.__eq__("not an error") is NotImplemented

    def test_inherits_risk_error(self):
        e = RiskParameterConsistencyError("a", 1, "b", 2, "d")
        assert isinstance(e, RiskError)

    def test_base_field_name_is_field_a(self):
        e = RiskParameterConsistencyError("alpha", 1, "beta", 2, "inv")
        assert e.field_name == "alpha"
        assert e.value == 1
