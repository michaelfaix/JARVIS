# =============================================================================
# JARVIS v6.1.0 -- REGIME DURATION MODEL
# File:   jarvis/intelligence/regime_duration_model.py
# Version: 1.0.0
# =============================================================================
#
# SCOPE
# -----
# Deterministic computation of regime duration stress metrics.
# Provides DecisionQualityEngine with regime age analysis:
#   - regime_age_ratio:              current age / historical average duration
#   - duration_z_score:              z-score of age vs historical distribution
#   - transition_acceleration_flag:  True when |z_score| >= DURATION_STRESS_Z_LIMIT
#
# CLASSIFICATION: Phase 3 — Decision Quality sub-component.
# Output feeds ONLY DecisionQualityEngine.
# May NOT directly alter Risk Engine thresholds.
#
# PUBLIC SYMBOLS
# --------------
#   DURATION_STRESS_Z_LIMIT   float constant (2.0)
#   RegimeDurationResult      frozen dataclass — computation output
#   RegimeDurationModel       stateless model — compute() method
#
# GOVERNANCE CONSTRAINTS
# ----------------------
#   - DETERMINISTIC: identical inputs produce identical outputs.
#   - SNAPSHOT-ONLY: operates on passed-in values; does not read live buffers.
#   - NO STATE MUTATION: never calls ctrl.update().
#   - NO EXECUTION SEMANTICS: output is purely analytical metadata.
#   - OUTPUT ROUTING: RegimeDurationResult is consumed ONLY by
#     DecisionQualityEngine. No other layer may read it directly.
#   - FORBIDDEN: stochastic transition simulation, Monte Carlo,
#     random seeds, live feed access, broker concepts.
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  No I/O, no logging, no datetime.now().
# DET-05  All branching is deterministic.
# DET-06  Fixed literals are not parametrised.
# DET-07  Same inputs = bit-identical outputs.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No numpy / scipy
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
#   No broker / order / account references
#   No direct Risk Engine threshold modification
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

DURATION_STRESS_Z_LIMIT: float = 2.0
"""
Z-score threshold at which RegimeDurationModel sets
transition_acceleration_flag = True.
Signals that the current regime has exceeded its statistically expected
lifespan (or is unusually short-lived).
Does NOT directly modify Risk Engine thresholds.
Fixed literal per DET-06 — not parametrisable.
"""


# ---------------------------------------------------------------------------
# REGIME DURATION RESULT (frozen)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegimeDurationResult:
    """
    Frozen output of RegimeDurationModel.
    All fields are deterministically computed from snapshot inputs.
    No randomness. No time-dependent non-deterministic logic.

    Attributes:
        regime_age_ratio:
            Current regime age / historical_avg_duration.
            1.0 = regime has lived exactly its historical average lifespan.
            > 1.0 = regime is aging beyond its historical norm.
            Clipped to [0.0, 5.0] for numerical stability.

        duration_z_score:
            (current_age - historical_avg_duration) / historical_std_duration
            Z-score of current regime age relative to its historical
            distribution. Clipped to [-5.0, 5.0].

        transition_acceleration_flag:
            True when |duration_z_score| >= DURATION_STRESS_Z_LIMIT (2.0).
            Signals the regime has significantly exceeded or fallen short
            of its historical mean duration.
            Does NOT trigger any Risk Engine action directly.
    """
    regime_age_ratio: float
    duration_z_score: float
    transition_acceleration_flag: bool


# ---------------------------------------------------------------------------
# REGIME DURATION MODEL (stateless)
# ---------------------------------------------------------------------------

class RegimeDurationModel:
    """
    Deterministic regime duration stress analyser.

    Computes how long the current regime has been active relative to
    historical norms, producing a frozen RegimeDurationResult.

    Stateless: all inputs are passed explicitly to compute().
    No internal buffers, no mutable state, no side effects.

    Performance budget: < 2 ms per call.
    """

    DURATION_STRESS_Z_LIMIT: float = DURATION_STRESS_Z_LIMIT

    def compute(
        self,
        regime_start_timestamp: float,
        current_timestamp: float,
        historical_avg_duration: float,
        historical_std_duration: float,
    ) -> RegimeDurationResult:
        """
        Deterministically compute regime duration stress metrics.

        Args:
            regime_start_timestamp: Timestamp when current regime began
                                    (unix epoch seconds, snapshot value).
                                    Must be <= current_timestamp.
            current_timestamp:      Snapshot timestamp at evaluation time
                                    (unix epoch seconds).
            historical_avg_duration: Rolling mean of past regime durations
                                     for this regime type (seconds).
                                     Must be > 0.
            historical_std_duration: Rolling std of past regime durations
                                     (seconds). Clipped to min 1.0 to
                                     avoid division by zero.

        Returns:
            RegimeDurationResult (frozen, deterministic).

        Raises:
            ValueError: if current_timestamp < regime_start_timestamp,
                        or historical_avg_duration <= 0.
        """
        # --- Input validation ---
        if current_timestamp < regime_start_timestamp:
            raise ValueError(
                "current_timestamp must be >= regime_start_timestamp. "
                f"Got current={current_timestamp}, start={regime_start_timestamp}"
            )
        if historical_avg_duration <= 0.0:
            raise ValueError(
                f"historical_avg_duration must be > 0. "
                f"Got {historical_avg_duration}"
            )

        # --- Computation ---
        current_age: float = current_timestamp - regime_start_timestamp

        # Safe std (floor at 1.0 to prevent division by zero)
        std_safe: float = max(historical_std_duration, 1.0)

        # Regime age ratio: clipped to [0.0, 5.0]
        age_ratio: float = float(
            max(0.0, min(5.0, current_age / historical_avg_duration))
        )

        # Z-score: clipped to [-5.0, 5.0]
        z_score: float = float(
            max(-5.0, min(5.0,
                (current_age - historical_avg_duration) / std_safe))
        )

        # Acceleration flag
        acceleration_flag: bool = abs(z_score) >= self.DURATION_STRESS_Z_LIMIT

        return RegimeDurationResult(
            regime_age_ratio=age_ratio,
            duration_z_score=z_score,
            transition_acceleration_flag=acceleration_flag,
        )


__all__ = [
    "DURATION_STRESS_Z_LIMIT",
    "RegimeDurationResult",
    "RegimeDurationModel",
]
