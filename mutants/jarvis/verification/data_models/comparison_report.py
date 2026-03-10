# jarvis/verification/data_models/comparison_report.py
# ComparisonReport data class for BIC and CCV output.

from dataclasses import dataclass
from typing import List, Optional
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


@dataclass(frozen=True)
class FieldMismatch:
    """
    Record of a single field mismatch detected by the bit comparator.
    """
    vector_id:    str
    field_name:   str
    er_value_hex: str    # hex representation of ER-stage value
    re_value_hex: str    # hex representation of RE-stage value
    failure_type: str    # e.g., DETERMINISM_BREACH, BACKWARD_COMPAT_VIOLATION


@dataclass(frozen=True)
class ComparisonReport:
    """
    Full comparison report produced after BIC and CCV complete.

    Fields:
      passed          -- True iff all comparisons passed with zero failures.
      total_vectors   -- Number of vector pairs compared.
      mismatches      -- List of FieldMismatch records. Empty on pass.
      clip_violations -- List of clip-chain violation description strings.
      notes           -- Any non-failure informational notes.
    """
    passed:          bool
    total_vectors:   int
    mismatches:      tuple    # tuple of FieldMismatch, immutable
    clip_violations: tuple    # tuple of str, immutable
    notes:           tuple    # tuple of str, immutable
