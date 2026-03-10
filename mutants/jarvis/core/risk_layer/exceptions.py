# =============================================================================
# JARVIS v6.1.0 -- PHASE 7: RISK & CAPITAL MANAGEMENT LAYER
# File:   jarvis/risk_layer/exceptions.py
# Authority: JARVIS FAS v6.1.0 -- Phase 7, Risk Engine
# =============================================================================
#
# SCOPE
# -----
# Defines the exception hierarchy for the Risk & Capital Management Layer.
# All exceptions are pure value objects: no side effects, no logging,
# no external references, no I/O of any kind.
#
# EXCEPTION HIERARCHY
# -------------------
#   RiskError(Exception)                         -- base; never raised directly
#     RiskNumericalError(RiskError)              -- NaN / Inf in a numeric field
#     RiskValidationError(RiskError)             -- range / sign / type violation
#     RiskParameterConsistencyError(RiskError)   -- cross-field logic violation
#
# DETERMINISM GUARANTEES
# ----------------------
# DET-01  No stochastic operations.
# DET-02  All message content is derived exclusively from constructor arguments.
# DET-03  No side effects. Exception construction is a pure value operation.
# DET-04  No module-level mutable state.
# DET-05  No datetime / time / random / uuid.
# DET-06  No file I/O, no network I/O.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No logging module
#   No numpy / scipy
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO
#   No domain imports (exceptions must remain leaf dependencies)
#
# MESSAGE CONTRACT
# ----------------
# Every exception message is:
#   - Deterministic: identical inputs -> identical message string.
#   - Explicit: field name and violating value always included.
#   - ASCII-safe: no Unicode outside the basic Latin block.
#   - Non-empty: always contains enough context to identify the violation site.
#
# =============================================================================

from __future__ import annotations

from typing import Any
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


# =============================================================================
# BASE EXCEPTION
# =============================================================================

class RiskError(Exception):
    """
    Base class for all Risk & Capital Management Layer exceptions.

    Never raised directly. Use a concrete subclass.

    Attributes:
        field_name:  Name of the offending field, or empty string if not
                     applicable (e.g. cross-field consistency errors report
                     both fields via the message instead).
        value:       The offending value at the time of validation,
                     or None if the violation is relational rather than
                     field-local.
        message:     Human-readable description of the violation.
                     Always non-empty. Always deterministic.
    """

    def __init__(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        args = [message, field_name, value]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRiskErrorǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁRiskErrorǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁRiskErrorǁ__init____mutmut_orig(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_1(
        self,
        message:    str,
        field_name: str = "XXXX",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_2(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) and not message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_3(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if isinstance(message, str) or not message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_4(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_5(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                None
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_6(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "XXRiskError: message must be a non-empty stringXX"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_7(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "riskerror: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_8(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "RISKERROR: MESSAGE MUST BE A NON-EMPTY STRING"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_9(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_10(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                None
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_11(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "XXRiskError: field_name must be a stringXX"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_12(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "riskerror: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_13(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RISKERROR: FIELD_NAME MUST BE A STRING"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_14(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(None)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_15(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = None
        self.value:      Any = value
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_16(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = None
        self.message:    str = message

    def xǁRiskErrorǁ__init____mutmut_17(
        self,
        message:    str,
        field_name: str = "",
        value:      Any = None,
    ) -> None:
        if not isinstance(message, str) or not message:
            raise ValueError(
                "RiskError: message must be a non-empty string"
            )
        if not isinstance(field_name, str):
            raise ValueError(
                "RiskError: field_name must be a string"
            )
        super().__init__(message)
        self.field_name: str = field_name
        self.value:      Any = value
        self.message:    str = None
    
    xǁRiskErrorǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRiskErrorǁ__init____mutmut_1': xǁRiskErrorǁ__init____mutmut_1, 
        'xǁRiskErrorǁ__init____mutmut_2': xǁRiskErrorǁ__init____mutmut_2, 
        'xǁRiskErrorǁ__init____mutmut_3': xǁRiskErrorǁ__init____mutmut_3, 
        'xǁRiskErrorǁ__init____mutmut_4': xǁRiskErrorǁ__init____mutmut_4, 
        'xǁRiskErrorǁ__init____mutmut_5': xǁRiskErrorǁ__init____mutmut_5, 
        'xǁRiskErrorǁ__init____mutmut_6': xǁRiskErrorǁ__init____mutmut_6, 
        'xǁRiskErrorǁ__init____mutmut_7': xǁRiskErrorǁ__init____mutmut_7, 
        'xǁRiskErrorǁ__init____mutmut_8': xǁRiskErrorǁ__init____mutmut_8, 
        'xǁRiskErrorǁ__init____mutmut_9': xǁRiskErrorǁ__init____mutmut_9, 
        'xǁRiskErrorǁ__init____mutmut_10': xǁRiskErrorǁ__init____mutmut_10, 
        'xǁRiskErrorǁ__init____mutmut_11': xǁRiskErrorǁ__init____mutmut_11, 
        'xǁRiskErrorǁ__init____mutmut_12': xǁRiskErrorǁ__init____mutmut_12, 
        'xǁRiskErrorǁ__init____mutmut_13': xǁRiskErrorǁ__init____mutmut_13, 
        'xǁRiskErrorǁ__init____mutmut_14': xǁRiskErrorǁ__init____mutmut_14, 
        'xǁRiskErrorǁ__init____mutmut_15': xǁRiskErrorǁ__init____mutmut_15, 
        'xǁRiskErrorǁ__init____mutmut_16': xǁRiskErrorǁ__init____mutmut_16, 
        'xǁRiskErrorǁ__init____mutmut_17': xǁRiskErrorǁ__init____mutmut_17
    }
    xǁRiskErrorǁ__init____mutmut_orig.__name__ = 'xǁRiskErrorǁ__init__'

    def __repr__(self) -> str:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRiskErrorǁ__repr____mutmut_orig'), object.__getattribute__(self, 'xǁRiskErrorǁ__repr____mutmut_mutants'), args, kwargs, self)

    def xǁRiskErrorǁ__repr____mutmut_orig(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(self.field_name)
            + ", value=" + repr(self.value)
            + ", message=" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_1(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(self.field_name)
            + ", value=" + repr(self.value)
            + ", message=" + repr(self.message) - ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_2(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(self.field_name)
            + ", value=" + repr(self.value)
            + ", message=" - repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_3(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(self.field_name)
            + ", value=" + repr(self.value) - ", message=" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_4(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(self.field_name)
            + ", value=" - repr(self.value)
            + ", message=" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_5(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(self.field_name) - ", value=" + repr(self.value)
            + ", message=" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_6(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" - repr(self.field_name)
            + ", value=" + repr(self.value)
            + ", message=" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_7(self) -> str:
        return (
            self.__class__.__name__ - "(field_name=" + repr(self.field_name)
            + ", value=" + repr(self.value)
            + ", message=" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_8(self) -> str:
        return (
            self.__class__.__name__
            + "XX(field_name=XX" + repr(self.field_name)
            + ", value=" + repr(self.value)
            + ", message=" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_9(self) -> str:
        return (
            self.__class__.__name__
            + "(FIELD_NAME=" + repr(self.field_name)
            + ", value=" + repr(self.value)
            + ", message=" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_10(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(None)
            + ", value=" + repr(self.value)
            + ", message=" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_11(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(self.field_name)
            + "XX, value=XX" + repr(self.value)
            + ", message=" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_12(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(self.field_name)
            + ", VALUE=" + repr(self.value)
            + ", message=" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_13(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(self.field_name)
            + ", value=" + repr(None)
            + ", message=" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_14(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(self.field_name)
            + ", value=" + repr(self.value)
            + "XX, message=XX" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_15(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(self.field_name)
            + ", value=" + repr(self.value)
            + ", MESSAGE=" + repr(self.message)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_16(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(self.field_name)
            + ", value=" + repr(self.value)
            + ", message=" + repr(None)
            + ")"
        )

    def xǁRiskErrorǁ__repr____mutmut_17(self) -> str:
        return (
            self.__class__.__name__
            + "(field_name=" + repr(self.field_name)
            + ", value=" + repr(self.value)
            + ", message=" + repr(self.message)
            + "XX)XX"
        )
    
    xǁRiskErrorǁ__repr____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRiskErrorǁ__repr____mutmut_1': xǁRiskErrorǁ__repr____mutmut_1, 
        'xǁRiskErrorǁ__repr____mutmut_2': xǁRiskErrorǁ__repr____mutmut_2, 
        'xǁRiskErrorǁ__repr____mutmut_3': xǁRiskErrorǁ__repr____mutmut_3, 
        'xǁRiskErrorǁ__repr____mutmut_4': xǁRiskErrorǁ__repr____mutmut_4, 
        'xǁRiskErrorǁ__repr____mutmut_5': xǁRiskErrorǁ__repr____mutmut_5, 
        'xǁRiskErrorǁ__repr____mutmut_6': xǁRiskErrorǁ__repr____mutmut_6, 
        'xǁRiskErrorǁ__repr____mutmut_7': xǁRiskErrorǁ__repr____mutmut_7, 
        'xǁRiskErrorǁ__repr____mutmut_8': xǁRiskErrorǁ__repr____mutmut_8, 
        'xǁRiskErrorǁ__repr____mutmut_9': xǁRiskErrorǁ__repr____mutmut_9, 
        'xǁRiskErrorǁ__repr____mutmut_10': xǁRiskErrorǁ__repr____mutmut_10, 
        'xǁRiskErrorǁ__repr____mutmut_11': xǁRiskErrorǁ__repr____mutmut_11, 
        'xǁRiskErrorǁ__repr____mutmut_12': xǁRiskErrorǁ__repr____mutmut_12, 
        'xǁRiskErrorǁ__repr____mutmut_13': xǁRiskErrorǁ__repr____mutmut_13, 
        'xǁRiskErrorǁ__repr____mutmut_14': xǁRiskErrorǁ__repr____mutmut_14, 
        'xǁRiskErrorǁ__repr____mutmut_15': xǁRiskErrorǁ__repr____mutmut_15, 
        'xǁRiskErrorǁ__repr____mutmut_16': xǁRiskErrorǁ__repr____mutmut_16, 
        'xǁRiskErrorǁ__repr____mutmut_17': xǁRiskErrorǁ__repr____mutmut_17
    }
    xǁRiskErrorǁ__repr____mutmut_orig.__name__ = 'xǁRiskErrorǁ__repr__'

    def __eq__(self, other: object) -> bool:
        args = [other]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRiskErrorǁ__eq____mutmut_orig'), object.__getattribute__(self, 'xǁRiskErrorǁ__eq____mutmut_mutants'), args, kwargs, self)

    def xǁRiskErrorǁ__eq____mutmut_orig(self, other: object) -> bool:
        if not isinstance(other, RiskError):
            return NotImplemented
        return (
            type(self) is type(other)
            and self.field_name == other.field_name
            and self.value == other.value
            and self.message == other.message
        )

    def xǁRiskErrorǁ__eq____mutmut_1(self, other: object) -> bool:
        if isinstance(other, RiskError):
            return NotImplemented
        return (
            type(self) is type(other)
            and self.field_name == other.field_name
            and self.value == other.value
            and self.message == other.message
        )

    def xǁRiskErrorǁ__eq____mutmut_2(self, other: object) -> bool:
        if not isinstance(other, RiskError):
            return NotImplemented
        return (
            type(self) is type(other)
            and self.field_name == other.field_name
            and self.value == other.value or self.message == other.message
        )

    def xǁRiskErrorǁ__eq____mutmut_3(self, other: object) -> bool:
        if not isinstance(other, RiskError):
            return NotImplemented
        return (
            type(self) is type(other)
            and self.field_name == other.field_name or self.value == other.value
            and self.message == other.message
        )

    def xǁRiskErrorǁ__eq____mutmut_4(self, other: object) -> bool:
        if not isinstance(other, RiskError):
            return NotImplemented
        return (
            type(self) is type(other) or self.field_name == other.field_name
            and self.value == other.value
            and self.message == other.message
        )

    def xǁRiskErrorǁ__eq____mutmut_5(self, other: object) -> bool:
        if not isinstance(other, RiskError):
            return NotImplemented
        return (
            type(None) is type(other)
            and self.field_name == other.field_name
            and self.value == other.value
            and self.message == other.message
        )

    def xǁRiskErrorǁ__eq____mutmut_6(self, other: object) -> bool:
        if not isinstance(other, RiskError):
            return NotImplemented
        return (
            type(self) is not type(other)
            and self.field_name == other.field_name
            and self.value == other.value
            and self.message == other.message
        )

    def xǁRiskErrorǁ__eq____mutmut_7(self, other: object) -> bool:
        if not isinstance(other, RiskError):
            return NotImplemented
        return (
            type(self) is type(None)
            and self.field_name == other.field_name
            and self.value == other.value
            and self.message == other.message
        )

    def xǁRiskErrorǁ__eq____mutmut_8(self, other: object) -> bool:
        if not isinstance(other, RiskError):
            return NotImplemented
        return (
            type(self) is type(other)
            and self.field_name != other.field_name
            and self.value == other.value
            and self.message == other.message
        )

    def xǁRiskErrorǁ__eq____mutmut_9(self, other: object) -> bool:
        if not isinstance(other, RiskError):
            return NotImplemented
        return (
            type(self) is type(other)
            and self.field_name == other.field_name
            and self.value != other.value
            and self.message == other.message
        )

    def xǁRiskErrorǁ__eq____mutmut_10(self, other: object) -> bool:
        if not isinstance(other, RiskError):
            return NotImplemented
        return (
            type(self) is type(other)
            and self.field_name == other.field_name
            and self.value == other.value
            and self.message != other.message
        )
    
    xǁRiskErrorǁ__eq____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRiskErrorǁ__eq____mutmut_1': xǁRiskErrorǁ__eq____mutmut_1, 
        'xǁRiskErrorǁ__eq____mutmut_2': xǁRiskErrorǁ__eq____mutmut_2, 
        'xǁRiskErrorǁ__eq____mutmut_3': xǁRiskErrorǁ__eq____mutmut_3, 
        'xǁRiskErrorǁ__eq____mutmut_4': xǁRiskErrorǁ__eq____mutmut_4, 
        'xǁRiskErrorǁ__eq____mutmut_5': xǁRiskErrorǁ__eq____mutmut_5, 
        'xǁRiskErrorǁ__eq____mutmut_6': xǁRiskErrorǁ__eq____mutmut_6, 
        'xǁRiskErrorǁ__eq____mutmut_7': xǁRiskErrorǁ__eq____mutmut_7, 
        'xǁRiskErrorǁ__eq____mutmut_8': xǁRiskErrorǁ__eq____mutmut_8, 
        'xǁRiskErrorǁ__eq____mutmut_9': xǁRiskErrorǁ__eq____mutmut_9, 
        'xǁRiskErrorǁ__eq____mutmut_10': xǁRiskErrorǁ__eq____mutmut_10
    }
    xǁRiskErrorǁ__eq____mutmut_orig.__name__ = 'xǁRiskErrorǁ__eq__'


# =============================================================================
# CONCRETE EXCEPTIONS
# =============================================================================

class RiskNumericalError(RiskError):
    """
    Raised when a numeric field contains NaN or Inf.

    This is the first validation gate. NaN and Inf are unconditionally
    rejected; no downstream validation, clipping, or recovery is attempted
    after this error is raised.

    Message format:
        "RiskNumericalError: field '<field_name>' contains non-finite
         value: <value>. NaN and Inf are not permitted."

    Args:
        field_name:  Name of the field that contains the non-finite value.
                     Must be a non-empty string.
        value:       The non-finite value (float NaN, float Inf, or
                     float -Inf). Stored on the exception for programmatic
                     inspection.

    Raises:
        ValueError if field_name is empty.
    """

    def __init__(self, field_name: str, value: float) -> None:
        args = [field_name, value]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRiskNumericalErrorǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁRiskNumericalErrorǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁRiskNumericalErrorǁ__init____mutmut_orig(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_1(self, field_name: str, value: float) -> None:
        if field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_2(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                None
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_3(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "XXRiskNumericalError: field_name must be a non-empty stringXX"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_4(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "risknumericalerror: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_5(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RISKNUMERICALERROR: FIELD_NAME MUST BE A NON-EMPTY STRING"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_6(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = None
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_7(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value) - ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_8(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: " - repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_9(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name - "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_10(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '" - field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_11(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "XXRiskNumericalError: field 'XX"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_12(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "risknumericalerror: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_13(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RISKNUMERICALERROR: FIELD '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_14(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "XX' contains non-finite value: XX"
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_15(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' CONTAINS NON-FINITE VALUE: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_16(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(None)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_17(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + "XX. NaN and Inf are not permitted.XX"
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_18(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". nan and inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_19(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NAN AND INF ARE NOT PERMITTED."
        )
        super().__init__(message=message, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_20(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=None, field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_21(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=None, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_22(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, value=None)

    def xǁRiskNumericalErrorǁ__init____mutmut_23(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(field_name=field_name, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_24(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, value=value)

    def xǁRiskNumericalErrorǁ__init____mutmut_25(self, field_name: str, value: float) -> None:
        if not field_name:
            raise ValueError(
                "RiskNumericalError: field_name must be a non-empty string"
            )
        message = (
            "RiskNumericalError: field '"
            + field_name
            + "' contains non-finite value: "
            + repr(value)
            + ". NaN and Inf are not permitted."
        )
        super().__init__(message=message, field_name=field_name, )
    
    xǁRiskNumericalErrorǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRiskNumericalErrorǁ__init____mutmut_1': xǁRiskNumericalErrorǁ__init____mutmut_1, 
        'xǁRiskNumericalErrorǁ__init____mutmut_2': xǁRiskNumericalErrorǁ__init____mutmut_2, 
        'xǁRiskNumericalErrorǁ__init____mutmut_3': xǁRiskNumericalErrorǁ__init____mutmut_3, 
        'xǁRiskNumericalErrorǁ__init____mutmut_4': xǁRiskNumericalErrorǁ__init____mutmut_4, 
        'xǁRiskNumericalErrorǁ__init____mutmut_5': xǁRiskNumericalErrorǁ__init____mutmut_5, 
        'xǁRiskNumericalErrorǁ__init____mutmut_6': xǁRiskNumericalErrorǁ__init____mutmut_6, 
        'xǁRiskNumericalErrorǁ__init____mutmut_7': xǁRiskNumericalErrorǁ__init____mutmut_7, 
        'xǁRiskNumericalErrorǁ__init____mutmut_8': xǁRiskNumericalErrorǁ__init____mutmut_8, 
        'xǁRiskNumericalErrorǁ__init____mutmut_9': xǁRiskNumericalErrorǁ__init____mutmut_9, 
        'xǁRiskNumericalErrorǁ__init____mutmut_10': xǁRiskNumericalErrorǁ__init____mutmut_10, 
        'xǁRiskNumericalErrorǁ__init____mutmut_11': xǁRiskNumericalErrorǁ__init____mutmut_11, 
        'xǁRiskNumericalErrorǁ__init____mutmut_12': xǁRiskNumericalErrorǁ__init____mutmut_12, 
        'xǁRiskNumericalErrorǁ__init____mutmut_13': xǁRiskNumericalErrorǁ__init____mutmut_13, 
        'xǁRiskNumericalErrorǁ__init____mutmut_14': xǁRiskNumericalErrorǁ__init____mutmut_14, 
        'xǁRiskNumericalErrorǁ__init____mutmut_15': xǁRiskNumericalErrorǁ__init____mutmut_15, 
        'xǁRiskNumericalErrorǁ__init____mutmut_16': xǁRiskNumericalErrorǁ__init____mutmut_16, 
        'xǁRiskNumericalErrorǁ__init____mutmut_17': xǁRiskNumericalErrorǁ__init____mutmut_17, 
        'xǁRiskNumericalErrorǁ__init____mutmut_18': xǁRiskNumericalErrorǁ__init____mutmut_18, 
        'xǁRiskNumericalErrorǁ__init____mutmut_19': xǁRiskNumericalErrorǁ__init____mutmut_19, 
        'xǁRiskNumericalErrorǁ__init____mutmut_20': xǁRiskNumericalErrorǁ__init____mutmut_20, 
        'xǁRiskNumericalErrorǁ__init____mutmut_21': xǁRiskNumericalErrorǁ__init____mutmut_21, 
        'xǁRiskNumericalErrorǁ__init____mutmut_22': xǁRiskNumericalErrorǁ__init____mutmut_22, 
        'xǁRiskNumericalErrorǁ__init____mutmut_23': xǁRiskNumericalErrorǁ__init____mutmut_23, 
        'xǁRiskNumericalErrorǁ__init____mutmut_24': xǁRiskNumericalErrorǁ__init____mutmut_24, 
        'xǁRiskNumericalErrorǁ__init____mutmut_25': xǁRiskNumericalErrorǁ__init____mutmut_25
    }
    xǁRiskNumericalErrorǁ__init____mutmut_orig.__name__ = 'xǁRiskNumericalErrorǁ__init__'


class RiskValidationError(RiskError):
    """
    Raised when a field value violates a range, sign, type, or membership
    constraint.

    This covers:
      - Values outside a required numeric range (e.g. pct not in [0.0, 1.0]).
      - Non-positive values where strictly positive is required.
      - Enum / set membership failures (unknown asset_class, unknown Side).
      - Integer constraint failures (e.g. open_positions < 0).

    Message format:
        "RiskValidationError: field '<field_name>' violates constraint
         '<constraint>': got <value>."

    Args:
        field_name:  Name of the offending field. Must be non-empty.
        value:       The offending value.
        constraint:  Human-readable constraint description.
                     Examples:
                       "must be > 0"
                       "must be in (0.0, 1.0]"
                       "must be in VALID_ASSET_CLASSES"
                       "must be a valid Side enum member"
                     Must be non-empty.

    Raises:
        ValueError if field_name or constraint is empty.
    """

    def __init__(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        args = [field_name, value, constraint]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRiskValidationErrorǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁRiskValidationErrorǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁRiskValidationErrorǁ__init____mutmut_orig(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_1(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_2(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                None
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_3(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "XXRiskValidationError: field_name must be a non-empty stringXX"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_4(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "riskvalidationerror: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_5(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RISKVALIDATIONERROR: FIELD_NAME MUST BE A NON-EMPTY STRING"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_6(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) and not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_7(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_8(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_9(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                None
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_10(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "XXRiskValidationError: constraint must be a non-empty stringXX"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_11(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "riskvalidationerror: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_12(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RISKVALIDATIONERROR: CONSTRAINT MUST BE A NON-EMPTY STRING"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_13(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = None
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_14(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value) - "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_15(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got " - repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_16(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint - "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_17(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '" - constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_18(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name - "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_19(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '" - field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_20(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "XXRiskValidationError: field 'XX"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_21(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "riskvalidationerror: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_22(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RISKVALIDATIONERROR: FIELD '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_23(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "XX' violates constraint 'XX"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_24(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' VIOLATES CONSTRAINT '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_25(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "XX': got XX"
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_26(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': GOT "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_27(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(None)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_28(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "XX.XX"
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_29(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=None, field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_30(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=None, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_31(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=None)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_32(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(field_name=field_name, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_33(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, value=value)
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_34(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, )
        self.constraint: str = constraint

    def xǁRiskValidationErrorǁ__init____mutmut_35(
        self,
        field_name:  str,
        value:       Any,
        constraint:  str,
    ) -> None:
        if not field_name:
            raise ValueError(
                "RiskValidationError: field_name must be a non-empty string"
            )
        if not isinstance(constraint, str) or not constraint:
            raise ValueError(
                "RiskValidationError: constraint must be a non-empty string"
            )
        message = (
            "RiskValidationError: field '"
            + field_name
            + "' violates constraint '"
            + constraint
            + "': got "
            + repr(value)
            + "."
        )
        super().__init__(message=message, field_name=field_name, value=value)
        self.constraint: str = None
    
    xǁRiskValidationErrorǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRiskValidationErrorǁ__init____mutmut_1': xǁRiskValidationErrorǁ__init____mutmut_1, 
        'xǁRiskValidationErrorǁ__init____mutmut_2': xǁRiskValidationErrorǁ__init____mutmut_2, 
        'xǁRiskValidationErrorǁ__init____mutmut_3': xǁRiskValidationErrorǁ__init____mutmut_3, 
        'xǁRiskValidationErrorǁ__init____mutmut_4': xǁRiskValidationErrorǁ__init____mutmut_4, 
        'xǁRiskValidationErrorǁ__init____mutmut_5': xǁRiskValidationErrorǁ__init____mutmut_5, 
        'xǁRiskValidationErrorǁ__init____mutmut_6': xǁRiskValidationErrorǁ__init____mutmut_6, 
        'xǁRiskValidationErrorǁ__init____mutmut_7': xǁRiskValidationErrorǁ__init____mutmut_7, 
        'xǁRiskValidationErrorǁ__init____mutmut_8': xǁRiskValidationErrorǁ__init____mutmut_8, 
        'xǁRiskValidationErrorǁ__init____mutmut_9': xǁRiskValidationErrorǁ__init____mutmut_9, 
        'xǁRiskValidationErrorǁ__init____mutmut_10': xǁRiskValidationErrorǁ__init____mutmut_10, 
        'xǁRiskValidationErrorǁ__init____mutmut_11': xǁRiskValidationErrorǁ__init____mutmut_11, 
        'xǁRiskValidationErrorǁ__init____mutmut_12': xǁRiskValidationErrorǁ__init____mutmut_12, 
        'xǁRiskValidationErrorǁ__init____mutmut_13': xǁRiskValidationErrorǁ__init____mutmut_13, 
        'xǁRiskValidationErrorǁ__init____mutmut_14': xǁRiskValidationErrorǁ__init____mutmut_14, 
        'xǁRiskValidationErrorǁ__init____mutmut_15': xǁRiskValidationErrorǁ__init____mutmut_15, 
        'xǁRiskValidationErrorǁ__init____mutmut_16': xǁRiskValidationErrorǁ__init____mutmut_16, 
        'xǁRiskValidationErrorǁ__init____mutmut_17': xǁRiskValidationErrorǁ__init____mutmut_17, 
        'xǁRiskValidationErrorǁ__init____mutmut_18': xǁRiskValidationErrorǁ__init____mutmut_18, 
        'xǁRiskValidationErrorǁ__init____mutmut_19': xǁRiskValidationErrorǁ__init____mutmut_19, 
        'xǁRiskValidationErrorǁ__init____mutmut_20': xǁRiskValidationErrorǁ__init____mutmut_20, 
        'xǁRiskValidationErrorǁ__init____mutmut_21': xǁRiskValidationErrorǁ__init____mutmut_21, 
        'xǁRiskValidationErrorǁ__init____mutmut_22': xǁRiskValidationErrorǁ__init____mutmut_22, 
        'xǁRiskValidationErrorǁ__init____mutmut_23': xǁRiskValidationErrorǁ__init____mutmut_23, 
        'xǁRiskValidationErrorǁ__init____mutmut_24': xǁRiskValidationErrorǁ__init____mutmut_24, 
        'xǁRiskValidationErrorǁ__init____mutmut_25': xǁRiskValidationErrorǁ__init____mutmut_25, 
        'xǁRiskValidationErrorǁ__init____mutmut_26': xǁRiskValidationErrorǁ__init____mutmut_26, 
        'xǁRiskValidationErrorǁ__init____mutmut_27': xǁRiskValidationErrorǁ__init____mutmut_27, 
        'xǁRiskValidationErrorǁ__init____mutmut_28': xǁRiskValidationErrorǁ__init____mutmut_28, 
        'xǁRiskValidationErrorǁ__init____mutmut_29': xǁRiskValidationErrorǁ__init____mutmut_29, 
        'xǁRiskValidationErrorǁ__init____mutmut_30': xǁRiskValidationErrorǁ__init____mutmut_30, 
        'xǁRiskValidationErrorǁ__init____mutmut_31': xǁRiskValidationErrorǁ__init____mutmut_31, 
        'xǁRiskValidationErrorǁ__init____mutmut_32': xǁRiskValidationErrorǁ__init____mutmut_32, 
        'xǁRiskValidationErrorǁ__init____mutmut_33': xǁRiskValidationErrorǁ__init____mutmut_33, 
        'xǁRiskValidationErrorǁ__init____mutmut_34': xǁRiskValidationErrorǁ__init____mutmut_34, 
        'xǁRiskValidationErrorǁ__init____mutmut_35': xǁRiskValidationErrorǁ__init____mutmut_35
    }
    xǁRiskValidationErrorǁ__init____mutmut_orig.__name__ = 'xǁRiskValidationErrorǁ__init__'


class RiskParameterConsistencyError(RiskError):
    """
    Raised when two or more fields are individually valid but together
    violate a cross-field consistency invariant.

    This covers:
      - max_drawdown_soft_warn >= max_drawdown_hard_stop
      - peak_nav < nav (portfolio state incoherence)
      - Any other relational constraint between two distinct fields.

    Message format:
        "RiskParameterConsistencyError: cross-field invariant violated --
         <invariant_description>. Field '<field_a>' = <value_a>,
         field '<field_b>' = <value_b>."

    Args:
        field_a:               Name of the first field involved.
        value_a:               Value of the first field.
        field_b:               Name of the second field involved.
        value_b:               Value of the second field.
        invariant_description: Human-readable description of the required
                               relationship between the two fields.
                               Example:
                                 "max_drawdown_soft_warn must be strictly
                                  less than max_drawdown_hard_stop"
                               Must be non-empty.

    Raises:
        ValueError if field_a, field_b, or invariant_description is empty.

    Note on field_name / value attributes:
        The base class field_name is set to field_a and value to value_a.
        field_b and value_b are available as additional attributes.
        This is a pragmatic choice: callers that handle RiskError generically
        see the primary offending field; callers that handle
        RiskParameterConsistencyError specifically can inspect both.
    """

    def __init__(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        args = [field_a, value_a, field_b, value_b, invariant_description]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRiskParameterConsistencyErrorǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁRiskParameterConsistencyErrorǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_orig(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_1(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_2(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                None
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_3(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "XXRiskParameterConsistencyError: field_a must be non-emptyXX"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_4(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "riskparameterconsistencyerror: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_5(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RISKPARAMETERCONSISTENCYERROR: FIELD_A MUST BE NON-EMPTY"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_6(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_7(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                None
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_8(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "XXRiskParameterConsistencyError: field_b must be non-emptyXX"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_9(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "riskparameterconsistencyerror: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_10(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RISKPARAMETERCONSISTENCYERROR: FIELD_B MUST BE NON-EMPTY"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_11(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) and not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_12(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_13(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_14(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                None
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_15(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "XXRiskParameterConsistencyError: invariant_description must be non-emptyXX"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_16(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "riskparameterconsistencyerror: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_17(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RISKPARAMETERCONSISTENCYERROR: INVARIANT_DESCRIPTION MUST BE NON-EMPTY"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_18(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = None
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_19(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b) - "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_20(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = " - repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_21(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b - "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_22(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '" - field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_23(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a) - ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_24(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = " - repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_25(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a - "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_26(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '" - field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_27(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description - ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_28(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- " - invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_29(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "XXRiskParameterConsistencyError: cross-field invariant violated -- XX"
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_30(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "riskparameterconsistencyerror: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_31(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RISKPARAMETERCONSISTENCYERROR: CROSS-FIELD INVARIANT VIOLATED -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_32(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + "XX. Field 'XX"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_33(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_34(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". FIELD '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_35(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "XX' = XX"
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_36(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(None)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_37(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + "XX, field 'XX"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_38(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", FIELD '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_39(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "XX' = XX"
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_40(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(None)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_41(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "XX.XX"
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_42(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=None, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_43(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=None, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_44(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=None)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_45(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_46(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_47(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, )
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_48(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = None
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_49(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = None
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_50(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = None
        self.value_b:               Any = value_b
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_51(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = None
        self.invariant_description: str = invariant_description

    def xǁRiskParameterConsistencyErrorǁ__init____mutmut_52(
        self,
        field_a:               str,
        value_a:               Any,
        field_b:               str,
        value_b:               Any,
        invariant_description: str,
    ) -> None:
        if not field_a:
            raise ValueError(
                "RiskParameterConsistencyError: field_a must be non-empty"
            )
        if not field_b:
            raise ValueError(
                "RiskParameterConsistencyError: field_b must be non-empty"
            )
        if not isinstance(invariant_description, str) or not invariant_description:
            raise ValueError(
                "RiskParameterConsistencyError: invariant_description must be non-empty"
            )
        message = (
            "RiskParameterConsistencyError: cross-field invariant violated -- "
            + invariant_description
            + ". Field '"
            + field_a
            + "' = "
            + repr(value_a)
            + ", field '"
            + field_b
            + "' = "
            + repr(value_b)
            + "."
        )
        super().__init__(message=message, field_name=field_a, value=value_a)
        self.field_a:               str = field_a
        self.value_a:               Any = value_a
        self.field_b:               str = field_b
        self.value_b:               Any = value_b
        self.invariant_description: str = None
    
    xǁRiskParameterConsistencyErrorǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRiskParameterConsistencyErrorǁ__init____mutmut_1': xǁRiskParameterConsistencyErrorǁ__init____mutmut_1, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_2': xǁRiskParameterConsistencyErrorǁ__init____mutmut_2, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_3': xǁRiskParameterConsistencyErrorǁ__init____mutmut_3, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_4': xǁRiskParameterConsistencyErrorǁ__init____mutmut_4, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_5': xǁRiskParameterConsistencyErrorǁ__init____mutmut_5, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_6': xǁRiskParameterConsistencyErrorǁ__init____mutmut_6, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_7': xǁRiskParameterConsistencyErrorǁ__init____mutmut_7, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_8': xǁRiskParameterConsistencyErrorǁ__init____mutmut_8, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_9': xǁRiskParameterConsistencyErrorǁ__init____mutmut_9, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_10': xǁRiskParameterConsistencyErrorǁ__init____mutmut_10, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_11': xǁRiskParameterConsistencyErrorǁ__init____mutmut_11, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_12': xǁRiskParameterConsistencyErrorǁ__init____mutmut_12, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_13': xǁRiskParameterConsistencyErrorǁ__init____mutmut_13, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_14': xǁRiskParameterConsistencyErrorǁ__init____mutmut_14, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_15': xǁRiskParameterConsistencyErrorǁ__init____mutmut_15, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_16': xǁRiskParameterConsistencyErrorǁ__init____mutmut_16, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_17': xǁRiskParameterConsistencyErrorǁ__init____mutmut_17, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_18': xǁRiskParameterConsistencyErrorǁ__init____mutmut_18, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_19': xǁRiskParameterConsistencyErrorǁ__init____mutmut_19, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_20': xǁRiskParameterConsistencyErrorǁ__init____mutmut_20, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_21': xǁRiskParameterConsistencyErrorǁ__init____mutmut_21, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_22': xǁRiskParameterConsistencyErrorǁ__init____mutmut_22, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_23': xǁRiskParameterConsistencyErrorǁ__init____mutmut_23, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_24': xǁRiskParameterConsistencyErrorǁ__init____mutmut_24, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_25': xǁRiskParameterConsistencyErrorǁ__init____mutmut_25, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_26': xǁRiskParameterConsistencyErrorǁ__init____mutmut_26, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_27': xǁRiskParameterConsistencyErrorǁ__init____mutmut_27, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_28': xǁRiskParameterConsistencyErrorǁ__init____mutmut_28, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_29': xǁRiskParameterConsistencyErrorǁ__init____mutmut_29, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_30': xǁRiskParameterConsistencyErrorǁ__init____mutmut_30, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_31': xǁRiskParameterConsistencyErrorǁ__init____mutmut_31, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_32': xǁRiskParameterConsistencyErrorǁ__init____mutmut_32, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_33': xǁRiskParameterConsistencyErrorǁ__init____mutmut_33, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_34': xǁRiskParameterConsistencyErrorǁ__init____mutmut_34, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_35': xǁRiskParameterConsistencyErrorǁ__init____mutmut_35, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_36': xǁRiskParameterConsistencyErrorǁ__init____mutmut_36, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_37': xǁRiskParameterConsistencyErrorǁ__init____mutmut_37, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_38': xǁRiskParameterConsistencyErrorǁ__init____mutmut_38, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_39': xǁRiskParameterConsistencyErrorǁ__init____mutmut_39, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_40': xǁRiskParameterConsistencyErrorǁ__init____mutmut_40, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_41': xǁRiskParameterConsistencyErrorǁ__init____mutmut_41, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_42': xǁRiskParameterConsistencyErrorǁ__init____mutmut_42, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_43': xǁRiskParameterConsistencyErrorǁ__init____mutmut_43, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_44': xǁRiskParameterConsistencyErrorǁ__init____mutmut_44, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_45': xǁRiskParameterConsistencyErrorǁ__init____mutmut_45, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_46': xǁRiskParameterConsistencyErrorǁ__init____mutmut_46, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_47': xǁRiskParameterConsistencyErrorǁ__init____mutmut_47, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_48': xǁRiskParameterConsistencyErrorǁ__init____mutmut_48, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_49': xǁRiskParameterConsistencyErrorǁ__init____mutmut_49, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_50': xǁRiskParameterConsistencyErrorǁ__init____mutmut_50, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_51': xǁRiskParameterConsistencyErrorǁ__init____mutmut_51, 
        'xǁRiskParameterConsistencyErrorǁ__init____mutmut_52': xǁRiskParameterConsistencyErrorǁ__init____mutmut_52
    }
    xǁRiskParameterConsistencyErrorǁ__init____mutmut_orig.__name__ = 'xǁRiskParameterConsistencyErrorǁ__init__'

    def __repr__(self) -> str:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_orig'), object.__getattribute__(self, 'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_mutants'), args, kwargs, self)

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_orig(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_1(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description) - ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_2(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" - repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_3(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b) - ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_4(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" - repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_5(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b) - ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_6(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" - repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_7(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a) - ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_8(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" - repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_9(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a) - ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_10(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" - repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_11(self) -> str:
        return (
            "RiskParameterConsistencyError(" - "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_12(self) -> str:
        return (
            "XXRiskParameterConsistencyError(XX"
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_13(self) -> str:
        return (
            "riskparameterconsistencyerror("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_14(self) -> str:
        return (
            "RISKPARAMETERCONSISTENCYERROR("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_15(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "XXfield_a=XX" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_16(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "FIELD_A=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_17(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(None)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_18(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + "XX, value_a=XX" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_19(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", VALUE_A=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_20(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(None)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_21(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + "XX, field_b=XX" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_22(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", FIELD_B=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_23(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(None)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_24(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + "XX, value_b=XX" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_25(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", VALUE_B=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_26(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(None)
            + ", invariant_description=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_27(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + "XX, invariant_description=XX" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_28(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", INVARIANT_DESCRIPTION=" + repr(self.invariant_description)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_29(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(None)
            + ")"
        )

    def xǁRiskParameterConsistencyErrorǁ__repr____mutmut_30(self) -> str:
        return (
            "RiskParameterConsistencyError("
            + "field_a=" + repr(self.field_a)
            + ", value_a=" + repr(self.value_a)
            + ", field_b=" + repr(self.field_b)
            + ", value_b=" + repr(self.value_b)
            + ", invariant_description=" + repr(self.invariant_description)
            + "XX)XX"
        )
    
    xǁRiskParameterConsistencyErrorǁ__repr____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_1': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_1, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_2': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_2, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_3': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_3, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_4': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_4, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_5': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_5, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_6': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_6, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_7': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_7, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_8': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_8, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_9': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_9, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_10': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_10, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_11': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_11, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_12': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_12, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_13': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_13, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_14': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_14, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_15': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_15, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_16': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_16, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_17': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_17, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_18': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_18, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_19': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_19, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_20': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_20, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_21': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_21, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_22': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_22, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_23': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_23, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_24': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_24, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_25': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_25, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_26': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_26, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_27': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_27, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_28': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_28, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_29': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_29, 
        'xǁRiskParameterConsistencyErrorǁ__repr____mutmut_30': xǁRiskParameterConsistencyErrorǁ__repr____mutmut_30
    }
    xǁRiskParameterConsistencyErrorǁ__repr____mutmut_orig.__name__ = 'xǁRiskParameterConsistencyErrorǁ__repr__'

    def __eq__(self, other: object) -> bool:
        args = [other]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRiskParameterConsistencyErrorǁ__eq____mutmut_orig'), object.__getattribute__(self, 'xǁRiskParameterConsistencyErrorǁ__eq____mutmut_mutants'), args, kwargs, self)

    def xǁRiskParameterConsistencyErrorǁ__eq____mutmut_orig(self, other: object) -> bool:
        if not isinstance(other, RiskParameterConsistencyError):
            return NotImplemented
        return (
            self.field_a               == other.field_a
            and self.value_a           == other.value_a
            and self.field_b           == other.field_b
            and self.value_b           == other.value_b
            and self.invariant_description == other.invariant_description
        )

    def xǁRiskParameterConsistencyErrorǁ__eq____mutmut_1(self, other: object) -> bool:
        if isinstance(other, RiskParameterConsistencyError):
            return NotImplemented
        return (
            self.field_a               == other.field_a
            and self.value_a           == other.value_a
            and self.field_b           == other.field_b
            and self.value_b           == other.value_b
            and self.invariant_description == other.invariant_description
        )

    def xǁRiskParameterConsistencyErrorǁ__eq____mutmut_2(self, other: object) -> bool:
        if not isinstance(other, RiskParameterConsistencyError):
            return NotImplemented
        return (
            self.field_a               == other.field_a
            and self.value_a           == other.value_a
            and self.field_b           == other.field_b
            and self.value_b           == other.value_b or self.invariant_description == other.invariant_description
        )

    def xǁRiskParameterConsistencyErrorǁ__eq____mutmut_3(self, other: object) -> bool:
        if not isinstance(other, RiskParameterConsistencyError):
            return NotImplemented
        return (
            self.field_a               == other.field_a
            and self.value_a           == other.value_a
            and self.field_b           == other.field_b or self.value_b           == other.value_b
            and self.invariant_description == other.invariant_description
        )

    def xǁRiskParameterConsistencyErrorǁ__eq____mutmut_4(self, other: object) -> bool:
        if not isinstance(other, RiskParameterConsistencyError):
            return NotImplemented
        return (
            self.field_a               == other.field_a
            and self.value_a           == other.value_a or self.field_b           == other.field_b
            and self.value_b           == other.value_b
            and self.invariant_description == other.invariant_description
        )

    def xǁRiskParameterConsistencyErrorǁ__eq____mutmut_5(self, other: object) -> bool:
        if not isinstance(other, RiskParameterConsistencyError):
            return NotImplemented
        return (
            self.field_a               == other.field_a or self.value_a           == other.value_a
            and self.field_b           == other.field_b
            and self.value_b           == other.value_b
            and self.invariant_description == other.invariant_description
        )

    def xǁRiskParameterConsistencyErrorǁ__eq____mutmut_6(self, other: object) -> bool:
        if not isinstance(other, RiskParameterConsistencyError):
            return NotImplemented
        return (
            self.field_a != other.field_a
            and self.value_a           == other.value_a
            and self.field_b           == other.field_b
            and self.value_b           == other.value_b
            and self.invariant_description == other.invariant_description
        )

    def xǁRiskParameterConsistencyErrorǁ__eq____mutmut_7(self, other: object) -> bool:
        if not isinstance(other, RiskParameterConsistencyError):
            return NotImplemented
        return (
            self.field_a               == other.field_a
            and self.value_a != other.value_a
            and self.field_b           == other.field_b
            and self.value_b           == other.value_b
            and self.invariant_description == other.invariant_description
        )

    def xǁRiskParameterConsistencyErrorǁ__eq____mutmut_8(self, other: object) -> bool:
        if not isinstance(other, RiskParameterConsistencyError):
            return NotImplemented
        return (
            self.field_a               == other.field_a
            and self.value_a           == other.value_a
            and self.field_b != other.field_b
            and self.value_b           == other.value_b
            and self.invariant_description == other.invariant_description
        )

    def xǁRiskParameterConsistencyErrorǁ__eq____mutmut_9(self, other: object) -> bool:
        if not isinstance(other, RiskParameterConsistencyError):
            return NotImplemented
        return (
            self.field_a               == other.field_a
            and self.value_a           == other.value_a
            and self.field_b           == other.field_b
            and self.value_b != other.value_b
            and self.invariant_description == other.invariant_description
        )

    def xǁRiskParameterConsistencyErrorǁ__eq____mutmut_10(self, other: object) -> bool:
        if not isinstance(other, RiskParameterConsistencyError):
            return NotImplemented
        return (
            self.field_a               == other.field_a
            and self.value_a           == other.value_a
            and self.field_b           == other.field_b
            and self.value_b           == other.value_b
            and self.invariant_description != other.invariant_description
        )
    
    xǁRiskParameterConsistencyErrorǁ__eq____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRiskParameterConsistencyErrorǁ__eq____mutmut_1': xǁRiskParameterConsistencyErrorǁ__eq____mutmut_1, 
        'xǁRiskParameterConsistencyErrorǁ__eq____mutmut_2': xǁRiskParameterConsistencyErrorǁ__eq____mutmut_2, 
        'xǁRiskParameterConsistencyErrorǁ__eq____mutmut_3': xǁRiskParameterConsistencyErrorǁ__eq____mutmut_3, 
        'xǁRiskParameterConsistencyErrorǁ__eq____mutmut_4': xǁRiskParameterConsistencyErrorǁ__eq____mutmut_4, 
        'xǁRiskParameterConsistencyErrorǁ__eq____mutmut_5': xǁRiskParameterConsistencyErrorǁ__eq____mutmut_5, 
        'xǁRiskParameterConsistencyErrorǁ__eq____mutmut_6': xǁRiskParameterConsistencyErrorǁ__eq____mutmut_6, 
        'xǁRiskParameterConsistencyErrorǁ__eq____mutmut_7': xǁRiskParameterConsistencyErrorǁ__eq____mutmut_7, 
        'xǁRiskParameterConsistencyErrorǁ__eq____mutmut_8': xǁRiskParameterConsistencyErrorǁ__eq____mutmut_8, 
        'xǁRiskParameterConsistencyErrorǁ__eq____mutmut_9': xǁRiskParameterConsistencyErrorǁ__eq____mutmut_9, 
        'xǁRiskParameterConsistencyErrorǁ__eq____mutmut_10': xǁRiskParameterConsistencyErrorǁ__eq____mutmut_10
    }
    xǁRiskParameterConsistencyErrorǁ__eq____mutmut_orig.__name__ = 'xǁRiskParameterConsistencyErrorǁ__eq__'


# =============================================================================
# MODULE __all__
# =============================================================================

__all__ = [
    "RiskError",
    "RiskNumericalError",
    "RiskValidationError",
    "RiskParameterConsistencyError",
]
