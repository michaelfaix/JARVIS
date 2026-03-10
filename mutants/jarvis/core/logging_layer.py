# jarvis/core/logging_layer.py
# S02 -- Logging Layer
# JARVIS v6.0.1 -- Decision Quality Maximization Platform
#
# Scope: Event-sourced logging with hash-chain integration.
# Zero tolerance for lost events. No file IO. No global mutable state.
# All timestamps are caller-supplied. All hashes are deterministic.
#
# Canonical import:
#   from jarvis.core.logging_layer import EventLogger, Event, EventFilter
#
# Dependencies: S01 (jarvis.core.integrity_layer)
# Prohibited: datetime.now(), uuid, random, file IO, global mutable state

# ===========================================================================
# SECTION 1 -- STDLIB IMPORTS
# ===========================================================================

import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional

# ===========================================================================
# SECTION 2 -- S01 DEPENDENCY
# ===========================================================================

from jarvis.core.integrity_layer import IntegrityLayer

# ===========================================================================
# SECTION 3 -- CONSTANTS
# ===========================================================================

# Sentinel strings used when numeric sanitization detects invalid values.
# These are logged in place of the invalid value; the event is never silently
# dropped. Values are ASCII string literals -- no float arithmetic involved.
_NAN_SENTINEL: str = "NaN_DETECTED"
_INF_SENTINEL: str = "Inf_DETECTED"

# Field separator used inside hash preimage. Chosen to be unlikely to appear
# in any field value; does not affect correctness, only collision resistance.
_HASH_SEP: str = "|"
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

# ===========================================================================
# SECTION 4 -- DATACLASSES: Event, EventFilter
# ===========================================================================

@dataclass
class Event:
    """
    Immutable record of a single system event.

    Fields
    ------
    id        : Deterministic string identifier derived from instance counter.
    type      : Category string (e.g. DECISION, ERROR, STATE_CHANGE, ...).
    timestamp : Caller-supplied datetime. Never generated internally.
    data      : Sanitized key-value payload. NaN/Inf values replaced with
                sentinel strings before storage.
    hash      : SHA-256 hex digest over (id, type, timestamp, data).
                Deterministic; depends only on the four explicit fields above.
    """
    id: str
    type: str
    timestamp: datetime
    data: Dict[str, Any]
    hash: str


@dataclass
class EventFilter:
    """
    Filter specification for EventLogger.query_events().

    All fields are optional. Omitted fields apply no constraint.

    Fields
    ------
    event_type : If set, only events whose .type equals this value are returned.
    start_time : If set, only events with timestamp >= start_time are returned.
    end_time   : If set, only events with timestamp <= end_time are returned.
    limit      : If set, at most this many events are returned (from the front
                 of the filtered sequence, i.e. oldest first).
    """
    event_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: Optional[int] = None


# ===========================================================================
# SECTION 5 -- INTERNAL HELPERS
# ===========================================================================

def _sanitize_numeric(value: Any) -> Any:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__sanitize_numeric__mutmut_orig, x__sanitize_numeric__mutmut_mutants, args, kwargs, None)


# ===========================================================================
# SECTION 5 -- INTERNAL HELPERS
# ===========================================================================

def x__sanitize_numeric__mutmut_orig(value: Any) -> Any:
    """
    Replace float NaN or Inf with the appropriate sentinel string.

    Non-float values are returned unchanged. This function never raises;
    it is the last line of defence before a value enters Event.data.

    Deterministic: output depends only on the input value.
    No IO. No side effects. No randomness.
    """
    if isinstance(value, float):
        if math.isnan(value):
            return _NAN_SENTINEL
        if math.isinf(value):
            return _INF_SENTINEL
    return value


# ===========================================================================
# SECTION 5 -- INTERNAL HELPERS
# ===========================================================================

def x__sanitize_numeric__mutmut_1(value: Any) -> Any:
    """
    Replace float NaN or Inf with the appropriate sentinel string.

    Non-float values are returned unchanged. This function never raises;
    it is the last line of defence before a value enters Event.data.

    Deterministic: output depends only on the input value.
    No IO. No side effects. No randomness.
    """
    if isinstance(value, float):
        if math.isnan(None):
            return _NAN_SENTINEL
        if math.isinf(value):
            return _INF_SENTINEL
    return value


# ===========================================================================
# SECTION 5 -- INTERNAL HELPERS
# ===========================================================================

def x__sanitize_numeric__mutmut_2(value: Any) -> Any:
    """
    Replace float NaN or Inf with the appropriate sentinel string.

    Non-float values are returned unchanged. This function never raises;
    it is the last line of defence before a value enters Event.data.

    Deterministic: output depends only on the input value.
    No IO. No side effects. No randomness.
    """
    if isinstance(value, float):
        if math.isnan(value):
            return _NAN_SENTINEL
        if math.isinf(None):
            return _INF_SENTINEL
    return value

x__sanitize_numeric__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__sanitize_numeric__mutmut_1': x__sanitize_numeric__mutmut_1, 
    'x__sanitize_numeric__mutmut_2': x__sanitize_numeric__mutmut_2
}
x__sanitize_numeric__mutmut_orig.__name__ = 'x__sanitize_numeric'


def _sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    args = [data]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__sanitize_data__mutmut_orig, x__sanitize_data__mutmut_mutants, args, kwargs, None)


def x__sanitize_data__mutmut_orig(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a new dict with all float values sanitized via _sanitize_numeric().

    The original dict is not mutated. Keys are not modified.
    Deterministic: output depends only on the input dict.
    """
    return {k: _sanitize_numeric(v) for k, v in data.items()}


def x__sanitize_data__mutmut_1(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a new dict with all float values sanitized via _sanitize_numeric().

    The original dict is not mutated. Keys are not modified.
    Deterministic: output depends only on the input dict.
    """
    return {k: _sanitize_numeric(None) for k, v in data.items()}

x__sanitize_data__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__sanitize_data__mutmut_1': x__sanitize_data__mutmut_1
}
x__sanitize_data__mutmut_orig.__name__ = 'x__sanitize_data'


def _compute_hash(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    args = [event_id, event_type, timestamp, data]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__compute_hash__mutmut_orig, x__compute_hash__mutmut_mutants, args, kwargs, None)


def x__compute_hash__mutmut_orig(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", errors="replace")).hexdigest()


def x__compute_hash__mutmut_1(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = None
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", errors="replace")).hexdigest()


def x__compute_hash__mutmut_2(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(None)
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", errors="replace")).hexdigest()


def x__compute_hash__mutmut_3(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(None))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", errors="replace")).hexdigest()


def x__compute_hash__mutmut_4(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = None
    return hashlib.sha256(preimage.encode("ascii", errors="replace")).hexdigest()


def x__compute_hash__mutmut_5(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP - sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", errors="replace")).hexdigest()


def x__compute_hash__mutmut_6(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat() - _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", errors="replace")).hexdigest()


def x__compute_hash__mutmut_7(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP - timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", errors="replace")).hexdigest()


def x__compute_hash__mutmut_8(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type - _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", errors="replace")).hexdigest()


def x__compute_hash__mutmut_9(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP - event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", errors="replace")).hexdigest()


def x__compute_hash__mutmut_10(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id - _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", errors="replace")).hexdigest()


def x__compute_hash__mutmut_11(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(None).hexdigest()


def x__compute_hash__mutmut_12(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode(None, errors="replace")).hexdigest()


def x__compute_hash__mutmut_13(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", errors=None)).hexdigest()


def x__compute_hash__mutmut_14(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode(errors="replace")).hexdigest()


def x__compute_hash__mutmut_15(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", )).hexdigest()


def x__compute_hash__mutmut_16(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("XXasciiXX", errors="replace")).hexdigest()


def x__compute_hash__mutmut_17(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ASCII", errors="replace")).hexdigest()


def x__compute_hash__mutmut_18(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", errors="XXreplaceXX")).hexdigest()


def x__compute_hash__mutmut_19(
    event_id: str,
    event_type: str,
    timestamp: datetime,
    data: Dict[str, Any],
) -> str:
    """
    Compute a deterministic SHA-256 hex digest for an event.

    Hash preimage construction
    --------------------------
    Fields are serialized in fixed order:
        event_id  + SEP
        event_type + SEP
        timestamp.isoformat() + SEP
        sorted_items_repr

    sorted_items_repr is repr(sorted(data.items())), which gives a
    deterministic string regardless of dict insertion order.

    No implicit values (time, pid, entropy) are included.
    Returns a 64-character lowercase hex string.
    """
    sorted_items: str = repr(sorted(data.items()))
    preimage: str = (
        event_id
        + _HASH_SEP
        + event_type
        + _HASH_SEP
        + timestamp.isoformat()
        + _HASH_SEP
        + sorted_items
    )
    return hashlib.sha256(preimage.encode("ascii", errors="REPLACE")).hexdigest()

x__compute_hash__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__compute_hash__mutmut_1': x__compute_hash__mutmut_1, 
    'x__compute_hash__mutmut_2': x__compute_hash__mutmut_2, 
    'x__compute_hash__mutmut_3': x__compute_hash__mutmut_3, 
    'x__compute_hash__mutmut_4': x__compute_hash__mutmut_4, 
    'x__compute_hash__mutmut_5': x__compute_hash__mutmut_5, 
    'x__compute_hash__mutmut_6': x__compute_hash__mutmut_6, 
    'x__compute_hash__mutmut_7': x__compute_hash__mutmut_7, 
    'x__compute_hash__mutmut_8': x__compute_hash__mutmut_8, 
    'x__compute_hash__mutmut_9': x__compute_hash__mutmut_9, 
    'x__compute_hash__mutmut_10': x__compute_hash__mutmut_10, 
    'x__compute_hash__mutmut_11': x__compute_hash__mutmut_11, 
    'x__compute_hash__mutmut_12': x__compute_hash__mutmut_12, 
    'x__compute_hash__mutmut_13': x__compute_hash__mutmut_13, 
    'x__compute_hash__mutmut_14': x__compute_hash__mutmut_14, 
    'x__compute_hash__mutmut_15': x__compute_hash__mutmut_15, 
    'x__compute_hash__mutmut_16': x__compute_hash__mutmut_16, 
    'x__compute_hash__mutmut_17': x__compute_hash__mutmut_17, 
    'x__compute_hash__mutmut_18': x__compute_hash__mutmut_18, 
    'x__compute_hash__mutmut_19': x__compute_hash__mutmut_19
}
x__compute_hash__mutmut_orig.__name__ = 'x__compute_hash'


def _make_event_id(counter: int) -> str:
    args = [counter]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__make_event_id__mutmut_orig, x__make_event_id__mutmut_mutants, args, kwargs, None)


def x__make_event_id__mutmut_orig(counter: int) -> str:
    """
    Derive a deterministic event ID from a monotonic integer counter.

    Format: "EVT-{counter:016d}"
    Zero-padded to 16 digits for lexicographic sort stability.
    No uuid. No randomness. No time dependency.
    """
    return "EVT-{:016d}".format(counter)


def x__make_event_id__mutmut_1(counter: int) -> str:
    """
    Derive a deterministic event ID from a monotonic integer counter.

    Format: "EVT-{counter:016d}"
    Zero-padded to 16 digits for lexicographic sort stability.
    No uuid. No randomness. No time dependency.
    """
    return "EVT-{:016d}".format(None)


def x__make_event_id__mutmut_2(counter: int) -> str:
    """
    Derive a deterministic event ID from a monotonic integer counter.

    Format: "EVT-{counter:016d}"
    Zero-padded to 16 digits for lexicographic sort stability.
    No uuid. No randomness. No time dependency.
    """
    return "XXEVT-{:016d}XX".format(counter)


def x__make_event_id__mutmut_3(counter: int) -> str:
    """
    Derive a deterministic event ID from a monotonic integer counter.

    Format: "EVT-{counter:016d}"
    Zero-padded to 16 digits for lexicographic sort stability.
    No uuid. No randomness. No time dependency.
    """
    return "evt-{:016d}".format(counter)


def x__make_event_id__mutmut_4(counter: int) -> str:
    """
    Derive a deterministic event ID from a monotonic integer counter.

    Format: "EVT-{counter:016d}"
    Zero-padded to 16 digits for lexicographic sort stability.
    No uuid. No randomness. No time dependency.
    """
    return "EVT-{:016D}".format(counter)

x__make_event_id__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__make_event_id__mutmut_1': x__make_event_id__mutmut_1, 
    'x__make_event_id__mutmut_2': x__make_event_id__mutmut_2, 
    'x__make_event_id__mutmut_3': x__make_event_id__mutmut_3, 
    'x__make_event_id__mutmut_4': x__make_event_id__mutmut_4
}
x__make_event_id__mutmut_orig.__name__ = 'x__make_event_id'


# ===========================================================================
# SECTION 6 -- EventLogger
# ===========================================================================

class EventLogger:
    """
    Event-sourced logger with deterministic hash-chain integrity.

    Storage
    -------
    Events are held in an instance-level list (_store). No file IO.
    No global state. Each EventLogger instance is fully independent.

    Determinism guarantees
    ----------------------
    - Timestamps are caller-supplied; never generated internally.
    - Event IDs are derived from a monotonic counter (_counter).
    - Hashes depend only on the four explicit event fields.
    - No randomness anywhere in this class.

    Zero lost events
    ----------------
    log_event() raises LoggingError on any failure condition instead of
    silently discarding the event. Callers must handle or propagate.

    Numeric safety
    --------------
    All float values in Event.data are sanitized before storage.
    NaN -> "NaN_DETECTED", Inf -> "Inf_DETECTED".
    Logging is never interrupted by numeric errors in the payload.

    Dependencies
    ------------
    Uses IntegrityLayer from S01 for future hash-chain verification hooks.
    The IntegrityLayer instance is held on self._integrity and is available
    for downstream verification without adding coupling here.
    """

    def __init__(self) -> None:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁEventLoggerǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁEventLoggerǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁEventLoggerǁ__init____mutmut_orig(self) -> None:
        """
        Initialise an empty EventLogger.

        No arguments. No side effects. No IO.
        """
        self._store: List[Event] = []
        self._counter: int = 0
        self._integrity: IntegrityLayer = IntegrityLayer()

    def xǁEventLoggerǁ__init____mutmut_1(self) -> None:
        """
        Initialise an empty EventLogger.

        No arguments. No side effects. No IO.
        """
        self._store: List[Event] = None
        self._counter: int = 0
        self._integrity: IntegrityLayer = IntegrityLayer()

    def xǁEventLoggerǁ__init____mutmut_2(self) -> None:
        """
        Initialise an empty EventLogger.

        No arguments. No side effects. No IO.
        """
        self._store: List[Event] = []
        self._counter: int = None
        self._integrity: IntegrityLayer = IntegrityLayer()

    def xǁEventLoggerǁ__init____mutmut_3(self) -> None:
        """
        Initialise an empty EventLogger.

        No arguments. No side effects. No IO.
        """
        self._store: List[Event] = []
        self._counter: int = 1
        self._integrity: IntegrityLayer = IntegrityLayer()

    def xǁEventLoggerǁ__init____mutmut_4(self) -> None:
        """
        Initialise an empty EventLogger.

        No arguments. No side effects. No IO.
        """
        self._store: List[Event] = []
        self._counter: int = 0
        self._integrity: IntegrityLayer = None
    
    xǁEventLoggerǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁEventLoggerǁ__init____mutmut_1': xǁEventLoggerǁ__init____mutmut_1, 
        'xǁEventLoggerǁ__init____mutmut_2': xǁEventLoggerǁ__init____mutmut_2, 
        'xǁEventLoggerǁ__init____mutmut_3': xǁEventLoggerǁ__init____mutmut_3, 
        'xǁEventLoggerǁ__init____mutmut_4': xǁEventLoggerǁ__init____mutmut_4
    }
    xǁEventLoggerǁ__init____mutmut_orig.__name__ = 'xǁEventLoggerǁ__init__'

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def log_event(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        args = [event_type, data, timestamp]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁEventLoggerǁlog_event__mutmut_orig'), object.__getattribute__(self, 'xǁEventLoggerǁlog_event__mutmut_mutants'), args, kwargs, self)

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_orig(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_1(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_2(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError(None)
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_3(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("XXevent_type must be a non-empty stringXX")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_4(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("EVENT_TYPE MUST BE A NON-EMPTY STRING")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_5(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is not None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_6(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError(None)
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_7(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("XXtimestamp must be caller-supplied; None is not permittedXX")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_8(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; none is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_9(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("TIMESTAMP MUST BE CALLER-SUPPLIED; NONE IS NOT PERMITTED")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_10(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_11(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                None
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_12(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(None)
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_13(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "XXtimestamp must be a datetime instance; got: {}XX".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_14(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "TIMESTAMP MUST BE A DATETIME INSTANCE; GOT: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_15(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(None))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_16(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter = 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_17(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter -= 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_18(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 2
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_19(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = None
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_20(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(None)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_21(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = None
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_22(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(None)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_23(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = None

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_24(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(None, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_25(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, None, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_26(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, None, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_27(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, None)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_28(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_29(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_30(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_31(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, )

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_32(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = None
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_33(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=None,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_34(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=None,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_35(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=None,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_36(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=None,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_37(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=None,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_38(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_39(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_40(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_41(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            hash=event_hash,
        )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_42(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            )
        self._store.append(event)
        return event_id

    # -----------------------------------------------------------------------
    # SECTION 6.1 -- log_event
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_event__mutmut_43(self, event_type: str, data: Dict[str, Any], timestamp: datetime) -> str:
        """
        Record one event atomically. Return the assigned event ID.

        Parameters
        ----------
        event_type : Non-empty string categorising the event.
                     Examples: DECISION, ERROR, STATE_CHANGE,
                               OOD_DETECTED, CALIBRATION_FAILED.
        data       : Arbitrary key-value payload. Float values are
                     sanitized; all other values are stored as-is.
        timestamp  : Caller-supplied datetime. Must not be None.
                     Never generated internally; required for determinism.

        Returns
        -------
        str : The event ID assigned to this event (e.g. "EVT-0000000000000001").

        Raises
        ------
        LoggingError : If event_type is empty, timestamp is None, or any
                       other invariant is violated. Never silently swallows
                       errors -- zero lost events is a hard invariant.

        Determinism: given the same counter state, event_type, data, and
        timestamp, this method always produces an identical Event record.
        """
        if not event_type:
            raise LoggingError("event_type must be a non-empty string")
        if timestamp is None:
            raise LoggingError("timestamp must be caller-supplied; None is not permitted")
        if not isinstance(timestamp, datetime):
            raise LoggingError(
                "timestamp must be a datetime instance; got: {}".format(type(timestamp))
            )

        self._counter += 1
        event_id: str = _make_event_id(self._counter)
        sanitized: Dict[str, Any] = _sanitize_data(data)
        event_hash: str = _compute_hash(event_id, event_type, timestamp, sanitized)

        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            data=sanitized,
            hash=event_hash,
        )
        self._store.append(None)
        return event_id
    
    xǁEventLoggerǁlog_event__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁEventLoggerǁlog_event__mutmut_1': xǁEventLoggerǁlog_event__mutmut_1, 
        'xǁEventLoggerǁlog_event__mutmut_2': xǁEventLoggerǁlog_event__mutmut_2, 
        'xǁEventLoggerǁlog_event__mutmut_3': xǁEventLoggerǁlog_event__mutmut_3, 
        'xǁEventLoggerǁlog_event__mutmut_4': xǁEventLoggerǁlog_event__mutmut_4, 
        'xǁEventLoggerǁlog_event__mutmut_5': xǁEventLoggerǁlog_event__mutmut_5, 
        'xǁEventLoggerǁlog_event__mutmut_6': xǁEventLoggerǁlog_event__mutmut_6, 
        'xǁEventLoggerǁlog_event__mutmut_7': xǁEventLoggerǁlog_event__mutmut_7, 
        'xǁEventLoggerǁlog_event__mutmut_8': xǁEventLoggerǁlog_event__mutmut_8, 
        'xǁEventLoggerǁlog_event__mutmut_9': xǁEventLoggerǁlog_event__mutmut_9, 
        'xǁEventLoggerǁlog_event__mutmut_10': xǁEventLoggerǁlog_event__mutmut_10, 
        'xǁEventLoggerǁlog_event__mutmut_11': xǁEventLoggerǁlog_event__mutmut_11, 
        'xǁEventLoggerǁlog_event__mutmut_12': xǁEventLoggerǁlog_event__mutmut_12, 
        'xǁEventLoggerǁlog_event__mutmut_13': xǁEventLoggerǁlog_event__mutmut_13, 
        'xǁEventLoggerǁlog_event__mutmut_14': xǁEventLoggerǁlog_event__mutmut_14, 
        'xǁEventLoggerǁlog_event__mutmut_15': xǁEventLoggerǁlog_event__mutmut_15, 
        'xǁEventLoggerǁlog_event__mutmut_16': xǁEventLoggerǁlog_event__mutmut_16, 
        'xǁEventLoggerǁlog_event__mutmut_17': xǁEventLoggerǁlog_event__mutmut_17, 
        'xǁEventLoggerǁlog_event__mutmut_18': xǁEventLoggerǁlog_event__mutmut_18, 
        'xǁEventLoggerǁlog_event__mutmut_19': xǁEventLoggerǁlog_event__mutmut_19, 
        'xǁEventLoggerǁlog_event__mutmut_20': xǁEventLoggerǁlog_event__mutmut_20, 
        'xǁEventLoggerǁlog_event__mutmut_21': xǁEventLoggerǁlog_event__mutmut_21, 
        'xǁEventLoggerǁlog_event__mutmut_22': xǁEventLoggerǁlog_event__mutmut_22, 
        'xǁEventLoggerǁlog_event__mutmut_23': xǁEventLoggerǁlog_event__mutmut_23, 
        'xǁEventLoggerǁlog_event__mutmut_24': xǁEventLoggerǁlog_event__mutmut_24, 
        'xǁEventLoggerǁlog_event__mutmut_25': xǁEventLoggerǁlog_event__mutmut_25, 
        'xǁEventLoggerǁlog_event__mutmut_26': xǁEventLoggerǁlog_event__mutmut_26, 
        'xǁEventLoggerǁlog_event__mutmut_27': xǁEventLoggerǁlog_event__mutmut_27, 
        'xǁEventLoggerǁlog_event__mutmut_28': xǁEventLoggerǁlog_event__mutmut_28, 
        'xǁEventLoggerǁlog_event__mutmut_29': xǁEventLoggerǁlog_event__mutmut_29, 
        'xǁEventLoggerǁlog_event__mutmut_30': xǁEventLoggerǁlog_event__mutmut_30, 
        'xǁEventLoggerǁlog_event__mutmut_31': xǁEventLoggerǁlog_event__mutmut_31, 
        'xǁEventLoggerǁlog_event__mutmut_32': xǁEventLoggerǁlog_event__mutmut_32, 
        'xǁEventLoggerǁlog_event__mutmut_33': xǁEventLoggerǁlog_event__mutmut_33, 
        'xǁEventLoggerǁlog_event__mutmut_34': xǁEventLoggerǁlog_event__mutmut_34, 
        'xǁEventLoggerǁlog_event__mutmut_35': xǁEventLoggerǁlog_event__mutmut_35, 
        'xǁEventLoggerǁlog_event__mutmut_36': xǁEventLoggerǁlog_event__mutmut_36, 
        'xǁEventLoggerǁlog_event__mutmut_37': xǁEventLoggerǁlog_event__mutmut_37, 
        'xǁEventLoggerǁlog_event__mutmut_38': xǁEventLoggerǁlog_event__mutmut_38, 
        'xǁEventLoggerǁlog_event__mutmut_39': xǁEventLoggerǁlog_event__mutmut_39, 
        'xǁEventLoggerǁlog_event__mutmut_40': xǁEventLoggerǁlog_event__mutmut_40, 
        'xǁEventLoggerǁlog_event__mutmut_41': xǁEventLoggerǁlog_event__mutmut_41, 
        'xǁEventLoggerǁlog_event__mutmut_42': xǁEventLoggerǁlog_event__mutmut_42, 
        'xǁEventLoggerǁlog_event__mutmut_43': xǁEventLoggerǁlog_event__mutmut_43
    }
    xǁEventLoggerǁlog_event__mutmut_orig.__name__ = 'xǁEventLoggerǁlog_event'

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def log_state_change(self, new_state: Any, timestamp: datetime) -> str:
        args = [new_state, timestamp]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁEventLoggerǁlog_state_change__mutmut_orig'), object.__getattribute__(self, 'xǁEventLoggerǁlog_state_change__mutmut_mutants'), args, kwargs, self)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_orig(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event("STATE_CHANGE", data, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_1(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is not None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event("STATE_CHANGE", data, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_2(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError(None)
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event("STATE_CHANGE", data, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_3(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("XXnew_state must not be NoneXX")
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event("STATE_CHANGE", data, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_4(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be none")
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event("STATE_CHANGE", data, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_5(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("NEW_STATE MUST NOT BE NONE")
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event("STATE_CHANGE", data, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_6(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = None
        return self.log_event("STATE_CHANGE", data, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_7(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = {"XXstate_reprXX": repr(new_state)}
        return self.log_event("STATE_CHANGE", data, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_8(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = {"STATE_REPR": repr(new_state)}
        return self.log_event("STATE_CHANGE", data, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_9(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = {"state_repr": repr(None)}
        return self.log_event("STATE_CHANGE", data, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_10(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event(None, data, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_11(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event("STATE_CHANGE", None, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_12(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event("STATE_CHANGE", data, None)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_13(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event(data, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_14(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event("STATE_CHANGE", timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_15(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event("STATE_CHANGE", data, )

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_16(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event("XXSTATE_CHANGEXX", data, timestamp)

    # -----------------------------------------------------------------------
    # SECTION 6.2 -- log_state_change
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁlog_state_change__mutmut_17(self, new_state: Any, timestamp: datetime) -> str:
        """
        Log a GlobalSystemState transition event.

        This method accepts any object as new_state to avoid importing
        jarvis.core.system_state (S05), which is not yet in the dependency
        chain for S02. The state is serialized via repr() for the payload.

        Parameters
        ----------
        new_state : GlobalSystemState instance (or any state object).
                    Stored as repr(new_state) in the event payload.
        timestamp : Caller-supplied datetime. Required; never generated here.

        Returns
        -------
        str : Event ID of the recorded STATE_CHANGE event.

        Raises
        ------
        LoggingError : If new_state is None or timestamp is invalid.
        """
        if new_state is None:
            raise LoggingError("new_state must not be None")
        data: Dict[str, Any] = {"state_repr": repr(new_state)}
        return self.log_event("state_change", data, timestamp)
    
    xǁEventLoggerǁlog_state_change__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁEventLoggerǁlog_state_change__mutmut_1': xǁEventLoggerǁlog_state_change__mutmut_1, 
        'xǁEventLoggerǁlog_state_change__mutmut_2': xǁEventLoggerǁlog_state_change__mutmut_2, 
        'xǁEventLoggerǁlog_state_change__mutmut_3': xǁEventLoggerǁlog_state_change__mutmut_3, 
        'xǁEventLoggerǁlog_state_change__mutmut_4': xǁEventLoggerǁlog_state_change__mutmut_4, 
        'xǁEventLoggerǁlog_state_change__mutmut_5': xǁEventLoggerǁlog_state_change__mutmut_5, 
        'xǁEventLoggerǁlog_state_change__mutmut_6': xǁEventLoggerǁlog_state_change__mutmut_6, 
        'xǁEventLoggerǁlog_state_change__mutmut_7': xǁEventLoggerǁlog_state_change__mutmut_7, 
        'xǁEventLoggerǁlog_state_change__mutmut_8': xǁEventLoggerǁlog_state_change__mutmut_8, 
        'xǁEventLoggerǁlog_state_change__mutmut_9': xǁEventLoggerǁlog_state_change__mutmut_9, 
        'xǁEventLoggerǁlog_state_change__mutmut_10': xǁEventLoggerǁlog_state_change__mutmut_10, 
        'xǁEventLoggerǁlog_state_change__mutmut_11': xǁEventLoggerǁlog_state_change__mutmut_11, 
        'xǁEventLoggerǁlog_state_change__mutmut_12': xǁEventLoggerǁlog_state_change__mutmut_12, 
        'xǁEventLoggerǁlog_state_change__mutmut_13': xǁEventLoggerǁlog_state_change__mutmut_13, 
        'xǁEventLoggerǁlog_state_change__mutmut_14': xǁEventLoggerǁlog_state_change__mutmut_14, 
        'xǁEventLoggerǁlog_state_change__mutmut_15': xǁEventLoggerǁlog_state_change__mutmut_15, 
        'xǁEventLoggerǁlog_state_change__mutmut_16': xǁEventLoggerǁlog_state_change__mutmut_16, 
        'xǁEventLoggerǁlog_state_change__mutmut_17': xǁEventLoggerǁlog_state_change__mutmut_17
    }
    xǁEventLoggerǁlog_state_change__mutmut_orig.__name__ = 'xǁEventLoggerǁlog_state_change'

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def query_events(self, filter: EventFilter) -> List[Event]:
        args = [filter]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁEventLoggerǁquery_events__mutmut_orig'), object.__getattribute__(self, 'xǁEventLoggerǁquery_events__mutmut_mutants'), args, kwargs, self)

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_orig(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_1(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is not None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_2(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError(None)

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_3(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("XXfilter must not be NoneXX")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_4(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be none")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_5(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("FILTER MUST NOT BE NONE")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_6(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = None
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_7(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None or event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_8(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_9(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type == filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_10(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                break
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_11(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None or event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_12(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_13(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp <= filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_14(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                break
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_15(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None or event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_16(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_17(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp >= filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_18(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                break
            results.append(event)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_19(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(None)

        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_20(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is None:
            results = results[: filter.limit]

        return results

    # -----------------------------------------------------------------------
    # SECTION 6.3 -- query_events
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁquery_events__mutmut_21(self, filter: EventFilter) -> List[Event]:
        """
        Return a list of events matching the given filter.

        Filtering is applied in this order:
            1. event_type equality check (if set)
            2. start_time lower bound (inclusive, if set)
            3. end_time upper bound (inclusive, if set)
            4. limit truncation (oldest-first, if set)

        Parameters
        ----------
        filter : EventFilter instance. All fields are optional.

        Returns
        -------
        List[Event] : Matching events in insertion order (oldest first).
                      Empty list if no events match.

        Raises
        ------
        LoggingError : If filter is None.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if filter is None:
            raise LoggingError("filter must not be None")

        results: List[Event] = []
        for event in self._store:
            if filter.event_type is not None and event.type != filter.event_type:
                continue
            if filter.start_time is not None and event.timestamp < filter.start_time:
                continue
            if filter.end_time is not None and event.timestamp > filter.end_time:
                continue
            results.append(event)

        if filter.limit is not None:
            results = None

        return results
    
    xǁEventLoggerǁquery_events__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁEventLoggerǁquery_events__mutmut_1': xǁEventLoggerǁquery_events__mutmut_1, 
        'xǁEventLoggerǁquery_events__mutmut_2': xǁEventLoggerǁquery_events__mutmut_2, 
        'xǁEventLoggerǁquery_events__mutmut_3': xǁEventLoggerǁquery_events__mutmut_3, 
        'xǁEventLoggerǁquery_events__mutmut_4': xǁEventLoggerǁquery_events__mutmut_4, 
        'xǁEventLoggerǁquery_events__mutmut_5': xǁEventLoggerǁquery_events__mutmut_5, 
        'xǁEventLoggerǁquery_events__mutmut_6': xǁEventLoggerǁquery_events__mutmut_6, 
        'xǁEventLoggerǁquery_events__mutmut_7': xǁEventLoggerǁquery_events__mutmut_7, 
        'xǁEventLoggerǁquery_events__mutmut_8': xǁEventLoggerǁquery_events__mutmut_8, 
        'xǁEventLoggerǁquery_events__mutmut_9': xǁEventLoggerǁquery_events__mutmut_9, 
        'xǁEventLoggerǁquery_events__mutmut_10': xǁEventLoggerǁquery_events__mutmut_10, 
        'xǁEventLoggerǁquery_events__mutmut_11': xǁEventLoggerǁquery_events__mutmut_11, 
        'xǁEventLoggerǁquery_events__mutmut_12': xǁEventLoggerǁquery_events__mutmut_12, 
        'xǁEventLoggerǁquery_events__mutmut_13': xǁEventLoggerǁquery_events__mutmut_13, 
        'xǁEventLoggerǁquery_events__mutmut_14': xǁEventLoggerǁquery_events__mutmut_14, 
        'xǁEventLoggerǁquery_events__mutmut_15': xǁEventLoggerǁquery_events__mutmut_15, 
        'xǁEventLoggerǁquery_events__mutmut_16': xǁEventLoggerǁquery_events__mutmut_16, 
        'xǁEventLoggerǁquery_events__mutmut_17': xǁEventLoggerǁquery_events__mutmut_17, 
        'xǁEventLoggerǁquery_events__mutmut_18': xǁEventLoggerǁquery_events__mutmut_18, 
        'xǁEventLoggerǁquery_events__mutmut_19': xǁEventLoggerǁquery_events__mutmut_19, 
        'xǁEventLoggerǁquery_events__mutmut_20': xǁEventLoggerǁquery_events__mutmut_20, 
        'xǁEventLoggerǁquery_events__mutmut_21': xǁEventLoggerǁquery_events__mutmut_21
    }
    xǁEventLoggerǁquery_events__mutmut_orig.__name__ = 'xǁEventLoggerǁquery_events'

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def get_event_stream(self, start_time: datetime) -> Iterator[Event]:
        args = [start_time]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁEventLoggerǁget_event_stream__mutmut_orig'), object.__getattribute__(self, 'xǁEventLoggerǁget_event_stream__mutmut_mutants'), args, kwargs, self)

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁget_event_stream__mutmut_orig(self, start_time: datetime) -> Iterator[Event]:
        """
        Yield events one by one in insertion order starting from start_time.

        Parameters
        ----------
        start_time : Caller-supplied datetime lower bound (inclusive).

        Yields
        ------
        Event : Each matching event in insertion order.

        Raises
        ------
        LoggingError : If start_time is None or not a datetime instance.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if start_time is None:
            raise LoggingError("start_time must be caller-supplied; None is not permitted")
        if not isinstance(start_time, datetime):
            raise LoggingError(
                "start_time must be a datetime instance; got: {}".format(type(start_time))
            )
        for event in self._store:
            if event.timestamp >= start_time:
                yield event

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁget_event_stream__mutmut_1(self, start_time: datetime) -> Iterator[Event]:
        """
        Yield events one by one in insertion order starting from start_time.

        Parameters
        ----------
        start_time : Caller-supplied datetime lower bound (inclusive).

        Yields
        ------
        Event : Each matching event in insertion order.

        Raises
        ------
        LoggingError : If start_time is None or not a datetime instance.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if start_time is not None:
            raise LoggingError("start_time must be caller-supplied; None is not permitted")
        if not isinstance(start_time, datetime):
            raise LoggingError(
                "start_time must be a datetime instance; got: {}".format(type(start_time))
            )
        for event in self._store:
            if event.timestamp >= start_time:
                yield event

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁget_event_stream__mutmut_2(self, start_time: datetime) -> Iterator[Event]:
        """
        Yield events one by one in insertion order starting from start_time.

        Parameters
        ----------
        start_time : Caller-supplied datetime lower bound (inclusive).

        Yields
        ------
        Event : Each matching event in insertion order.

        Raises
        ------
        LoggingError : If start_time is None or not a datetime instance.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if start_time is None:
            raise LoggingError(None)
        if not isinstance(start_time, datetime):
            raise LoggingError(
                "start_time must be a datetime instance; got: {}".format(type(start_time))
            )
        for event in self._store:
            if event.timestamp >= start_time:
                yield event

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁget_event_stream__mutmut_3(self, start_time: datetime) -> Iterator[Event]:
        """
        Yield events one by one in insertion order starting from start_time.

        Parameters
        ----------
        start_time : Caller-supplied datetime lower bound (inclusive).

        Yields
        ------
        Event : Each matching event in insertion order.

        Raises
        ------
        LoggingError : If start_time is None or not a datetime instance.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if start_time is None:
            raise LoggingError("XXstart_time must be caller-supplied; None is not permittedXX")
        if not isinstance(start_time, datetime):
            raise LoggingError(
                "start_time must be a datetime instance; got: {}".format(type(start_time))
            )
        for event in self._store:
            if event.timestamp >= start_time:
                yield event

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁget_event_stream__mutmut_4(self, start_time: datetime) -> Iterator[Event]:
        """
        Yield events one by one in insertion order starting from start_time.

        Parameters
        ----------
        start_time : Caller-supplied datetime lower bound (inclusive).

        Yields
        ------
        Event : Each matching event in insertion order.

        Raises
        ------
        LoggingError : If start_time is None or not a datetime instance.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if start_time is None:
            raise LoggingError("start_time must be caller-supplied; none is not permitted")
        if not isinstance(start_time, datetime):
            raise LoggingError(
                "start_time must be a datetime instance; got: {}".format(type(start_time))
            )
        for event in self._store:
            if event.timestamp >= start_time:
                yield event

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁget_event_stream__mutmut_5(self, start_time: datetime) -> Iterator[Event]:
        """
        Yield events one by one in insertion order starting from start_time.

        Parameters
        ----------
        start_time : Caller-supplied datetime lower bound (inclusive).

        Yields
        ------
        Event : Each matching event in insertion order.

        Raises
        ------
        LoggingError : If start_time is None or not a datetime instance.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if start_time is None:
            raise LoggingError("START_TIME MUST BE CALLER-SUPPLIED; NONE IS NOT PERMITTED")
        if not isinstance(start_time, datetime):
            raise LoggingError(
                "start_time must be a datetime instance; got: {}".format(type(start_time))
            )
        for event in self._store:
            if event.timestamp >= start_time:
                yield event

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁget_event_stream__mutmut_6(self, start_time: datetime) -> Iterator[Event]:
        """
        Yield events one by one in insertion order starting from start_time.

        Parameters
        ----------
        start_time : Caller-supplied datetime lower bound (inclusive).

        Yields
        ------
        Event : Each matching event in insertion order.

        Raises
        ------
        LoggingError : If start_time is None or not a datetime instance.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if start_time is None:
            raise LoggingError("start_time must be caller-supplied; None is not permitted")
        if isinstance(start_time, datetime):
            raise LoggingError(
                "start_time must be a datetime instance; got: {}".format(type(start_time))
            )
        for event in self._store:
            if event.timestamp >= start_time:
                yield event

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁget_event_stream__mutmut_7(self, start_time: datetime) -> Iterator[Event]:
        """
        Yield events one by one in insertion order starting from start_time.

        Parameters
        ----------
        start_time : Caller-supplied datetime lower bound (inclusive).

        Yields
        ------
        Event : Each matching event in insertion order.

        Raises
        ------
        LoggingError : If start_time is None or not a datetime instance.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if start_time is None:
            raise LoggingError("start_time must be caller-supplied; None is not permitted")
        if not isinstance(start_time, datetime):
            raise LoggingError(
                None
            )
        for event in self._store:
            if event.timestamp >= start_time:
                yield event

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁget_event_stream__mutmut_8(self, start_time: datetime) -> Iterator[Event]:
        """
        Yield events one by one in insertion order starting from start_time.

        Parameters
        ----------
        start_time : Caller-supplied datetime lower bound (inclusive).

        Yields
        ------
        Event : Each matching event in insertion order.

        Raises
        ------
        LoggingError : If start_time is None or not a datetime instance.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if start_time is None:
            raise LoggingError("start_time must be caller-supplied; None is not permitted")
        if not isinstance(start_time, datetime):
            raise LoggingError(
                "start_time must be a datetime instance; got: {}".format(None)
            )
        for event in self._store:
            if event.timestamp >= start_time:
                yield event

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁget_event_stream__mutmut_9(self, start_time: datetime) -> Iterator[Event]:
        """
        Yield events one by one in insertion order starting from start_time.

        Parameters
        ----------
        start_time : Caller-supplied datetime lower bound (inclusive).

        Yields
        ------
        Event : Each matching event in insertion order.

        Raises
        ------
        LoggingError : If start_time is None or not a datetime instance.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if start_time is None:
            raise LoggingError("start_time must be caller-supplied; None is not permitted")
        if not isinstance(start_time, datetime):
            raise LoggingError(
                "XXstart_time must be a datetime instance; got: {}XX".format(type(start_time))
            )
        for event in self._store:
            if event.timestamp >= start_time:
                yield event

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁget_event_stream__mutmut_10(self, start_time: datetime) -> Iterator[Event]:
        """
        Yield events one by one in insertion order starting from start_time.

        Parameters
        ----------
        start_time : Caller-supplied datetime lower bound (inclusive).

        Yields
        ------
        Event : Each matching event in insertion order.

        Raises
        ------
        LoggingError : If start_time is None or not a datetime instance.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if start_time is None:
            raise LoggingError("start_time must be caller-supplied; None is not permitted")
        if not isinstance(start_time, datetime):
            raise LoggingError(
                "START_TIME MUST BE A DATETIME INSTANCE; GOT: {}".format(type(start_time))
            )
        for event in self._store:
            if event.timestamp >= start_time:
                yield event

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁget_event_stream__mutmut_11(self, start_time: datetime) -> Iterator[Event]:
        """
        Yield events one by one in insertion order starting from start_time.

        Parameters
        ----------
        start_time : Caller-supplied datetime lower bound (inclusive).

        Yields
        ------
        Event : Each matching event in insertion order.

        Raises
        ------
        LoggingError : If start_time is None or not a datetime instance.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if start_time is None:
            raise LoggingError("start_time must be caller-supplied; None is not permitted")
        if not isinstance(start_time, datetime):
            raise LoggingError(
                "start_time must be a datetime instance; got: {}".format(type(None))
            )
        for event in self._store:
            if event.timestamp >= start_time:
                yield event

    # -----------------------------------------------------------------------
    # SECTION 6.4 -- get_event_stream
    # -----------------------------------------------------------------------

    def xǁEventLoggerǁget_event_stream__mutmut_12(self, start_time: datetime) -> Iterator[Event]:
        """
        Yield events one by one in insertion order starting from start_time.

        Parameters
        ----------
        start_time : Caller-supplied datetime lower bound (inclusive).

        Yields
        ------
        Event : Each matching event in insertion order.

        Raises
        ------
        LoggingError : If start_time is None or not a datetime instance.

        Pure read. Does not mutate _store. No IO. Deterministic.
        """
        if start_time is None:
            raise LoggingError("start_time must be caller-supplied; None is not permitted")
        if not isinstance(start_time, datetime):
            raise LoggingError(
                "start_time must be a datetime instance; got: {}".format(type(start_time))
            )
        for event in self._store:
            if event.timestamp > start_time:
                yield event
    
    xǁEventLoggerǁget_event_stream__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁEventLoggerǁget_event_stream__mutmut_1': xǁEventLoggerǁget_event_stream__mutmut_1, 
        'xǁEventLoggerǁget_event_stream__mutmut_2': xǁEventLoggerǁget_event_stream__mutmut_2, 
        'xǁEventLoggerǁget_event_stream__mutmut_3': xǁEventLoggerǁget_event_stream__mutmut_3, 
        'xǁEventLoggerǁget_event_stream__mutmut_4': xǁEventLoggerǁget_event_stream__mutmut_4, 
        'xǁEventLoggerǁget_event_stream__mutmut_5': xǁEventLoggerǁget_event_stream__mutmut_5, 
        'xǁEventLoggerǁget_event_stream__mutmut_6': xǁEventLoggerǁget_event_stream__mutmut_6, 
        'xǁEventLoggerǁget_event_stream__mutmut_7': xǁEventLoggerǁget_event_stream__mutmut_7, 
        'xǁEventLoggerǁget_event_stream__mutmut_8': xǁEventLoggerǁget_event_stream__mutmut_8, 
        'xǁEventLoggerǁget_event_stream__mutmut_9': xǁEventLoggerǁget_event_stream__mutmut_9, 
        'xǁEventLoggerǁget_event_stream__mutmut_10': xǁEventLoggerǁget_event_stream__mutmut_10, 
        'xǁEventLoggerǁget_event_stream__mutmut_11': xǁEventLoggerǁget_event_stream__mutmut_11, 
        'xǁEventLoggerǁget_event_stream__mutmut_12': xǁEventLoggerǁget_event_stream__mutmut_12
    }
    xǁEventLoggerǁget_event_stream__mutmut_orig.__name__ = 'xǁEventLoggerǁget_event_stream'

    # -----------------------------------------------------------------------
    # SECTION 6.5 -- event_count (utility)
    # -----------------------------------------------------------------------

    def event_count(self) -> int:
        """
        Return the total number of events currently stored.

        Deterministic. Pure read. No IO. No side effects.
        """
        return len(self._store)


# ===========================================================================
# SECTION 7 -- EXCEPTIONS
# ===========================================================================

class LoggingError(Exception):
    """
    Raised by EventLogger when an invariant is violated.

    Never silently swallowed. Every call site that invokes log_event()
    must either handle LoggingError or let it propagate. Silent failure
    is prohibited (zero lost events invariant).
    """
