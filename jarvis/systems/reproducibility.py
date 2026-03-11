# =============================================================================
# jarvis/systems/reproducibility.py
# Authority: FAS v6.0.1 -- S15.5, Reproducibility Controller
# =============================================================================
#
# SCOPE
# -----
# Guarantees bit-for-bit reproducibility across CPUs/GPUs and system
# configurations.  Provides float precision enforcement, array rounding,
# run comparison, and system fingerprinting.
#
# Public symbols:
#   FLOAT_PRECISION            Decimal places for reproducible floats (15)
#   TOLERANCE_FLOAT_COMPARE    Tolerance for float comparison (1e-14)
#   ReproducibilityResult      Frozen dataclass for verification result
#   ReproducibilityController  Controller class
#
# GOVERNANCE
# ----------
# Reproducibility is a certification gate.  Failure blocks deployment.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, hashlib, math, sys, platform
#   external:  numpy
#   internal:  NONE
#   PROHIBITED: logging, random, file IO, network IO, datetime.now()
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  All arithmetic deterministic (np.float64 fixed precision).
# DET-06  Fixed literals (FLOAT_PRECISION, TOLERANCE) not parametrisable.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

import hashlib
import math
import platform
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Union

import numpy as np

__all__ = [
    "FLOAT_PRECISION",
    "TOLERANCE_FLOAT_COMPARE",
    "ReproducibilityResult",
    "ReproducibilityController",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

FLOAT_PRECISION: int = 15
"""Decimal places for reproducible float rounding."""

TOLERANCE_FLOAT_COMPARE: float = 1e-14
"""Absolute tolerance for float comparison across runs."""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class ReproducibilityResult:
    """
    Result of a reproducibility verification.

    Fields:
        reproducible:  True if both outputs match within tolerance.
        mismatches:    List of mismatch descriptions (empty if reproducible).
        fingerprint:   System fingerprint used for the comparison.
    """
    reproducible: bool
    mismatches: tuple
    fingerprint: str


# =============================================================================
# SECTION 3 -- CONTROLLER
# =============================================================================

class ReproducibilityController:
    """
    Guarantees bit-for-bit reproducibility.

    Strategy:
    1. Float precision limited to FLOAT_PRECISION decimal places.
    2. Arrays rounded via np.around.
    3. Verification via tolerance-based comparison.
    4. System fingerprint for audit trail.

    Stateless: all inputs passed explicitly.
    """

    def ensure_reproducible(self, value: float) -> float:
        """
        Round a float to defined precision for reproducibility.

        Args:
            value: Float value to round.

        Returns:
            Float rounded to FLOAT_PRECISION decimal places.

        Raises:
            TypeError:  If value is not numeric.
            ValueError: If value is NaN or Inf.
        """
        if not isinstance(value, (int, float)):
            raise TypeError(
                f"value must be numeric, got {type(value).__name__}"
            )
        fval = float(value)
        if math.isnan(fval):
            raise ValueError("Cannot make NaN reproducible")
        if math.isinf(fval):
            raise ValueError("Cannot make Inf reproducible")
        return round(fval, FLOAT_PRECISION)

    def ensure_reproducible_array(self, arr: np.ndarray) -> np.ndarray:
        """
        Round a numpy array to defined precision for reproducibility.

        Args:
            arr: numpy array.

        Returns:
            Array rounded to FLOAT_PRECISION decimal places.

        Raises:
            TypeError:  If arr is not a numpy ndarray.
            ValueError: If arr contains NaN or Inf.
        """
        if not isinstance(arr, np.ndarray):
            raise TypeError(
                f"arr must be a numpy ndarray, got {type(arr).__name__}"
            )
        if np.any(np.isnan(arr)):
            raise ValueError("Array contains NaN — cannot make reproducible")
        if np.any(np.isinf(arr)):
            raise ValueError("Array contains Inf — cannot make reproducible")
        return np.around(arr, FLOAT_PRECISION)

    def verify_reproducibility(
        self,
        run1_output: Any,
        run2_output: Any,
    ) -> ReproducibilityResult:
        """
        Verify identical results between two runs.

        Handles float, np.ndarray, dict, list, and direct equality.

        Args:
            run1_output: Output from first run.
            run2_output: Output from second run.

        Returns:
            ReproducibilityResult.
        """
        mismatches: List[str] = []
        self._compare("root", run1_output, run2_output, mismatches)
        fingerprint = self.get_system_fingerprint()
        return ReproducibilityResult(
            reproducible=len(mismatches) == 0,
            mismatches=tuple(mismatches),
            fingerprint=fingerprint,
        )

    def _compare(
        self,
        path: str,
        a: Any,
        b: Any,
        mismatches: List[str],
    ) -> None:
        """Recursively compare two values."""
        if isinstance(a, float) and isinstance(b, float):
            if math.isnan(a) or math.isnan(b):
                if not (math.isnan(a) and math.isnan(b)):
                    mismatches.append(f"{path}: NaN mismatch")
                return
            if abs(a - b) >= TOLERANCE_FLOAT_COMPARE:
                mismatches.append(
                    f"{path}: {a} != {b} (diff={abs(a - b):.2e})"
                )
        elif isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
            if a.shape != b.shape:
                mismatches.append(
                    f"{path}: shape mismatch {a.shape} vs {b.shape}"
                )
            elif not np.allclose(a, b, atol=TOLERANCE_FLOAT_COMPARE, equal_nan=True):
                max_diff = float(np.max(np.abs(a - b)))
                mismatches.append(
                    f"{path}: array mismatch (max_diff={max_diff:.2e})"
                )
        elif isinstance(a, dict) and isinstance(b, dict):
            if set(a.keys()) != set(b.keys()):
                mismatches.append(
                    f"{path}: key mismatch {set(a.keys())} vs {set(b.keys())}"
                )
            else:
                for key in sorted(a.keys(), key=str):
                    self._compare(f"{path}.{key}", a[key], b[key], mismatches)
        elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            if len(a) != len(b):
                mismatches.append(
                    f"{path}: length mismatch {len(a)} vs {len(b)}"
                )
            else:
                for i, (va, vb) in enumerate(zip(a, b)):
                    self._compare(f"{path}[{i}]", va, vb, mismatches)
        elif type(a) != type(b):
            mismatches.append(
                f"{path}: type mismatch {type(a).__name__} vs {type(b).__name__}"
            )
        else:
            if a != b:
                mismatches.append(f"{path}: {a!r} != {b!r}")

    def get_system_fingerprint(self) -> str:
        """
        Generate system fingerprint for reproducibility audit.

        Components: Python version, platform machine, numpy version.

        Returns:
            SHA-256 hash of fingerprint (first 16 hex chars).
        """
        components = [
            sys.version,
            platform.machine(),
            np.__version__,
        ]
        raw = "|".join(components)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
