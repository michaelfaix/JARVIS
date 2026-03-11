# =============================================================================
# jarvis/intelligence/regime_transition.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, lines 8629-8720
# =============================================================================
#
# SCOPE
# -----
# Markov-style NxN transition probability matrix for regime dynamics.
# Built via deterministic frequency counting from observed regime sequences.
# No random sampling, no stochastic simulation.
#
# Public symbols:
#   CANONICAL_REGIMES           Canonical regime ordering (5 regimes)
#   N_REGIMES                   Number of canonical regimes
#   RegimeTransitionMatrix      Frozen dataclass for NxN probabilities
#   RegimeTransitionEstimator   Estimator using frequency counting
#
# GOVERNANCE
# ----------
# Output feeds ONLY:
#   - P8 Confidence Engine (probability weighting)
#   - P9 Visual Output (display)
# Must NOT trigger execution or strategy switching directly.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, typing
#   external:  numpy
#   internal:  jarvis.core.schema_versions (GLOBAL_STATE_VERSION)
#   PROHIBITED: logging, random, file IO, network IO, datetime.now()
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations (pure frequency counting).
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-07  Same input sequence = identical matrix.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from jarvis.core.schema_versions import GLOBAL_STATE_VERSION

__all__ = [
    "CANONICAL_REGIMES",
    "N_REGIMES",
    "RegimeTransitionMatrix",
    "RegimeTransitionEstimator",
]


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

CANONICAL_REGIMES: List[str] = [
    "TRENDING", "RANGING", "HIGH_VOL", "SHOCK", "UNKNOWN",
]
"""Canonical regime ordering for transition matrix."""

N_REGIMES: int = len(CANONICAL_REGIMES)
"""Number of canonical regimes."""


# =============================================================================
# SECTION 2 -- REGIME TRANSITION MATRIX
# =============================================================================

@dataclass(frozen=True)
class RegimeTransitionMatrix:
    """
    Immutable NxN regime transition probability matrix.

    Fields:
        regimes:  Canonical regime labels (N,).
        matrix:   NxN transition probabilities; rows sum to 1.0.
        n_obs:    Number of observed transitions used for estimation.
        version:  Schema version from schema_versions.py.
    """
    regimes: Tuple[str, ...]
    matrix:  Tuple[Tuple[float, ...], ...]
    n_obs:   int
    version: str

    def __post_init__(self) -> None:
        """Validate matrix shape and row normalization."""
        n = len(self.regimes)
        if len(self.matrix) != n:
            raise ValueError(
                f"Matrix row count ({len(self.matrix)}) must equal "
                f"regime count ({n})"
            )
        for i, row in enumerate(self.matrix):
            if len(row) != n:
                raise ValueError(
                    f"Matrix row {i} length ({len(row)}) must equal "
                    f"regime count ({n})"
                )

        # Row sums must be 1.0 within tolerance
        arr = np.array(self.matrix, dtype=np.float64)
        row_sums = arr.sum(axis=1)
        if not np.allclose(row_sums, 1.0, atol=1e-6):
            raise ValueError(
                f"RegimeTransitionMatrix rows must sum to 1.0; "
                f"got row sums: {row_sums.tolist()}"
            )

    def transition_probability(
        self, from_regime: str, to_regime: str,
    ) -> float:
        """
        Deterministic lookup of P(to_regime | from_regime).

        Args:
            from_regime: Source regime name.
            to_regime:   Target regime name.

        Returns:
            Transition probability in [0, 1].

        Raises:
            ValueError: If regime not found.
        """
        try:
            i = self.regimes.index(from_regime)
        except ValueError:
            raise ValueError(
                f"from_regime {from_regime!r} not in regimes: "
                f"{list(self.regimes)}"
            )
        try:
            j = self.regimes.index(to_regime)
        except ValueError:
            raise ValueError(
                f"to_regime {to_regime!r} not in regimes: "
                f"{list(self.regimes)}"
            )
        return self.matrix[i][j]

    def most_likely_next(self, current_regime: str) -> str:
        """
        Return regime with highest transition probability from current.

        Args:
            current_regime: Current regime name.

        Returns:
            Regime name with highest P(next | current).
            On tie, returns first in canonical order (np.argmax).

        Raises:
            ValueError: If current_regime not found.
        """
        try:
            i = self.regimes.index(current_regime)
        except ValueError:
            raise ValueError(
                f"current_regime {current_regime!r} not in regimes: "
                f"{list(self.regimes)}"
            )
        row = np.array(self.matrix[i], dtype=np.float64)
        return self.regimes[int(np.argmax(row))]


# =============================================================================
# SECTION 3 -- REGIME TRANSITION ESTIMATOR
# =============================================================================

class RegimeTransitionEstimator:
    """
    Estimates regime transition matrix via deterministic frequency counting.

    Uses Laplace smoothing to avoid zero-probability transitions.
    No stochastic sampling — pure counting.
    """

    def estimate(
        self,
        observed_regimes: List[str],
        regimes: Optional[List[str]] = None,
        laplace_smoothing: float = 0.1,
    ) -> RegimeTransitionMatrix:
        """
        Compute transition matrix from observed regime sequence.

        Args:
            observed_regimes:  Observed regime sequence (min 2 elements).
            regimes:           Regime labels (default: CANONICAL_REGIMES).
            laplace_smoothing: Smoothing constant (>= 0.0, default 0.1).

        Returns:
            RegimeTransitionMatrix with normalized probabilities.

        Raises:
            TypeError:  If arguments have wrong types.
            ValueError: If observed_regimes has < 2 elements.
            ValueError: If regimes is empty.
            ValueError: If laplace_smoothing < 0.
        """
        if not isinstance(observed_regimes, list):
            raise TypeError(
                f"observed_regimes must be a list, "
                f"got {type(observed_regimes).__name__}"
            )
        if len(observed_regimes) < 2:
            raise ValueError(
                f"observed_regimes must have >= 2 elements, "
                f"got {len(observed_regimes)}"
            )
        if not isinstance(laplace_smoothing, (int, float)):
            raise TypeError(
                f"laplace_smoothing must be numeric, "
                f"got {type(laplace_smoothing).__name__}"
            )
        if laplace_smoothing < 0:
            raise ValueError(
                f"laplace_smoothing must be >= 0, got {laplace_smoothing}"
            )

        if regimes is None:
            regimes = CANONICAL_REGIMES
        if not regimes:
            raise ValueError("regimes must not be empty")

        n = len(regimes)
        idx: Dict[str, int] = {r: i for i, r in enumerate(regimes)}

        # Initialize counts with Laplace smoothing
        counts = np.full((n, n), float(laplace_smoothing), dtype=np.float64)
        n_obs = 0

        # Count transitions
        for t in range(len(observed_regimes) - 1):
            fr = observed_regimes[t]
            to = observed_regimes[t + 1]
            if fr in idx and to in idx:
                counts[idx[fr], idx[to]] += 1.0
                n_obs += 1

        # Normalize rows
        row_sums = counts.sum(axis=1, keepdims=True)
        matrix_arr = counts / np.maximum(row_sums, 1e-10)

        # Build frozen result
        return RegimeTransitionMatrix(
            regimes=tuple(regimes),
            matrix=tuple(
                tuple(float(v) for v in row)
                for row in matrix_arr
            ),
            n_obs=n_obs,
            version=GLOBAL_STATE_VERSION,
        )
