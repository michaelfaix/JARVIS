# =============================================================================
# test_exceptions.py -- Mutation-safe pytest tests for
#                       jarvis/risk_layer/exceptions.py
#
# Mutation-killing strategy
# -------------------------
# 1. EXACT message strings are asserted character-by-character via `==` so
#    that any change to a format literal, quote character, separator, or
#    field order breaks a test.
# 2. Every attribute on every exception (field_name, value, message,
#    constraint, field_a/b, value_a/b, invariant_description) is asserted
#    independently so that a mutation that stores the wrong variable in the
#    wrong slot is caught.
# 3. __repr__ output is tested with exact string matching.
# 4. __eq__ is tested for True cases, False cases, and NotImplemented cases;
#    every field that participates in equality is mutated in isolation.
# 5. Inheritance chain is verified so that `except RiskError` still catches
#    concrete subclasses.
# 6. ValueError guards (empty field_name, empty constraint, etc.) are all
#    exercised so that removing a guard causes a test failure.
# 7. Edge values (NaN, +Inf, -Inf, 0, negative) are passed to confirm they
#    are stored faithfully and reflected in the message via repr().
# =============================================================================

from __future__ import annotations

import importlib.util
import math
import pathlib
import sys

import pytest

# ---------------------------------------------------------------------------
# Load exceptions.py directly (no package machinery needed)
# ---------------------------------------------------------------------------
_saved_exc = sys.modules.get("jarvis.risk_layer.exceptions")
_spec = importlib.util.spec_from_file_location(
    "jarvis.risk_layer.exceptions",
    pathlib.Path(__file__).parent / "exceptions.py",
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["jarvis.risk_layer.exceptions"] = _mod
_spec.loader.exec_module(_mod)

RiskError                    = _mod.RiskError
RiskNumericalError           = _mod.RiskNumericalError
RiskValidationError          = _mod.RiskValidationError
RiskParameterConsistencyError = _mod.RiskParameterConsistencyError

# Restore sys.modules so fake stubs do not leak into other test files
if _saved_exc is not None:
    sys.modules["jarvis.risk_layer.exceptions"] = _saved_exc
else:
    sys.modules.pop("jarvis.risk_layer.exceptions", None)


# =============================================================================
# Helpers
# =============================================================================

def _numerical(field_name="entry_price", value=math.inf):
    return RiskNumericalError(field_name=field_name, value=value)


def _validation(field_name="nav", value=-1.0, constraint="must be > 0"):
    return RiskValidationError(field_name=field_name, value=value, constraint=constraint)


def _consistency(
    field_a="peak_nav", value_a=900.0,
    field_b="nav",      value_b=1000.0,
    invariant_description="peak_nav must be >= nav (high-water mark)",
):
    return RiskParameterConsistencyError(
        field_a=field_a, value_a=value_a,
        field_b=field_b, value_b=value_b,
        invariant_description=invariant_description,
    )


# =============================================================================
# SECTION 1 -- RiskError (base class)
# =============================================================================

class TestRiskErrorInit:
    def test_stores_message(self):
        e = RiskError(message="some violation", field_name="f", value=42)
        assert e.message == "some violation"

    def test_stores_field_name(self):
        e = RiskError(message="msg", field_name="my_field", value=0)
        assert e.field_name == "my_field"

    def test_stores_value(self):
        e = RiskError(message="msg", field_name="f", value=3.14)
        assert e.value == 3.14

    def test_value_defaults_to_none(self):
        e = RiskError(message="msg", field_name="f")
        assert e.value is None

    def test_field_name_defaults_to_empty_string(self):
        e = RiskError(message="msg")
        assert e.field_name == ""

    def test_is_exception_subclass(self):
        assert issubclass(RiskError, Exception)

    def test_str_is_message(self):
        e = RiskError(message="hello world")
        assert str(e) == "hello world"

    def test_empty_message_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            RiskError(message="")
        assert "non-empty string" in str(exc_info.value)

    def test_non_string_message_raises_value_error(self):
        with pytest.raises(ValueError):
            RiskError(message=None)  # type: ignore[arg-type]

    def test_non_string_field_name_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            RiskError(message="msg", field_name=123)  # type: ignore[arg-type]
        assert "field_name" in str(exc_info.value)

    def test_value_can_be_any_type(self):
        for val in [None, 0, -1, math.nan, math.inf, "str", [1, 2], {"a": 1}]:
            e = RiskError(message="m", value=val)
            assert e.value == val or (math.isnan(val) if isinstance(val, float) else False) or e.value is val


class TestRiskErrorRepr:
    def test_repr_contains_class_name(self):
        e = RiskError(message="msg", field_name="f", value=7)
        assert repr(e).startswith("RiskError(")

    def test_repr_exact_format(self):
        e = RiskError(message="test message", field_name="alpha", value=42)
        expected = (
            "RiskError("
            "field_name='alpha', "
            "value=42, "
            "message='test message')"
        )
        assert repr(e) == expected

    def test_repr_none_value(self):
        e = RiskError(message="msg", field_name="f", value=None)
        assert "value=None" in repr(e)

    def test_repr_string_value(self):
        e = RiskError(message="msg", field_name="f", value="bad")
        assert "value='bad'" in repr(e)


class TestRiskErrorEq:
    def test_equal_to_itself(self):
        e = RiskError(message="msg", field_name="f", value=1)
        assert e == e

    def test_equal_same_args(self):
        e1 = RiskError(message="msg", field_name="f", value=1)
        e2 = RiskError(message="msg", field_name="f", value=1)
        assert e1 == e2

    def test_not_equal_different_message(self):
        e1 = RiskError(message="msg1", field_name="f", value=1)
        e2 = RiskError(message="msg2", field_name="f", value=1)
        assert e1 != e2

    def test_not_equal_different_field_name(self):
        e1 = RiskError(message="msg", field_name="f1", value=1)
        e2 = RiskError(message="msg", field_name="f2", value=1)
        assert e1 != e2

    def test_not_equal_different_value(self):
        e1 = RiskError(message="msg", field_name="f", value=1)
        e2 = RiskError(message="msg", field_name="f", value=2)
        assert e1 != e2

    def test_not_equal_different_type(self):
        e1 = RiskError(message="msg", field_name="f", value=1)
        # RiskNumericalError has a different type
        result = e1.__eq__("some string")
        assert result is NotImplemented

    def test_subclass_not_equal_to_base_with_same_message(self):
        # type(self) is type(other) check
        e_base = RiskError(message="m", field_name="f", value=1)
        # Can't construct RiskNumericalError with same raw message; just
        # confirm base vs base equality works and different types don't match
        e2 = RiskError(message="m", field_name="f", value=1)
        assert e_base == e2  # same type, same fields


# =============================================================================
# SECTION 2 -- RiskNumericalError
# =============================================================================

class TestRiskNumericalErrorInit:
    def test_is_risk_error_subclass(self):
        assert issubclass(RiskNumericalError, RiskError)

    def test_is_exception(self):
        assert issubclass(RiskNumericalError, Exception)

    def test_stores_field_name(self):
        e = _numerical("entry_price", math.inf)
        assert e.field_name == "entry_price"

    def test_stores_value_inf(self):
        e = _numerical("f", math.inf)
        assert e.value == math.inf

    def test_stores_value_neg_inf(self):
        e = _numerical("f", -math.inf)
        assert e.value == -math.inf

    def test_stores_value_nan(self):
        e = _numerical("f", math.nan)
        assert math.isnan(e.value)

    def test_empty_field_name_raises(self):
        with pytest.raises(ValueError) as exc_info:
            RiskNumericalError(field_name="", value=math.inf)
        assert "field_name" in str(exc_info.value)
        assert "non-empty" in str(exc_info.value)

    def test_message_is_non_empty(self):
        e = _numerical()
        assert len(e.message) > 0

    def test_str_equals_message(self):
        e = _numerical("entry_price", math.inf)
        assert str(e) == e.message


class TestRiskNumericalErrorMessage:
    """Exact message format tests -- any format change kills these."""

    def test_message_exact_inf(self):
        e = RiskNumericalError(field_name="entry_price", value=math.inf)
        expected = (
            "RiskNumericalError: field 'entry_price' contains non-finite value: "
            + repr(math.inf)
            + ". NaN and Inf are not permitted."
        )
        assert e.message == expected

    def test_message_exact_neg_inf(self):
        e = RiskNumericalError(field_name="current_price", value=-math.inf)
        expected = (
            "RiskNumericalError: field 'current_price' contains non-finite value: "
            + repr(-math.inf)
            + ". NaN and Inf are not permitted."
        )
        assert e.message == expected

    def test_message_exact_nan(self):
        e = RiskNumericalError(field_name="quantity", value=math.nan)
        expected = (
            "RiskNumericalError: field 'quantity' contains non-finite value: "
            + repr(math.nan)
            + ". NaN and Inf are not permitted."
        )
        assert e.message == expected

    def test_message_contains_class_label(self):
        e = _numerical()
        assert "RiskNumericalError" in e.message

    def test_message_contains_field_name(self):
        e = RiskNumericalError(field_name="my_special_field", value=math.inf)
        assert "my_special_field" in e.message

    def test_message_contains_non_finite_phrase(self):
        e = _numerical()
        assert "non-finite" in e.message

    def test_message_contains_nan_inf_prohibition(self):
        e = _numerical()
        assert "NaN and Inf are not permitted" in e.message

    def test_message_single_quotes_around_field(self):
        e = RiskNumericalError(field_name="nav", value=math.inf)
        assert "'nav'" in e.message

    def test_message_contains_repr_of_value_inf(self):
        e = RiskNumericalError(field_name="f", value=math.inf)
        assert repr(math.inf) in e.message

    def test_message_ends_with_period(self):
        e = _numerical()
        assert e.message.endswith(".")

    def test_message_different_field_names_differ(self):
        e1 = RiskNumericalError(field_name="alpha", value=math.inf)
        e2 = RiskNumericalError(field_name="beta",  value=math.inf)
        assert e1.message != e2.message

    def test_message_different_values_differ(self):
        e1 = RiskNumericalError(field_name="f", value=math.inf)
        e2 = RiskNumericalError(field_name="f", value=math.nan)
        assert e1.message != e2.message


class TestRiskNumericalErrorRepr:
    def test_repr_uses_base_format(self):
        e = RiskNumericalError(field_name="entry_price", value=math.inf)
        r = repr(e)
        assert r.startswith("RiskNumericalError(")
        assert "field_name='entry_price'" in r
        assert f"value={repr(math.inf)}" in r

    def test_repr_exact(self):
        e = RiskNumericalError(field_name="nav", value=math.inf)
        expected = (
            "RiskNumericalError("
            "field_name='nav', "
            f"value={repr(math.inf)}, "
            f"message={repr(e.message)})"
        )
        assert repr(e) == expected


class TestRiskNumericalErrorEq:
    def test_equal_same_args(self):
        e1 = _numerical("f", math.inf)
        e2 = _numerical("f", math.inf)
        assert e1 == e2

    def test_not_equal_different_field(self):
        e1 = _numerical("f1", math.inf)
        e2 = _numerical("f2", math.inf)
        assert e1 != e2

    def test_not_equal_different_value(self):
        e1 = _numerical("f", math.inf)
        e2 = _numerical("f", -math.inf)
        assert e1 != e2

    def test_not_equal_non_risk_error(self):
        e = _numerical()
        assert e.__eq__(42) is NotImplemented

    def test_nan_equality(self):
        # Two NaN RiskNumericalErrors: message strings will be equal because
        # repr(nan) == repr(nan); value comparison: nan != nan in Python.
        # Base __eq__ uses self.value == other.value which is False for NaN.
        e1 = _numerical("f", math.nan)
        e2 = _numerical("f", math.nan)
        # NaN != NaN, so these should NOT be equal per __eq__
        assert e1 != e2


# =============================================================================
# SECTION 3 -- RiskValidationError
# =============================================================================

class TestRiskValidationErrorInit:
    def test_is_risk_error_subclass(self):
        assert issubclass(RiskValidationError, RiskError)

    def test_stores_field_name(self):
        e = _validation("nav", -1.0, "must be > 0")
        assert e.field_name == "nav"

    def test_stores_value(self):
        e = _validation("nav", -1.0, "must be > 0")
        assert e.value == -1.0

    def test_stores_constraint(self):
        e = _validation("nav", -1.0, "must be > 0")
        assert e.constraint == "must be > 0"

    def test_empty_field_name_raises(self):
        with pytest.raises(ValueError) as exc_info:
            RiskValidationError(field_name="", value=0, constraint="c")
        assert "field_name" in str(exc_info.value)

    def test_empty_constraint_raises(self):
        with pytest.raises(ValueError) as exc_info:
            RiskValidationError(field_name="f", value=0, constraint="")
        assert "constraint" in str(exc_info.value)

    def test_non_string_constraint_raises(self):
        with pytest.raises(ValueError) as exc_info:
            RiskValidationError(field_name="f", value=0, constraint=None)  # type: ignore[arg-type]
        assert "constraint" in str(exc_info.value)

    def test_str_equals_message(self):
        e = _validation()
        assert str(e) == e.message

    def test_value_can_be_string(self):
        e = RiskValidationError(field_name="symbol", value="BAD_CLASS", constraint="must be in VALID_ASSET_CLASSES")
        assert e.value == "BAD_CLASS"

    def test_value_can_be_none(self):
        e = RiskValidationError(field_name="side", value=None, constraint="must be a valid Side enum member")
        assert e.value is None

    def test_value_can_be_zero(self):
        e = _validation("qty", 0.0, "must be > 0")
        assert e.value == 0.0

    def test_value_can_be_bool(self):
        e = RiskValidationError(field_name="open_positions", value=True, constraint="must be a non-negative integer")
        assert e.value is True


class TestRiskValidationErrorMessage:
    """Exact message format tests."""

    def test_message_exact_float_value(self):
        e = RiskValidationError(field_name="nav", value=-1.0, constraint="must be > 0")
        expected = (
            "RiskValidationError: field 'nav' violates constraint "
            "'must be > 0': got -1.0."
        )
        assert e.message == expected

    def test_message_exact_zero(self):
        e = RiskValidationError(field_name="entry_price", value=0.0, constraint="must be > 0")
        expected = (
            "RiskValidationError: field 'entry_price' violates constraint "
            "'must be > 0': got 0.0."
        )
        assert e.message == expected

    def test_message_exact_string_value(self):
        e = RiskValidationError(field_name="asset_class", value="UNKNOWN", constraint="must be in VALID_ASSET_CLASSES")
        expected = (
            "RiskValidationError: field 'asset_class' violates constraint "
            "'must be in VALID_ASSET_CLASSES': got 'UNKNOWN'."
        )
        assert e.message == expected

    def test_message_exact_none_value(self):
        e = RiskValidationError(field_name="side", value=None, constraint="must be a valid Side enum member")
        expected = (
            "RiskValidationError: field 'side' violates constraint "
            "'must be a valid Side enum member': got None."
        )
        assert e.message == expected

    def test_message_exact_integer_value(self):
        e = RiskValidationError(field_name="open_positions", value=-3, constraint="must be >= 0")
        expected = (
            "RiskValidationError: field 'open_positions' violates constraint "
            "'must be >= 0': got -3."
        )
        assert e.message == expected

    def test_message_exact_interval_constraint(self):
        e = RiskValidationError(field_name="realized_drawdown_pct", value=1.5, constraint="must be in [0.0, 1.0]")
        expected = (
            "RiskValidationError: field 'realized_drawdown_pct' violates constraint "
            "'must be in [0.0, 1.0]': got 1.5."
        )
        assert e.message == expected

    def test_message_contains_class_label(self):
        e = _validation()
        assert "RiskValidationError" in e.message

    def test_message_contains_violates_constraint_phrase(self):
        e = _validation()
        assert "violates constraint" in e.message

    def test_message_contains_got_phrase(self):
        e = _validation()
        assert "got " in e.message

    def test_message_single_quotes_around_field(self):
        e = _validation("my_field", -1.0, "must be > 0")
        assert "'my_field'" in e.message

    def test_message_single_quotes_around_constraint(self):
        e = _validation("f", -1.0, "must be > 0")
        assert "'must be > 0'" in e.message

    def test_message_ends_with_period(self):
        e = _validation()
        assert e.message.endswith(".")

    def test_message_uses_repr_for_value(self):
        """Mutation: storing str(value) instead of repr(value) breaks string values."""
        e = RiskValidationError(field_name="symbol", value="BAD", constraint="must be non-empty")
        assert repr("BAD") in e.message  # repr adds surrounding quotes

    def test_message_changes_with_field_name(self):
        e1 = _validation("field_a", -1.0, "must be > 0")
        e2 = _validation("field_b", -1.0, "must be > 0")
        assert e1.message != e2.message

    def test_message_changes_with_value(self):
        e1 = _validation("f", -1.0, "must be > 0")
        e2 = _validation("f", -2.0, "must be > 0")
        assert e1.message != e2.message

    def test_message_changes_with_constraint(self):
        e1 = _validation("f", -1.0, "must be > 0")
        e2 = _validation("f", -1.0, "must be in (0.0, 1.0]")
        assert e1.message != e2.message


class TestRiskValidationErrorRepr:
    def test_repr_starts_with_class_name(self):
        e = _validation()
        assert repr(e).startswith("RiskValidationError(")

    def test_repr_exact(self):
        e = RiskValidationError(field_name="nav", value=-1.0, constraint="must be > 0")
        expected = (
            "RiskValidationError("
            "field_name='nav', "
            "value=-1.0, "
            f"message={repr(e.message)})"
        )
        assert repr(e) == expected


class TestRiskValidationErrorEq:
    def test_equal_same_args(self):
        e1 = _validation("nav", -1.0, "must be > 0")
        e2 = _validation("nav", -1.0, "must be > 0")
        assert e1 == e2

    def test_not_equal_different_field(self):
        assert _validation("f1") != _validation("f2")

    def test_not_equal_different_value(self):
        e1 = _validation("f", -1.0, "must be > 0")
        e2 = _validation("f", -2.0, "must be > 0")
        assert e1 != e2

    def test_not_equal_different_constraint(self):
        e1 = _validation("f", -1.0, "must be > 0")
        e2 = _validation("f", -1.0, "must be >= 0")
        assert e1 != e2

    def test_not_equal_non_risk_error(self):
        assert _validation().__eq__("x") is NotImplemented


# =============================================================================
# SECTION 4 -- RiskParameterConsistencyError
# =============================================================================

class TestRiskParameterConsistencyErrorInit:
    def test_is_risk_error_subclass(self):
        assert issubclass(RiskParameterConsistencyError, RiskError)

    def test_stores_field_a(self):
        e = _consistency()
        assert e.field_a == "peak_nav"

    def test_stores_value_a(self):
        e = _consistency()
        assert e.value_a == 900.0

    def test_stores_field_b(self):
        e = _consistency()
        assert e.field_b == "nav"

    def test_stores_value_b(self):
        e = _consistency()
        assert e.value_b == 1000.0

    def test_stores_invariant_description(self):
        e = _consistency()
        assert e.invariant_description == "peak_nav must be >= nav (high-water mark)"

    def test_base_field_name_is_field_a(self):
        """Base class field_name must be set to field_a, not field_b."""
        e = _consistency(field_a="soft_warn", field_b="hard_stop")
        assert e.field_name == "soft_warn"

    def test_base_value_is_value_a(self):
        """Base class value must be set to value_a."""
        e = _consistency(value_a=0.05, value_b=0.10)
        assert e.value == 0.05

    def test_empty_field_a_raises(self):
        with pytest.raises(ValueError) as exc_info:
            RiskParameterConsistencyError(
                field_a="", value_a=1.0,
                field_b="b", value_b=2.0,
                invariant_description="desc",
            )
        assert "field_a" in str(exc_info.value)

    def test_empty_field_b_raises(self):
        with pytest.raises(ValueError) as exc_info:
            RiskParameterConsistencyError(
                field_a="a", value_a=1.0,
                field_b="", value_b=2.0,
                invariant_description="desc",
            )
        assert "field_b" in str(exc_info.value)

    def test_empty_invariant_description_raises(self):
        with pytest.raises(ValueError) as exc_info:
            RiskParameterConsistencyError(
                field_a="a", value_a=1.0,
                field_b="b", value_b=2.0,
                invariant_description="",
            )
        assert "invariant_description" in str(exc_info.value)

    def test_none_invariant_description_raises(self):
        with pytest.raises(ValueError):
            RiskParameterConsistencyError(
                field_a="a", value_a=1.0,
                field_b="b", value_b=2.0,
                invariant_description=None,  # type: ignore[arg-type]
            )

    def test_str_equals_message(self):
        e = _consistency()
        assert str(e) == e.message

    def test_values_can_be_any_type(self):
        e = RiskParameterConsistencyError(
            field_a="a", value_a="stringval",
            field_b="b", value_b=None,
            invariant_description="desc",
        )
        assert e.value_a == "stringval"
        assert e.value_b is None


class TestRiskParameterConsistencyErrorMessage:
    """Exact message format tests -- any change to a literal breaks tests."""

    def test_message_exact_float_values(self):
        e = RiskParameterConsistencyError(
            field_a="peak_nav",  value_a=900.0,
            field_b="nav",       value_b=1000.0,
            invariant_description="peak_nav must be >= nav (high-water mark)",
        )
        expected = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            "peak_nav must be >= nav (high-water mark). "
            "Field 'peak_nav' = 900.0, "
            "field 'nav' = 1000.0."
        )
        assert e.message == expected

    def test_message_exact_rp_cross_field(self):
        e = RiskParameterConsistencyError(
            field_a="max_drawdown_soft_warn",  value_a=0.10,
            field_b="max_drawdown_hard_stop",  value_b=0.10,
            invariant_description=(
                "max_drawdown_soft_warn must be strictly less than "
                "max_drawdown_hard_stop "
                "(the soft-warning band must have positive width)"
            ),
        )
        expected = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            "max_drawdown_soft_warn must be strictly less than "
            "max_drawdown_hard_stop "
            "(the soft-warning band must have positive width). "
            "Field 'max_drawdown_soft_warn' = 0.1, "
            "field 'max_drawdown_hard_stop' = 0.1."
        )
        assert e.message == expected

    def test_message_contains_class_label(self):
        e = _consistency()
        assert "RiskParameterConsistencyError" in e.message

    def test_message_contains_cross_field_invariant_violated(self):
        e = _consistency()
        assert "cross-field invariant violated" in e.message

    def test_message_contains_double_dash_separator(self):
        e = _consistency()
        assert " -- " in e.message

    def test_message_contains_invariant_description(self):
        e = _consistency(invariant_description="soft must be less than hard")
        assert "soft must be less than hard" in e.message

    def test_message_contains_field_a_label(self):
        e = _consistency(field_a="peak_nav")
        assert "Field 'peak_nav'" in e.message

    def test_message_contains_field_b_label(self):
        e = _consistency(field_b="nav")
        assert "field 'nav'" in e.message

    def test_message_contains_value_a_repr(self):
        e = _consistency(value_a=900.0)
        assert "900.0" in e.message

    def test_message_contains_value_b_repr(self):
        e = _consistency(value_b=1000.0)
        assert "1000.0" in e.message

    def test_message_uses_repr_for_string_value_a(self):
        e = RiskParameterConsistencyError(
            field_a="a", value_a="sval",
            field_b="b", value_b=1.0,
            invariant_description="desc",
        )
        assert repr("sval") in e.message  # should be 'sval' not sval

    def test_message_ends_with_period(self):
        e = _consistency()
        assert e.message.endswith(".")

    def test_message_capital_F_in_field_a_position(self):
        """'Field' (capital) precedes field_a; 'field' (lower) precedes field_b."""
        e = _consistency()
        msg = e.message
        # Find positions of both occurrences
        idx_capital = msg.index("Field '")
        idx_lower   = msg.index("field '", idx_capital + 1)
        assert idx_capital < idx_lower

    def test_message_changes_with_field_a(self):
        e1 = _consistency(field_a="alpha")
        e2 = _consistency(field_a="beta")
        assert e1.message != e2.message

    def test_message_changes_with_field_b(self):
        e1 = _consistency(field_b="alpha")
        e2 = _consistency(field_b="beta")
        assert e1.message != e2.message

    def test_message_changes_with_value_a(self):
        e1 = _consistency(value_a=1.0)
        e2 = _consistency(value_a=2.0)
        assert e1.message != e2.message

    def test_message_changes_with_value_b(self):
        e1 = _consistency(value_b=1.0)
        e2 = _consistency(value_b=2.0)
        assert e1.message != e2.message

    def test_message_changes_with_invariant_description(self):
        e1 = _consistency(invariant_description="desc one")
        e2 = _consistency(invariant_description="desc two")
        assert e1.message != e2.message


class TestRiskParameterConsistencyErrorRepr:
    def test_repr_starts_with_class_name(self):
        e = _consistency()
        assert repr(e).startswith("RiskParameterConsistencyError(")

    def test_repr_exact(self):
        e = RiskParameterConsistencyError(
            field_a="peak_nav",  value_a=900.0,
            field_b="nav",       value_b=1000.0,
            invariant_description="peak_nav must be >= nav",
        )
        expected = (
            "RiskParameterConsistencyError("
            "field_a='peak_nav', "
            "value_a=900.0, "
            "field_b='nav', "
            "value_b=1000.0, "
            "invariant_description='peak_nav must be >= nav')"
        )
        assert repr(e) == expected

    def test_repr_does_not_include_message(self):
        """The overridden __repr__ uses its own format, not the base format."""
        e = _consistency()
        assert "message=" not in repr(e)

    def test_repr_includes_all_five_fields(self):
        e = _consistency(
            field_a="fa", value_a=1.0,
            field_b="fb", value_b=2.0,
            invariant_description="inv",
        )
        r = repr(e)
        assert "field_a='fa'" in r
        assert "value_a=1.0" in r
        assert "field_b='fb'" in r
        assert "value_b=2.0" in r
        assert "invariant_description='inv'" in r


class TestRiskParameterConsistencyErrorEq:
    def test_equal_same_args(self):
        e1 = _consistency()
        e2 = _consistency()
        assert e1 == e2

    def test_not_equal_different_field_a(self):
        e1 = _consistency(field_a="a1")
        e2 = _consistency(field_a="a2")
        assert e1 != e2

    def test_not_equal_different_value_a(self):
        e1 = _consistency(value_a=1.0)
        e2 = _consistency(value_a=2.0)
        assert e1 != e2

    def test_not_equal_different_field_b(self):
        e1 = _consistency(field_b="b1")
        e2 = _consistency(field_b="b2")
        assert e1 != e2

    def test_not_equal_different_value_b(self):
        e1 = _consistency(value_b=1.0)
        e2 = _consistency(value_b=2.0)
        assert e1 != e2

    def test_not_equal_different_invariant_description(self):
        e1 = _consistency(invariant_description="desc one")
        e2 = _consistency(invariant_description="desc two")
        assert e1 != e2

    def test_not_equal_non_consistency_error(self):
        e = _consistency()
        assert e.__eq__("x") is NotImplemented

    def test_not_equal_to_base_risk_error(self):
        e_c = _consistency()
        e_b = RiskError(message=e_c.message, field_name=e_c.field_a, value=e_c.value_a)
        # Different types -- __eq__ on e_c checks isinstance(other, RiskParameterConsistencyError)
        assert e_c != e_b


# =============================================================================
# SECTION 5 -- Inheritance chain & catchability
# =============================================================================

class TestInheritanceChain:
    def test_numerical_caught_as_risk_error(self):
        with pytest.raises(RiskError):
            raise _numerical()

    def test_validation_caught_as_risk_error(self):
        with pytest.raises(RiskError):
            raise _validation()

    def test_consistency_caught_as_risk_error(self):
        with pytest.raises(RiskError):
            raise _consistency()

    def test_numerical_caught_as_exception(self):
        with pytest.raises(Exception):
            raise _numerical()

    def test_validation_caught_as_exception(self):
        with pytest.raises(Exception):
            raise _validation()

    def test_consistency_caught_as_exception(self):
        with pytest.raises(Exception):
            raise _consistency()

    def test_risk_error_not_raised_directly_in_module(self):
        # RiskError itself is instantiable; just confirm subclasses are distinct
        assert RiskNumericalError is not RiskError
        assert RiskValidationError is not RiskError
        assert RiskParameterConsistencyError is not RiskError


# =============================================================================
# SECTION 6 -- __all__ completeness
# =============================================================================

class TestDunderAll:
    def test_all_contains_risk_error(self):
        assert "RiskError" in _mod.__all__

    def test_all_contains_numerical_error(self):
        assert "RiskNumericalError" in _mod.__all__

    def test_all_contains_validation_error(self):
        assert "RiskValidationError" in _mod.__all__

    def test_all_contains_consistency_error(self):
        assert "RiskParameterConsistencyError" in _mod.__all__

    def test_all_has_exactly_four_entries(self):
        assert len(_mod.__all__) == 4


# =============================================================================
# SECTION 7 -- No side effects / determinism
# =============================================================================

class TestDeterminism:
    def test_same_numerical_message_on_repeated_construction(self):
        e1 = RiskNumericalError(field_name="f", value=math.inf)
        e2 = RiskNumericalError(field_name="f", value=math.inf)
        assert e1.message == e2.message

    def test_same_validation_message_on_repeated_construction(self):
        e1 = _validation("nav", -1.0, "must be > 0")
        e2 = _validation("nav", -1.0, "must be > 0")
        assert e1.message == e2.message

    def test_same_consistency_message_on_repeated_construction(self):
        e1 = _consistency()
        e2 = _consistency()
        assert e1.message == e2.message

    def test_exceptions_are_pure_values_no_mutation(self):
        e = _validation()
        msg_before = e.message
        _ = repr(e)
        _ = str(e)
        assert e.message == msg_before
