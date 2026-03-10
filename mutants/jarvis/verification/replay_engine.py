# jarvis/verification/replay_engine.py
# ReplayEngine -- re-executes all vectors to produce the RE-stage records.
# Authority: DVH Implementation Blueprint v1.0.0 Sections 3 and 7.
#
# The ReplayEngine is structurally identical to the ExecutionRecorder but
# produces records with stage="RE". It uses the same InputVector list and
# the same production RiskEngine. No state is shared between ER and RE passes.
# OC-05: Production results are NOT cached or reused between ER and RE stages.

from typing import List

from jarvis.verification.data_models.input_vector import InputVector
from jarvis.verification.data_models.execution_record import ExecutionRecord
from jarvis.verification.execution_recorder import ExecutionRecorder
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


class ReplayEngine:
    """
    Re-executes all input vectors through the production Risk Engine.
    Produces RE-stage ExecutionRecords for comparison against ER-stage records.

    The ReplayEngine re-invokes the production Risk Engine fresh for every vector.
    No ER results are reused (OC-05). The production module is invoked with
    identical inputs and must produce identical outputs (DET-P-01).

    In cross-session replay mode (DIM-05/DIM-06), the ReplayEngine still executes
    all vectors normally. The loaded prior records substitute for ER records in
    the BIC stage -- the RE stage is not skipped.
    """

    def __init__(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
    ):
        args = [manifest_hash, module_version, run_id]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReplayEngineǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁReplayEngineǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁReplayEngineǁ__init____mutmut_orig(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
    ):
        self._recorder = ExecutionRecorder(
            manifest_hash=manifest_hash,
            module_version=module_version,
            run_id=run_id,
            stage="RE",
        )

    def xǁReplayEngineǁ__init____mutmut_1(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
    ):
        self._recorder = None

    def xǁReplayEngineǁ__init____mutmut_2(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
    ):
        self._recorder = ExecutionRecorder(
            manifest_hash=None,
            module_version=module_version,
            run_id=run_id,
            stage="RE",
        )

    def xǁReplayEngineǁ__init____mutmut_3(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
    ):
        self._recorder = ExecutionRecorder(
            manifest_hash=manifest_hash,
            module_version=None,
            run_id=run_id,
            stage="RE",
        )

    def xǁReplayEngineǁ__init____mutmut_4(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
    ):
        self._recorder = ExecutionRecorder(
            manifest_hash=manifest_hash,
            module_version=module_version,
            run_id=None,
            stage="RE",
        )

    def xǁReplayEngineǁ__init____mutmut_5(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
    ):
        self._recorder = ExecutionRecorder(
            manifest_hash=manifest_hash,
            module_version=module_version,
            run_id=run_id,
            stage=None,
        )

    def xǁReplayEngineǁ__init____mutmut_6(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
    ):
        self._recorder = ExecutionRecorder(
            module_version=module_version,
            run_id=run_id,
            stage="RE",
        )

    def xǁReplayEngineǁ__init____mutmut_7(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
    ):
        self._recorder = ExecutionRecorder(
            manifest_hash=manifest_hash,
            run_id=run_id,
            stage="RE",
        )

    def xǁReplayEngineǁ__init____mutmut_8(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
    ):
        self._recorder = ExecutionRecorder(
            manifest_hash=manifest_hash,
            module_version=module_version,
            stage="RE",
        )

    def xǁReplayEngineǁ__init____mutmut_9(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
    ):
        self._recorder = ExecutionRecorder(
            manifest_hash=manifest_hash,
            module_version=module_version,
            run_id=run_id,
            )

    def xǁReplayEngineǁ__init____mutmut_10(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
    ):
        self._recorder = ExecutionRecorder(
            manifest_hash=manifest_hash,
            module_version=module_version,
            run_id=run_id,
            stage="XXREXX",
        )

    def xǁReplayEngineǁ__init____mutmut_11(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
    ):
        self._recorder = ExecutionRecorder(
            manifest_hash=manifest_hash,
            module_version=module_version,
            run_id=run_id,
            stage="re",
        )
    
    xǁReplayEngineǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReplayEngineǁ__init____mutmut_1': xǁReplayEngineǁ__init____mutmut_1, 
        'xǁReplayEngineǁ__init____mutmut_2': xǁReplayEngineǁ__init____mutmut_2, 
        'xǁReplayEngineǁ__init____mutmut_3': xǁReplayEngineǁ__init____mutmut_3, 
        'xǁReplayEngineǁ__init____mutmut_4': xǁReplayEngineǁ__init____mutmut_4, 
        'xǁReplayEngineǁ__init____mutmut_5': xǁReplayEngineǁ__init____mutmut_5, 
        'xǁReplayEngineǁ__init____mutmut_6': xǁReplayEngineǁ__init____mutmut_6, 
        'xǁReplayEngineǁ__init____mutmut_7': xǁReplayEngineǁ__init____mutmut_7, 
        'xǁReplayEngineǁ__init____mutmut_8': xǁReplayEngineǁ__init____mutmut_8, 
        'xǁReplayEngineǁ__init____mutmut_9': xǁReplayEngineǁ__init____mutmut_9, 
        'xǁReplayEngineǁ__init____mutmut_10': xǁReplayEngineǁ__init____mutmut_10, 
        'xǁReplayEngineǁ__init____mutmut_11': xǁReplayEngineǁ__init____mutmut_11
    }
    xǁReplayEngineǁ__init____mutmut_orig.__name__ = 'xǁReplayEngineǁ__init__'

    def replay_all(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        args = [vectors]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁReplayEngineǁreplay_all__mutmut_orig'), object.__getattribute__(self, 'xǁReplayEngineǁreplay_all__mutmut_mutants'), args, kwargs, self)

    def xǁReplayEngineǁreplay_all__mutmut_orig(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Re-execute all vectors and return RE-stage ExecutionRecords.
        Execution order is identical to the ER stage (same vector list).
        """
        return self._recorder.record_all(vectors)

    def xǁReplayEngineǁreplay_all__mutmut_1(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Re-execute all vectors and return RE-stage ExecutionRecords.
        Execution order is identical to the ER stage (same vector list).
        """
        return self._recorder.record_all(None)
    
    xǁReplayEngineǁreplay_all__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁReplayEngineǁreplay_all__mutmut_1': xǁReplayEngineǁreplay_all__mutmut_1
    }
    xǁReplayEngineǁreplay_all__mutmut_orig.__name__ = 'xǁReplayEngineǁreplay_all'
