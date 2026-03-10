# jarvis/verification/storage/record_serializer.py
# RecordSerializer -- serializes ExecutionRecord sets to JSON files.
# Authority: DVH Implementation Blueprint v1.0.0 Section 9.
#
# RSF-01: All float values serialized using float.hex() (lossless IEEE 754).
# RSF-02: +0.0, -0.0, +inf, -inf, NaN each serialize to distinct strings.
# RSF-04: File name format: {run_id}_{stage}_{timestamp}.json
# RSF-05: runs directory created if it does not exist.
#
# Canonical enum instances (GlobalRegimeState, CorrelationRegimeState) are
# serialized as their .value string. Deserialization restores enum instances.

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from jarvis.core.regime import GlobalRegimeState, CorrelationRegimeState
from jarvis.verification.data_models.execution_record import ExecutionRecord, ObservedOutput
from jarvis.verification.data_models.input_vector import InputVector
from jarvis.verification.harness_version import HARNESS_VERSION, STORAGE_FORMAT_VERSION
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


def _serialize_float(value: float) -> str:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__serialize_float__mutmut_orig, x__serialize_float__mutmut_mutants, args, kwargs, None)


def x__serialize_float__mutmut_orig(value: float) -> str:
    """
    RSF-01: Serialize float to lossless hexadecimal representation.
    RSF-02: Handles +0.0, -0.0, +inf, -inf, NaN distinctly.
    """
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return value.hex()


def x__serialize_float__mutmut_1(value: float) -> str:
    """
    RSF-01: Serialize float to lossless hexadecimal representation.
    RSF-02: Handles +0.0, -0.0, +inf, -inf, NaN distinctly.
    """
    if math.isnan(None):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return value.hex()


def x__serialize_float__mutmut_2(value: float) -> str:
    """
    RSF-01: Serialize float to lossless hexadecimal representation.
    RSF-02: Handles +0.0, -0.0, +inf, -inf, NaN distinctly.
    """
    if math.isnan(value):
        return "XXnanXX"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return value.hex()


def x__serialize_float__mutmut_3(value: float) -> str:
    """
    RSF-01: Serialize float to lossless hexadecimal representation.
    RSF-02: Handles +0.0, -0.0, +inf, -inf, NaN distinctly.
    """
    if math.isnan(value):
        return "NAN"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return value.hex()


def x__serialize_float__mutmut_4(value: float) -> str:
    """
    RSF-01: Serialize float to lossless hexadecimal representation.
    RSF-02: Handles +0.0, -0.0, +inf, -inf, NaN distinctly.
    """
    if math.isnan(value):
        return "nan"
    if math.isinf(None):
        return "inf" if value > 0 else "-inf"
    return value.hex()


def x__serialize_float__mutmut_5(value: float) -> str:
    """
    RSF-01: Serialize float to lossless hexadecimal representation.
    RSF-02: Handles +0.0, -0.0, +inf, -inf, NaN distinctly.
    """
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "XXinfXX" if value > 0 else "-inf"
    return value.hex()


def x__serialize_float__mutmut_6(value: float) -> str:
    """
    RSF-01: Serialize float to lossless hexadecimal representation.
    RSF-02: Handles +0.0, -0.0, +inf, -inf, NaN distinctly.
    """
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "INF" if value > 0 else "-inf"
    return value.hex()


def x__serialize_float__mutmut_7(value: float) -> str:
    """
    RSF-01: Serialize float to lossless hexadecimal representation.
    RSF-02: Handles +0.0, -0.0, +inf, -inf, NaN distinctly.
    """
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value >= 0 else "-inf"
    return value.hex()


def x__serialize_float__mutmut_8(value: float) -> str:
    """
    RSF-01: Serialize float to lossless hexadecimal representation.
    RSF-02: Handles +0.0, -0.0, +inf, -inf, NaN distinctly.
    """
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 1 else "-inf"
    return value.hex()


def x__serialize_float__mutmut_9(value: float) -> str:
    """
    RSF-01: Serialize float to lossless hexadecimal representation.
    RSF-02: Handles +0.0, -0.0, +inf, -inf, NaN distinctly.
    """
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "XX-infXX"
    return value.hex()


def x__serialize_float__mutmut_10(value: float) -> str:
    """
    RSF-01: Serialize float to lossless hexadecimal representation.
    RSF-02: Handles +0.0, -0.0, +inf, -inf, NaN distinctly.
    """
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-INF"
    return value.hex()

x__serialize_float__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__serialize_float__mutmut_1': x__serialize_float__mutmut_1, 
    'x__serialize_float__mutmut_2': x__serialize_float__mutmut_2, 
    'x__serialize_float__mutmut_3': x__serialize_float__mutmut_3, 
    'x__serialize_float__mutmut_4': x__serialize_float__mutmut_4, 
    'x__serialize_float__mutmut_5': x__serialize_float__mutmut_5, 
    'x__serialize_float__mutmut_6': x__serialize_float__mutmut_6, 
    'x__serialize_float__mutmut_7': x__serialize_float__mutmut_7, 
    'x__serialize_float__mutmut_8': x__serialize_float__mutmut_8, 
    'x__serialize_float__mutmut_9': x__serialize_float__mutmut_9, 
    'x__serialize_float__mutmut_10': x__serialize_float__mutmut_10
}
x__serialize_float__mutmut_orig.__name__ = 'x__serialize_float'


def _serialize_global_regime(r: Optional[GlobalRegimeState]) -> Optional[str]:
    args = [r]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__serialize_global_regime__mutmut_orig, x__serialize_global_regime__mutmut_mutants, args, kwargs, None)


def x__serialize_global_regime__mutmut_orig(r: Optional[GlobalRegimeState]) -> Optional[str]:
    """Serialize GlobalRegimeState enum to its .value string, or None."""
    if r is None:
        return None
    return r.value


def x__serialize_global_regime__mutmut_1(r: Optional[GlobalRegimeState]) -> Optional[str]:
    """Serialize GlobalRegimeState enum to its .value string, or None."""
    if r is not None:
        return None
    return r.value

x__serialize_global_regime__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__serialize_global_regime__mutmut_1': x__serialize_global_regime__mutmut_1
}
x__serialize_global_regime__mutmut_orig.__name__ = 'x__serialize_global_regime'


def _serialize_correlation_regime(r: Optional[CorrelationRegimeState]) -> Optional[str]:
    args = [r]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__serialize_correlation_regime__mutmut_orig, x__serialize_correlation_regime__mutmut_mutants, args, kwargs, None)


def x__serialize_correlation_regime__mutmut_orig(r: Optional[CorrelationRegimeState]) -> Optional[str]:
    """Serialize CorrelationRegimeState enum to its .value string, or None."""
    if r is None:
        return None
    return r.value


def x__serialize_correlation_regime__mutmut_1(r: Optional[CorrelationRegimeState]) -> Optional[str]:
    """Serialize CorrelationRegimeState enum to its .value string, or None."""
    if r is not None:
        return None
    return r.value

x__serialize_correlation_regime__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__serialize_correlation_regime__mutmut_1': x__serialize_correlation_regime__mutmut_1
}
x__serialize_correlation_regime__mutmut_orig.__name__ = 'x__serialize_correlation_regime'


def _serialize_input_vector(iv: InputVector) -> dict:
    args = [iv]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__serialize_input_vector__mutmut_orig, x__serialize_input_vector__mutmut_mutants, args, kwargs, None)


def x__serialize_input_vector__mutmut_orig(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_1(iv: InputVector) -> dict:
    return {
        "XXvector_idXX":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_2(iv: InputVector) -> dict:
    return {
        "VECTOR_ID":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_3(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "XXgroup_idXX":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_4(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "GROUP_ID":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_5(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "XXreturns_historyXX":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_6(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "RETURNS_HISTORY":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_7(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(None) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_8(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "XXcurrent_regime_strXX": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_9(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "CURRENT_REGIME_STR": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_10(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "XXmeta_uncertaintyXX":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_11(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "META_UNCERTAINTY":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_12(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(None),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_13(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "XXmacro_regimeXX":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_14(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "MACRO_REGIME":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_15(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(None),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_16(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "XXcorrelation_regimeXX": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_17(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "CORRELATION_REGIME": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_18(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(None),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_19(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "XXrealized_volXX":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_20(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "REALIZED_VOL":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_21(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(None) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_22(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_23(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "XXtarget_volXX":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_24(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "TARGET_VOL":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_25(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(None) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_26(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_27(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "XXregime_posteriorXX":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_28(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "REGIME_POSTERIOR":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_29(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(None) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_30(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is None else None,
        "expect_exception":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_31(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "XXexpect_exceptionXX":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_32(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "EXPECT_EXCEPTION":   iv.expect_exception,
        "description":        iv.description,
    }


def x__serialize_input_vector__mutmut_33(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "XXdescriptionXX":        iv.description,
    }


def x__serialize_input_vector__mutmut_34(iv: InputVector) -> dict:
    return {
        "vector_id":          iv.vector_id,
        "group_id":           iv.group_id,
        "returns_history":    [_serialize_float(r) for r in iv.returns_history],
        "current_regime_str": iv.current_regime_str,
        "meta_uncertainty":   _serialize_float(iv.meta_uncertainty),
        "macro_regime":       _serialize_global_regime(iv.macro_regime),
        "correlation_regime": _serialize_correlation_regime(iv.correlation_regime),
        "realized_vol":       _serialize_float(iv.realized_vol) if iv.realized_vol is not None else None,
        "target_vol":         _serialize_float(iv.target_vol) if iv.target_vol is not None else None,
        "regime_posterior":   _serialize_float(iv.regime_posterior) if iv.regime_posterior is not None else None,
        "expect_exception":   iv.expect_exception,
        "DESCRIPTION":        iv.description,
    }

x__serialize_input_vector__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__serialize_input_vector__mutmut_1': x__serialize_input_vector__mutmut_1, 
    'x__serialize_input_vector__mutmut_2': x__serialize_input_vector__mutmut_2, 
    'x__serialize_input_vector__mutmut_3': x__serialize_input_vector__mutmut_3, 
    'x__serialize_input_vector__mutmut_4': x__serialize_input_vector__mutmut_4, 
    'x__serialize_input_vector__mutmut_5': x__serialize_input_vector__mutmut_5, 
    'x__serialize_input_vector__mutmut_6': x__serialize_input_vector__mutmut_6, 
    'x__serialize_input_vector__mutmut_7': x__serialize_input_vector__mutmut_7, 
    'x__serialize_input_vector__mutmut_8': x__serialize_input_vector__mutmut_8, 
    'x__serialize_input_vector__mutmut_9': x__serialize_input_vector__mutmut_9, 
    'x__serialize_input_vector__mutmut_10': x__serialize_input_vector__mutmut_10, 
    'x__serialize_input_vector__mutmut_11': x__serialize_input_vector__mutmut_11, 
    'x__serialize_input_vector__mutmut_12': x__serialize_input_vector__mutmut_12, 
    'x__serialize_input_vector__mutmut_13': x__serialize_input_vector__mutmut_13, 
    'x__serialize_input_vector__mutmut_14': x__serialize_input_vector__mutmut_14, 
    'x__serialize_input_vector__mutmut_15': x__serialize_input_vector__mutmut_15, 
    'x__serialize_input_vector__mutmut_16': x__serialize_input_vector__mutmut_16, 
    'x__serialize_input_vector__mutmut_17': x__serialize_input_vector__mutmut_17, 
    'x__serialize_input_vector__mutmut_18': x__serialize_input_vector__mutmut_18, 
    'x__serialize_input_vector__mutmut_19': x__serialize_input_vector__mutmut_19, 
    'x__serialize_input_vector__mutmut_20': x__serialize_input_vector__mutmut_20, 
    'x__serialize_input_vector__mutmut_21': x__serialize_input_vector__mutmut_21, 
    'x__serialize_input_vector__mutmut_22': x__serialize_input_vector__mutmut_22, 
    'x__serialize_input_vector__mutmut_23': x__serialize_input_vector__mutmut_23, 
    'x__serialize_input_vector__mutmut_24': x__serialize_input_vector__mutmut_24, 
    'x__serialize_input_vector__mutmut_25': x__serialize_input_vector__mutmut_25, 
    'x__serialize_input_vector__mutmut_26': x__serialize_input_vector__mutmut_26, 
    'x__serialize_input_vector__mutmut_27': x__serialize_input_vector__mutmut_27, 
    'x__serialize_input_vector__mutmut_28': x__serialize_input_vector__mutmut_28, 
    'x__serialize_input_vector__mutmut_29': x__serialize_input_vector__mutmut_29, 
    'x__serialize_input_vector__mutmut_30': x__serialize_input_vector__mutmut_30, 
    'x__serialize_input_vector__mutmut_31': x__serialize_input_vector__mutmut_31, 
    'x__serialize_input_vector__mutmut_32': x__serialize_input_vector__mutmut_32, 
    'x__serialize_input_vector__mutmut_33': x__serialize_input_vector__mutmut_33, 
    'x__serialize_input_vector__mutmut_34': x__serialize_input_vector__mutmut_34
}
x__serialize_input_vector__mutmut_orig.__name__ = 'x__serialize_input_vector'


def _serialize_observed_output(out: ObservedOutput) -> dict:
    args = [out]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__serialize_observed_output__mutmut_orig, x__serialize_observed_output__mutmut_mutants, args, kwargs, None)


def x__serialize_observed_output__mutmut_orig(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_1(out: ObservedOutput) -> dict:
    return {
        "XXexpected_drawdownXX":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_2(out: ObservedOutput) -> dict:
    return {
        "EXPECTED_DRAWDOWN":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_3(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(None),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_4(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "XXexpected_drawdown_p95XX":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_5(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "EXPECTED_DRAWDOWN_P95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_6(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(None),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_7(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "XXvolatility_forecastXX":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_8(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "VOLATILITY_FORECAST":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_9(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(None),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_10(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "XXrisk_compression_activeXX": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_11(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "RISK_COMPRESSION_ACTIVE": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_12(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "XXposition_size_factorXX":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_13(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "POSITION_SIZE_FACTOR":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_14(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(None),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_15(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "XXexposure_weightXX":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_16(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "EXPOSURE_WEIGHT":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_17(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(None),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_18(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "XXrisk_regimeXX":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_19(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "RISK_REGIME":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_20(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "XXexception_raisedXX":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_21(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "EXCEPTION_RAISED":        out.exception_raised,
        "exception_type":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_22(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "XXexception_typeXX":          out.exception_type,
    }


def x__serialize_observed_output__mutmut_23(out: ObservedOutput) -> dict:
    return {
        "expected_drawdown":       _serialize_float(out.expected_drawdown),
        "expected_drawdown_p95":   _serialize_float(out.expected_drawdown_p95),
        "volatility_forecast":     _serialize_float(out.volatility_forecast),
        "risk_compression_active": out.risk_compression_active,
        "position_size_factor":    _serialize_float(out.position_size_factor),
        "exposure_weight":         _serialize_float(out.exposure_weight),
        "risk_regime":             out.risk_regime,
        "exception_raised":        out.exception_raised,
        "EXCEPTION_TYPE":          out.exception_type,
    }

x__serialize_observed_output__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__serialize_observed_output__mutmut_1': x__serialize_observed_output__mutmut_1, 
    'x__serialize_observed_output__mutmut_2': x__serialize_observed_output__mutmut_2, 
    'x__serialize_observed_output__mutmut_3': x__serialize_observed_output__mutmut_3, 
    'x__serialize_observed_output__mutmut_4': x__serialize_observed_output__mutmut_4, 
    'x__serialize_observed_output__mutmut_5': x__serialize_observed_output__mutmut_5, 
    'x__serialize_observed_output__mutmut_6': x__serialize_observed_output__mutmut_6, 
    'x__serialize_observed_output__mutmut_7': x__serialize_observed_output__mutmut_7, 
    'x__serialize_observed_output__mutmut_8': x__serialize_observed_output__mutmut_8, 
    'x__serialize_observed_output__mutmut_9': x__serialize_observed_output__mutmut_9, 
    'x__serialize_observed_output__mutmut_10': x__serialize_observed_output__mutmut_10, 
    'x__serialize_observed_output__mutmut_11': x__serialize_observed_output__mutmut_11, 
    'x__serialize_observed_output__mutmut_12': x__serialize_observed_output__mutmut_12, 
    'x__serialize_observed_output__mutmut_13': x__serialize_observed_output__mutmut_13, 
    'x__serialize_observed_output__mutmut_14': x__serialize_observed_output__mutmut_14, 
    'x__serialize_observed_output__mutmut_15': x__serialize_observed_output__mutmut_15, 
    'x__serialize_observed_output__mutmut_16': x__serialize_observed_output__mutmut_16, 
    'x__serialize_observed_output__mutmut_17': x__serialize_observed_output__mutmut_17, 
    'x__serialize_observed_output__mutmut_18': x__serialize_observed_output__mutmut_18, 
    'x__serialize_observed_output__mutmut_19': x__serialize_observed_output__mutmut_19, 
    'x__serialize_observed_output__mutmut_20': x__serialize_observed_output__mutmut_20, 
    'x__serialize_observed_output__mutmut_21': x__serialize_observed_output__mutmut_21, 
    'x__serialize_observed_output__mutmut_22': x__serialize_observed_output__mutmut_22, 
    'x__serialize_observed_output__mutmut_23': x__serialize_observed_output__mutmut_23
}
x__serialize_observed_output__mutmut_orig.__name__ = 'x__serialize_observed_output'


def _serialize_record(rec: ExecutionRecord) -> dict:
    args = [rec]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__serialize_record__mutmut_orig, x__serialize_record__mutmut_mutants, args, kwargs, None)


def x__serialize_record__mutmut_orig(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_1(rec: ExecutionRecord) -> dict:
    return {
        "XXvector_idXX":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_2(rec: ExecutionRecord) -> dict:
    return {
        "VECTOR_ID":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_3(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "XXgroup_idXX":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_4(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "GROUP_ID":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_5(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "XXinput_vectorXX":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_6(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "INPUT_VECTOR":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_7(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(None),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_8(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "XXobserved_outputXX": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_9(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "OBSERVED_OUTPUT": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_10(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(None),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_11(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "XXstageXX":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_12(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "STAGE":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_13(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "XXmanifest_hashXX":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_14(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "MANIFEST_HASH":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_15(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "XXtimestamp_isoXX":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_16(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "TIMESTAMP_ISO":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_17(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "XXexecution_idXX":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_18(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "EXECUTION_ID":    rec.execution_id,
        "harness_version": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_19(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "XXharness_versionXX": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_20(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "HARNESS_VERSION": rec.harness_version,
        "module_version":  rec.module_version,
    }


def x__serialize_record__mutmut_21(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "XXmodule_versionXX":  rec.module_version,
    }


def x__serialize_record__mutmut_22(rec: ExecutionRecord) -> dict:
    return {
        "vector_id":       rec.vector_id,
        "group_id":        rec.group_id,
        "input_vector":    _serialize_input_vector(rec.input_vector),
        "observed_output": _serialize_observed_output(rec.observed_output),
        "stage":           rec.stage,
        "manifest_hash":   rec.manifest_hash,
        "timestamp_iso":   rec.timestamp_iso,
        "execution_id":    rec.execution_id,
        "harness_version": rec.harness_version,
        "MODULE_VERSION":  rec.module_version,
    }

x__serialize_record__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__serialize_record__mutmut_1': x__serialize_record__mutmut_1, 
    'x__serialize_record__mutmut_2': x__serialize_record__mutmut_2, 
    'x__serialize_record__mutmut_3': x__serialize_record__mutmut_3, 
    'x__serialize_record__mutmut_4': x__serialize_record__mutmut_4, 
    'x__serialize_record__mutmut_5': x__serialize_record__mutmut_5, 
    'x__serialize_record__mutmut_6': x__serialize_record__mutmut_6, 
    'x__serialize_record__mutmut_7': x__serialize_record__mutmut_7, 
    'x__serialize_record__mutmut_8': x__serialize_record__mutmut_8, 
    'x__serialize_record__mutmut_9': x__serialize_record__mutmut_9, 
    'x__serialize_record__mutmut_10': x__serialize_record__mutmut_10, 
    'x__serialize_record__mutmut_11': x__serialize_record__mutmut_11, 
    'x__serialize_record__mutmut_12': x__serialize_record__mutmut_12, 
    'x__serialize_record__mutmut_13': x__serialize_record__mutmut_13, 
    'x__serialize_record__mutmut_14': x__serialize_record__mutmut_14, 
    'x__serialize_record__mutmut_15': x__serialize_record__mutmut_15, 
    'x__serialize_record__mutmut_16': x__serialize_record__mutmut_16, 
    'x__serialize_record__mutmut_17': x__serialize_record__mutmut_17, 
    'x__serialize_record__mutmut_18': x__serialize_record__mutmut_18, 
    'x__serialize_record__mutmut_19': x__serialize_record__mutmut_19, 
    'x__serialize_record__mutmut_20': x__serialize_record__mutmut_20, 
    'x__serialize_record__mutmut_21': x__serialize_record__mutmut_21, 
    'x__serialize_record__mutmut_22': x__serialize_record__mutmut_22
}
x__serialize_record__mutmut_orig.__name__ = 'x__serialize_record'


class RecordSerializer:
    """
    Serializes a list of ExecutionRecords to a JSON file per RSF-04/RSF-05.
    Float values serialized using float.hex() (RSF-01).
    Enum values serialized as their .value strings.
    """

    def serialize(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        args = [records, runs_dir, run_id, stage]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRecordSerializerǁserialize__mutmut_orig'), object.__getattribute__(self, 'xǁRecordSerializerǁserialize__mutmut_mutants'), args, kwargs, self)

    def xǁRecordSerializerǁserialize__mutmut_orig(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_1(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=None, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_2(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=None)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_3(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_4(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, )

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_5(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=False, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_6(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=False)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_7(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = None
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_8(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime(None)
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_9(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(None).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_10(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("XX%Y%m%dT%H%M%SZXX")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_11(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%y%m%dt%h%m%sz")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_12(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%M%DT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_13(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = None
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_14(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = None

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_15(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir * filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_16(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = None

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_17(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "XXformat_versionXX":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_18(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "FORMAT_VERSION":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_19(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "XXharness_versionXX": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_20(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "HARNESS_VERSION": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_21(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "XXmodule_versionXX":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_22(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "MODULE_VERSION":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_23(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[1].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_24(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "XXXX",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_25(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "XXrun_idXX":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_26(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "RUN_ID":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_27(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "XXstageXX":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_28(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "STAGE":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_29(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "XXvector_countXX":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_30(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "VECTOR_COUNT":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_31(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "XXrecordsXX":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_32(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "RECORDS":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_33(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(None) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_34(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(None, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_35(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, None, encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_36(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding=None) as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_37(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_38(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_39(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", ) as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_40(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "XXwXX", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_41(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "W", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_42(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="XXutf-8XX") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_43(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="UTF-8") as f:
            json.dump(payload, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_44(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(None, f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_45(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, None, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_46(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=None)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_47(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(f, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_48(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, indent=2)

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_49(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, )

        return filepath

    def xǁRecordSerializerǁserialize__mutmut_50(
        self,
        records:  List[ExecutionRecord],
        runs_dir: Path,
        run_id:   str,
        stage:    str,
    ) -> Path:
        """
        Write records to a JSON file in runs_dir.
        Returns the path of the written file.
        """
        runs_dir.mkdir(parents=True, exist_ok=True)

        ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{run_id}_{stage}_{ts}.json"
        filepath = runs_dir / filename

        payload = {
            "format_version":  STORAGE_FORMAT_VERSION,
            "harness_version": HARNESS_VERSION,
            "module_version":  records[0].module_version if records else "",
            "run_id":          run_id,
            "stage":           stage,
            "vector_count":    len(records),
            "records":         [_serialize_record(r) for r in records],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=3)

        return filepath
    
    xǁRecordSerializerǁserialize__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRecordSerializerǁserialize__mutmut_1': xǁRecordSerializerǁserialize__mutmut_1, 
        'xǁRecordSerializerǁserialize__mutmut_2': xǁRecordSerializerǁserialize__mutmut_2, 
        'xǁRecordSerializerǁserialize__mutmut_3': xǁRecordSerializerǁserialize__mutmut_3, 
        'xǁRecordSerializerǁserialize__mutmut_4': xǁRecordSerializerǁserialize__mutmut_4, 
        'xǁRecordSerializerǁserialize__mutmut_5': xǁRecordSerializerǁserialize__mutmut_5, 
        'xǁRecordSerializerǁserialize__mutmut_6': xǁRecordSerializerǁserialize__mutmut_6, 
        'xǁRecordSerializerǁserialize__mutmut_7': xǁRecordSerializerǁserialize__mutmut_7, 
        'xǁRecordSerializerǁserialize__mutmut_8': xǁRecordSerializerǁserialize__mutmut_8, 
        'xǁRecordSerializerǁserialize__mutmut_9': xǁRecordSerializerǁserialize__mutmut_9, 
        'xǁRecordSerializerǁserialize__mutmut_10': xǁRecordSerializerǁserialize__mutmut_10, 
        'xǁRecordSerializerǁserialize__mutmut_11': xǁRecordSerializerǁserialize__mutmut_11, 
        'xǁRecordSerializerǁserialize__mutmut_12': xǁRecordSerializerǁserialize__mutmut_12, 
        'xǁRecordSerializerǁserialize__mutmut_13': xǁRecordSerializerǁserialize__mutmut_13, 
        'xǁRecordSerializerǁserialize__mutmut_14': xǁRecordSerializerǁserialize__mutmut_14, 
        'xǁRecordSerializerǁserialize__mutmut_15': xǁRecordSerializerǁserialize__mutmut_15, 
        'xǁRecordSerializerǁserialize__mutmut_16': xǁRecordSerializerǁserialize__mutmut_16, 
        'xǁRecordSerializerǁserialize__mutmut_17': xǁRecordSerializerǁserialize__mutmut_17, 
        'xǁRecordSerializerǁserialize__mutmut_18': xǁRecordSerializerǁserialize__mutmut_18, 
        'xǁRecordSerializerǁserialize__mutmut_19': xǁRecordSerializerǁserialize__mutmut_19, 
        'xǁRecordSerializerǁserialize__mutmut_20': xǁRecordSerializerǁserialize__mutmut_20, 
        'xǁRecordSerializerǁserialize__mutmut_21': xǁRecordSerializerǁserialize__mutmut_21, 
        'xǁRecordSerializerǁserialize__mutmut_22': xǁRecordSerializerǁserialize__mutmut_22, 
        'xǁRecordSerializerǁserialize__mutmut_23': xǁRecordSerializerǁserialize__mutmut_23, 
        'xǁRecordSerializerǁserialize__mutmut_24': xǁRecordSerializerǁserialize__mutmut_24, 
        'xǁRecordSerializerǁserialize__mutmut_25': xǁRecordSerializerǁserialize__mutmut_25, 
        'xǁRecordSerializerǁserialize__mutmut_26': xǁRecordSerializerǁserialize__mutmut_26, 
        'xǁRecordSerializerǁserialize__mutmut_27': xǁRecordSerializerǁserialize__mutmut_27, 
        'xǁRecordSerializerǁserialize__mutmut_28': xǁRecordSerializerǁserialize__mutmut_28, 
        'xǁRecordSerializerǁserialize__mutmut_29': xǁRecordSerializerǁserialize__mutmut_29, 
        'xǁRecordSerializerǁserialize__mutmut_30': xǁRecordSerializerǁserialize__mutmut_30, 
        'xǁRecordSerializerǁserialize__mutmut_31': xǁRecordSerializerǁserialize__mutmut_31, 
        'xǁRecordSerializerǁserialize__mutmut_32': xǁRecordSerializerǁserialize__mutmut_32, 
        'xǁRecordSerializerǁserialize__mutmut_33': xǁRecordSerializerǁserialize__mutmut_33, 
        'xǁRecordSerializerǁserialize__mutmut_34': xǁRecordSerializerǁserialize__mutmut_34, 
        'xǁRecordSerializerǁserialize__mutmut_35': xǁRecordSerializerǁserialize__mutmut_35, 
        'xǁRecordSerializerǁserialize__mutmut_36': xǁRecordSerializerǁserialize__mutmut_36, 
        'xǁRecordSerializerǁserialize__mutmut_37': xǁRecordSerializerǁserialize__mutmut_37, 
        'xǁRecordSerializerǁserialize__mutmut_38': xǁRecordSerializerǁserialize__mutmut_38, 
        'xǁRecordSerializerǁserialize__mutmut_39': xǁRecordSerializerǁserialize__mutmut_39, 
        'xǁRecordSerializerǁserialize__mutmut_40': xǁRecordSerializerǁserialize__mutmut_40, 
        'xǁRecordSerializerǁserialize__mutmut_41': xǁRecordSerializerǁserialize__mutmut_41, 
        'xǁRecordSerializerǁserialize__mutmut_42': xǁRecordSerializerǁserialize__mutmut_42, 
        'xǁRecordSerializerǁserialize__mutmut_43': xǁRecordSerializerǁserialize__mutmut_43, 
        'xǁRecordSerializerǁserialize__mutmut_44': xǁRecordSerializerǁserialize__mutmut_44, 
        'xǁRecordSerializerǁserialize__mutmut_45': xǁRecordSerializerǁserialize__mutmut_45, 
        'xǁRecordSerializerǁserialize__mutmut_46': xǁRecordSerializerǁserialize__mutmut_46, 
        'xǁRecordSerializerǁserialize__mutmut_47': xǁRecordSerializerǁserialize__mutmut_47, 
        'xǁRecordSerializerǁserialize__mutmut_48': xǁRecordSerializerǁserialize__mutmut_48, 
        'xǁRecordSerializerǁserialize__mutmut_49': xǁRecordSerializerǁserialize__mutmut_49, 
        'xǁRecordSerializerǁserialize__mutmut_50': xǁRecordSerializerǁserialize__mutmut_50
    }
    xǁRecordSerializerǁserialize__mutmut_orig.__name__ = 'xǁRecordSerializerǁserialize'
