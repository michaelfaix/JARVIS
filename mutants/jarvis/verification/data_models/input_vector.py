# jarvis/verification/data_models/input_vector.py
# InputVector data class for the Deterministic Verification Harness.
# Fields conform to Section 8.1 of DVH Implementation Blueprint v1.0.0.

from dataclasses import dataclass
from typing import Optional

from jarvis.core.regime import GlobalRegimeState, CorrelationRegimeState
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
class InputVector:
    """
    A single immutable input vector for the Deterministic Verification Harness.

    Each InputVector corresponds to one invocation of RiskEngine.assess().
    The matrix is version-controlled and fully deterministic (Section 7).

    Fields:
      vector_id          -- Unique identifier for this vector (e.g., "VOL-01").
      group_id           -- Group to which this vector belongs
                            (G-VOL, G-DD, G-MU, G-RP, G-JM, G-CR, G-BC, G-EX).
      returns_history    -- Returns tuple passed to assess().
      current_regime_str -- String value of GlobalRegimeState (e.g., "RISK_ON").
                            Stored as string for serialization; converted to
                            GlobalRegimeState instance before assess() invocation.
      meta_uncertainty   -- meta_uncertainty float passed to assess().
      macro_regime       -- Optional GlobalRegimeState instance for JRM.
                            Must be a canonical enum from jarvis.core.regime.
                            None when JRM is inactive for this vector.
      correlation_regime -- Optional CorrelationRegimeState instance for JRM.
                            Must be a canonical enum from jarvis.core.regime.
                            None when JRM is inactive for this vector.
      realized_vol       -- Optional float for vol scaling.
      target_vol         -- Optional float for vol scaling.
      regime_posterior   -- Optional float for posterior confidence.
      expect_exception   -- If True, assess() is expected to raise ValueError.
      description        -- Human-readable description of what this vector tests.
    """
    vector_id:          str
    group_id:           str
    returns_history:    tuple                          # tuple of float, immutable
    current_regime_str: str
    meta_uncertainty:   float
    macro_regime:       Optional[GlobalRegimeState]    # canonical enum or None
    correlation_regime: Optional[CorrelationRegimeState]  # canonical enum or None
    realized_vol:       Optional[float]
    target_vol:         Optional[float]
    regime_posterior:   Optional[float]
    expect_exception:   bool
    description:        str
