# jarvis/verification/execution_recorder.py
# ExecutionRecorder -- invokes the production Risk Engine and records results.
# Authority: DVH Implementation Blueprint v1.0.0 Section 8.
#
# NIC-06: No mock, stub, or test double is injected into the production path.
# NIC-09: No introspection or bytecode manipulation is used.
# NIC-10: Exceptions from the production module propagate naturally and are
#         observed through standard exception handling at the call site.
# EEP-01: Single-threaded. Each invocation completes before the next begins.
# EEP-02: Production Risk Engine is invoked synchronously.

import uuid
from datetime import datetime, timezone
from typing import List, Dict

from jarvis.risk.risk_engine import RiskEngine
from jarvis.core.regime import GlobalRegimeState
from jarvis.verification.data_models.input_vector import InputVector
from jarvis.verification.data_models.execution_record import ExecutionRecord, ObservedOutput
from jarvis.verification.harness_version import HARNESS_VERSION
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


def _now_iso() -> str:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__now_iso__mutmut_orig, x__now_iso__mutmut_mutants, args, kwargs, None)


def x__now_iso__mutmut_orig() -> str:
    """Return current UTC time as ISO-8601 string. For audit timestamps only."""
    return datetime.now(timezone.utc).isoformat()


def x__now_iso__mutmut_1() -> str:
    """Return current UTC time as ISO-8601 string. For audit timestamps only."""
    return datetime.now(None).isoformat()

x__now_iso__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__now_iso__mutmut_1': x__now_iso__mutmut_1
}
x__now_iso__mutmut_orig.__name__ = 'x__now_iso'


def _regime_from_string(regime_str: str) -> GlobalRegimeState:
    args = [regime_str]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__regime_from_string__mutmut_orig, x__regime_from_string__mutmut_mutants, args, kwargs, None)


def x__regime_from_string__mutmut_orig(regime_str: str) -> GlobalRegimeState:
    """Map regime string to GlobalRegimeState. Raises ValueError on unknown string."""
    try:
        return GlobalRegimeState(regime_str)
    except ValueError:
        raise ValueError(
            f"CONTRACT_VIOLATION: Unknown GlobalRegimeState string: '{regime_str}'"
        )


def x__regime_from_string__mutmut_1(regime_str: str) -> GlobalRegimeState:
    """Map regime string to GlobalRegimeState. Raises ValueError on unknown string."""
    try:
        return GlobalRegimeState(None)
    except ValueError:
        raise ValueError(
            f"CONTRACT_VIOLATION: Unknown GlobalRegimeState string: '{regime_str}'"
        )


def x__regime_from_string__mutmut_2(regime_str: str) -> GlobalRegimeState:
    """Map regime string to GlobalRegimeState. Raises ValueError on unknown string."""
    try:
        return GlobalRegimeState(regime_str)
    except ValueError:
        raise ValueError(
            None
        )

x__regime_from_string__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__regime_from_string__mutmut_1': x__regime_from_string__mutmut_1, 
    'x__regime_from_string__mutmut_2': x__regime_from_string__mutmut_2
}
x__regime_from_string__mutmut_orig.__name__ = 'x__regime_from_string'


class ExecutionRecorder:
    """
    Invokes the production RiskEngine for each InputVector and records results.

    For each vector:
      - If vector.expect_exception is False: invokes assess(), records output.
      - If vector.expect_exception is True: invokes assess(), expects ValueError.
        If ValueError is raised: records exception_raised=True.
        If no exception or wrong exception: raises RuntimeError for FailureHandler.

    The production module is not wrapped, decorated, or instrumented (NIC-01).
    All inputs to RiskEngine are of production types and values (NIC-02).
    """

    def __init__(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
        stage:          str = "ER",
    ):
        args = [manifest_hash, module_version, run_id, stage]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁExecutionRecorderǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁExecutionRecorderǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁExecutionRecorderǁ__init____mutmut_orig(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
        stage:          str = "ER",
    ):
        self._manifest_hash  = manifest_hash
        self._module_version = module_version
        self._run_id         = run_id
        self._stage          = stage
        self._engine         = RiskEngine()

    def xǁExecutionRecorderǁ__init____mutmut_1(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
        stage:          str = "XXERXX",
    ):
        self._manifest_hash  = manifest_hash
        self._module_version = module_version
        self._run_id         = run_id
        self._stage          = stage
        self._engine         = RiskEngine()

    def xǁExecutionRecorderǁ__init____mutmut_2(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
        stage:          str = "er",
    ):
        self._manifest_hash  = manifest_hash
        self._module_version = module_version
        self._run_id         = run_id
        self._stage          = stage
        self._engine         = RiskEngine()

    def xǁExecutionRecorderǁ__init____mutmut_3(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
        stage:          str = "ER",
    ):
        self._manifest_hash  = None
        self._module_version = module_version
        self._run_id         = run_id
        self._stage          = stage
        self._engine         = RiskEngine()

    def xǁExecutionRecorderǁ__init____mutmut_4(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
        stage:          str = "ER",
    ):
        self._manifest_hash  = manifest_hash
        self._module_version = None
        self._run_id         = run_id
        self._stage          = stage
        self._engine         = RiskEngine()

    def xǁExecutionRecorderǁ__init____mutmut_5(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
        stage:          str = "ER",
    ):
        self._manifest_hash  = manifest_hash
        self._module_version = module_version
        self._run_id         = None
        self._stage          = stage
        self._engine         = RiskEngine()

    def xǁExecutionRecorderǁ__init____mutmut_6(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
        stage:          str = "ER",
    ):
        self._manifest_hash  = manifest_hash
        self._module_version = module_version
        self._run_id         = run_id
        self._stage          = None
        self._engine         = RiskEngine()

    def xǁExecutionRecorderǁ__init____mutmut_7(
        self,
        manifest_hash:  str,
        module_version: str,
        run_id:         str,
        stage:          str = "ER",
    ):
        self._manifest_hash  = manifest_hash
        self._module_version = module_version
        self._run_id         = run_id
        self._stage          = stage
        self._engine         = None
    
    xǁExecutionRecorderǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁExecutionRecorderǁ__init____mutmut_1': xǁExecutionRecorderǁ__init____mutmut_1, 
        'xǁExecutionRecorderǁ__init____mutmut_2': xǁExecutionRecorderǁ__init____mutmut_2, 
        'xǁExecutionRecorderǁ__init____mutmut_3': xǁExecutionRecorderǁ__init____mutmut_3, 
        'xǁExecutionRecorderǁ__init____mutmut_4': xǁExecutionRecorderǁ__init____mutmut_4, 
        'xǁExecutionRecorderǁ__init____mutmut_5': xǁExecutionRecorderǁ__init____mutmut_5, 
        'xǁExecutionRecorderǁ__init____mutmut_6': xǁExecutionRecorderǁ__init____mutmut_6, 
        'xǁExecutionRecorderǁ__init____mutmut_7': xǁExecutionRecorderǁ__init____mutmut_7
    }
    xǁExecutionRecorderǁ__init____mutmut_orig.__name__ = 'xǁExecutionRecorderǁ__init__'

    def _invoke(self, vector: InputVector) -> ObservedOutput:
        args = [vector]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁExecutionRecorderǁ_invoke__mutmut_orig'), object.__getattribute__(self, 'xǁExecutionRecorderǁ_invoke__mutmut_mutants'), args, kwargs, self)

    def xǁExecutionRecorderǁ_invoke__mutmut_orig(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_1(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = None

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_2(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(None)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_3(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = None

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_4(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=None,
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_5(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=None,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_6(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=None,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_7(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=None,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_8(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=None,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_9(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=None,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_10(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=None,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_11(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=None,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_12(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_13(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_14(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_15(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_16(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_17(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_18(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_19(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_20(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(None),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_21(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    None
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_22(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "XXexpected ValueError but production module returned normally.XX"
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_23(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected valueerror but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_24(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "EXPECTED VALUEERROR BUT PRODUCTION MODULE RETURNED NORMALLY."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_25(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=None,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_26(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=None,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_27(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=None,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_28(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=None,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_29(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=None,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_30(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=None,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_31(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=None,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_32(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=None,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_33(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type=None,
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_34(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_35(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_36(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_37(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_38(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_39(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_40(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_41(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_42(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_43(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=True,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_44(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="XXXX",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_45(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_46(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    None
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_47(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=None,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_48(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=None,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_49(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=None,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_50(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=None,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_51(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=None,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_52(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=None,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_53(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime=None,
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_54(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=None,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_55(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type=None,
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_56(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_57(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_58(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_59(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_60(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_61(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_62(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_63(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_64(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_65(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=1.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_66(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=1.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_67(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=1.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_68(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=True,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_69(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=1.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_70(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=1.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_71(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="XXXX",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_72(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=False,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_73(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="XXValueErrorXX",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_74(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="valueerror",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_75(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="VALUEERROR",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_76(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = None
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_77(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(None).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_78(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    None
                ) from exc
            raise RuntimeError(
                f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                f"unexpected {exc_name}: {exc}"
            ) from exc

    def xǁExecutionRecorderǁ_invoke__mutmut_79(self, vector: InputVector) -> ObservedOutput:
        """
        Invoke production RiskEngine.assess() with the given InputVector.
        Returns an ObservedOutput.

        Exceptions from the production module are caught ONLY to record them.
        They are not suppressed (NIC-10). For unexpected exceptions, the caller
        receives a re-raised RuntimeError.
        """
        regime = _regime_from_string(vector.current_regime_str)

        try:
            result = self._engine.assess(
                returns_history=list(vector.returns_history),
                current_regime=regime,
                meta_uncertainty=vector.meta_uncertainty,
                macro_regime=vector.macro_regime,
                correlation_regime=vector.correlation_regime,
                realized_vol=vector.realized_vol,
                target_vol=vector.target_vol,
                regime_posterior=vector.regime_posterior,
            )

            if vector.expect_exception:
                # Production should have raised; it did not.
                raise RuntimeError(
                    f"MISSING_EXPECTED_EXCEPTION: Vector {vector.vector_id} "
                    "expected ValueError but production module returned normally."
                )

            return ObservedOutput(
                expected_drawdown=result.expected_drawdown,
                expected_drawdown_p95=result.expected_drawdown_p95,
                volatility_forecast=result.volatility_forecast,
                risk_compression_active=result.risk_compression_active,
                position_size_factor=result.position_size_factor,
                exposure_weight=result.exposure_weight,
                risk_regime=result.risk_regime,
                exception_raised=False,
                exception_type="",
            )

        except RuntimeError:
            # Re-raise harness-generated RuntimeErrors (not from production).
            raise

        except ValueError as exc:
            if not vector.expect_exception:
                # Unexpected exception from production.
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} raised "
                    f"unexpected ValueError: {exc}"
                ) from exc
            # Expected ValueError. Record the exception outcome.
            return ObservedOutput(
                expected_drawdown=0.0,
                expected_drawdown_p95=0.0,
                volatility_forecast=0.0,
                risk_compression_active=False,
                position_size_factor=0.0,
                exposure_weight=0.0,
                risk_regime="",
                exception_raised=True,
                exception_type="ValueError",
            )

        except Exception as exc:
            # Production raised an unexpected exception type.
            exc_name = type(exc).__name__
            if vector.expect_exception:
                raise RuntimeError(
                    f"EXCEPTION_TYPE_MISMATCH: Vector {vector.vector_id} expected "
                    f"ValueError but got {exc_name}: {exc}"
                ) from exc
            raise RuntimeError(
                None
            ) from exc
    
    xǁExecutionRecorderǁ_invoke__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁExecutionRecorderǁ_invoke__mutmut_1': xǁExecutionRecorderǁ_invoke__mutmut_1, 
        'xǁExecutionRecorderǁ_invoke__mutmut_2': xǁExecutionRecorderǁ_invoke__mutmut_2, 
        'xǁExecutionRecorderǁ_invoke__mutmut_3': xǁExecutionRecorderǁ_invoke__mutmut_3, 
        'xǁExecutionRecorderǁ_invoke__mutmut_4': xǁExecutionRecorderǁ_invoke__mutmut_4, 
        'xǁExecutionRecorderǁ_invoke__mutmut_5': xǁExecutionRecorderǁ_invoke__mutmut_5, 
        'xǁExecutionRecorderǁ_invoke__mutmut_6': xǁExecutionRecorderǁ_invoke__mutmut_6, 
        'xǁExecutionRecorderǁ_invoke__mutmut_7': xǁExecutionRecorderǁ_invoke__mutmut_7, 
        'xǁExecutionRecorderǁ_invoke__mutmut_8': xǁExecutionRecorderǁ_invoke__mutmut_8, 
        'xǁExecutionRecorderǁ_invoke__mutmut_9': xǁExecutionRecorderǁ_invoke__mutmut_9, 
        'xǁExecutionRecorderǁ_invoke__mutmut_10': xǁExecutionRecorderǁ_invoke__mutmut_10, 
        'xǁExecutionRecorderǁ_invoke__mutmut_11': xǁExecutionRecorderǁ_invoke__mutmut_11, 
        'xǁExecutionRecorderǁ_invoke__mutmut_12': xǁExecutionRecorderǁ_invoke__mutmut_12, 
        'xǁExecutionRecorderǁ_invoke__mutmut_13': xǁExecutionRecorderǁ_invoke__mutmut_13, 
        'xǁExecutionRecorderǁ_invoke__mutmut_14': xǁExecutionRecorderǁ_invoke__mutmut_14, 
        'xǁExecutionRecorderǁ_invoke__mutmut_15': xǁExecutionRecorderǁ_invoke__mutmut_15, 
        'xǁExecutionRecorderǁ_invoke__mutmut_16': xǁExecutionRecorderǁ_invoke__mutmut_16, 
        'xǁExecutionRecorderǁ_invoke__mutmut_17': xǁExecutionRecorderǁ_invoke__mutmut_17, 
        'xǁExecutionRecorderǁ_invoke__mutmut_18': xǁExecutionRecorderǁ_invoke__mutmut_18, 
        'xǁExecutionRecorderǁ_invoke__mutmut_19': xǁExecutionRecorderǁ_invoke__mutmut_19, 
        'xǁExecutionRecorderǁ_invoke__mutmut_20': xǁExecutionRecorderǁ_invoke__mutmut_20, 
        'xǁExecutionRecorderǁ_invoke__mutmut_21': xǁExecutionRecorderǁ_invoke__mutmut_21, 
        'xǁExecutionRecorderǁ_invoke__mutmut_22': xǁExecutionRecorderǁ_invoke__mutmut_22, 
        'xǁExecutionRecorderǁ_invoke__mutmut_23': xǁExecutionRecorderǁ_invoke__mutmut_23, 
        'xǁExecutionRecorderǁ_invoke__mutmut_24': xǁExecutionRecorderǁ_invoke__mutmut_24, 
        'xǁExecutionRecorderǁ_invoke__mutmut_25': xǁExecutionRecorderǁ_invoke__mutmut_25, 
        'xǁExecutionRecorderǁ_invoke__mutmut_26': xǁExecutionRecorderǁ_invoke__mutmut_26, 
        'xǁExecutionRecorderǁ_invoke__mutmut_27': xǁExecutionRecorderǁ_invoke__mutmut_27, 
        'xǁExecutionRecorderǁ_invoke__mutmut_28': xǁExecutionRecorderǁ_invoke__mutmut_28, 
        'xǁExecutionRecorderǁ_invoke__mutmut_29': xǁExecutionRecorderǁ_invoke__mutmut_29, 
        'xǁExecutionRecorderǁ_invoke__mutmut_30': xǁExecutionRecorderǁ_invoke__mutmut_30, 
        'xǁExecutionRecorderǁ_invoke__mutmut_31': xǁExecutionRecorderǁ_invoke__mutmut_31, 
        'xǁExecutionRecorderǁ_invoke__mutmut_32': xǁExecutionRecorderǁ_invoke__mutmut_32, 
        'xǁExecutionRecorderǁ_invoke__mutmut_33': xǁExecutionRecorderǁ_invoke__mutmut_33, 
        'xǁExecutionRecorderǁ_invoke__mutmut_34': xǁExecutionRecorderǁ_invoke__mutmut_34, 
        'xǁExecutionRecorderǁ_invoke__mutmut_35': xǁExecutionRecorderǁ_invoke__mutmut_35, 
        'xǁExecutionRecorderǁ_invoke__mutmut_36': xǁExecutionRecorderǁ_invoke__mutmut_36, 
        'xǁExecutionRecorderǁ_invoke__mutmut_37': xǁExecutionRecorderǁ_invoke__mutmut_37, 
        'xǁExecutionRecorderǁ_invoke__mutmut_38': xǁExecutionRecorderǁ_invoke__mutmut_38, 
        'xǁExecutionRecorderǁ_invoke__mutmut_39': xǁExecutionRecorderǁ_invoke__mutmut_39, 
        'xǁExecutionRecorderǁ_invoke__mutmut_40': xǁExecutionRecorderǁ_invoke__mutmut_40, 
        'xǁExecutionRecorderǁ_invoke__mutmut_41': xǁExecutionRecorderǁ_invoke__mutmut_41, 
        'xǁExecutionRecorderǁ_invoke__mutmut_42': xǁExecutionRecorderǁ_invoke__mutmut_42, 
        'xǁExecutionRecorderǁ_invoke__mutmut_43': xǁExecutionRecorderǁ_invoke__mutmut_43, 
        'xǁExecutionRecorderǁ_invoke__mutmut_44': xǁExecutionRecorderǁ_invoke__mutmut_44, 
        'xǁExecutionRecorderǁ_invoke__mutmut_45': xǁExecutionRecorderǁ_invoke__mutmut_45, 
        'xǁExecutionRecorderǁ_invoke__mutmut_46': xǁExecutionRecorderǁ_invoke__mutmut_46, 
        'xǁExecutionRecorderǁ_invoke__mutmut_47': xǁExecutionRecorderǁ_invoke__mutmut_47, 
        'xǁExecutionRecorderǁ_invoke__mutmut_48': xǁExecutionRecorderǁ_invoke__mutmut_48, 
        'xǁExecutionRecorderǁ_invoke__mutmut_49': xǁExecutionRecorderǁ_invoke__mutmut_49, 
        'xǁExecutionRecorderǁ_invoke__mutmut_50': xǁExecutionRecorderǁ_invoke__mutmut_50, 
        'xǁExecutionRecorderǁ_invoke__mutmut_51': xǁExecutionRecorderǁ_invoke__mutmut_51, 
        'xǁExecutionRecorderǁ_invoke__mutmut_52': xǁExecutionRecorderǁ_invoke__mutmut_52, 
        'xǁExecutionRecorderǁ_invoke__mutmut_53': xǁExecutionRecorderǁ_invoke__mutmut_53, 
        'xǁExecutionRecorderǁ_invoke__mutmut_54': xǁExecutionRecorderǁ_invoke__mutmut_54, 
        'xǁExecutionRecorderǁ_invoke__mutmut_55': xǁExecutionRecorderǁ_invoke__mutmut_55, 
        'xǁExecutionRecorderǁ_invoke__mutmut_56': xǁExecutionRecorderǁ_invoke__mutmut_56, 
        'xǁExecutionRecorderǁ_invoke__mutmut_57': xǁExecutionRecorderǁ_invoke__mutmut_57, 
        'xǁExecutionRecorderǁ_invoke__mutmut_58': xǁExecutionRecorderǁ_invoke__mutmut_58, 
        'xǁExecutionRecorderǁ_invoke__mutmut_59': xǁExecutionRecorderǁ_invoke__mutmut_59, 
        'xǁExecutionRecorderǁ_invoke__mutmut_60': xǁExecutionRecorderǁ_invoke__mutmut_60, 
        'xǁExecutionRecorderǁ_invoke__mutmut_61': xǁExecutionRecorderǁ_invoke__mutmut_61, 
        'xǁExecutionRecorderǁ_invoke__mutmut_62': xǁExecutionRecorderǁ_invoke__mutmut_62, 
        'xǁExecutionRecorderǁ_invoke__mutmut_63': xǁExecutionRecorderǁ_invoke__mutmut_63, 
        'xǁExecutionRecorderǁ_invoke__mutmut_64': xǁExecutionRecorderǁ_invoke__mutmut_64, 
        'xǁExecutionRecorderǁ_invoke__mutmut_65': xǁExecutionRecorderǁ_invoke__mutmut_65, 
        'xǁExecutionRecorderǁ_invoke__mutmut_66': xǁExecutionRecorderǁ_invoke__mutmut_66, 
        'xǁExecutionRecorderǁ_invoke__mutmut_67': xǁExecutionRecorderǁ_invoke__mutmut_67, 
        'xǁExecutionRecorderǁ_invoke__mutmut_68': xǁExecutionRecorderǁ_invoke__mutmut_68, 
        'xǁExecutionRecorderǁ_invoke__mutmut_69': xǁExecutionRecorderǁ_invoke__mutmut_69, 
        'xǁExecutionRecorderǁ_invoke__mutmut_70': xǁExecutionRecorderǁ_invoke__mutmut_70, 
        'xǁExecutionRecorderǁ_invoke__mutmut_71': xǁExecutionRecorderǁ_invoke__mutmut_71, 
        'xǁExecutionRecorderǁ_invoke__mutmut_72': xǁExecutionRecorderǁ_invoke__mutmut_72, 
        'xǁExecutionRecorderǁ_invoke__mutmut_73': xǁExecutionRecorderǁ_invoke__mutmut_73, 
        'xǁExecutionRecorderǁ_invoke__mutmut_74': xǁExecutionRecorderǁ_invoke__mutmut_74, 
        'xǁExecutionRecorderǁ_invoke__mutmut_75': xǁExecutionRecorderǁ_invoke__mutmut_75, 
        'xǁExecutionRecorderǁ_invoke__mutmut_76': xǁExecutionRecorderǁ_invoke__mutmut_76, 
        'xǁExecutionRecorderǁ_invoke__mutmut_77': xǁExecutionRecorderǁ_invoke__mutmut_77, 
        'xǁExecutionRecorderǁ_invoke__mutmut_78': xǁExecutionRecorderǁ_invoke__mutmut_78, 
        'xǁExecutionRecorderǁ_invoke__mutmut_79': xǁExecutionRecorderǁ_invoke__mutmut_79
    }
    xǁExecutionRecorderǁ_invoke__mutmut_orig.__name__ = 'xǁExecutionRecorderǁ_invoke'

    def record_all(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        args = [vectors]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁExecutionRecorderǁrecord_all__mutmut_orig'), object.__getattribute__(self, 'xǁExecutionRecorderǁrecord_all__mutmut_mutants'), args, kwargs, self)

    def xǁExecutionRecorderǁrecord_all__mutmut_orig(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_1(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = None
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_2(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = None
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_3(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(None)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_4(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = None
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_5(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=None,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_6(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=None,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_7(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=None,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_8(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=None,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_9(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=None,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_10(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=None,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_11(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=None,
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_12(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=None,
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_13(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=None,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_14(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=None,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_15(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_16(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_17(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_18(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_19(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_20(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_21(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_22(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_23(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_24(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_25(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(None),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(record)
        return records

    def xǁExecutionRecorderǁrecord_all__mutmut_26(self, vectors: List[InputVector]) -> List[ExecutionRecord]:
        """
        Execute all vectors in order. Return a list of ExecutionRecord.
        Single-threaded. Each invocation completes before the next begins (EEP-01).
        """
        records = []
        for vector in vectors:
            observed = self._invoke(vector)
            record = ExecutionRecord(
                vector_id=vector.vector_id,
                group_id=vector.group_id,
                input_vector=vector,
                observed_output=observed,
                stage=self._stage,
                manifest_hash=self._manifest_hash,
                timestamp_iso=_now_iso(),
                execution_id=str(uuid.uuid4()),
                harness_version=HARNESS_VERSION,
                module_version=self._module_version,
            )
            records.append(None)
        return records
    
    xǁExecutionRecorderǁrecord_all__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁExecutionRecorderǁrecord_all__mutmut_1': xǁExecutionRecorderǁrecord_all__mutmut_1, 
        'xǁExecutionRecorderǁrecord_all__mutmut_2': xǁExecutionRecorderǁrecord_all__mutmut_2, 
        'xǁExecutionRecorderǁrecord_all__mutmut_3': xǁExecutionRecorderǁrecord_all__mutmut_3, 
        'xǁExecutionRecorderǁrecord_all__mutmut_4': xǁExecutionRecorderǁrecord_all__mutmut_4, 
        'xǁExecutionRecorderǁrecord_all__mutmut_5': xǁExecutionRecorderǁrecord_all__mutmut_5, 
        'xǁExecutionRecorderǁrecord_all__mutmut_6': xǁExecutionRecorderǁrecord_all__mutmut_6, 
        'xǁExecutionRecorderǁrecord_all__mutmut_7': xǁExecutionRecorderǁrecord_all__mutmut_7, 
        'xǁExecutionRecorderǁrecord_all__mutmut_8': xǁExecutionRecorderǁrecord_all__mutmut_8, 
        'xǁExecutionRecorderǁrecord_all__mutmut_9': xǁExecutionRecorderǁrecord_all__mutmut_9, 
        'xǁExecutionRecorderǁrecord_all__mutmut_10': xǁExecutionRecorderǁrecord_all__mutmut_10, 
        'xǁExecutionRecorderǁrecord_all__mutmut_11': xǁExecutionRecorderǁrecord_all__mutmut_11, 
        'xǁExecutionRecorderǁrecord_all__mutmut_12': xǁExecutionRecorderǁrecord_all__mutmut_12, 
        'xǁExecutionRecorderǁrecord_all__mutmut_13': xǁExecutionRecorderǁrecord_all__mutmut_13, 
        'xǁExecutionRecorderǁrecord_all__mutmut_14': xǁExecutionRecorderǁrecord_all__mutmut_14, 
        'xǁExecutionRecorderǁrecord_all__mutmut_15': xǁExecutionRecorderǁrecord_all__mutmut_15, 
        'xǁExecutionRecorderǁrecord_all__mutmut_16': xǁExecutionRecorderǁrecord_all__mutmut_16, 
        'xǁExecutionRecorderǁrecord_all__mutmut_17': xǁExecutionRecorderǁrecord_all__mutmut_17, 
        'xǁExecutionRecorderǁrecord_all__mutmut_18': xǁExecutionRecorderǁrecord_all__mutmut_18, 
        'xǁExecutionRecorderǁrecord_all__mutmut_19': xǁExecutionRecorderǁrecord_all__mutmut_19, 
        'xǁExecutionRecorderǁrecord_all__mutmut_20': xǁExecutionRecorderǁrecord_all__mutmut_20, 
        'xǁExecutionRecorderǁrecord_all__mutmut_21': xǁExecutionRecorderǁrecord_all__mutmut_21, 
        'xǁExecutionRecorderǁrecord_all__mutmut_22': xǁExecutionRecorderǁrecord_all__mutmut_22, 
        'xǁExecutionRecorderǁrecord_all__mutmut_23': xǁExecutionRecorderǁrecord_all__mutmut_23, 
        'xǁExecutionRecorderǁrecord_all__mutmut_24': xǁExecutionRecorderǁrecord_all__mutmut_24, 
        'xǁExecutionRecorderǁrecord_all__mutmut_25': xǁExecutionRecorderǁrecord_all__mutmut_25, 
        'xǁExecutionRecorderǁrecord_all__mutmut_26': xǁExecutionRecorderǁrecord_all__mutmut_26
    }
    xǁExecutionRecorderǁrecord_all__mutmut_orig.__name__ = 'xǁExecutionRecorderǁrecord_all'
