# jarvis/verification/storage/record_loader.py
# RecordLoader -- loads and validates serialized ExecutionRecord sets.
# Authority: DVH Implementation Blueprint v1.0.0 Sections 9.4 and RSF-06/RSF-07.
#
# RSF-06: Validates format_version, harness_version, module_version, vector_count.
# RSF-07: Detects NaN in any float field during deserialization -- hard failure.
# Used for cross-session replay (DIM-05/DIM-06).
#
# Enum fields (macro_regime, correlation_regime) are deserialized from their
# .value strings back to canonical enum instances from jarvis.core.regime.

import json
import math
from pathlib import Path
from typing import List, Optional

from jarvis.core.regime import GlobalRegimeState, CorrelationRegimeState
from jarvis.verification.data_models.input_vector import InputVector
from jarvis.verification.data_models.execution_record import ExecutionRecord, ObservedOutput
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


def _deserialize_float(value: str) -> float:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__deserialize_float__mutmut_orig, x__deserialize_float__mutmut_mutants, args, kwargs, None)


def x__deserialize_float__mutmut_orig(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value == "inf":
        return float("inf")
    if value == "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_1(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value != "nan":
        return float("nan")
    if value == "inf":
        return float("inf")
    if value == "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_2(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "XXnanXX":
        return float("nan")
    if value == "inf":
        return float("inf")
    if value == "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_3(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "NAN":
        return float("nan")
    if value == "inf":
        return float("inf")
    if value == "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_4(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float(None)
    if value == "inf":
        return float("inf")
    if value == "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_5(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("XXnanXX")
    if value == "inf":
        return float("inf")
    if value == "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_6(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("NAN")
    if value == "inf":
        return float("inf")
    if value == "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_7(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value != "inf":
        return float("inf")
    if value == "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_8(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value == "XXinfXX":
        return float("inf")
    if value == "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_9(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value == "INF":
        return float("inf")
    if value == "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_10(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value == "inf":
        return float(None)
    if value == "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_11(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value == "inf":
        return float("XXinfXX")
    if value == "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_12(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value == "inf":
        return float("INF")
    if value == "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_13(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value == "inf":
        return float("inf")
    if value != "-inf":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_14(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value == "inf":
        return float("inf")
    if value == "XX-infXX":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_15(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value == "inf":
        return float("inf")
    if value == "-INF":
        return float("-inf")
    return float.fromhex(value)


def x__deserialize_float__mutmut_16(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value == "inf":
        return float("inf")
    if value == "-inf":
        return float(None)
    return float.fromhex(value)


def x__deserialize_float__mutmut_17(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value == "inf":
        return float("inf")
    if value == "-inf":
        return float("XX-infXX")
    return float.fromhex(value)


def x__deserialize_float__mutmut_18(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value == "inf":
        return float("inf")
    if value == "-inf":
        return float("-INF")
    return float.fromhex(value)


def x__deserialize_float__mutmut_19(value: str) -> float:
    """
    RSF-01: Deserialize lossless hex float string to float.
    RSF-02: Handles nan, inf, -inf distinctly.
    """
    if value == "nan":
        return float("nan")
    if value == "inf":
        return float("inf")
    if value == "-inf":
        return float("-inf")
    return float.fromhex(None)

x__deserialize_float__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__deserialize_float__mutmut_1': x__deserialize_float__mutmut_1, 
    'x__deserialize_float__mutmut_2': x__deserialize_float__mutmut_2, 
    'x__deserialize_float__mutmut_3': x__deserialize_float__mutmut_3, 
    'x__deserialize_float__mutmut_4': x__deserialize_float__mutmut_4, 
    'x__deserialize_float__mutmut_5': x__deserialize_float__mutmut_5, 
    'x__deserialize_float__mutmut_6': x__deserialize_float__mutmut_6, 
    'x__deserialize_float__mutmut_7': x__deserialize_float__mutmut_7, 
    'x__deserialize_float__mutmut_8': x__deserialize_float__mutmut_8, 
    'x__deserialize_float__mutmut_9': x__deserialize_float__mutmut_9, 
    'x__deserialize_float__mutmut_10': x__deserialize_float__mutmut_10, 
    'x__deserialize_float__mutmut_11': x__deserialize_float__mutmut_11, 
    'x__deserialize_float__mutmut_12': x__deserialize_float__mutmut_12, 
    'x__deserialize_float__mutmut_13': x__deserialize_float__mutmut_13, 
    'x__deserialize_float__mutmut_14': x__deserialize_float__mutmut_14, 
    'x__deserialize_float__mutmut_15': x__deserialize_float__mutmut_15, 
    'x__deserialize_float__mutmut_16': x__deserialize_float__mutmut_16, 
    'x__deserialize_float__mutmut_17': x__deserialize_float__mutmut_17, 
    'x__deserialize_float__mutmut_18': x__deserialize_float__mutmut_18, 
    'x__deserialize_float__mutmut_19': x__deserialize_float__mutmut_19
}
x__deserialize_float__mutmut_orig.__name__ = 'x__deserialize_float'


def _deserialize_global_regime(value: Optional[str]) -> Optional[GlobalRegimeState]:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__deserialize_global_regime__mutmut_orig, x__deserialize_global_regime__mutmut_mutants, args, kwargs, None)


def x__deserialize_global_regime__mutmut_orig(value: Optional[str]) -> Optional[GlobalRegimeState]:
    """
    Deserialize a GlobalRegimeState .value string back to the canonical enum instance.
    Returns None if value is None.
    Raises ValueError on unrecognized string (hard failure path).
    """
    if value is None:
        return None
    try:
        return GlobalRegimeState(value)
    except ValueError:
        raise RuntimeError(
            f"DATA_CORRUPTION: Unrecognized GlobalRegimeState value string "
            f"'{value}' in serialized record. Cannot restore canonical enum."
        )


def x__deserialize_global_regime__mutmut_1(value: Optional[str]) -> Optional[GlobalRegimeState]:
    """
    Deserialize a GlobalRegimeState .value string back to the canonical enum instance.
    Returns None if value is None.
    Raises ValueError on unrecognized string (hard failure path).
    """
    if value is not None:
        return None
    try:
        return GlobalRegimeState(value)
    except ValueError:
        raise RuntimeError(
            f"DATA_CORRUPTION: Unrecognized GlobalRegimeState value string "
            f"'{value}' in serialized record. Cannot restore canonical enum."
        )


def x__deserialize_global_regime__mutmut_2(value: Optional[str]) -> Optional[GlobalRegimeState]:
    """
    Deserialize a GlobalRegimeState .value string back to the canonical enum instance.
    Returns None if value is None.
    Raises ValueError on unrecognized string (hard failure path).
    """
    if value is None:
        return None
    try:
        return GlobalRegimeState(None)
    except ValueError:
        raise RuntimeError(
            f"DATA_CORRUPTION: Unrecognized GlobalRegimeState value string "
            f"'{value}' in serialized record. Cannot restore canonical enum."
        )


def x__deserialize_global_regime__mutmut_3(value: Optional[str]) -> Optional[GlobalRegimeState]:
    """
    Deserialize a GlobalRegimeState .value string back to the canonical enum instance.
    Returns None if value is None.
    Raises ValueError on unrecognized string (hard failure path).
    """
    if value is None:
        return None
    try:
        return GlobalRegimeState(value)
    except ValueError:
        raise RuntimeError(
            None
        )

x__deserialize_global_regime__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__deserialize_global_regime__mutmut_1': x__deserialize_global_regime__mutmut_1, 
    'x__deserialize_global_regime__mutmut_2': x__deserialize_global_regime__mutmut_2, 
    'x__deserialize_global_regime__mutmut_3': x__deserialize_global_regime__mutmut_3
}
x__deserialize_global_regime__mutmut_orig.__name__ = 'x__deserialize_global_regime'


def _deserialize_correlation_regime(value: Optional[str]) -> Optional[CorrelationRegimeState]:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__deserialize_correlation_regime__mutmut_orig, x__deserialize_correlation_regime__mutmut_mutants, args, kwargs, None)


def x__deserialize_correlation_regime__mutmut_orig(value: Optional[str]) -> Optional[CorrelationRegimeState]:
    """
    Deserialize a CorrelationRegimeState .value string back to the canonical enum instance.
    Returns None if value is None.
    Raises RuntimeError on unrecognized string (hard failure path).
    """
    if value is None:
        return None
    try:
        return CorrelationRegimeState(value)
    except ValueError:
        raise RuntimeError(
            f"DATA_CORRUPTION: Unrecognized CorrelationRegimeState value string "
            f"'{value}' in serialized record. Cannot restore canonical enum."
        )


def x__deserialize_correlation_regime__mutmut_1(value: Optional[str]) -> Optional[CorrelationRegimeState]:
    """
    Deserialize a CorrelationRegimeState .value string back to the canonical enum instance.
    Returns None if value is None.
    Raises RuntimeError on unrecognized string (hard failure path).
    """
    if value is not None:
        return None
    try:
        return CorrelationRegimeState(value)
    except ValueError:
        raise RuntimeError(
            f"DATA_CORRUPTION: Unrecognized CorrelationRegimeState value string "
            f"'{value}' in serialized record. Cannot restore canonical enum."
        )


def x__deserialize_correlation_regime__mutmut_2(value: Optional[str]) -> Optional[CorrelationRegimeState]:
    """
    Deserialize a CorrelationRegimeState .value string back to the canonical enum instance.
    Returns None if value is None.
    Raises RuntimeError on unrecognized string (hard failure path).
    """
    if value is None:
        return None
    try:
        return CorrelationRegimeState(None)
    except ValueError:
        raise RuntimeError(
            f"DATA_CORRUPTION: Unrecognized CorrelationRegimeState value string "
            f"'{value}' in serialized record. Cannot restore canonical enum."
        )


def x__deserialize_correlation_regime__mutmut_3(value: Optional[str]) -> Optional[CorrelationRegimeState]:
    """
    Deserialize a CorrelationRegimeState .value string back to the canonical enum instance.
    Returns None if value is None.
    Raises RuntimeError on unrecognized string (hard failure path).
    """
    if value is None:
        return None
    try:
        return CorrelationRegimeState(value)
    except ValueError:
        raise RuntimeError(
            None
        )

x__deserialize_correlation_regime__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__deserialize_correlation_regime__mutmut_1': x__deserialize_correlation_regime__mutmut_1, 
    'x__deserialize_correlation_regime__mutmut_2': x__deserialize_correlation_regime__mutmut_2, 
    'x__deserialize_correlation_regime__mutmut_3': x__deserialize_correlation_regime__mutmut_3
}
x__deserialize_correlation_regime__mutmut_orig.__name__ = 'x__deserialize_correlation_regime'


def _check_nan(value: float, field: str, vector_id: str) -> None:
    args = [value, field, vector_id]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__check_nan__mutmut_orig, x__check_nan__mutmut_mutants, args, kwargs, None)


def x__check_nan__mutmut_orig(value: float, field: str, vector_id: str) -> None:
    """RSF-07: Detect NaN. Raise RuntimeError (hard failure)."""
    if math.isnan(value):
        raise RuntimeError(
            f"DATA_CORRUPTION: NaN detected in field '{field}' for vector "
            f"'{vector_id}' during record deserialization. "
            "Record is corrupt. Hard failure per RSF-07."
        )


def x__check_nan__mutmut_1(value: float, field: str, vector_id: str) -> None:
    """RSF-07: Detect NaN. Raise RuntimeError (hard failure)."""
    if math.isnan(None):
        raise RuntimeError(
            f"DATA_CORRUPTION: NaN detected in field '{field}' for vector "
            f"'{vector_id}' during record deserialization. "
            "Record is corrupt. Hard failure per RSF-07."
        )


def x__check_nan__mutmut_2(value: float, field: str, vector_id: str) -> None:
    """RSF-07: Detect NaN. Raise RuntimeError (hard failure)."""
    if math.isnan(value):
        raise RuntimeError(
            None
        )


def x__check_nan__mutmut_3(value: float, field: str, vector_id: str) -> None:
    """RSF-07: Detect NaN. Raise RuntimeError (hard failure)."""
    if math.isnan(value):
        raise RuntimeError(
            f"DATA_CORRUPTION: NaN detected in field '{field}' for vector "
            f"'{vector_id}' during record deserialization. "
            "XXRecord is corrupt. Hard failure per RSF-07.XX"
        )


def x__check_nan__mutmut_4(value: float, field: str, vector_id: str) -> None:
    """RSF-07: Detect NaN. Raise RuntimeError (hard failure)."""
    if math.isnan(value):
        raise RuntimeError(
            f"DATA_CORRUPTION: NaN detected in field '{field}' for vector "
            f"'{vector_id}' during record deserialization. "
            "record is corrupt. hard failure per rsf-07."
        )


def x__check_nan__mutmut_5(value: float, field: str, vector_id: str) -> None:
    """RSF-07: Detect NaN. Raise RuntimeError (hard failure)."""
    if math.isnan(value):
        raise RuntimeError(
            f"DATA_CORRUPTION: NaN detected in field '{field}' for vector "
            f"'{vector_id}' during record deserialization. "
            "RECORD IS CORRUPT. HARD FAILURE PER RSF-07."
        )

x__check_nan__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__check_nan__mutmut_1': x__check_nan__mutmut_1, 
    'x__check_nan__mutmut_2': x__check_nan__mutmut_2, 
    'x__check_nan__mutmut_3': x__check_nan__mutmut_3, 
    'x__check_nan__mutmut_4': x__check_nan__mutmut_4, 
    'x__check_nan__mutmut_5': x__check_nan__mutmut_5
}
x__check_nan__mutmut_orig.__name__ = 'x__check_nan'


def _load_input_vector(d: dict) -> InputVector:
    args = [d]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__load_input_vector__mutmut_orig, x__load_input_vector__mutmut_mutants, args, kwargs, None)


def x__load_input_vector__mutmut_orig(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_1(d: dict) -> InputVector:
    returns_history = None
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_2(d: dict) -> InputVector:
    returns_history = tuple(None)
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_3(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(None) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_4(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["XXreturns_historyXX"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_5(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["RETURNS_HISTORY"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_6(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=None,
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_7(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=None,
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_8(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=None,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_9(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=None,
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_10(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=None,
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_11(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=None,
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_12(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=None,
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_13(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_14(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_15(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_16(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=None,
        description=d["description"],
    )


def x__load_input_vector__mutmut_17(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=None,
    )


def x__load_input_vector__mutmut_18(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_19(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_20(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_21(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_22(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_23(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_24(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_25(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_26(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_27(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_28(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        description=d["description"],
    )


def x__load_input_vector__mutmut_29(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        )


def x__load_input_vector__mutmut_30(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["XXvector_idXX"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_31(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["VECTOR_ID"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_32(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["XXgroup_idXX"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_33(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["GROUP_ID"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_34(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["XXcurrent_regime_strXX"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_35(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["CURRENT_REGIME_STR"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_36(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(None),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_37(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["XXmeta_uncertaintyXX"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_38(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["META_UNCERTAINTY"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_39(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(None),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_40(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["XXmacro_regimeXX"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_41(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["MACRO_REGIME"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_42(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(None),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_43(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["XXcorrelation_regimeXX"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_44(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["CORRELATION_REGIME"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_45(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(None) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_46(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["XXrealized_volXX"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_47(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["REALIZED_VOL"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_48(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["XXrealized_volXX"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_49(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["REALIZED_VOL"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_50(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_51(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(None) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_52(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["XXtarget_volXX"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_53(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["TARGET_VOL"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_54(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["XXtarget_volXX"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_55(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["TARGET_VOL"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_56(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_57(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(None) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_58(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["XXregime_posteriorXX"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_59(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["REGIME_POSTERIOR"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_60(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["XXregime_posteriorXX"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_61(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["REGIME_POSTERIOR"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_62(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is None else None,
        expect_exception=d["expect_exception"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_63(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["XXexpect_exceptionXX"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_64(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["EXPECT_EXCEPTION"],
        description=d["description"],
    )


def x__load_input_vector__mutmut_65(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["XXdescriptionXX"],
    )


def x__load_input_vector__mutmut_66(d: dict) -> InputVector:
    returns_history = tuple(_deserialize_float(r) for r in d["returns_history"])
    return InputVector(
        vector_id=d["vector_id"],
        group_id=d["group_id"],
        returns_history=returns_history,
        current_regime_str=d["current_regime_str"],
        meta_uncertainty=_deserialize_float(d["meta_uncertainty"]),
        macro_regime=_deserialize_global_regime(d["macro_regime"]),
        correlation_regime=_deserialize_correlation_regime(d["correlation_regime"]),
        realized_vol=_deserialize_float(d["realized_vol"]) if d["realized_vol"] is not None else None,
        target_vol=_deserialize_float(d["target_vol"]) if d["target_vol"] is not None else None,
        regime_posterior=_deserialize_float(d["regime_posterior"]) if d["regime_posterior"] is not None else None,
        expect_exception=d["expect_exception"],
        description=d["DESCRIPTION"],
    )

x__load_input_vector__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__load_input_vector__mutmut_1': x__load_input_vector__mutmut_1, 
    'x__load_input_vector__mutmut_2': x__load_input_vector__mutmut_2, 
    'x__load_input_vector__mutmut_3': x__load_input_vector__mutmut_3, 
    'x__load_input_vector__mutmut_4': x__load_input_vector__mutmut_4, 
    'x__load_input_vector__mutmut_5': x__load_input_vector__mutmut_5, 
    'x__load_input_vector__mutmut_6': x__load_input_vector__mutmut_6, 
    'x__load_input_vector__mutmut_7': x__load_input_vector__mutmut_7, 
    'x__load_input_vector__mutmut_8': x__load_input_vector__mutmut_8, 
    'x__load_input_vector__mutmut_9': x__load_input_vector__mutmut_9, 
    'x__load_input_vector__mutmut_10': x__load_input_vector__mutmut_10, 
    'x__load_input_vector__mutmut_11': x__load_input_vector__mutmut_11, 
    'x__load_input_vector__mutmut_12': x__load_input_vector__mutmut_12, 
    'x__load_input_vector__mutmut_13': x__load_input_vector__mutmut_13, 
    'x__load_input_vector__mutmut_14': x__load_input_vector__mutmut_14, 
    'x__load_input_vector__mutmut_15': x__load_input_vector__mutmut_15, 
    'x__load_input_vector__mutmut_16': x__load_input_vector__mutmut_16, 
    'x__load_input_vector__mutmut_17': x__load_input_vector__mutmut_17, 
    'x__load_input_vector__mutmut_18': x__load_input_vector__mutmut_18, 
    'x__load_input_vector__mutmut_19': x__load_input_vector__mutmut_19, 
    'x__load_input_vector__mutmut_20': x__load_input_vector__mutmut_20, 
    'x__load_input_vector__mutmut_21': x__load_input_vector__mutmut_21, 
    'x__load_input_vector__mutmut_22': x__load_input_vector__mutmut_22, 
    'x__load_input_vector__mutmut_23': x__load_input_vector__mutmut_23, 
    'x__load_input_vector__mutmut_24': x__load_input_vector__mutmut_24, 
    'x__load_input_vector__mutmut_25': x__load_input_vector__mutmut_25, 
    'x__load_input_vector__mutmut_26': x__load_input_vector__mutmut_26, 
    'x__load_input_vector__mutmut_27': x__load_input_vector__mutmut_27, 
    'x__load_input_vector__mutmut_28': x__load_input_vector__mutmut_28, 
    'x__load_input_vector__mutmut_29': x__load_input_vector__mutmut_29, 
    'x__load_input_vector__mutmut_30': x__load_input_vector__mutmut_30, 
    'x__load_input_vector__mutmut_31': x__load_input_vector__mutmut_31, 
    'x__load_input_vector__mutmut_32': x__load_input_vector__mutmut_32, 
    'x__load_input_vector__mutmut_33': x__load_input_vector__mutmut_33, 
    'x__load_input_vector__mutmut_34': x__load_input_vector__mutmut_34, 
    'x__load_input_vector__mutmut_35': x__load_input_vector__mutmut_35, 
    'x__load_input_vector__mutmut_36': x__load_input_vector__mutmut_36, 
    'x__load_input_vector__mutmut_37': x__load_input_vector__mutmut_37, 
    'x__load_input_vector__mutmut_38': x__load_input_vector__mutmut_38, 
    'x__load_input_vector__mutmut_39': x__load_input_vector__mutmut_39, 
    'x__load_input_vector__mutmut_40': x__load_input_vector__mutmut_40, 
    'x__load_input_vector__mutmut_41': x__load_input_vector__mutmut_41, 
    'x__load_input_vector__mutmut_42': x__load_input_vector__mutmut_42, 
    'x__load_input_vector__mutmut_43': x__load_input_vector__mutmut_43, 
    'x__load_input_vector__mutmut_44': x__load_input_vector__mutmut_44, 
    'x__load_input_vector__mutmut_45': x__load_input_vector__mutmut_45, 
    'x__load_input_vector__mutmut_46': x__load_input_vector__mutmut_46, 
    'x__load_input_vector__mutmut_47': x__load_input_vector__mutmut_47, 
    'x__load_input_vector__mutmut_48': x__load_input_vector__mutmut_48, 
    'x__load_input_vector__mutmut_49': x__load_input_vector__mutmut_49, 
    'x__load_input_vector__mutmut_50': x__load_input_vector__mutmut_50, 
    'x__load_input_vector__mutmut_51': x__load_input_vector__mutmut_51, 
    'x__load_input_vector__mutmut_52': x__load_input_vector__mutmut_52, 
    'x__load_input_vector__mutmut_53': x__load_input_vector__mutmut_53, 
    'x__load_input_vector__mutmut_54': x__load_input_vector__mutmut_54, 
    'x__load_input_vector__mutmut_55': x__load_input_vector__mutmut_55, 
    'x__load_input_vector__mutmut_56': x__load_input_vector__mutmut_56, 
    'x__load_input_vector__mutmut_57': x__load_input_vector__mutmut_57, 
    'x__load_input_vector__mutmut_58': x__load_input_vector__mutmut_58, 
    'x__load_input_vector__mutmut_59': x__load_input_vector__mutmut_59, 
    'x__load_input_vector__mutmut_60': x__load_input_vector__mutmut_60, 
    'x__load_input_vector__mutmut_61': x__load_input_vector__mutmut_61, 
    'x__load_input_vector__mutmut_62': x__load_input_vector__mutmut_62, 
    'x__load_input_vector__mutmut_63': x__load_input_vector__mutmut_63, 
    'x__load_input_vector__mutmut_64': x__load_input_vector__mutmut_64, 
    'x__load_input_vector__mutmut_65': x__load_input_vector__mutmut_65, 
    'x__load_input_vector__mutmut_66': x__load_input_vector__mutmut_66
}
x__load_input_vector__mutmut_orig.__name__ = 'x__load_input_vector'


def _load_observed_output(d: dict, vector_id: str) -> ObservedOutput:
    args = [d, vector_id]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__load_observed_output__mutmut_orig, x__load_observed_output__mutmut_mutants, args, kwargs, None)


def x__load_observed_output__mutmut_orig(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_1(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = None
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_2(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "XXexpected_drawdownXX",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_3(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "EXPECTED_DRAWDOWN",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_4(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "XXexpected_drawdown_p95XX",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_5(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "EXPECTED_DRAWDOWN_P95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_6(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "XXvolatility_forecastXX",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_7(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "VOLATILITY_FORECAST",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_8(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "XXposition_size_factorXX",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_9(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "POSITION_SIZE_FACTOR",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_10(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "XXexposure_weightXX",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_11(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "EXPOSURE_WEIGHT",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_12(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = None
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_13(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = None
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_14(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(None)
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_15(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(None, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_16(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, None, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_17(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, None)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_18(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_19(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_20(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, )
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_21(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = None

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_22(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=None,
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_23(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=None,
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_24(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=None,
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_25(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=None,
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_26(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=None,
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_27(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=None,
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_28(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=None,
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_29(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=None,
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_30(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=None,
    )


def x__load_observed_output__mutmut_31(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_32(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_33(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_34(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_35(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_36(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_37(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_38(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_39(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        )


def x__load_observed_output__mutmut_40(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["XXexpected_drawdownXX"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_41(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["EXPECTED_DRAWDOWN"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_42(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["XXexpected_drawdown_p95XX"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_43(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["EXPECTED_DRAWDOWN_P95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_44(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["XXvolatility_forecastXX"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_45(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["VOLATILITY_FORECAST"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_46(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(None),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_47(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["XXrisk_compression_activeXX"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_48(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["RISK_COMPRESSION_ACTIVE"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_49(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["XXposition_size_factorXX"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_50(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["POSITION_SIZE_FACTOR"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_51(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["XXexposure_weightXX"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_52(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["EXPOSURE_WEIGHT"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_53(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(None),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_54(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["XXrisk_regimeXX"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_55(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["RISK_REGIME"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_56(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(None),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_57(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["XXexception_raisedXX"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_58(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["EXCEPTION_RAISED"]),
        exception_type=str(d["exception_type"]),
    )


def x__load_observed_output__mutmut_59(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(None),
    )


def x__load_observed_output__mutmut_60(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["XXexception_typeXX"]),
    )


def x__load_observed_output__mutmut_61(d: dict, vector_id: str) -> ObservedOutput:
    float_fields = [
        "expected_drawdown",
        "expected_drawdown_p95",
        "volatility_forecast",
        "position_size_factor",
        "exposure_weight",
    ]
    values = {}
    for field in float_fields:
        val = _deserialize_float(d[field])
        _check_nan(val, field, vector_id)
        values[field] = val

    return ObservedOutput(
        expected_drawdown=values["expected_drawdown"],
        expected_drawdown_p95=values["expected_drawdown_p95"],
        volatility_forecast=values["volatility_forecast"],
        risk_compression_active=bool(d["risk_compression_active"]),
        position_size_factor=values["position_size_factor"],
        exposure_weight=values["exposure_weight"],
        risk_regime=str(d["risk_regime"]),
        exception_raised=bool(d["exception_raised"]),
        exception_type=str(d["EXCEPTION_TYPE"]),
    )

x__load_observed_output__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__load_observed_output__mutmut_1': x__load_observed_output__mutmut_1, 
    'x__load_observed_output__mutmut_2': x__load_observed_output__mutmut_2, 
    'x__load_observed_output__mutmut_3': x__load_observed_output__mutmut_3, 
    'x__load_observed_output__mutmut_4': x__load_observed_output__mutmut_4, 
    'x__load_observed_output__mutmut_5': x__load_observed_output__mutmut_5, 
    'x__load_observed_output__mutmut_6': x__load_observed_output__mutmut_6, 
    'x__load_observed_output__mutmut_7': x__load_observed_output__mutmut_7, 
    'x__load_observed_output__mutmut_8': x__load_observed_output__mutmut_8, 
    'x__load_observed_output__mutmut_9': x__load_observed_output__mutmut_9, 
    'x__load_observed_output__mutmut_10': x__load_observed_output__mutmut_10, 
    'x__load_observed_output__mutmut_11': x__load_observed_output__mutmut_11, 
    'x__load_observed_output__mutmut_12': x__load_observed_output__mutmut_12, 
    'x__load_observed_output__mutmut_13': x__load_observed_output__mutmut_13, 
    'x__load_observed_output__mutmut_14': x__load_observed_output__mutmut_14, 
    'x__load_observed_output__mutmut_15': x__load_observed_output__mutmut_15, 
    'x__load_observed_output__mutmut_16': x__load_observed_output__mutmut_16, 
    'x__load_observed_output__mutmut_17': x__load_observed_output__mutmut_17, 
    'x__load_observed_output__mutmut_18': x__load_observed_output__mutmut_18, 
    'x__load_observed_output__mutmut_19': x__load_observed_output__mutmut_19, 
    'x__load_observed_output__mutmut_20': x__load_observed_output__mutmut_20, 
    'x__load_observed_output__mutmut_21': x__load_observed_output__mutmut_21, 
    'x__load_observed_output__mutmut_22': x__load_observed_output__mutmut_22, 
    'x__load_observed_output__mutmut_23': x__load_observed_output__mutmut_23, 
    'x__load_observed_output__mutmut_24': x__load_observed_output__mutmut_24, 
    'x__load_observed_output__mutmut_25': x__load_observed_output__mutmut_25, 
    'x__load_observed_output__mutmut_26': x__load_observed_output__mutmut_26, 
    'x__load_observed_output__mutmut_27': x__load_observed_output__mutmut_27, 
    'x__load_observed_output__mutmut_28': x__load_observed_output__mutmut_28, 
    'x__load_observed_output__mutmut_29': x__load_observed_output__mutmut_29, 
    'x__load_observed_output__mutmut_30': x__load_observed_output__mutmut_30, 
    'x__load_observed_output__mutmut_31': x__load_observed_output__mutmut_31, 
    'x__load_observed_output__mutmut_32': x__load_observed_output__mutmut_32, 
    'x__load_observed_output__mutmut_33': x__load_observed_output__mutmut_33, 
    'x__load_observed_output__mutmut_34': x__load_observed_output__mutmut_34, 
    'x__load_observed_output__mutmut_35': x__load_observed_output__mutmut_35, 
    'x__load_observed_output__mutmut_36': x__load_observed_output__mutmut_36, 
    'x__load_observed_output__mutmut_37': x__load_observed_output__mutmut_37, 
    'x__load_observed_output__mutmut_38': x__load_observed_output__mutmut_38, 
    'x__load_observed_output__mutmut_39': x__load_observed_output__mutmut_39, 
    'x__load_observed_output__mutmut_40': x__load_observed_output__mutmut_40, 
    'x__load_observed_output__mutmut_41': x__load_observed_output__mutmut_41, 
    'x__load_observed_output__mutmut_42': x__load_observed_output__mutmut_42, 
    'x__load_observed_output__mutmut_43': x__load_observed_output__mutmut_43, 
    'x__load_observed_output__mutmut_44': x__load_observed_output__mutmut_44, 
    'x__load_observed_output__mutmut_45': x__load_observed_output__mutmut_45, 
    'x__load_observed_output__mutmut_46': x__load_observed_output__mutmut_46, 
    'x__load_observed_output__mutmut_47': x__load_observed_output__mutmut_47, 
    'x__load_observed_output__mutmut_48': x__load_observed_output__mutmut_48, 
    'x__load_observed_output__mutmut_49': x__load_observed_output__mutmut_49, 
    'x__load_observed_output__mutmut_50': x__load_observed_output__mutmut_50, 
    'x__load_observed_output__mutmut_51': x__load_observed_output__mutmut_51, 
    'x__load_observed_output__mutmut_52': x__load_observed_output__mutmut_52, 
    'x__load_observed_output__mutmut_53': x__load_observed_output__mutmut_53, 
    'x__load_observed_output__mutmut_54': x__load_observed_output__mutmut_54, 
    'x__load_observed_output__mutmut_55': x__load_observed_output__mutmut_55, 
    'x__load_observed_output__mutmut_56': x__load_observed_output__mutmut_56, 
    'x__load_observed_output__mutmut_57': x__load_observed_output__mutmut_57, 
    'x__load_observed_output__mutmut_58': x__load_observed_output__mutmut_58, 
    'x__load_observed_output__mutmut_59': x__load_observed_output__mutmut_59, 
    'x__load_observed_output__mutmut_60': x__load_observed_output__mutmut_60, 
    'x__load_observed_output__mutmut_61': x__load_observed_output__mutmut_61
}
x__load_observed_output__mutmut_orig.__name__ = 'x__load_observed_output'


def _load_record(d: dict) -> ExecutionRecord:
    args = [d]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__load_record__mutmut_orig, x__load_record__mutmut_mutants, args, kwargs, None)


def x__load_record__mutmut_orig(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_1(d: dict) -> ExecutionRecord:
    vector_id = None
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_2(d: dict) -> ExecutionRecord:
    vector_id = d["XXvector_idXX"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_3(d: dict) -> ExecutionRecord:
    vector_id = d["VECTOR_ID"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_4(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = None
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_5(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(None)
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_6(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["XXinput_vectorXX"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_7(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["INPUT_VECTOR"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_8(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = None
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_9(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(None, vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_10(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], None)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_11(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_12(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], )
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_13(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["XXobserved_outputXX"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_14(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["OBSERVED_OUTPUT"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_15(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=None,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_16(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=None,
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_17(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=None,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_18(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=None,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_19(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=None,
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_20(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=None,
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_21(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=None,
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_22(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=None,
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_23(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=None,
        module_version=d["module_version"],
    )


def x__load_record__mutmut_24(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=None,
    )


def x__load_record__mutmut_25(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_26(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_27(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_28(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_29(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_30(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_31(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_32(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_33(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_34(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        )


def x__load_record__mutmut_35(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["XXgroup_idXX"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_36(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["GROUP_ID"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_37(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["XXstageXX"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_38(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["STAGE"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_39(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["XXmanifest_hashXX"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_40(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["MANIFEST_HASH"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_41(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["XXtimestamp_isoXX"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_42(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["TIMESTAMP_ISO"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_43(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["XXexecution_idXX"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_44(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["EXECUTION_ID"],
        harness_version=d["harness_version"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_45(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["XXharness_versionXX"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_46(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["HARNESS_VERSION"],
        module_version=d["module_version"],
    )


def x__load_record__mutmut_47(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["XXmodule_versionXX"],
    )


def x__load_record__mutmut_48(d: dict) -> ExecutionRecord:
    vector_id = d["vector_id"]
    iv  = _load_input_vector(d["input_vector"])
    out = _load_observed_output(d["observed_output"], vector_id)
    return ExecutionRecord(
        vector_id=vector_id,
        group_id=d["group_id"],
        input_vector=iv,
        observed_output=out,
        stage=d["stage"],
        manifest_hash=d["manifest_hash"],
        timestamp_iso=d["timestamp_iso"],
        execution_id=d["execution_id"],
        harness_version=d["harness_version"],
        module_version=d["MODULE_VERSION"],
    )

x__load_record__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__load_record__mutmut_1': x__load_record__mutmut_1, 
    'x__load_record__mutmut_2': x__load_record__mutmut_2, 
    'x__load_record__mutmut_3': x__load_record__mutmut_3, 
    'x__load_record__mutmut_4': x__load_record__mutmut_4, 
    'x__load_record__mutmut_5': x__load_record__mutmut_5, 
    'x__load_record__mutmut_6': x__load_record__mutmut_6, 
    'x__load_record__mutmut_7': x__load_record__mutmut_7, 
    'x__load_record__mutmut_8': x__load_record__mutmut_8, 
    'x__load_record__mutmut_9': x__load_record__mutmut_9, 
    'x__load_record__mutmut_10': x__load_record__mutmut_10, 
    'x__load_record__mutmut_11': x__load_record__mutmut_11, 
    'x__load_record__mutmut_12': x__load_record__mutmut_12, 
    'x__load_record__mutmut_13': x__load_record__mutmut_13, 
    'x__load_record__mutmut_14': x__load_record__mutmut_14, 
    'x__load_record__mutmut_15': x__load_record__mutmut_15, 
    'x__load_record__mutmut_16': x__load_record__mutmut_16, 
    'x__load_record__mutmut_17': x__load_record__mutmut_17, 
    'x__load_record__mutmut_18': x__load_record__mutmut_18, 
    'x__load_record__mutmut_19': x__load_record__mutmut_19, 
    'x__load_record__mutmut_20': x__load_record__mutmut_20, 
    'x__load_record__mutmut_21': x__load_record__mutmut_21, 
    'x__load_record__mutmut_22': x__load_record__mutmut_22, 
    'x__load_record__mutmut_23': x__load_record__mutmut_23, 
    'x__load_record__mutmut_24': x__load_record__mutmut_24, 
    'x__load_record__mutmut_25': x__load_record__mutmut_25, 
    'x__load_record__mutmut_26': x__load_record__mutmut_26, 
    'x__load_record__mutmut_27': x__load_record__mutmut_27, 
    'x__load_record__mutmut_28': x__load_record__mutmut_28, 
    'x__load_record__mutmut_29': x__load_record__mutmut_29, 
    'x__load_record__mutmut_30': x__load_record__mutmut_30, 
    'x__load_record__mutmut_31': x__load_record__mutmut_31, 
    'x__load_record__mutmut_32': x__load_record__mutmut_32, 
    'x__load_record__mutmut_33': x__load_record__mutmut_33, 
    'x__load_record__mutmut_34': x__load_record__mutmut_34, 
    'x__load_record__mutmut_35': x__load_record__mutmut_35, 
    'x__load_record__mutmut_36': x__load_record__mutmut_36, 
    'x__load_record__mutmut_37': x__load_record__mutmut_37, 
    'x__load_record__mutmut_38': x__load_record__mutmut_38, 
    'x__load_record__mutmut_39': x__load_record__mutmut_39, 
    'x__load_record__mutmut_40': x__load_record__mutmut_40, 
    'x__load_record__mutmut_41': x__load_record__mutmut_41, 
    'x__load_record__mutmut_42': x__load_record__mutmut_42, 
    'x__load_record__mutmut_43': x__load_record__mutmut_43, 
    'x__load_record__mutmut_44': x__load_record__mutmut_44, 
    'x__load_record__mutmut_45': x__load_record__mutmut_45, 
    'x__load_record__mutmut_46': x__load_record__mutmut_46, 
    'x__load_record__mutmut_47': x__load_record__mutmut_47, 
    'x__load_record__mutmut_48': x__load_record__mutmut_48
}
x__load_record__mutmut_orig.__name__ = 'x__load_record'


class RecordLoader:
    """
    Loads and validates a serialized ExecutionRecord set from a JSON file.
    Implements RSF-06 and RSF-07 validation.
    Restores canonical enum instances for macro_regime and correlation_regime.
    """

    def load(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        args = [filepath, module_version]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRecordLoaderǁload__mutmut_orig'), object.__getattribute__(self, 'xǁRecordLoaderǁload__mutmut_mutants'), args, kwargs, self)

    def xǁRecordLoaderǁload__mutmut_orig(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_1(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_2(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                None
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_3(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(None, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_4(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, None, encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_5(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding=None) as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_6(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open("r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_7(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_8(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", ) as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_9(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "XXrXX", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_10(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "R", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_11(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="XXutf-8XX") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_12(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="UTF-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_13(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = None
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_14(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(None)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_15(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                None
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_16(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get(None) != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_17(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("XXformat_versionXX") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_18(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("FORMAT_VERSION") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_19(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") == STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_20(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                None
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_21(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get(None)}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_22(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('XXformat_versionXX')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_23(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('FORMAT_VERSION')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_24(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get(None) != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_25(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("XXharness_versionXX") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_26(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("HARNESS_VERSION") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_27(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") == HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_28(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                None
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_29(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get(None)}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_30(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('XXharness_versionXX')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_31(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('HARNESS_VERSION')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_32(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get(None) != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_33(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("XXmodule_versionXX") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_34(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("MODULE_VERSION") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_35(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") == module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_36(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                None
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_37(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get(None)}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_38(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('XXmodule_versionXX')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_39(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('MODULE_VERSION')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_40(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = None
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_41(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get(None, [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_42(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", None)
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_43(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get([])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_44(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", )
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_45(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("XXrecordsXX", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_46(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("RECORDS", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_47(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get(None) != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_48(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("XXvector_countXX") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_49(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("VECTOR_COUNT") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_50(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") == len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_51(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                None
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_52(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get(None)} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_53(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('XXvector_countXX')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_54(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('VECTOR_COUNT')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_55(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = None
        for d in raw_records:
            rec = _load_record(d)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_56(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = None
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_57(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(None)
            records.append(rec)

        return records

    def xǁRecordLoaderǁload__mutmut_58(
        self,
        filepath:       Path,
        module_version: str,
    ) -> List[ExecutionRecord]:
        """
        Load records from filepath. Validate per RSF-06.
        Detect NaN per RSF-07.
        Restore canonical enum instances per Single Authoritative Regime Source rule.
        """
        if not filepath.exists():
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Prior record file not found: {filepath}"
            )

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            raise RuntimeError(
                f"DATA_CORRUPTION: Failed to load record file {filepath}: {exc}"
            ) from exc

        # RSF-06: Validate header fields.
        if payload.get("format_version") != STORAGE_FORMAT_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: format_version mismatch. "
                f"File: {payload.get('format_version')}, "
                f"Expected: {STORAGE_FORMAT_VERSION}."
            )
        if payload.get("harness_version") != HARNESS_VERSION:
            raise RuntimeError(
                f"DATA_CORRUPTION: harness_version mismatch. "
                f"File: {payload.get('harness_version')}, "
                f"Expected: {HARNESS_VERSION}."
            )
        if payload.get("module_version") != module_version:
            raise RuntimeError(
                f"DATA_CORRUPTION: module_version mismatch. "
                f"File: {payload.get('module_version')}, "
                f"Expected: {module_version}."
            )

        raw_records = payload.get("records", [])
        if payload.get("vector_count") != len(raw_records):
            raise RuntimeError(
                f"DATA_CORRUPTION: vector_count={payload.get('vector_count')} "
                f"does not match actual record count={len(raw_records)}."
            )

        records = []
        for d in raw_records:
            rec = _load_record(d)
            records.append(None)

        return records
    
    xǁRecordLoaderǁload__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRecordLoaderǁload__mutmut_1': xǁRecordLoaderǁload__mutmut_1, 
        'xǁRecordLoaderǁload__mutmut_2': xǁRecordLoaderǁload__mutmut_2, 
        'xǁRecordLoaderǁload__mutmut_3': xǁRecordLoaderǁload__mutmut_3, 
        'xǁRecordLoaderǁload__mutmut_4': xǁRecordLoaderǁload__mutmut_4, 
        'xǁRecordLoaderǁload__mutmut_5': xǁRecordLoaderǁload__mutmut_5, 
        'xǁRecordLoaderǁload__mutmut_6': xǁRecordLoaderǁload__mutmut_6, 
        'xǁRecordLoaderǁload__mutmut_7': xǁRecordLoaderǁload__mutmut_7, 
        'xǁRecordLoaderǁload__mutmut_8': xǁRecordLoaderǁload__mutmut_8, 
        'xǁRecordLoaderǁload__mutmut_9': xǁRecordLoaderǁload__mutmut_9, 
        'xǁRecordLoaderǁload__mutmut_10': xǁRecordLoaderǁload__mutmut_10, 
        'xǁRecordLoaderǁload__mutmut_11': xǁRecordLoaderǁload__mutmut_11, 
        'xǁRecordLoaderǁload__mutmut_12': xǁRecordLoaderǁload__mutmut_12, 
        'xǁRecordLoaderǁload__mutmut_13': xǁRecordLoaderǁload__mutmut_13, 
        'xǁRecordLoaderǁload__mutmut_14': xǁRecordLoaderǁload__mutmut_14, 
        'xǁRecordLoaderǁload__mutmut_15': xǁRecordLoaderǁload__mutmut_15, 
        'xǁRecordLoaderǁload__mutmut_16': xǁRecordLoaderǁload__mutmut_16, 
        'xǁRecordLoaderǁload__mutmut_17': xǁRecordLoaderǁload__mutmut_17, 
        'xǁRecordLoaderǁload__mutmut_18': xǁRecordLoaderǁload__mutmut_18, 
        'xǁRecordLoaderǁload__mutmut_19': xǁRecordLoaderǁload__mutmut_19, 
        'xǁRecordLoaderǁload__mutmut_20': xǁRecordLoaderǁload__mutmut_20, 
        'xǁRecordLoaderǁload__mutmut_21': xǁRecordLoaderǁload__mutmut_21, 
        'xǁRecordLoaderǁload__mutmut_22': xǁRecordLoaderǁload__mutmut_22, 
        'xǁRecordLoaderǁload__mutmut_23': xǁRecordLoaderǁload__mutmut_23, 
        'xǁRecordLoaderǁload__mutmut_24': xǁRecordLoaderǁload__mutmut_24, 
        'xǁRecordLoaderǁload__mutmut_25': xǁRecordLoaderǁload__mutmut_25, 
        'xǁRecordLoaderǁload__mutmut_26': xǁRecordLoaderǁload__mutmut_26, 
        'xǁRecordLoaderǁload__mutmut_27': xǁRecordLoaderǁload__mutmut_27, 
        'xǁRecordLoaderǁload__mutmut_28': xǁRecordLoaderǁload__mutmut_28, 
        'xǁRecordLoaderǁload__mutmut_29': xǁRecordLoaderǁload__mutmut_29, 
        'xǁRecordLoaderǁload__mutmut_30': xǁRecordLoaderǁload__mutmut_30, 
        'xǁRecordLoaderǁload__mutmut_31': xǁRecordLoaderǁload__mutmut_31, 
        'xǁRecordLoaderǁload__mutmut_32': xǁRecordLoaderǁload__mutmut_32, 
        'xǁRecordLoaderǁload__mutmut_33': xǁRecordLoaderǁload__mutmut_33, 
        'xǁRecordLoaderǁload__mutmut_34': xǁRecordLoaderǁload__mutmut_34, 
        'xǁRecordLoaderǁload__mutmut_35': xǁRecordLoaderǁload__mutmut_35, 
        'xǁRecordLoaderǁload__mutmut_36': xǁRecordLoaderǁload__mutmut_36, 
        'xǁRecordLoaderǁload__mutmut_37': xǁRecordLoaderǁload__mutmut_37, 
        'xǁRecordLoaderǁload__mutmut_38': xǁRecordLoaderǁload__mutmut_38, 
        'xǁRecordLoaderǁload__mutmut_39': xǁRecordLoaderǁload__mutmut_39, 
        'xǁRecordLoaderǁload__mutmut_40': xǁRecordLoaderǁload__mutmut_40, 
        'xǁRecordLoaderǁload__mutmut_41': xǁRecordLoaderǁload__mutmut_41, 
        'xǁRecordLoaderǁload__mutmut_42': xǁRecordLoaderǁload__mutmut_42, 
        'xǁRecordLoaderǁload__mutmut_43': xǁRecordLoaderǁload__mutmut_43, 
        'xǁRecordLoaderǁload__mutmut_44': xǁRecordLoaderǁload__mutmut_44, 
        'xǁRecordLoaderǁload__mutmut_45': xǁRecordLoaderǁload__mutmut_45, 
        'xǁRecordLoaderǁload__mutmut_46': xǁRecordLoaderǁload__mutmut_46, 
        'xǁRecordLoaderǁload__mutmut_47': xǁRecordLoaderǁload__mutmut_47, 
        'xǁRecordLoaderǁload__mutmut_48': xǁRecordLoaderǁload__mutmut_48, 
        'xǁRecordLoaderǁload__mutmut_49': xǁRecordLoaderǁload__mutmut_49, 
        'xǁRecordLoaderǁload__mutmut_50': xǁRecordLoaderǁload__mutmut_50, 
        'xǁRecordLoaderǁload__mutmut_51': xǁRecordLoaderǁload__mutmut_51, 
        'xǁRecordLoaderǁload__mutmut_52': xǁRecordLoaderǁload__mutmut_52, 
        'xǁRecordLoaderǁload__mutmut_53': xǁRecordLoaderǁload__mutmut_53, 
        'xǁRecordLoaderǁload__mutmut_54': xǁRecordLoaderǁload__mutmut_54, 
        'xǁRecordLoaderǁload__mutmut_55': xǁRecordLoaderǁload__mutmut_55, 
        'xǁRecordLoaderǁload__mutmut_56': xǁRecordLoaderǁload__mutmut_56, 
        'xǁRecordLoaderǁload__mutmut_57': xǁRecordLoaderǁload__mutmut_57, 
        'xǁRecordLoaderǁload__mutmut_58': xǁRecordLoaderǁload__mutmut_58
    }
    xǁRecordLoaderǁload__mutmut_orig.__name__ = 'xǁRecordLoaderǁload'
