# =============================================================================
# jarvis/models/auto_recalibrator.py — S09.5 AutoRecalibrator
#
# Authority: FAS v6.0.1, S09.5
#
# Monitors calibration quality and triggers recalibration when needed.
#
# Entry point: AutoRecalibrator.check()
# Consumes: ECE_HARD_GATE, ECE_REGIME_DRIFT_GATE from calibration module
#
# CLASSIFICATION: Tier 6 — ANALYSIS AND STRATEGY RESEARCH TOOL.
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects (beyond instance state tracking).
# DET-04  Deterministic arithmetic only.
# DET-05  All branching is deterministic.
# DET-06  Fixed literals are not parametrised.
# DET-07  Same inputs = bit-identical outputs.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No numpy / scipy / sklearn / torch
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
#
# DEPENDENCIES
# ------------
#   stdlib:   dataclasses, math
#   internal: NONE (uses constants inline to avoid circular imports)
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass


__all__ = [
    "RecalibrationTrigger",
    "AutoRecalibrator",
]


# =============================================================================
# SECTION 1 -- DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class RecalibrationTrigger:
    """
    Result of a recalibration check.

    Fields:
        triggered: True if recalibration is needed.
        reason:    One of "ECE_EXCEEDED", "DRIFT_EXCEEDED", "SCHEDULED", "NONE".
        current_ece: The current ECE value that was checked.
        threshold:   The threshold that was compared against.
        drift:       |current_ece - previous_ece|.
    """
    triggered: bool
    reason: str
    current_ece: float
    threshold: float
    drift: float

    def __post_init__(self) -> None:
        _VALID_REASONS = ("ECE_EXCEEDED", "DRIFT_EXCEEDED", "SCHEDULED", "NONE")
        if self.reason not in _VALID_REASONS:
            raise ValueError(
                f"RecalibrationTrigger.reason must be one of "
                f"{_VALID_REASONS}, got {self.reason!r}"
            )
        for name, val in [
            ("current_ece", self.current_ece),
            ("threshold", self.threshold),
            ("drift", self.drift),
        ]:
            if not isinstance(val, (int, float)):
                raise TypeError(
                    f"RecalibrationTrigger.{name} must be numeric, "
                    f"got {type(val).__name__}"
                )
            if not math.isfinite(val):
                raise ValueError(
                    f"RecalibrationTrigger.{name} must be finite, "
                    f"got {val!r}"
                )


# =============================================================================
# SECTION 2 -- AUTO-RECALIBRATOR
# =============================================================================

class AutoRecalibrator:
    """
    Monitors calibration quality and triggers recalibration when needed.

    Triggers when:
      1. current_ece >= ECE_THRESHOLD (0.05)
      2. |current_ece - previous_ece| > DRIFT_THRESHOLD (0.02)
      3. sample_count >= MIN_SAMPLES (100) and scheduled check fires

    Instance state is per-object (no global mutable state). A fresh
    AutoRecalibrator should be created per session (DET-02).
    """

    ECE_THRESHOLD: float = 0.05
    """Same as ECE_HARD_GATE."""

    DRIFT_THRESHOLD: float = 0.02
    """Same as ECE_REGIME_DRIFT_GATE."""

    MIN_SAMPLES: int = 100
    """Minimum sample count before scheduled checks apply."""

    # Blocking threshold: ECE this high means predictions are unreliable.
    _BLOCK_THRESHOLD: float = 0.10

    def __init__(self) -> None:
        self._previous_ece: float = 0.0
        self._sample_count: int = 0
        self._last_check_count: int = 0

    def check(self, current_ece: float) -> RecalibrationTrigger:
        """
        Check if recalibration is needed.

        Evaluates three conditions in priority order:
          1. ECE >= ECE_THRESHOLD  -> "ECE_EXCEEDED"
          2. |drift| > DRIFT_THRESHOLD -> "DRIFT_EXCEEDED"
          3. Scheduled (enough samples since last check) -> "SCHEDULED"
          4. Otherwise -> "NONE"

        After checking, updates previous_ece to current_ece and resets
        the scheduled check counter.

        Args:
            current_ece: Current ECE value.

        Returns:
            RecalibrationTrigger with trigger status and details.
        """
        # NaN/Inf guard: treat non-finite ECE as maximum violation
        if not isinstance(current_ece, (int, float)) or not math.isfinite(current_ece):
            current_ece = 1.0

        # Clamp negative values to 0.0
        if current_ece < 0.0:
            current_ece = 0.0

        drift = abs(current_ece - self._previous_ece)

        # Condition 1: ECE exceeds hard gate
        if current_ece >= self.ECE_THRESHOLD:
            trigger = RecalibrationTrigger(
                triggered=True,
                reason="ECE_EXCEEDED",
                current_ece=current_ece,
                threshold=self.ECE_THRESHOLD,
                drift=drift,
            )
            self._previous_ece = current_ece
            self._last_check_count = self._sample_count
            return trigger

        # Condition 2: Drift exceeds gate
        if drift > self.DRIFT_THRESHOLD:
            trigger = RecalibrationTrigger(
                triggered=True,
                reason="DRIFT_EXCEEDED",
                current_ece=current_ece,
                threshold=self.DRIFT_THRESHOLD,
                drift=drift,
            )
            self._previous_ece = current_ece
            self._last_check_count = self._sample_count
            return trigger

        # Condition 3: Scheduled check (enough samples accumulated)
        if (self._sample_count >= self.MIN_SAMPLES
                and self._sample_count - self._last_check_count
                >= self.MIN_SAMPLES):
            trigger = RecalibrationTrigger(
                triggered=True,
                reason="SCHEDULED",
                current_ece=current_ece,
                threshold=self.ECE_THRESHOLD,
                drift=drift,
            )
            self._previous_ece = current_ece
            self._last_check_count = self._sample_count
            return trigger

        # No trigger
        trigger = RecalibrationTrigger(
            triggered=False,
            reason="NONE",
            current_ece=current_ece,
            threshold=self.ECE_THRESHOLD,
            drift=drift,
        )
        self._previous_ece = current_ece
        self._last_check_count = self._sample_count
        return trigger

    def add_samples(self, n: int = 1) -> None:
        """
        Track sample count.

        Args:
            n: Number of samples to add (default 1). Must be >= 0.
        """
        if not isinstance(n, int):
            raise TypeError(f"n must be an int, got {type(n).__name__}")
        if n < 0:
            raise ValueError(f"n must be non-negative, got {n}")
        self._sample_count += n

    def should_block_predictions(self, current_ece: float) -> bool:
        """
        Check if ECE is so high that predictions should be blocked.

        Returns True if current_ece >= 2 * ECE_THRESHOLD (i.e. 0.10).

        Args:
            current_ece: Current ECE value.

        Returns:
            True if predictions should be blocked.
        """
        # NaN/Inf guard
        if not isinstance(current_ece, (int, float)) or not math.isfinite(current_ece):
            return True
        return current_ece >= self._BLOCK_THRESHOLD

    def reset(self) -> None:
        """
        Reset state after successful recalibration.

        Clears the previous ECE to 0.0 and resets counters.
        """
        self._previous_ece = 0.0
        self._sample_count = 0
        self._last_check_count = 0
