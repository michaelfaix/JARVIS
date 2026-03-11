# =============================================================================
# jarvis/intelligence/volatility_markov.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, lines 8727-8779
# =============================================================================
#
# SCOPE
# -----
# Markov transition matrix for volatility state dynamics.
# Used ONLY for probability scoring, NOT for stochastic simulation.
# Deterministic frequency counting from observed NVU history.
#
# Public symbols:
#   VOL_STATES                   Tuple of volatility state labels
#   N_VOL_STATES                 Number of volatility states
#   classify_vol_state           Classify NVU-normalized value to state
#   VolatilityTransitionMatrix   Frozen dataclass for MxM probabilities
#   VolatilityTransitionEstimator Estimator using frequency counting
#
# GOVERNANCE
# ----------
# Output feeds ONLY:
#   - P6 Strategy Layer (read-only input)
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
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-06  Fixed threshold literals are not parametrisable.
# DET-07  Same input sequence = identical matrix.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from jarvis.core.schema_versions import GLOBAL_STATE_VERSION

__all__ = [
    "VOL_STATES",
    "N_VOL_STATES",
    "classify_vol_state",
    "VolatilityTransitionMatrix",
    "VolatilityTransitionEstimator",
]


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

VOL_STATES: Tuple[str, ...] = ("LOW", "MEDIUM", "HIGH", "EXTREME")
"""Volatility state bins (immutable tuple, 4 states)."""

N_VOL_STATES: int = len(VOL_STATES)
"""Number of volatility states."""


# =============================================================================
# SECTION 2 -- CLASSIFICATION
# =============================================================================

def classify_vol_state(nvu_normalized: float) -> str:
    """
    Deterministic classification of volatility state.

    Thresholds (NVU-normalized, DET-06 fixed literals):
        LOW:      nvu < 1.0
        MEDIUM:   1.0 <= nvu < 2.0
        HIGH:     2.0 <= nvu < 3.0
        EXTREME:  nvu >= 3.0  (FM-02 trigger threshold)

    Args:
        nvu_normalized: NVU-normalized volatility value (>= 0).

    Returns:
        Volatility state string ("LOW", "MEDIUM", "HIGH", "EXTREME").

    Raises:
        TypeError:  If nvu_normalized is not numeric.
        ValueError: If nvu_normalized is negative.
    """
    if not isinstance(nvu_normalized, (int, float)):
        raise TypeError(
            f"nvu_normalized must be numeric, "
            f"got {type(nvu_normalized).__name__}"
        )
    if nvu_normalized < 0:
        raise ValueError(
            f"nvu_normalized must be >= 0, got {nvu_normalized}"
        )

    if nvu_normalized < 1.0:
        return "LOW"
    elif nvu_normalized < 2.0:
        return "MEDIUM"
    elif nvu_normalized < 3.0:
        return "HIGH"
    else:
        return "EXTREME"


# =============================================================================
# SECTION 3 -- VOLATILITY TRANSITION MATRIX
# =============================================================================

@dataclass(frozen=True)
class VolatilityTransitionMatrix:
    """
    Immutable MxM volatility state transition probability matrix.

    Fields:
        states:   Volatility state labels (M,).
        matrix:   MxM transition probabilities; rows sum to 1.0.
        n_obs:    Number of observed transitions used for estimation.
        version:  Schema version from schema_versions.py.
    """
    states:  Tuple[str, ...]
    matrix:  Tuple[Tuple[float, ...], ...]
    n_obs:   int
    version: str

    def __post_init__(self) -> None:
        """Validate matrix shape and row normalization."""
        m = len(self.states)
        if len(self.matrix) != m:
            raise ValueError(
                f"Matrix row count ({len(self.matrix)}) must equal "
                f"state count ({m})"
            )
        for i, row in enumerate(self.matrix):
            if len(row) != m:
                raise ValueError(
                    f"Matrix row {i} length ({len(row)}) must equal "
                    f"state count ({m})"
                )

        arr = np.array(self.matrix, dtype=np.float64)
        row_sums = arr.sum(axis=1)
        if not np.allclose(row_sums, 1.0, atol=1e-6):
            raise ValueError(
                f"VolatilityTransitionMatrix rows must sum to 1.0; "
                f"got row sums: {row_sums.tolist()}"
            )

    def transition_probability(
        self, from_state: str, to_state: str,
    ) -> float:
        """
        Deterministic lookup of P(to_state | from_state).

        Args:
            from_state: Source volatility state.
            to_state:   Target volatility state.

        Returns:
            Transition probability in [0, 1].

        Raises:
            ValueError: If state not found.
        """
        try:
            i = self.states.index(from_state)
        except ValueError:
            raise ValueError(
                f"from_state {from_state!r} not in states: "
                f"{list(self.states)}"
            )
        try:
            j = self.states.index(to_state)
        except ValueError:
            raise ValueError(
                f"to_state {to_state!r} not in states: "
                f"{list(self.states)}"
            )
        return self.matrix[i][j]

    def prob_fm02_trigger(self, current_state: str) -> float:
        """
        Probability of FM-02 vol spike trigger (transition to EXTREME).

        Args:
            current_state: Current volatility state.

        Returns:
            P(EXTREME | current_state) in [0, 1].

        Raises:
            ValueError: If current_state not found.
        """
        return self.transition_probability(current_state, "EXTREME")


# =============================================================================
# SECTION 4 -- VOLATILITY TRANSITION ESTIMATOR
# =============================================================================

class VolatilityTransitionEstimator:
    """
    Estimates volatility transition matrix via deterministic frequency counting.

    Accepts either pre-classified state sequences or raw NVU values.
    Uses Laplace smoothing to avoid zero-probability transitions.
    """

    def estimate_from_states(
        self,
        observed_states: List[str],
        states: Optional[Tuple[str, ...]] = None,
        laplace_smoothing: float = 0.1,
    ) -> VolatilityTransitionMatrix:
        """
        Compute transition matrix from observed state sequence.

        Args:
            observed_states:   Observed state sequence (min 2 elements).
            states:            State labels (default: VOL_STATES).
            laplace_smoothing: Smoothing constant (>= 0.0, default 0.1).

        Returns:
            VolatilityTransitionMatrix with normalized probabilities.

        Raises:
            TypeError:  If arguments have wrong types.
            ValueError: If observed_states has < 2 elements.
            ValueError: If states is empty.
            ValueError: If laplace_smoothing < 0.
        """
        if not isinstance(observed_states, list):
            raise TypeError(
                f"observed_states must be a list, "
                f"got {type(observed_states).__name__}"
            )
        if len(observed_states) < 2:
            raise ValueError(
                f"observed_states must have >= 2 elements, "
                f"got {len(observed_states)}"
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

        if states is None:
            states = VOL_STATES
        if not states:
            raise ValueError("states must not be empty")

        m = len(states)
        idx: Dict[str, int] = {s: i for i, s in enumerate(states)}

        # Initialize counts with Laplace smoothing
        counts = np.full((m, m), float(laplace_smoothing), dtype=np.float64)
        n_obs = 0

        # Count transitions
        for t in range(len(observed_states) - 1):
            fr = observed_states[t]
            to = observed_states[t + 1]
            if fr in idx and to in idx:
                counts[idx[fr], idx[to]] += 1.0
                n_obs += 1

        # Normalize rows
        row_sums = counts.sum(axis=1, keepdims=True)
        matrix_arr = counts / np.maximum(row_sums, 1e-10)

        return VolatilityTransitionMatrix(
            states=tuple(states),
            matrix=tuple(
                tuple(float(v) for v in row)
                for row in matrix_arr
            ),
            n_obs=n_obs,
            version=GLOBAL_STATE_VERSION,
        )

    def estimate_from_nvu(
        self,
        nvu_series: List[float],
        laplace_smoothing: float = 0.1,
    ) -> VolatilityTransitionMatrix:
        """
        Compute transition matrix from raw NVU-normalized values.

        Classifies each value via classify_vol_state(), then estimates.

        Args:
            nvu_series:        NVU-normalized volatility series (min 2).
            laplace_smoothing: Smoothing constant (>= 0.0).

        Returns:
            VolatilityTransitionMatrix.

        Raises:
            TypeError:  If nvu_series is not a list.
            ValueError: If nvu_series has < 2 elements.
        """
        if not isinstance(nvu_series, list):
            raise TypeError(
                f"nvu_series must be a list, "
                f"got {type(nvu_series).__name__}"
            )
        if len(nvu_series) < 2:
            raise ValueError(
                f"nvu_series must have >= 2 elements, "
                f"got {len(nvu_series)}"
            )

        classified = [classify_vol_state(v) for v in nvu_series]
        return self.estimate_from_states(
            classified,
            laplace_smoothing=laplace_smoothing,
        )
