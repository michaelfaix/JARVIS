# jarvis/verification/__init__.py
# Deterministic Verification Harness for Risk Engine FAS v6.1.0.
# Harness Version: 1.0.0
# Authority: DVH Implementation Blueprint v1.0.0 | DVH Architecture v1.0.0
#
# DEPLOYMENT RESTRICTION (DIM-01):
#   This package is excluded from the production runtime build.
#   No production import chain may import any module from jarvis.verification.
#   The harness is a development and verification dependency only.
#
# ENTRY POINT (API-01 through API-03):
#   python -m jarvis.verification.run_harness --manifest-path [path]
#       --module-version 6.1.0 --runs-dir [path]
#
# CI GATE:
#   python -m jarvis.verification.ci_dvh_gate

from .harness_version import (
    HARNESS_VERSION,
    EXPECTED_MODULE_VERSION,
    STORAGE_FORMAT_VERSION,
)
from .bit_comparator import BitComparator
from .clip_verifier import ClipVerifier
from .execution_recorder import ExecutionRecorder
from .failure_handler import FailureHandler
from .input_vector_generator import InputVectorGenerator
from .manifest_validator import ManifestValidator
from .replay_engine import ReplayEngine
from .ci_dvh_gate import main as run_ci_gate
from .run_harness import main as run_harness

__all__ = [
    # Version constants
    "HARNESS_VERSION",
    "EXPECTED_MODULE_VERSION",
    "STORAGE_FORMAT_VERSION",
    # Pipeline components
    "BitComparator",
    "ClipVerifier",
    "ExecutionRecorder",
    "FailureHandler",
    "InputVectorGenerator",
    "ManifestValidator",
    "ReplayEngine",
    # Entry points
    "run_ci_gate",
    "run_harness",
]
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
