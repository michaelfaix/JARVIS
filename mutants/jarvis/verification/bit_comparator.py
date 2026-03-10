# jarvis/verification/bit_comparator.py
# BitComparator -- exact IEEE 754 bit-pattern comparison of ER and RE records.
# Authority: DVH Implementation Blueprint v1.0.0 Section 10.
#
# BIC-F-02: math.isclose(), numpy.allclose(), pytest.approx(), and all other
#           tolerance-based comparison functions are PROHIBITED in this module.
# BIC-F-03: The Python equality operator applied directly to float values is
#           PROHIBITED because it considers +0.0 equal to -0.0.
# All float comparisons use struct.pack big-endian double-precision byte sequences.

import struct
import math
from typing import List, Dict, Tuple

from jarvis.verification.data_models.execution_record import ExecutionRecord, ObservedOutput
from jarvis.verification.data_models.comparison_report import ComparisonReport, FieldMismatch
from jarvis.verification.vectors.vector_definitions import BC_PAIRS
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore


def _float_bits(value: float) -> bytes:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__float_bits__mutmut_orig, x__float_bits__mutmut_mutants, args, kwargs, None)


def x__float_bits__mutmut_orig(value: float) -> bytes:
    """
    Return 8-byte big-endian IEEE 754 representation (BIC-F-01).
    Distinguishes +0.0 from -0.0.
    """
    return struct.pack(">d", value)


def x__float_bits__mutmut_1(value: float) -> bytes:
    """
    Return 8-byte big-endian IEEE 754 representation (BIC-F-01).
    Distinguishes +0.0 from -0.0.
    """
    return struct.pack(None, value)


def x__float_bits__mutmut_2(value: float) -> bytes:
    """
    Return 8-byte big-endian IEEE 754 representation (BIC-F-01).
    Distinguishes +0.0 from -0.0.
    """
    return struct.pack(">d", None)


def x__float_bits__mutmut_3(value: float) -> bytes:
    """
    Return 8-byte big-endian IEEE 754 representation (BIC-F-01).
    Distinguishes +0.0 from -0.0.
    """
    return struct.pack(value)


def x__float_bits__mutmut_4(value: float) -> bytes:
    """
    Return 8-byte big-endian IEEE 754 representation (BIC-F-01).
    Distinguishes +0.0 from -0.0.
    """
    return struct.pack(">d", )


def x__float_bits__mutmut_5(value: float) -> bytes:
    """
    Return 8-byte big-endian IEEE 754 representation (BIC-F-01).
    Distinguishes +0.0 from -0.0.
    """
    return struct.pack("XX>dXX", value)


def x__float_bits__mutmut_6(value: float) -> bytes:
    """
    Return 8-byte big-endian IEEE 754 representation (BIC-F-01).
    Distinguishes +0.0 from -0.0.
    """
    return struct.pack(">D", value)

x__float_bits__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__float_bits__mutmut_1': x__float_bits__mutmut_1, 
    'x__float_bits__mutmut_2': x__float_bits__mutmut_2, 
    'x__float_bits__mutmut_3': x__float_bits__mutmut_3, 
    'x__float_bits__mutmut_4': x__float_bits__mutmut_4, 
    'x__float_bits__mutmut_5': x__float_bits__mutmut_5, 
    'x__float_bits__mutmut_6': x__float_bits__mutmut_6
}
x__float_bits__mutmut_orig.__name__ = 'x__float_bits'


def _floats_equal(a: float, b: float) -> bool:
    args = [a, b]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__floats_equal__mutmut_orig, x__floats_equal__mutmut_mutants, args, kwargs, None)


def x__floats_equal__mutmut_orig(a: float, b: float) -> bool:
    """
    Exact bit-pattern equality for floats (BIC-F-01).
    +0.0 and -0.0 are NOT equal under this comparison (BIC-S-01).
    """
    return _float_bits(a) == _float_bits(b)


def x__floats_equal__mutmut_1(a: float, b: float) -> bool:
    """
    Exact bit-pattern equality for floats (BIC-F-01).
    +0.0 and -0.0 are NOT equal under this comparison (BIC-S-01).
    """
    return _float_bits(None) == _float_bits(b)


def x__floats_equal__mutmut_2(a: float, b: float) -> bool:
    """
    Exact bit-pattern equality for floats (BIC-F-01).
    +0.0 and -0.0 are NOT equal under this comparison (BIC-S-01).
    """
    return _float_bits(a) != _float_bits(b)


def x__floats_equal__mutmut_3(a: float, b: float) -> bool:
    """
    Exact bit-pattern equality for floats (BIC-F-01).
    +0.0 and -0.0 are NOT equal under this comparison (BIC-S-01).
    """
    return _float_bits(a) == _float_bits(None)

x__floats_equal__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__floats_equal__mutmut_1': x__floats_equal__mutmut_1, 
    'x__floats_equal__mutmut_2': x__floats_equal__mutmut_2, 
    'x__floats_equal__mutmut_3': x__floats_equal__mutmut_3
}
x__floats_equal__mutmut_orig.__name__ = 'x__floats_equal'


def _check_special(value: float, field_name: str, vector_id: str) -> None:
    args = [value, field_name, vector_id]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__check_special__mutmut_orig, x__check_special__mutmut_mutants, args, kwargs, None)


def x__check_special__mutmut_orig(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "Hard failure before comparison."
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value > 0 else 'negative'} infinity. "
            "Hard failure before comparison."
        )


def x__check_special__mutmut_1(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(None):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "Hard failure before comparison."
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value > 0 else 'negative'} infinity. "
            "Hard failure before comparison."
        )


def x__check_special__mutmut_2(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            None
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value > 0 else 'negative'} infinity. "
            "Hard failure before comparison."
        )


def x__check_special__mutmut_3(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "XXHard failure before comparison.XX"
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value > 0 else 'negative'} infinity. "
            "Hard failure before comparison."
        )


def x__check_special__mutmut_4(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "hard failure before comparison."
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value > 0 else 'negative'} infinity. "
            "Hard failure before comparison."
        )


def x__check_special__mutmut_5(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "HARD FAILURE BEFORE COMPARISON."
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value > 0 else 'negative'} infinity. "
            "Hard failure before comparison."
        )


def x__check_special__mutmut_6(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "Hard failure before comparison."
        )
    if math.isinf(None):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value > 0 else 'negative'} infinity. "
            "Hard failure before comparison."
        )


def x__check_special__mutmut_7(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "Hard failure before comparison."
        )
    if math.isinf(value):
        raise RuntimeError(
            None
        )


def x__check_special__mutmut_8(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "Hard failure before comparison."
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'XXpositiveXX' if value > 0 else 'negative'} infinity. "
            "Hard failure before comparison."
        )


def x__check_special__mutmut_9(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "Hard failure before comparison."
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'POSITIVE' if value > 0 else 'negative'} infinity. "
            "Hard failure before comparison."
        )


def x__check_special__mutmut_10(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "Hard failure before comparison."
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value >= 0 else 'negative'} infinity. "
            "Hard failure before comparison."
        )


def x__check_special__mutmut_11(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "Hard failure before comparison."
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value > 1 else 'negative'} infinity. "
            "Hard failure before comparison."
        )


def x__check_special__mutmut_12(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "Hard failure before comparison."
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value > 0 else 'XXnegativeXX'} infinity. "
            "Hard failure before comparison."
        )


def x__check_special__mutmut_13(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "Hard failure before comparison."
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value > 0 else 'NEGATIVE'} infinity. "
            "Hard failure before comparison."
        )


def x__check_special__mutmut_14(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "Hard failure before comparison."
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value > 0 else 'negative'} infinity. "
            "XXHard failure before comparison.XX"
        )


def x__check_special__mutmut_15(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "Hard failure before comparison."
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value > 0 else 'negative'} infinity. "
            "hard failure before comparison."
        )


def x__check_special__mutmut_16(value: float, field_name: str, vector_id: str) -> None:
    """
    Check for NaN and Inf before any comparison (BIC-S-02, BIC-S-03).
    Raises RuntimeError with failure_type_id prefix on detection.
    """
    if math.isnan(value):
        raise RuntimeError(
            f"FIELD_NAN: Vector {vector_id} field {field_name} contains NaN. "
            "Hard failure before comparison."
        )
    if math.isinf(value):
        raise RuntimeError(
            f"FIELD_INFINITE: Vector {vector_id} field {field_name} contains "
            f"{'positive' if value > 0 else 'negative'} infinity. "
            "HARD FAILURE BEFORE COMPARISON."
        )

x__check_special__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__check_special__mutmut_1': x__check_special__mutmut_1, 
    'x__check_special__mutmut_2': x__check_special__mutmut_2, 
    'x__check_special__mutmut_3': x__check_special__mutmut_3, 
    'x__check_special__mutmut_4': x__check_special__mutmut_4, 
    'x__check_special__mutmut_5': x__check_special__mutmut_5, 
    'x__check_special__mutmut_6': x__check_special__mutmut_6, 
    'x__check_special__mutmut_7': x__check_special__mutmut_7, 
    'x__check_special__mutmut_8': x__check_special__mutmut_8, 
    'x__check_special__mutmut_9': x__check_special__mutmut_9, 
    'x__check_special__mutmut_10': x__check_special__mutmut_10, 
    'x__check_special__mutmut_11': x__check_special__mutmut_11, 
    'x__check_special__mutmut_12': x__check_special__mutmut_12, 
    'x__check_special__mutmut_13': x__check_special__mutmut_13, 
    'x__check_special__mutmut_14': x__check_special__mutmut_14, 
    'x__check_special__mutmut_15': x__check_special__mutmut_15, 
    'x__check_special__mutmut_16': x__check_special__mutmut_16
}
x__check_special__mutmut_orig.__name__ = 'x__check_special'


def _compare_outputs(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    args = [vector_id, er_out, re_out, failure_type]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__compare_outputs__mutmut_orig, x__compare_outputs__mutmut_mutants, args, kwargs, None)


def x__compare_outputs__mutmut_orig(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_1(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = None

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_2(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = None
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_3(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "XXexpected_drawdownXX",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_4(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "EXPECTED_DRAWDOWN",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_5(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "XXexpected_drawdown_p95XX",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_6(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "EXPECTED_DRAWDOWN_P95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_7(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "XXvolatility_forecastXX",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_8(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "VOLATILITY_FORECAST",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_9(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "XXposition_size_factorXX",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_10(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "POSITION_SIZE_FACTOR",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_11(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "XXexposure_weightXX",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_12(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "EXPOSURE_WEIGHT",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_13(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("XXERXX", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_14(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("er", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_15(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("XXREXX", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_16(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("re", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_17(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = None
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_18(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(None, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_19(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, None)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_20(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_21(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, )
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_22(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(None, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_23(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, None, vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_24(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", None)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_25(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_26(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_27(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", )

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_28(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = None
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_29(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(None, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_30(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, None)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_31(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_32(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, )
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_33(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = None
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_34(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(None, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_35(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, None)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_36(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_37(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, )
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_38(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_39(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(None, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_40(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, None):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_41(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_42(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, ):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_43(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(None)

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_44(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=None,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_45(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=None,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_46(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=None,
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_47(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=None,
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_48(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=None,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_49(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_50(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_51(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_52(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_53(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_54(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(None).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_55(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(None).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_56(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["XXrisk_compression_activeXX", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_57(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["RISK_COMPRESSION_ACTIVE", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_58(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "XXexception_raisedXX"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_59(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "EXCEPTION_RAISED"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_60(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = None
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_61(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(None, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_62(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, None)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_63(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_64(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, )
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_65(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = None
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_66(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(None, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_67(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, None)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_68(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_69(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, )
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_70(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_71(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(None)

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_72(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=None,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_73(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=None,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_74(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=None,
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_75(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=None,
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_76(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type=None,
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_77(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_78(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_79(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_80(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_81(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_82(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(None),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_83(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(None),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_84(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="XXFIELD_BOOLEAN_MISMATCHXX",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_85(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="field_boolean_mismatch",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_86(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["XXrisk_regimeXX", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_87(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["RISK_REGIME", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_88(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "XXexception_typeXX"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_89(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "EXCEPTION_TYPE"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_90(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = None
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_91(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(None, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_92(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, None)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_93(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_94(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, )
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_95(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = None
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_96(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(None, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_97(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, None)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_98(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_99(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, )
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_100(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val == re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_101(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(None)

    return mismatches


def x__compare_outputs__mutmut_102(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=None,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_103(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=None,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_104(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=None,
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_105(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=None,
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_106(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=None,
            ))

    return mismatches


def x__compare_outputs__mutmut_107(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_108(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_109(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_110(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_111(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(re_val),
                ))

    return mismatches


def x__compare_outputs__mutmut_112(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(None),
                re_value_hex=repr(re_val),
                failure_type=failure_type,
            ))

    return mismatches


def x__compare_outputs__mutmut_113(
    vector_id:    str,
    er_out:       ObservedOutput,
    re_out:       ObservedOutput,
    failure_type: str,
) -> List[FieldMismatch]:
    """
    Compare all nine ObservedOutput fields (BIC-C-01).
    Returns list of FieldMismatch records. Empty list means all fields match.

    Float fields: struct-based bit comparison (BIC-F-01).
    Boolean fields: Python identity comparison (BIC-B-01).
    String fields: exact byte-for-byte equality (BIC-S-04).
    Special value pre-check applied to all float fields (BIC-S-02, BIC-S-03).
    """
    mismatches = []

    # Pre-check all float fields for NaN and Inf before any comparison.
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    for field in float_fields:
        for rec_label, rec in [("ER", er_out), ("RE", re_out)]:
            val = getattr(rec, field)
            _check_special(val, f"{field}[{rec_label}]", vector_id)

    # Compare float fields: struct-based bit comparison.
    for field in float_fields:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if not _floats_equal(er_val, re_val):
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=_float_bits(er_val).hex(),
                re_value_hex=_float_bits(re_val).hex(),
                failure_type=failure_type,
            ))

    # Compare boolean: identity (BIC-B-01).
    for field in ["risk_compression_active", "exception_raised"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val is not re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=str(er_val),
                re_value_hex=str(re_val),
                failure_type="FIELD_BOOLEAN_MISMATCH",
            ))

    # Compare string fields: exact equality (BIC-S-04).
    for field in ["risk_regime", "exception_type"]:
        er_val = getattr(er_out, field)
        re_val = getattr(re_out, field)
        if er_val != re_val:
            mismatches.append(FieldMismatch(
                vector_id=vector_id,
                field_name=field,
                er_value_hex=repr(er_val),
                re_value_hex=repr(None),
                failure_type=failure_type,
            ))

    return mismatches

x__compare_outputs__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__compare_outputs__mutmut_1': x__compare_outputs__mutmut_1, 
    'x__compare_outputs__mutmut_2': x__compare_outputs__mutmut_2, 
    'x__compare_outputs__mutmut_3': x__compare_outputs__mutmut_3, 
    'x__compare_outputs__mutmut_4': x__compare_outputs__mutmut_4, 
    'x__compare_outputs__mutmut_5': x__compare_outputs__mutmut_5, 
    'x__compare_outputs__mutmut_6': x__compare_outputs__mutmut_6, 
    'x__compare_outputs__mutmut_7': x__compare_outputs__mutmut_7, 
    'x__compare_outputs__mutmut_8': x__compare_outputs__mutmut_8, 
    'x__compare_outputs__mutmut_9': x__compare_outputs__mutmut_9, 
    'x__compare_outputs__mutmut_10': x__compare_outputs__mutmut_10, 
    'x__compare_outputs__mutmut_11': x__compare_outputs__mutmut_11, 
    'x__compare_outputs__mutmut_12': x__compare_outputs__mutmut_12, 
    'x__compare_outputs__mutmut_13': x__compare_outputs__mutmut_13, 
    'x__compare_outputs__mutmut_14': x__compare_outputs__mutmut_14, 
    'x__compare_outputs__mutmut_15': x__compare_outputs__mutmut_15, 
    'x__compare_outputs__mutmut_16': x__compare_outputs__mutmut_16, 
    'x__compare_outputs__mutmut_17': x__compare_outputs__mutmut_17, 
    'x__compare_outputs__mutmut_18': x__compare_outputs__mutmut_18, 
    'x__compare_outputs__mutmut_19': x__compare_outputs__mutmut_19, 
    'x__compare_outputs__mutmut_20': x__compare_outputs__mutmut_20, 
    'x__compare_outputs__mutmut_21': x__compare_outputs__mutmut_21, 
    'x__compare_outputs__mutmut_22': x__compare_outputs__mutmut_22, 
    'x__compare_outputs__mutmut_23': x__compare_outputs__mutmut_23, 
    'x__compare_outputs__mutmut_24': x__compare_outputs__mutmut_24, 
    'x__compare_outputs__mutmut_25': x__compare_outputs__mutmut_25, 
    'x__compare_outputs__mutmut_26': x__compare_outputs__mutmut_26, 
    'x__compare_outputs__mutmut_27': x__compare_outputs__mutmut_27, 
    'x__compare_outputs__mutmut_28': x__compare_outputs__mutmut_28, 
    'x__compare_outputs__mutmut_29': x__compare_outputs__mutmut_29, 
    'x__compare_outputs__mutmut_30': x__compare_outputs__mutmut_30, 
    'x__compare_outputs__mutmut_31': x__compare_outputs__mutmut_31, 
    'x__compare_outputs__mutmut_32': x__compare_outputs__mutmut_32, 
    'x__compare_outputs__mutmut_33': x__compare_outputs__mutmut_33, 
    'x__compare_outputs__mutmut_34': x__compare_outputs__mutmut_34, 
    'x__compare_outputs__mutmut_35': x__compare_outputs__mutmut_35, 
    'x__compare_outputs__mutmut_36': x__compare_outputs__mutmut_36, 
    'x__compare_outputs__mutmut_37': x__compare_outputs__mutmut_37, 
    'x__compare_outputs__mutmut_38': x__compare_outputs__mutmut_38, 
    'x__compare_outputs__mutmut_39': x__compare_outputs__mutmut_39, 
    'x__compare_outputs__mutmut_40': x__compare_outputs__mutmut_40, 
    'x__compare_outputs__mutmut_41': x__compare_outputs__mutmut_41, 
    'x__compare_outputs__mutmut_42': x__compare_outputs__mutmut_42, 
    'x__compare_outputs__mutmut_43': x__compare_outputs__mutmut_43, 
    'x__compare_outputs__mutmut_44': x__compare_outputs__mutmut_44, 
    'x__compare_outputs__mutmut_45': x__compare_outputs__mutmut_45, 
    'x__compare_outputs__mutmut_46': x__compare_outputs__mutmut_46, 
    'x__compare_outputs__mutmut_47': x__compare_outputs__mutmut_47, 
    'x__compare_outputs__mutmut_48': x__compare_outputs__mutmut_48, 
    'x__compare_outputs__mutmut_49': x__compare_outputs__mutmut_49, 
    'x__compare_outputs__mutmut_50': x__compare_outputs__mutmut_50, 
    'x__compare_outputs__mutmut_51': x__compare_outputs__mutmut_51, 
    'x__compare_outputs__mutmut_52': x__compare_outputs__mutmut_52, 
    'x__compare_outputs__mutmut_53': x__compare_outputs__mutmut_53, 
    'x__compare_outputs__mutmut_54': x__compare_outputs__mutmut_54, 
    'x__compare_outputs__mutmut_55': x__compare_outputs__mutmut_55, 
    'x__compare_outputs__mutmut_56': x__compare_outputs__mutmut_56, 
    'x__compare_outputs__mutmut_57': x__compare_outputs__mutmut_57, 
    'x__compare_outputs__mutmut_58': x__compare_outputs__mutmut_58, 
    'x__compare_outputs__mutmut_59': x__compare_outputs__mutmut_59, 
    'x__compare_outputs__mutmut_60': x__compare_outputs__mutmut_60, 
    'x__compare_outputs__mutmut_61': x__compare_outputs__mutmut_61, 
    'x__compare_outputs__mutmut_62': x__compare_outputs__mutmut_62, 
    'x__compare_outputs__mutmut_63': x__compare_outputs__mutmut_63, 
    'x__compare_outputs__mutmut_64': x__compare_outputs__mutmut_64, 
    'x__compare_outputs__mutmut_65': x__compare_outputs__mutmut_65, 
    'x__compare_outputs__mutmut_66': x__compare_outputs__mutmut_66, 
    'x__compare_outputs__mutmut_67': x__compare_outputs__mutmut_67, 
    'x__compare_outputs__mutmut_68': x__compare_outputs__mutmut_68, 
    'x__compare_outputs__mutmut_69': x__compare_outputs__mutmut_69, 
    'x__compare_outputs__mutmut_70': x__compare_outputs__mutmut_70, 
    'x__compare_outputs__mutmut_71': x__compare_outputs__mutmut_71, 
    'x__compare_outputs__mutmut_72': x__compare_outputs__mutmut_72, 
    'x__compare_outputs__mutmut_73': x__compare_outputs__mutmut_73, 
    'x__compare_outputs__mutmut_74': x__compare_outputs__mutmut_74, 
    'x__compare_outputs__mutmut_75': x__compare_outputs__mutmut_75, 
    'x__compare_outputs__mutmut_76': x__compare_outputs__mutmut_76, 
    'x__compare_outputs__mutmut_77': x__compare_outputs__mutmut_77, 
    'x__compare_outputs__mutmut_78': x__compare_outputs__mutmut_78, 
    'x__compare_outputs__mutmut_79': x__compare_outputs__mutmut_79, 
    'x__compare_outputs__mutmut_80': x__compare_outputs__mutmut_80, 
    'x__compare_outputs__mutmut_81': x__compare_outputs__mutmut_81, 
    'x__compare_outputs__mutmut_82': x__compare_outputs__mutmut_82, 
    'x__compare_outputs__mutmut_83': x__compare_outputs__mutmut_83, 
    'x__compare_outputs__mutmut_84': x__compare_outputs__mutmut_84, 
    'x__compare_outputs__mutmut_85': x__compare_outputs__mutmut_85, 
    'x__compare_outputs__mutmut_86': x__compare_outputs__mutmut_86, 
    'x__compare_outputs__mutmut_87': x__compare_outputs__mutmut_87, 
    'x__compare_outputs__mutmut_88': x__compare_outputs__mutmut_88, 
    'x__compare_outputs__mutmut_89': x__compare_outputs__mutmut_89, 
    'x__compare_outputs__mutmut_90': x__compare_outputs__mutmut_90, 
    'x__compare_outputs__mutmut_91': x__compare_outputs__mutmut_91, 
    'x__compare_outputs__mutmut_92': x__compare_outputs__mutmut_92, 
    'x__compare_outputs__mutmut_93': x__compare_outputs__mutmut_93, 
    'x__compare_outputs__mutmut_94': x__compare_outputs__mutmut_94, 
    'x__compare_outputs__mutmut_95': x__compare_outputs__mutmut_95, 
    'x__compare_outputs__mutmut_96': x__compare_outputs__mutmut_96, 
    'x__compare_outputs__mutmut_97': x__compare_outputs__mutmut_97, 
    'x__compare_outputs__mutmut_98': x__compare_outputs__mutmut_98, 
    'x__compare_outputs__mutmut_99': x__compare_outputs__mutmut_99, 
    'x__compare_outputs__mutmut_100': x__compare_outputs__mutmut_100, 
    'x__compare_outputs__mutmut_101': x__compare_outputs__mutmut_101, 
    'x__compare_outputs__mutmut_102': x__compare_outputs__mutmut_102, 
    'x__compare_outputs__mutmut_103': x__compare_outputs__mutmut_103, 
    'x__compare_outputs__mutmut_104': x__compare_outputs__mutmut_104, 
    'x__compare_outputs__mutmut_105': x__compare_outputs__mutmut_105, 
    'x__compare_outputs__mutmut_106': x__compare_outputs__mutmut_106, 
    'x__compare_outputs__mutmut_107': x__compare_outputs__mutmut_107, 
    'x__compare_outputs__mutmut_108': x__compare_outputs__mutmut_108, 
    'x__compare_outputs__mutmut_109': x__compare_outputs__mutmut_109, 
    'x__compare_outputs__mutmut_110': x__compare_outputs__mutmut_110, 
    'x__compare_outputs__mutmut_111': x__compare_outputs__mutmut_111, 
    'x__compare_outputs__mutmut_112': x__compare_outputs__mutmut_112, 
    'x__compare_outputs__mutmut_113': x__compare_outputs__mutmut_113
}
x__compare_outputs__mutmut_orig.__name__ = 'x__compare_outputs'


class BitComparator:
    """
    Performs exact bit-pattern comparison of ER-stage vs RE-stage records.

    Two comparison passes are performed:
      Pass 1 (BIC-F-01): ER vs RE for every vector (determinism verification).
      Pass 2 (BIC-BC-01): Backward compatibility pair comparison.

    Any mismatch in either pass produces a FieldMismatch and is a hard failure.

    Method:
      compare(er_records, re_records) -> ComparisonReport
    """

    def compare(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        args = [er_records, re_records]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁBitComparatorǁcompare__mutmut_orig'), object.__getattribute__(self, 'xǁBitComparatorǁcompare__mutmut_mutants'), args, kwargs, self)

    def xǁBitComparatorǁcompare__mutmut_orig(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_1(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = None
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_2(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = None

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_3(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = None

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_4(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_5(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(None)
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_6(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=None,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_7(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name=None,
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_8(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex=None,
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_9(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex=None,
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_10(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type=None,
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_11(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_12(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_13(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_14(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_15(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_16(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="XX(record missing)XX",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_17(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(RECORD MISSING)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_18(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="XXpresentXX",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_19(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="PRESENT",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_20(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="XXmissingXX",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_21(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="MISSING",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_22(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="XXDETERMINISM_BREACHXX",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_23(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="determinism_breach",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_24(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                break
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_25(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = None
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_26(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = None
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_27(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=None,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_28(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=None,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_29(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=None,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_30(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type=None,
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_31(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_32(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_33(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_34(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_35(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="XXDETERMINISM_BREACHXX",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_36(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="determinism_breach",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_37(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(None)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_38(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = None
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_39(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id and second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_40(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_41(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_42(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(None)
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_43(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=None,
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_44(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name=None,
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_45(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex=None,
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_46(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex=None,
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_47(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type=None,
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_48(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_49(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_50(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_51(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_52(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_53(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="XX(BC pair missing)XX",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_54(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(bc pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_55(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC PAIR MISSING)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_56(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="XXpresentXX",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_57(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="PRESENT",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_58(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="XXmissingXX",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_59(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="MISSING",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_60(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="XXBACKWARD_COMPAT_VIOLATIONXX",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_61(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="backward_compat_violation",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_62(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                break
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_63(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = None
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_64(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = None
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_65(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = None
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_66(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=None,
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_67(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=None,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_68(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=None,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_69(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type=None,
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_70(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_71(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_72(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_73(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_74(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="XXBACKWARD_COMPAT_VIOLATIONXX",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_75(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="backward_compat_violation",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_76(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(None)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_77(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(None)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_78(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = None
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_79(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) != 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_80(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 1
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_81(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=None,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_82(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=None,
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_83(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=None,
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_84(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=None,   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_85(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=None,
        )

    def xǁBitComparatorǁcompare__mutmut_86(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_87(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_88(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_89(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            notes=(),
        )

    def xǁBitComparatorǁcompare__mutmut_90(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(all_mismatches),
            clip_violations=(),   # Populated by ClipVerifier.
            )

    def xǁBitComparatorǁcompare__mutmut_91(
        self,
        er_records: List[ExecutionRecord],
        re_records: List[ExecutionRecord],
    ) -> ComparisonReport:
        """
        Compare ER and RE record sets. Returns ComparisonReport.

        Raises RuntimeError with failure_type_id prefix on NaN or Inf detection.
        All other failures are collected into ComparisonReport.mismatches.
        """
        # Build lookup dicts by vector_id.
        er_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}
        re_by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in re_records}

        all_mismatches = []

        # Pass 1: ER vs RE for every vector.
        for vector_id, er_rec in er_by_id.items():
            if vector_id not in re_by_id:
                all_mismatches.append(FieldMismatch(
                    vector_id=vector_id,
                    field_name="(record missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="DETERMINISM_BREACH",
                ))
                continue
            re_rec = re_by_id[vector_id]
            mismatches = _compare_outputs(
                vector_id=vector_id,
                er_out=er_rec.observed_output,
                re_out=re_rec.observed_output,
                failure_type="DETERMINISM_BREACH",
            )
            all_mismatches.extend(mismatches)

        # Pass 2: Backward compatibility pairs (BIC-BC-01).
        bc_mismatches = []
        for first_id, second_id in BC_PAIRS:
            if first_id not in er_by_id or second_id not in er_by_id:
                bc_mismatches.append(FieldMismatch(
                    vector_id=f"{first_id}/{second_id}",
                    field_name="(BC pair missing)",
                    er_value_hex="present",
                    re_value_hex="missing",
                    failure_type="BACKWARD_COMPAT_VIOLATION",
                ))
                continue
            first_out  = er_by_id[first_id].observed_output
            second_out = er_by_id[second_id].observed_output
            mismatches = _compare_outputs(
                vector_id=f"{first_id}/{second_id}",
                er_out=first_out,
                re_out=second_out,
                failure_type="BACKWARD_COMPAT_VIOLATION",
            )
            bc_mismatches.extend(mismatches)

        all_mismatches.extend(bc_mismatches)

        passed = len(all_mismatches) == 0
        return ComparisonReport(
            passed=passed,
            total_vectors=len(er_records),
            mismatches=tuple(None),
            clip_violations=(),   # Populated by ClipVerifier.
            notes=(),
        )
    
    xǁBitComparatorǁcompare__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁBitComparatorǁcompare__mutmut_1': xǁBitComparatorǁcompare__mutmut_1, 
        'xǁBitComparatorǁcompare__mutmut_2': xǁBitComparatorǁcompare__mutmut_2, 
        'xǁBitComparatorǁcompare__mutmut_3': xǁBitComparatorǁcompare__mutmut_3, 
        'xǁBitComparatorǁcompare__mutmut_4': xǁBitComparatorǁcompare__mutmut_4, 
        'xǁBitComparatorǁcompare__mutmut_5': xǁBitComparatorǁcompare__mutmut_5, 
        'xǁBitComparatorǁcompare__mutmut_6': xǁBitComparatorǁcompare__mutmut_6, 
        'xǁBitComparatorǁcompare__mutmut_7': xǁBitComparatorǁcompare__mutmut_7, 
        'xǁBitComparatorǁcompare__mutmut_8': xǁBitComparatorǁcompare__mutmut_8, 
        'xǁBitComparatorǁcompare__mutmut_9': xǁBitComparatorǁcompare__mutmut_9, 
        'xǁBitComparatorǁcompare__mutmut_10': xǁBitComparatorǁcompare__mutmut_10, 
        'xǁBitComparatorǁcompare__mutmut_11': xǁBitComparatorǁcompare__mutmut_11, 
        'xǁBitComparatorǁcompare__mutmut_12': xǁBitComparatorǁcompare__mutmut_12, 
        'xǁBitComparatorǁcompare__mutmut_13': xǁBitComparatorǁcompare__mutmut_13, 
        'xǁBitComparatorǁcompare__mutmut_14': xǁBitComparatorǁcompare__mutmut_14, 
        'xǁBitComparatorǁcompare__mutmut_15': xǁBitComparatorǁcompare__mutmut_15, 
        'xǁBitComparatorǁcompare__mutmut_16': xǁBitComparatorǁcompare__mutmut_16, 
        'xǁBitComparatorǁcompare__mutmut_17': xǁBitComparatorǁcompare__mutmut_17, 
        'xǁBitComparatorǁcompare__mutmut_18': xǁBitComparatorǁcompare__mutmut_18, 
        'xǁBitComparatorǁcompare__mutmut_19': xǁBitComparatorǁcompare__mutmut_19, 
        'xǁBitComparatorǁcompare__mutmut_20': xǁBitComparatorǁcompare__mutmut_20, 
        'xǁBitComparatorǁcompare__mutmut_21': xǁBitComparatorǁcompare__mutmut_21, 
        'xǁBitComparatorǁcompare__mutmut_22': xǁBitComparatorǁcompare__mutmut_22, 
        'xǁBitComparatorǁcompare__mutmut_23': xǁBitComparatorǁcompare__mutmut_23, 
        'xǁBitComparatorǁcompare__mutmut_24': xǁBitComparatorǁcompare__mutmut_24, 
        'xǁBitComparatorǁcompare__mutmut_25': xǁBitComparatorǁcompare__mutmut_25, 
        'xǁBitComparatorǁcompare__mutmut_26': xǁBitComparatorǁcompare__mutmut_26, 
        'xǁBitComparatorǁcompare__mutmut_27': xǁBitComparatorǁcompare__mutmut_27, 
        'xǁBitComparatorǁcompare__mutmut_28': xǁBitComparatorǁcompare__mutmut_28, 
        'xǁBitComparatorǁcompare__mutmut_29': xǁBitComparatorǁcompare__mutmut_29, 
        'xǁBitComparatorǁcompare__mutmut_30': xǁBitComparatorǁcompare__mutmut_30, 
        'xǁBitComparatorǁcompare__mutmut_31': xǁBitComparatorǁcompare__mutmut_31, 
        'xǁBitComparatorǁcompare__mutmut_32': xǁBitComparatorǁcompare__mutmut_32, 
        'xǁBitComparatorǁcompare__mutmut_33': xǁBitComparatorǁcompare__mutmut_33, 
        'xǁBitComparatorǁcompare__mutmut_34': xǁBitComparatorǁcompare__mutmut_34, 
        'xǁBitComparatorǁcompare__mutmut_35': xǁBitComparatorǁcompare__mutmut_35, 
        'xǁBitComparatorǁcompare__mutmut_36': xǁBitComparatorǁcompare__mutmut_36, 
        'xǁBitComparatorǁcompare__mutmut_37': xǁBitComparatorǁcompare__mutmut_37, 
        'xǁBitComparatorǁcompare__mutmut_38': xǁBitComparatorǁcompare__mutmut_38, 
        'xǁBitComparatorǁcompare__mutmut_39': xǁBitComparatorǁcompare__mutmut_39, 
        'xǁBitComparatorǁcompare__mutmut_40': xǁBitComparatorǁcompare__mutmut_40, 
        'xǁBitComparatorǁcompare__mutmut_41': xǁBitComparatorǁcompare__mutmut_41, 
        'xǁBitComparatorǁcompare__mutmut_42': xǁBitComparatorǁcompare__mutmut_42, 
        'xǁBitComparatorǁcompare__mutmut_43': xǁBitComparatorǁcompare__mutmut_43, 
        'xǁBitComparatorǁcompare__mutmut_44': xǁBitComparatorǁcompare__mutmut_44, 
        'xǁBitComparatorǁcompare__mutmut_45': xǁBitComparatorǁcompare__mutmut_45, 
        'xǁBitComparatorǁcompare__mutmut_46': xǁBitComparatorǁcompare__mutmut_46, 
        'xǁBitComparatorǁcompare__mutmut_47': xǁBitComparatorǁcompare__mutmut_47, 
        'xǁBitComparatorǁcompare__mutmut_48': xǁBitComparatorǁcompare__mutmut_48, 
        'xǁBitComparatorǁcompare__mutmut_49': xǁBitComparatorǁcompare__mutmut_49, 
        'xǁBitComparatorǁcompare__mutmut_50': xǁBitComparatorǁcompare__mutmut_50, 
        'xǁBitComparatorǁcompare__mutmut_51': xǁBitComparatorǁcompare__mutmut_51, 
        'xǁBitComparatorǁcompare__mutmut_52': xǁBitComparatorǁcompare__mutmut_52, 
        'xǁBitComparatorǁcompare__mutmut_53': xǁBitComparatorǁcompare__mutmut_53, 
        'xǁBitComparatorǁcompare__mutmut_54': xǁBitComparatorǁcompare__mutmut_54, 
        'xǁBitComparatorǁcompare__mutmut_55': xǁBitComparatorǁcompare__mutmut_55, 
        'xǁBitComparatorǁcompare__mutmut_56': xǁBitComparatorǁcompare__mutmut_56, 
        'xǁBitComparatorǁcompare__mutmut_57': xǁBitComparatorǁcompare__mutmut_57, 
        'xǁBitComparatorǁcompare__mutmut_58': xǁBitComparatorǁcompare__mutmut_58, 
        'xǁBitComparatorǁcompare__mutmut_59': xǁBitComparatorǁcompare__mutmut_59, 
        'xǁBitComparatorǁcompare__mutmut_60': xǁBitComparatorǁcompare__mutmut_60, 
        'xǁBitComparatorǁcompare__mutmut_61': xǁBitComparatorǁcompare__mutmut_61, 
        'xǁBitComparatorǁcompare__mutmut_62': xǁBitComparatorǁcompare__mutmut_62, 
        'xǁBitComparatorǁcompare__mutmut_63': xǁBitComparatorǁcompare__mutmut_63, 
        'xǁBitComparatorǁcompare__mutmut_64': xǁBitComparatorǁcompare__mutmut_64, 
        'xǁBitComparatorǁcompare__mutmut_65': xǁBitComparatorǁcompare__mutmut_65, 
        'xǁBitComparatorǁcompare__mutmut_66': xǁBitComparatorǁcompare__mutmut_66, 
        'xǁBitComparatorǁcompare__mutmut_67': xǁBitComparatorǁcompare__mutmut_67, 
        'xǁBitComparatorǁcompare__mutmut_68': xǁBitComparatorǁcompare__mutmut_68, 
        'xǁBitComparatorǁcompare__mutmut_69': xǁBitComparatorǁcompare__mutmut_69, 
        'xǁBitComparatorǁcompare__mutmut_70': xǁBitComparatorǁcompare__mutmut_70, 
        'xǁBitComparatorǁcompare__mutmut_71': xǁBitComparatorǁcompare__mutmut_71, 
        'xǁBitComparatorǁcompare__mutmut_72': xǁBitComparatorǁcompare__mutmut_72, 
        'xǁBitComparatorǁcompare__mutmut_73': xǁBitComparatorǁcompare__mutmut_73, 
        'xǁBitComparatorǁcompare__mutmut_74': xǁBitComparatorǁcompare__mutmut_74, 
        'xǁBitComparatorǁcompare__mutmut_75': xǁBitComparatorǁcompare__mutmut_75, 
        'xǁBitComparatorǁcompare__mutmut_76': xǁBitComparatorǁcompare__mutmut_76, 
        'xǁBitComparatorǁcompare__mutmut_77': xǁBitComparatorǁcompare__mutmut_77, 
        'xǁBitComparatorǁcompare__mutmut_78': xǁBitComparatorǁcompare__mutmut_78, 
        'xǁBitComparatorǁcompare__mutmut_79': xǁBitComparatorǁcompare__mutmut_79, 
        'xǁBitComparatorǁcompare__mutmut_80': xǁBitComparatorǁcompare__mutmut_80, 
        'xǁBitComparatorǁcompare__mutmut_81': xǁBitComparatorǁcompare__mutmut_81, 
        'xǁBitComparatorǁcompare__mutmut_82': xǁBitComparatorǁcompare__mutmut_82, 
        'xǁBitComparatorǁcompare__mutmut_83': xǁBitComparatorǁcompare__mutmut_83, 
        'xǁBitComparatorǁcompare__mutmut_84': xǁBitComparatorǁcompare__mutmut_84, 
        'xǁBitComparatorǁcompare__mutmut_85': xǁBitComparatorǁcompare__mutmut_85, 
        'xǁBitComparatorǁcompare__mutmut_86': xǁBitComparatorǁcompare__mutmut_86, 
        'xǁBitComparatorǁcompare__mutmut_87': xǁBitComparatorǁcompare__mutmut_87, 
        'xǁBitComparatorǁcompare__mutmut_88': xǁBitComparatorǁcompare__mutmut_88, 
        'xǁBitComparatorǁcompare__mutmut_89': xǁBitComparatorǁcompare__mutmut_89, 
        'xǁBitComparatorǁcompare__mutmut_90': xǁBitComparatorǁcompare__mutmut_90, 
        'xǁBitComparatorǁcompare__mutmut_91': xǁBitComparatorǁcompare__mutmut_91
    }
    xǁBitComparatorǁcompare__mutmut_orig.__name__ = 'xǁBitComparatorǁcompare'
