#!/usr/bin/env python3
# =============================================================================
# JARVIS v6.1.0 -- DVH CI GATE
# File:   jarvis/verification/ci_dvh_gate.py
# Version: 1.0.0
# =============================================================================
#
# PURPOSE
# -------
# CI enforcement script. Runs the Deterministic Verification Harness and
# exits with code 0 (PASS) or 1 (FAIL / ERROR).
#
# Intended for CI integration:
#   python -m jarvis.verification.ci_dvh_gate
#
# Exit codes:
#   0 -- DVH PASS: all vectors pass, BIC and CCV pass.
#   1 -- DVH FAIL or ERROR: CI must block merge.
#
# No I/O beyond stdout/stderr and the runs/ directory (via run_harness).
# No network calls. No external dependencies beyond stdlib and numpy.
# =============================================================================

from __future__ import annotations

import json
import pathlib
import sys
import importlib


_MANIFEST_PATH   = pathlib.Path(__file__).parent.parent / "risk" / "THRESHOLD_MANIFEST.json"
_MODULE_VERSION  = "6.1.0"
_RUNS_DIR        = pathlib.Path(__file__).parent / "runs"
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


def main() -> int:
    args = []# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_main__mutmut_orig, x_main__mutmut_mutants, args, kwargs, None)


def x_main__mutmut_orig() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_1() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = None
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_2() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module(None)
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_3() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("XXjarvis.verification.run_harnessXX")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_4() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("JARVIS.VERIFICATION.RUN_HARNESS")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_5() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = None
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_6() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(None, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_7() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, None, None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_8() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr("run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_9() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_10() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", )
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_11() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "XXrun_harnessXX", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_12() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "RUN_HARNESS", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_13() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is not None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_14() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print(None, file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_15() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=None)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_16() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print(file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_17() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", )
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_18() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("XXCI-DVH-GATE ERROR: run_harness.run_harness() not found.XX", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_19() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("ci-dvh-gate error: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_20() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: RUN_HARNESS.RUN_HARNESS() NOT FOUND.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_21() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 2

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_22() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = None

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_23() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=None,
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_24() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=None,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_25() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=None,
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_26() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_27() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_28() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_29() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(None),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_30() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(None),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_31() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result != 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_32() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 1:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_33() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(None)
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_34() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 1
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_35() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(None, file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_36() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=None)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_37() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_38() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", )
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_39() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 2

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 1


def x_main__mutmut_40() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(None, file=sys.stderr)
        return 1


def x_main__mutmut_41() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=None)
        return 1


def x_main__mutmut_42() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(file=sys.stderr)
        return 1


def x_main__mutmut_43() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", )
        return 1


def x_main__mutmut_44() -> int:
    """
    Run DVH and return exit code.

    Returns:
        0 if DVH result is PASS.
        1 if DVH result is FAIL, ERROR, or an exception occurs.
    """
    try:
        # Import run_harness dynamically to avoid circular imports at module level.
        run_harness_mod = importlib.import_module("jarvis.verification.run_harness")
        run_fn = getattr(run_harness_mod, "run_harness", None)
        if run_fn is None:
            print("CI-DVH-GATE ERROR: run_harness.run_harness() not found.", file=sys.stderr)
            return 1

        result = run_fn(
            manifest_path=str(_MANIFEST_PATH),
            module_version=_MODULE_VERSION,
            runs_dir=str(_RUNS_DIR),
        )

        if result == 0:
            print(f"CI-DVH-GATE: DVH result=PASS. Merge permitted.")
            return 0
        else:
            print(f"CI-DVH-GATE: DVH result={result}. Merge BLOCKED.", file=sys.stderr)
            return 1

    except Exception as exc:  # noqa: BLE001
        print(f"CI-DVH-GATE EXCEPTION: {exc}", file=sys.stderr)
        return 2

x_main__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_main__mutmut_1': x_main__mutmut_1, 
    'x_main__mutmut_2': x_main__mutmut_2, 
    'x_main__mutmut_3': x_main__mutmut_3, 
    'x_main__mutmut_4': x_main__mutmut_4, 
    'x_main__mutmut_5': x_main__mutmut_5, 
    'x_main__mutmut_6': x_main__mutmut_6, 
    'x_main__mutmut_7': x_main__mutmut_7, 
    'x_main__mutmut_8': x_main__mutmut_8, 
    'x_main__mutmut_9': x_main__mutmut_9, 
    'x_main__mutmut_10': x_main__mutmut_10, 
    'x_main__mutmut_11': x_main__mutmut_11, 
    'x_main__mutmut_12': x_main__mutmut_12, 
    'x_main__mutmut_13': x_main__mutmut_13, 
    'x_main__mutmut_14': x_main__mutmut_14, 
    'x_main__mutmut_15': x_main__mutmut_15, 
    'x_main__mutmut_16': x_main__mutmut_16, 
    'x_main__mutmut_17': x_main__mutmut_17, 
    'x_main__mutmut_18': x_main__mutmut_18, 
    'x_main__mutmut_19': x_main__mutmut_19, 
    'x_main__mutmut_20': x_main__mutmut_20, 
    'x_main__mutmut_21': x_main__mutmut_21, 
    'x_main__mutmut_22': x_main__mutmut_22, 
    'x_main__mutmut_23': x_main__mutmut_23, 
    'x_main__mutmut_24': x_main__mutmut_24, 
    'x_main__mutmut_25': x_main__mutmut_25, 
    'x_main__mutmut_26': x_main__mutmut_26, 
    'x_main__mutmut_27': x_main__mutmut_27, 
    'x_main__mutmut_28': x_main__mutmut_28, 
    'x_main__mutmut_29': x_main__mutmut_29, 
    'x_main__mutmut_30': x_main__mutmut_30, 
    'x_main__mutmut_31': x_main__mutmut_31, 
    'x_main__mutmut_32': x_main__mutmut_32, 
    'x_main__mutmut_33': x_main__mutmut_33, 
    'x_main__mutmut_34': x_main__mutmut_34, 
    'x_main__mutmut_35': x_main__mutmut_35, 
    'x_main__mutmut_36': x_main__mutmut_36, 
    'x_main__mutmut_37': x_main__mutmut_37, 
    'x_main__mutmut_38': x_main__mutmut_38, 
    'x_main__mutmut_39': x_main__mutmut_39, 
    'x_main__mutmut_40': x_main__mutmut_40, 
    'x_main__mutmut_41': x_main__mutmut_41, 
    'x_main__mutmut_42': x_main__mutmut_42, 
    'x_main__mutmut_43': x_main__mutmut_43, 
    'x_main__mutmut_44': x_main__mutmut_44
}
x_main__mutmut_orig.__name__ = 'x_main'


if __name__ == "__main__":
    sys.exit(main())
