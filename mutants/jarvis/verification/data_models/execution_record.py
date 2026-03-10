# jarvis/verification/data_models/execution_record.py
# ExecutionRecord and ObservedOutput data classes.
# Conform to Section 8 of DVH Implementation Blueprint v1.0.0.

from dataclasses import dataclass
from typing import Optional

from jarvis.verification.data_models.input_vector import InputVector
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
class ObservedOutput:
    """
    Observed output from one invocation of RiskEngine.assess().
    All nine fields are mandatory (BIC-C-01).

    Fields correspond to the seven RiskOutput fields plus exception metadata.
    When exception_raised is True, all float fields are set to 0.0 and
    string fields to empty string. Boolean fields are False.

    Nine fields (BIC-C-01):
      expected_drawdown       -- RiskOutput.expected_drawdown
      expected_drawdown_p95   -- RiskOutput.expected_drawdown_p95
      volatility_forecast     -- RiskOutput.volatility_forecast
      risk_compression_active -- RiskOutput.risk_compression_active
      position_size_factor    -- RiskOutput.position_size_factor
      exposure_weight         -- RiskOutput.exposure_weight
      risk_regime             -- RiskOutput.risk_regime
      exception_raised        -- True if assess() raised an exception.
      exception_type          -- Exception type name if raised; empty string otherwise.
    """
    expected_drawdown:       float
    expected_drawdown_p95:   float
    volatility_forecast:     float
    risk_compression_active: bool
    position_size_factor:    float
    exposure_weight:         float
    risk_regime:             str
    exception_raised:        bool
    exception_type:          str


@dataclass(frozen=True)
class ExecutionRecord:
    """
    Complete record for one input vector execution in the harness pipeline.
    Produced by ExecutionRecorder and ReplayEngine.
    All fields are mandatory (Section 8.3).

    Fields:
      vector_id         -- Matches InputVector.vector_id.
      group_id          -- Matches InputVector.group_id.
      input_vector      -- The InputVector that produced this record.
      observed_output   -- The ObservedOutput from the production module.
      stage             -- "ER" for initial execution; "RE" for replay.
      manifest_hash     -- Manifest hash observed by ManifestValidator at run start.
      timestamp_iso     -- UTC ISO-8601 timestamp at record creation (audit only).
      execution_id      -- UUID4 unique identifier for this record (traceability).
      harness_version   -- HARNESS_VERSION constant at time of execution.
      module_version    -- --module-version CLI argument for this run.
    """
    vector_id:       str
    group_id:        str
    input_vector:    InputVector
    observed_output: ObservedOutput
    stage:           str
    manifest_hash:   str
    timestamp_iso:   str
    execution_id:    str
    harness_version: str
    module_version:  str
