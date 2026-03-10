# jarvis/verification/failure_handler.py
# FailureHandler -- hard failure policy enforcement for the harness.
# Authority: DVH Implementation Blueprint v1.0.0 Section 14.
#
# HFP-01: Exit with non-zero exit code on any hard failure.
# HFP-03: No WARNING-level logging. All failures reported via record and exit code.
# HFP-04: No catch-and-continue. No retry. No fallback.
# HFP-06: Invoke immediately on failure detection. No further pipeline stage runs.
# HFP-07: If FailureHandler itself raises, write partial record to stderr and exit 4.

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from jarvis.verification.data_models.failure_record import FailureRecord, FAILURE_TYPES
from jarvis.verification.harness_version import HARNESS_VERSION

# Freeze invariant reference map (VFE-05).
_FREEZE_INV_REF = {
    "CLIP_A_VIOLATION":          "INV-01",
    "CLIP_B_FLOOR_VIOLATION":    "INV-02",
    "CLIP_B_RANGE_VIOLATION":    "INV-02",
    "CLIP_C_FLOOR_VIOLATION":    "INV-03",
    "CRISIS_ORDERING_VIOLATION": "INV-04",
    "BACKWARD_COMPAT_VIOLATION": "INV-08",
}
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
    return datetime.now(timezone.utc).isoformat()


def x__now_iso__mutmut_1() -> str:
    return datetime.now(None).isoformat()

x__now_iso__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__now_iso__mutmut_1': x__now_iso__mutmut_1
}
x__now_iso__mutmut_orig.__name__ = 'x__now_iso'


class FailureHandler:
    """
    Enforces the Hard Failure Policy (Section 14).

    On any hard failure:
      1. Construct FailureRecord.
      2. Write FailureRecord JSON to runs directory.
      3. Print failure summary to stdout (HFP-05).
      4. Call sys.exit(exit_code) -- must be last operation (HFP-02).

    If FailureHandler itself raises during record writing:
      - Write partial info to stderr.
      - sys.exit(4).
    """

    def __init__(
        self,
        runs_dir:       Path,
        run_id:         str,
        module_version: str,
        manifest_hash:  str,
    ):
        args = [runs_dir, run_id, module_version, manifest_hash]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁFailureHandlerǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁFailureHandlerǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁFailureHandlerǁ__init____mutmut_orig(
        self,
        runs_dir:       Path,
        run_id:         str,
        module_version: str,
        manifest_hash:  str,
    ):
        self._runs_dir      = runs_dir
        self._run_id        = run_id
        self._module_version = module_version
        self._manifest_hash = manifest_hash

    def xǁFailureHandlerǁ__init____mutmut_1(
        self,
        runs_dir:       Path,
        run_id:         str,
        module_version: str,
        manifest_hash:  str,
    ):
        self._runs_dir      = None
        self._run_id        = run_id
        self._module_version = module_version
        self._manifest_hash = manifest_hash

    def xǁFailureHandlerǁ__init____mutmut_2(
        self,
        runs_dir:       Path,
        run_id:         str,
        module_version: str,
        manifest_hash:  str,
    ):
        self._runs_dir      = runs_dir
        self._run_id        = None
        self._module_version = module_version
        self._manifest_hash = manifest_hash

    def xǁFailureHandlerǁ__init____mutmut_3(
        self,
        runs_dir:       Path,
        run_id:         str,
        module_version: str,
        manifest_hash:  str,
    ):
        self._runs_dir      = runs_dir
        self._run_id        = run_id
        self._module_version = None
        self._manifest_hash = manifest_hash

    def xǁFailureHandlerǁ__init____mutmut_4(
        self,
        runs_dir:       Path,
        run_id:         str,
        module_version: str,
        manifest_hash:  str,
    ):
        self._runs_dir      = runs_dir
        self._run_id        = run_id
        self._module_version = module_version
        self._manifest_hash = None
    
    xǁFailureHandlerǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁFailureHandlerǁ__init____mutmut_1': xǁFailureHandlerǁ__init____mutmut_1, 
        'xǁFailureHandlerǁ__init____mutmut_2': xǁFailureHandlerǁ__init____mutmut_2, 
        'xǁFailureHandlerǁ__init____mutmut_3': xǁFailureHandlerǁ__init____mutmut_3, 
        'xǁFailureHandlerǁ__init____mutmut_4': xǁFailureHandlerǁ__init____mutmut_4
    }
    xǁFailureHandlerǁ__init____mutmut_orig.__name__ = 'xǁFailureHandlerǁ__init__'

    def handle(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        args = [failure_type_id, detail, vector_id, field_name]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁFailureHandlerǁhandle__mutmut_orig'), object.__getattribute__(self, 'xǁFailureHandlerǁhandle__mutmut_mutants'), args, kwargs, self)

    def xǁFailureHandlerǁhandle__mutmut_orig(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_1(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "XXXX",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_2(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "XXXX",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_3(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = None
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_4(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(None, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_5(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, None)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_6(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_7(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, )
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_8(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 5)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_9(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = None
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_10(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(None, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_11(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, None)
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_12(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get("")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_13(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, )
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_14(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "XXXX")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_15(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = None

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_16(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = None

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_17(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=None,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_18(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=None,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_19(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=None,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_20(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=None,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_21(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=None,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_22(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=None,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_23(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=None,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_24(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=None,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_25(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=None,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_26(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=None,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_27(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=None,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_28(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_29(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_30(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_31(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_32(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_33(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_34(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_35(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_36(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_37(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_38(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_39(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = None

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_40(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "XXfailure_type_idXX":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_41(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "FAILURE_TYPE_ID":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_42(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "XXexit_codeXX":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_43(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "EXIT_CODE":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_44(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "XXvector_idXX":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_45(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "VECTOR_ID":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_46(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "XXfield_nameXX":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_47(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "FIELD_NAME":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_48(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "XXdetected_at_isoXX":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_49(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "DETECTED_AT_ISO":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_50(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "XXrun_idXX":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_51(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "RUN_ID":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_52(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "XXharness_versionXX":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_53(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "HARNESS_VERSION":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_54(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "XXmodule_versionXX":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_55(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "MODULE_VERSION":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_56(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "XXmanifest_hashXX":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_57(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "MANIFEST_HASH":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_58(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "XXfreeze_invariant_refXX": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_59(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "FREEZE_INVARIANT_REF": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_60(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "XXdetailXX":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_61(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "DETAIL":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_62(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=None, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_63(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=None)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_64(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_65(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, )
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_66(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=False, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_67(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=False)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_68(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = None
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_69(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace(None, "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_70(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", None)[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_71(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_72(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", )[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_73(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace(None, "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_74(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", None).replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_75(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_76(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", ).replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_77(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(None, "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_78(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", None).replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_79(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace("").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_80(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", ).replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_81(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace("XX:XX", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_82(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "XXXX").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_83(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("XX-XX", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_84(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "XXXX").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_85(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("XX+XX", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_86(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "XXZXX")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_87(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_88(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:17]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_89(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = None
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_90(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = None

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_91(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir * filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_92(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(None, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_93(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, None, encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_94(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding=None) as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_95(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open("w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_96(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_97(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", ) as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_98(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "XXwXX", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_99(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "W", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_100(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="XXutf-8XX") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_101(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="UTF-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_102(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(None, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_103(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, None, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_104(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=None)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_105(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_106(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_107(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, )

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_108(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=5)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_109(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                None
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_110(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id and '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_111(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or 'XX(not applicable)XX'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_112(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(NOT APPLICABLE)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_113(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:201]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_114(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                None
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_115(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(None)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_116(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(5)

        # HFP-02: sys.exit is the last operation.
        sys.exit(exit_code)

    def xǁFailureHandlerǁhandle__mutmut_117(
        self,
        failure_type_id: str,
        detail:          str,
        vector_id:       str = "",
        field_name:      str = "",
    ) -> None:
        """
        Execute the hard failure policy. This method does not return.

        Parses failure_type_id from RuntimeError messages if the RuntimeError
        starts with a known failure_type_id prefix.
        """
        exit_code          = FAILURE_TYPES.get(failure_type_id, 4)
        freeze_inv_ref     = _FREEZE_INV_REF.get(failure_type_id, "")
        detected_at        = _now_iso()

        record = FailureRecord(
            failure_type_id=failure_type_id,
            exit_code=exit_code,
            vector_id=vector_id,
            field_name=field_name,
            detected_at_iso=detected_at,
            run_id=self._run_id,
            harness_version=HARNESS_VERSION,
            module_version=self._module_version,
            manifest_hash=self._manifest_hash,
            freeze_invariant_ref=freeze_inv_ref,
            detail=detail,
        )

        record_dict = {
            "failure_type_id":      record.failure_type_id,
            "exit_code":            record.exit_code,
            "vector_id":            record.vector_id,
            "field_name":           record.field_name,
            "detected_at_iso":      record.detected_at_iso,
            "run_id":               record.run_id,
            "harness_version":      record.harness_version,
            "module_version":       record.module_version,
            "manifest_hash":        record.manifest_hash,
            "freeze_invariant_ref": record.freeze_invariant_ref,
            "detail":               record.detail,
        }

        try:
            self._runs_dir.mkdir(parents=True, exist_ok=True)
            ts_compact = detected_at.replace(":", "").replace("-", "").replace("+", "Z")[:16]
            filename   = f"{self._run_id}_FAIL_{ts_compact}.json"
            filepath   = self._runs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record_dict, f, indent=4)

            # HFP-05: Stdout contains only the pass/fail summary.
            print(
                f"HARNESS RESULT: FAIL\n"
                f"Failure type:   {failure_type_id}\n"
                f"Exit code:      {exit_code}\n"
                f"Vector:         {vector_id or '(not applicable)'}\n"
                f"Detail:         {detail[:200]}\n"
                f"Record written: {filepath}"
            )

        except Exception as exc:
            # HFP-07: Write partial info to stderr and exit 4.
            sys.stderr.write(
                f"HARNESS_INTERNAL_ERROR: FailureHandler failed to write record: {exc}\n"
                f"Original failure: {failure_type_id} -- {detail}\n"
            )
            sys.exit(4)

        # HFP-02: sys.exit is the last operation.
        sys.exit(None)
    
    xǁFailureHandlerǁhandle__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁFailureHandlerǁhandle__mutmut_1': xǁFailureHandlerǁhandle__mutmut_1, 
        'xǁFailureHandlerǁhandle__mutmut_2': xǁFailureHandlerǁhandle__mutmut_2, 
        'xǁFailureHandlerǁhandle__mutmut_3': xǁFailureHandlerǁhandle__mutmut_3, 
        'xǁFailureHandlerǁhandle__mutmut_4': xǁFailureHandlerǁhandle__mutmut_4, 
        'xǁFailureHandlerǁhandle__mutmut_5': xǁFailureHandlerǁhandle__mutmut_5, 
        'xǁFailureHandlerǁhandle__mutmut_6': xǁFailureHandlerǁhandle__mutmut_6, 
        'xǁFailureHandlerǁhandle__mutmut_7': xǁFailureHandlerǁhandle__mutmut_7, 
        'xǁFailureHandlerǁhandle__mutmut_8': xǁFailureHandlerǁhandle__mutmut_8, 
        'xǁFailureHandlerǁhandle__mutmut_9': xǁFailureHandlerǁhandle__mutmut_9, 
        'xǁFailureHandlerǁhandle__mutmut_10': xǁFailureHandlerǁhandle__mutmut_10, 
        'xǁFailureHandlerǁhandle__mutmut_11': xǁFailureHandlerǁhandle__mutmut_11, 
        'xǁFailureHandlerǁhandle__mutmut_12': xǁFailureHandlerǁhandle__mutmut_12, 
        'xǁFailureHandlerǁhandle__mutmut_13': xǁFailureHandlerǁhandle__mutmut_13, 
        'xǁFailureHandlerǁhandle__mutmut_14': xǁFailureHandlerǁhandle__mutmut_14, 
        'xǁFailureHandlerǁhandle__mutmut_15': xǁFailureHandlerǁhandle__mutmut_15, 
        'xǁFailureHandlerǁhandle__mutmut_16': xǁFailureHandlerǁhandle__mutmut_16, 
        'xǁFailureHandlerǁhandle__mutmut_17': xǁFailureHandlerǁhandle__mutmut_17, 
        'xǁFailureHandlerǁhandle__mutmut_18': xǁFailureHandlerǁhandle__mutmut_18, 
        'xǁFailureHandlerǁhandle__mutmut_19': xǁFailureHandlerǁhandle__mutmut_19, 
        'xǁFailureHandlerǁhandle__mutmut_20': xǁFailureHandlerǁhandle__mutmut_20, 
        'xǁFailureHandlerǁhandle__mutmut_21': xǁFailureHandlerǁhandle__mutmut_21, 
        'xǁFailureHandlerǁhandle__mutmut_22': xǁFailureHandlerǁhandle__mutmut_22, 
        'xǁFailureHandlerǁhandle__mutmut_23': xǁFailureHandlerǁhandle__mutmut_23, 
        'xǁFailureHandlerǁhandle__mutmut_24': xǁFailureHandlerǁhandle__mutmut_24, 
        'xǁFailureHandlerǁhandle__mutmut_25': xǁFailureHandlerǁhandle__mutmut_25, 
        'xǁFailureHandlerǁhandle__mutmut_26': xǁFailureHandlerǁhandle__mutmut_26, 
        'xǁFailureHandlerǁhandle__mutmut_27': xǁFailureHandlerǁhandle__mutmut_27, 
        'xǁFailureHandlerǁhandle__mutmut_28': xǁFailureHandlerǁhandle__mutmut_28, 
        'xǁFailureHandlerǁhandle__mutmut_29': xǁFailureHandlerǁhandle__mutmut_29, 
        'xǁFailureHandlerǁhandle__mutmut_30': xǁFailureHandlerǁhandle__mutmut_30, 
        'xǁFailureHandlerǁhandle__mutmut_31': xǁFailureHandlerǁhandle__mutmut_31, 
        'xǁFailureHandlerǁhandle__mutmut_32': xǁFailureHandlerǁhandle__mutmut_32, 
        'xǁFailureHandlerǁhandle__mutmut_33': xǁFailureHandlerǁhandle__mutmut_33, 
        'xǁFailureHandlerǁhandle__mutmut_34': xǁFailureHandlerǁhandle__mutmut_34, 
        'xǁFailureHandlerǁhandle__mutmut_35': xǁFailureHandlerǁhandle__mutmut_35, 
        'xǁFailureHandlerǁhandle__mutmut_36': xǁFailureHandlerǁhandle__mutmut_36, 
        'xǁFailureHandlerǁhandle__mutmut_37': xǁFailureHandlerǁhandle__mutmut_37, 
        'xǁFailureHandlerǁhandle__mutmut_38': xǁFailureHandlerǁhandle__mutmut_38, 
        'xǁFailureHandlerǁhandle__mutmut_39': xǁFailureHandlerǁhandle__mutmut_39, 
        'xǁFailureHandlerǁhandle__mutmut_40': xǁFailureHandlerǁhandle__mutmut_40, 
        'xǁFailureHandlerǁhandle__mutmut_41': xǁFailureHandlerǁhandle__mutmut_41, 
        'xǁFailureHandlerǁhandle__mutmut_42': xǁFailureHandlerǁhandle__mutmut_42, 
        'xǁFailureHandlerǁhandle__mutmut_43': xǁFailureHandlerǁhandle__mutmut_43, 
        'xǁFailureHandlerǁhandle__mutmut_44': xǁFailureHandlerǁhandle__mutmut_44, 
        'xǁFailureHandlerǁhandle__mutmut_45': xǁFailureHandlerǁhandle__mutmut_45, 
        'xǁFailureHandlerǁhandle__mutmut_46': xǁFailureHandlerǁhandle__mutmut_46, 
        'xǁFailureHandlerǁhandle__mutmut_47': xǁFailureHandlerǁhandle__mutmut_47, 
        'xǁFailureHandlerǁhandle__mutmut_48': xǁFailureHandlerǁhandle__mutmut_48, 
        'xǁFailureHandlerǁhandle__mutmut_49': xǁFailureHandlerǁhandle__mutmut_49, 
        'xǁFailureHandlerǁhandle__mutmut_50': xǁFailureHandlerǁhandle__mutmut_50, 
        'xǁFailureHandlerǁhandle__mutmut_51': xǁFailureHandlerǁhandle__mutmut_51, 
        'xǁFailureHandlerǁhandle__mutmut_52': xǁFailureHandlerǁhandle__mutmut_52, 
        'xǁFailureHandlerǁhandle__mutmut_53': xǁFailureHandlerǁhandle__mutmut_53, 
        'xǁFailureHandlerǁhandle__mutmut_54': xǁFailureHandlerǁhandle__mutmut_54, 
        'xǁFailureHandlerǁhandle__mutmut_55': xǁFailureHandlerǁhandle__mutmut_55, 
        'xǁFailureHandlerǁhandle__mutmut_56': xǁFailureHandlerǁhandle__mutmut_56, 
        'xǁFailureHandlerǁhandle__mutmut_57': xǁFailureHandlerǁhandle__mutmut_57, 
        'xǁFailureHandlerǁhandle__mutmut_58': xǁFailureHandlerǁhandle__mutmut_58, 
        'xǁFailureHandlerǁhandle__mutmut_59': xǁFailureHandlerǁhandle__mutmut_59, 
        'xǁFailureHandlerǁhandle__mutmut_60': xǁFailureHandlerǁhandle__mutmut_60, 
        'xǁFailureHandlerǁhandle__mutmut_61': xǁFailureHandlerǁhandle__mutmut_61, 
        'xǁFailureHandlerǁhandle__mutmut_62': xǁFailureHandlerǁhandle__mutmut_62, 
        'xǁFailureHandlerǁhandle__mutmut_63': xǁFailureHandlerǁhandle__mutmut_63, 
        'xǁFailureHandlerǁhandle__mutmut_64': xǁFailureHandlerǁhandle__mutmut_64, 
        'xǁFailureHandlerǁhandle__mutmut_65': xǁFailureHandlerǁhandle__mutmut_65, 
        'xǁFailureHandlerǁhandle__mutmut_66': xǁFailureHandlerǁhandle__mutmut_66, 
        'xǁFailureHandlerǁhandle__mutmut_67': xǁFailureHandlerǁhandle__mutmut_67, 
        'xǁFailureHandlerǁhandle__mutmut_68': xǁFailureHandlerǁhandle__mutmut_68, 
        'xǁFailureHandlerǁhandle__mutmut_69': xǁFailureHandlerǁhandle__mutmut_69, 
        'xǁFailureHandlerǁhandle__mutmut_70': xǁFailureHandlerǁhandle__mutmut_70, 
        'xǁFailureHandlerǁhandle__mutmut_71': xǁFailureHandlerǁhandle__mutmut_71, 
        'xǁFailureHandlerǁhandle__mutmut_72': xǁFailureHandlerǁhandle__mutmut_72, 
        'xǁFailureHandlerǁhandle__mutmut_73': xǁFailureHandlerǁhandle__mutmut_73, 
        'xǁFailureHandlerǁhandle__mutmut_74': xǁFailureHandlerǁhandle__mutmut_74, 
        'xǁFailureHandlerǁhandle__mutmut_75': xǁFailureHandlerǁhandle__mutmut_75, 
        'xǁFailureHandlerǁhandle__mutmut_76': xǁFailureHandlerǁhandle__mutmut_76, 
        'xǁFailureHandlerǁhandle__mutmut_77': xǁFailureHandlerǁhandle__mutmut_77, 
        'xǁFailureHandlerǁhandle__mutmut_78': xǁFailureHandlerǁhandle__mutmut_78, 
        'xǁFailureHandlerǁhandle__mutmut_79': xǁFailureHandlerǁhandle__mutmut_79, 
        'xǁFailureHandlerǁhandle__mutmut_80': xǁFailureHandlerǁhandle__mutmut_80, 
        'xǁFailureHandlerǁhandle__mutmut_81': xǁFailureHandlerǁhandle__mutmut_81, 
        'xǁFailureHandlerǁhandle__mutmut_82': xǁFailureHandlerǁhandle__mutmut_82, 
        'xǁFailureHandlerǁhandle__mutmut_83': xǁFailureHandlerǁhandle__mutmut_83, 
        'xǁFailureHandlerǁhandle__mutmut_84': xǁFailureHandlerǁhandle__mutmut_84, 
        'xǁFailureHandlerǁhandle__mutmut_85': xǁFailureHandlerǁhandle__mutmut_85, 
        'xǁFailureHandlerǁhandle__mutmut_86': xǁFailureHandlerǁhandle__mutmut_86, 
        'xǁFailureHandlerǁhandle__mutmut_87': xǁFailureHandlerǁhandle__mutmut_87, 
        'xǁFailureHandlerǁhandle__mutmut_88': xǁFailureHandlerǁhandle__mutmut_88, 
        'xǁFailureHandlerǁhandle__mutmut_89': xǁFailureHandlerǁhandle__mutmut_89, 
        'xǁFailureHandlerǁhandle__mutmut_90': xǁFailureHandlerǁhandle__mutmut_90, 
        'xǁFailureHandlerǁhandle__mutmut_91': xǁFailureHandlerǁhandle__mutmut_91, 
        'xǁFailureHandlerǁhandle__mutmut_92': xǁFailureHandlerǁhandle__mutmut_92, 
        'xǁFailureHandlerǁhandle__mutmut_93': xǁFailureHandlerǁhandle__mutmut_93, 
        'xǁFailureHandlerǁhandle__mutmut_94': xǁFailureHandlerǁhandle__mutmut_94, 
        'xǁFailureHandlerǁhandle__mutmut_95': xǁFailureHandlerǁhandle__mutmut_95, 
        'xǁFailureHandlerǁhandle__mutmut_96': xǁFailureHandlerǁhandle__mutmut_96, 
        'xǁFailureHandlerǁhandle__mutmut_97': xǁFailureHandlerǁhandle__mutmut_97, 
        'xǁFailureHandlerǁhandle__mutmut_98': xǁFailureHandlerǁhandle__mutmut_98, 
        'xǁFailureHandlerǁhandle__mutmut_99': xǁFailureHandlerǁhandle__mutmut_99, 
        'xǁFailureHandlerǁhandle__mutmut_100': xǁFailureHandlerǁhandle__mutmut_100, 
        'xǁFailureHandlerǁhandle__mutmut_101': xǁFailureHandlerǁhandle__mutmut_101, 
        'xǁFailureHandlerǁhandle__mutmut_102': xǁFailureHandlerǁhandle__mutmut_102, 
        'xǁFailureHandlerǁhandle__mutmut_103': xǁFailureHandlerǁhandle__mutmut_103, 
        'xǁFailureHandlerǁhandle__mutmut_104': xǁFailureHandlerǁhandle__mutmut_104, 
        'xǁFailureHandlerǁhandle__mutmut_105': xǁFailureHandlerǁhandle__mutmut_105, 
        'xǁFailureHandlerǁhandle__mutmut_106': xǁFailureHandlerǁhandle__mutmut_106, 
        'xǁFailureHandlerǁhandle__mutmut_107': xǁFailureHandlerǁhandle__mutmut_107, 
        'xǁFailureHandlerǁhandle__mutmut_108': xǁFailureHandlerǁhandle__mutmut_108, 
        'xǁFailureHandlerǁhandle__mutmut_109': xǁFailureHandlerǁhandle__mutmut_109, 
        'xǁFailureHandlerǁhandle__mutmut_110': xǁFailureHandlerǁhandle__mutmut_110, 
        'xǁFailureHandlerǁhandle__mutmut_111': xǁFailureHandlerǁhandle__mutmut_111, 
        'xǁFailureHandlerǁhandle__mutmut_112': xǁFailureHandlerǁhandle__mutmut_112, 
        'xǁFailureHandlerǁhandle__mutmut_113': xǁFailureHandlerǁhandle__mutmut_113, 
        'xǁFailureHandlerǁhandle__mutmut_114': xǁFailureHandlerǁhandle__mutmut_114, 
        'xǁFailureHandlerǁhandle__mutmut_115': xǁFailureHandlerǁhandle__mutmut_115, 
        'xǁFailureHandlerǁhandle__mutmut_116': xǁFailureHandlerǁhandle__mutmut_116, 
        'xǁFailureHandlerǁhandle__mutmut_117': xǁFailureHandlerǁhandle__mutmut_117
    }
    xǁFailureHandlerǁhandle__mutmut_orig.__name__ = 'xǁFailureHandlerǁhandle'

    def handle_from_exception(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        args = [exc, vector_id]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁFailureHandlerǁhandle_from_exception__mutmut_orig'), object.__getattribute__(self, 'xǁFailureHandlerǁhandle_from_exception__mutmut_mutants'), args, kwargs, self)

    def xǁFailureHandlerǁhandle_from_exception__mutmut_orig(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_1(
        self,
        exc:       RuntimeError,
        vector_id: str = "XXXX",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_2(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = None
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_3(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(None)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_4(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = None
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_5(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "XXHARNESS_INTERNAL_ERRORXX"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_6(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "harness_internal_error"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_7(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") and msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_8(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(None) or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_9(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type - ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_10(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + "XX:XX") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_11(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(None):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_12(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type - " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_13(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + "XX XX"):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_14(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = None
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_15(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                return
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_16(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=None,
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_17(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=None,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_18(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            vector_id=None,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_19(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            detail=msg,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_20(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            vector_id=vector_id,
        )

    def xǁFailureHandlerǁhandle_from_exception__mutmut_21(
        self,
        exc:       RuntimeError,
        vector_id: str = "",
    ) -> None:
        """
        Parse failure_type_id from RuntimeError message and invoke handle().

        Convention: RuntimeError messages from this harness start with
        FAILURE_TYPE_ID: detail
        """
        msg = str(exc)
        failure_type_id = "HARNESS_INTERNAL_ERROR"
        for known_type in FAILURE_TYPES:
            if msg.startswith(known_type + ":") or msg.startswith(known_type + " "):
                failure_type_id = known_type
                break
        self.handle(
            failure_type_id=failure_type_id,
            detail=msg,
            )
    
    xǁFailureHandlerǁhandle_from_exception__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁFailureHandlerǁhandle_from_exception__mutmut_1': xǁFailureHandlerǁhandle_from_exception__mutmut_1, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_2': xǁFailureHandlerǁhandle_from_exception__mutmut_2, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_3': xǁFailureHandlerǁhandle_from_exception__mutmut_3, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_4': xǁFailureHandlerǁhandle_from_exception__mutmut_4, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_5': xǁFailureHandlerǁhandle_from_exception__mutmut_5, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_6': xǁFailureHandlerǁhandle_from_exception__mutmut_6, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_7': xǁFailureHandlerǁhandle_from_exception__mutmut_7, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_8': xǁFailureHandlerǁhandle_from_exception__mutmut_8, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_9': xǁFailureHandlerǁhandle_from_exception__mutmut_9, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_10': xǁFailureHandlerǁhandle_from_exception__mutmut_10, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_11': xǁFailureHandlerǁhandle_from_exception__mutmut_11, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_12': xǁFailureHandlerǁhandle_from_exception__mutmut_12, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_13': xǁFailureHandlerǁhandle_from_exception__mutmut_13, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_14': xǁFailureHandlerǁhandle_from_exception__mutmut_14, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_15': xǁFailureHandlerǁhandle_from_exception__mutmut_15, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_16': xǁFailureHandlerǁhandle_from_exception__mutmut_16, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_17': xǁFailureHandlerǁhandle_from_exception__mutmut_17, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_18': xǁFailureHandlerǁhandle_from_exception__mutmut_18, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_19': xǁFailureHandlerǁhandle_from_exception__mutmut_19, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_20': xǁFailureHandlerǁhandle_from_exception__mutmut_20, 
        'xǁFailureHandlerǁhandle_from_exception__mutmut_21': xǁFailureHandlerǁhandle_from_exception__mutmut_21
    }
    xǁFailureHandlerǁhandle_from_exception__mutmut_orig.__name__ = 'xǁFailureHandlerǁhandle_from_exception'
