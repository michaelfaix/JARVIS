# jarvis/core/__init__.py
# Core canonical types for the JARVIS platform.
# Authoritative import source: jarvis.core.regime

from jarvis.core.integrity_layer import IntegrityLayer
from jarvis.core.logging_layer import EventLogger, Event, EventFilter
from jarvis.core.data_layer import (
    OHLCV,
    MarketData,
    EnhancedMarketData,
    ValidationResult,
    DataCache,
    NumericalInstabilityError,
    DataQualityError,
    SequenceError,
)
from jarvis.core.feature_layer import (
    FeatureLayer,
    FeatureDriftMonitor,
    DriftResult,
    DriftSummary,
    DriftAction,
    FeatureDimensionError,
    VolatilityScalingError,
)
from jarvis.core.execution_guard import (
    build_execution_order,
    ExecutionOrder,
)
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
