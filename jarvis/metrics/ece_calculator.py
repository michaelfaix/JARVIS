# =============================================================================
# jarvis/metrics/ece_calculator.py — Expected Calibration Error (ECE)
#
# Authority: FAS v6.0.1, S09 (Lines 1524-1620, 3558-3620)
#
# Deterministic ECE computation via equal-frequency (adaptive) binning.
# Pure function — no stochastic operations, no side effects, no file I/O.
#
# FAS REQUIREMENTS:
#   - compute_ece_adaptive() with equal-frequency binning, 10 bins default
#   - Epsilon-floor for bin_weight division (n-guard)
#   - ECE Hard Gate < 0.05 (enforced by governance, not here)
#   - All outputs finite floats in [0, 1]
#   - Computation < 50ms
#
# DETERMINISM:
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly.
#   DET-03  No side effects.
#   DET-06  Fixed literals (N_BINS=10, MIN_SAMPLES=1) not parametrisable.
#   DET-07  Same inputs = identical output.
#
# PROHIBITED: logging, random, file IO, network IO, datetime.now()
#
# DEPENDENCIES:
#   stdlib:   dataclasses, math
#   internal: NONE
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

N_BINS: int = 10
"""Number of equal-frequency bins for ECE computation."""

MIN_SAMPLES: int = 1
"""Minimum samples required per bin (division guard)."""

ECE_HARD_GATE: float = 0.05
"""ECE threshold — values >= this indicate miscalibration."""

CONFIDENCE_FLOOR: float = 1e-6
"""Minimum confidence value (clamp floor)."""

CONFIDENCE_CEILING: float = 1.0 - 1e-6
"""Maximum confidence value (clamp ceiling)."""


# =============================================================================
# SECTION 2 -- DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class BinStatistics:
    """
    Statistics for a single calibration bin.

    Fields:
        bin_index:      Zero-based bin index.
        n_samples:      Number of samples in this bin.
        avg_confidence: Mean predicted confidence in this bin.
        avg_accuracy:   Mean observed accuracy (outcome) in this bin.
        bin_weight:     Relative weight of this bin (n_samples / total).
        abs_error:      |avg_confidence - avg_accuracy|.
    """
    bin_index: int
    n_samples: int
    avg_confidence: float
    avg_accuracy: float
    bin_weight: float
    abs_error: float


@dataclass(frozen=True)
class ECEResult:
    """
    Result of ECE computation.

    Fields:
        ece:            Expected Calibration Error in [0, 1].
        n_bins_used:    Number of non-empty bins actually used.
        n_samples:      Total number of samples processed.
        max_bin_error:  Maximum per-bin |confidence - accuracy| (MCE).
        bin_statistics: Per-bin details as immutable tuple.
        is_calibrated:  True if ece < ECE_HARD_GATE (0.05).
    """
    ece: float
    n_bins_used: int
    n_samples: int
    max_bin_error: float
    bin_statistics: Tuple[BinStatistics, ...]
    is_calibrated: bool


# =============================================================================
# SECTION 3 -- HELPERS
# =============================================================================

def _clamp_confidence(value: float) -> float:
    """Clamp confidence to [CONFIDENCE_FLOOR, CONFIDENCE_CEILING]."""
    if value < CONFIDENCE_FLOOR:
        return CONFIDENCE_FLOOR
    if value > CONFIDENCE_CEILING:
        return CONFIDENCE_CEILING
    return value


def _validate_inputs(
    confidences: Sequence[float],
    outcomes: Sequence[float],
) -> None:
    """
    Validate ECE inputs.

    Raises:
        TypeError:  If inputs are not sequences or contain non-numeric values.
        ValueError: If lengths differ, sequences are empty, or values are
                    out of range / non-finite.
    """
    if not isinstance(confidences, (list, tuple)):
        raise TypeError(
            f"confidences must be a list or tuple, "
            f"got {type(confidences).__name__}"
        )
    if not isinstance(outcomes, (list, tuple)):
        raise TypeError(
            f"outcomes must be a list or tuple, "
            f"got {type(outcomes).__name__}"
        )

    if len(confidences) == 0:
        raise ValueError("confidences must not be empty")

    if len(confidences) != len(outcomes):
        raise ValueError(
            f"confidences and outcomes must have equal length. "
            f"Got {len(confidences)} vs {len(outcomes)}"
        )

    for i, c in enumerate(confidences):
        if not isinstance(c, (int, float)):
            raise TypeError(
                f"confidences[{i}] must be numeric, "
                f"got {type(c).__name__}"
            )
        if not math.isfinite(c):
            raise ValueError(
                f"confidences[{i}] must be finite, got {c}"
            )
        if c < 0.0 or c > 1.0:
            raise ValueError(
                f"confidences[{i}] must be in [0, 1], got {c}"
            )

    for i, o in enumerate(outcomes):
        if not isinstance(o, (int, float)):
            raise TypeError(
                f"outcomes[{i}] must be numeric, "
                f"got {type(o).__name__}"
            )
        if not math.isfinite(o):
            raise ValueError(
                f"outcomes[{i}] must be finite, got {o}"
            )
        if o < 0.0 or o > 1.0:
            raise ValueError(
                f"outcomes[{i}] must be in [0, 1], got {o}"
            )


# =============================================================================
# SECTION 4 -- CORE ECE COMPUTATION
# =============================================================================

def compute_ece(
    confidences: Sequence[float],
    outcomes: Sequence[float],
) -> ECEResult:
    """
    Compute Expected Calibration Error via equal-frequency adaptive binning.

    Sorts samples by confidence, splits into N_BINS equal-frequency bins,
    and computes the weighted average of |avg_confidence - avg_accuracy|
    per bin.

    This is the FAS-mandated ``compute_ece_adaptive`` algorithm (S09,
    lines 3558-3620) with equal-frequency binning and epsilon-floor
    division guards.

    Args:
        confidences: Predicted confidence values in [0, 1].
                     One per sample.
        outcomes:    Observed binary outcomes in [0, 1].
                     1.0 = correct prediction, 0.0 = incorrect.
                     Continuous values in [0, 1] are also accepted
                     (soft labels).

    Returns:
        ECEResult (frozen dataclass) with ECE value, per-bin statistics,
        and calibration assessment.

    Raises:
        TypeError:  If inputs are not list/tuple or contain non-numeric.
        ValueError: If inputs are empty, lengths differ, or values are
                    out of range / non-finite.
    """
    _validate_inputs(confidences, outcomes)

    n: int = len(confidences)

    # Clamp confidences to [CONFIDENCE_FLOOR, CONFIDENCE_CEILING]
    clamped: List[float] = [_clamp_confidence(c) for c in confidences]

    # Sort by confidence (deterministic: stable sort, ties broken by index)
    indexed_pairs: List[Tuple[float, float, int]] = [
        (clamped[i], float(outcomes[i]), i) for i in range(n)
    ]
    indexed_pairs.sort(key=lambda x: (x[0], x[2]))

    # Equal-frequency binning
    bin_size: int = max(n // N_BINS, MIN_SAMPLES)
    bin_stats_list: List[BinStatistics] = []
    ece: float = 0.0
    max_bin_error: float = 0.0

    for b in range(N_BINS):
        start: int = b * bin_size
        end: int = (b + 1) * bin_size if b < N_BINS - 1 else n

        if start >= n:
            break

        bin_data = indexed_pairs[start:end]
        if not bin_data:
            continue

        bin_n: int = len(bin_data)
        bin_conf: float = sum(c for c, _, _ in bin_data) / bin_n
        bin_acc: float = sum(o for _, o, _ in bin_data) / bin_n
        bin_weight: float = bin_n / n
        abs_err: float = abs(bin_conf - bin_acc)

        ece += bin_weight * abs_err
        if abs_err > max_bin_error:
            max_bin_error = abs_err

        bin_stats_list.append(BinStatistics(
            bin_index=b,
            n_samples=bin_n,
            avg_confidence=bin_conf,
            avg_accuracy=bin_acc,
            bin_weight=bin_weight,
            abs_error=abs_err,
        ))

    return ECEResult(
        ece=ece,
        n_bins_used=len(bin_stats_list),
        n_samples=n,
        max_bin_error=max_bin_error,
        bin_statistics=tuple(bin_stats_list),
        is_calibrated=(ece < ECE_HARD_GATE),
    )


def compute_ece_scalar(
    confidences: Sequence[float],
    outcomes: Sequence[float],
) -> float:
    """
    Convenience wrapper: return just the ECE float value.

    Same algorithm as compute_ece() but returns only the scalar ECE.
    Useful when only the numeric value is needed without bin details.

    Args:
        confidences: Predicted confidence values in [0, 1].
        outcomes:    Observed binary outcomes in [0, 1].

    Returns:
        ECE value as float in [0, 1].

    Raises:
        TypeError:  If inputs are not list/tuple or contain non-numeric.
        ValueError: If inputs are empty, lengths differ, or values out of range.
    """
    return compute_ece(confidences, outcomes).ece
