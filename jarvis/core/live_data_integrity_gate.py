# =============================================================================
# jarvis/core/live_data_integrity_gate.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, STAGE 0 DATA INTEGRITY GATE
# ARCHITECTURE.md Section 11, Stage 0
# =============================================================================
#
# SCOPE
# -----
# Mode-aware data integrity gate.  Validates incoming market data ticks/candles
# before admission to the pipeline.  Applies in MODE_LIVE_ANALYTICAL and
# MODE_HYBRID only; bypassed in MODE_HISTORICAL (data pre-validated in store).
#
# Five mandatory checks:
#   CHECK 1: Missing Data         -- OHLCV fields must be finite and > 0
#   CHECK 2: Timestamp Continuity -- sequence_id monotonically increasing
#   CHECK 3: Spread Anomaly       -- spread_bps < max_spread_threshold * 2.0
#   CHECK 4: Outlier Filter       -- robust z-score |z| < 5.0 on close
#   CHECK 5: Asset Class Valid.   -- asset_class in VALID_ASSET_CLASSES,
#                                    session_tag valid for asset_class
#
# Public symbols:
#   VALID_OPERATING_MODES          Tuple of permitted mode strings
#   GAP_MULTIPLIERS                Per-asset-class gap threshold multipliers
#   OUTLIER_Z_THRESHOLD            Robust z-score threshold (5.0)
#   OUTLIER_WINDOW                 Rolling window size for z-score (20)
#   OUTLIER_QUALITY_PENALTY        Quality reduction on outlier (0.30)
#   SPREAD_ANOMALY_FACTOR          Multiplier for spread threshold (2.0)
#   CheckResult                    Frozen dataclass for individual check result
#   GateVerdict                    Frozen dataclass for overall gate decision
#   IntegrityViolation             Frozen dataclass describing a single violation
#   check_missing_data             CHECK 1 function
#   check_timestamp_continuity     CHECK 2 function
#   check_spread_anomaly           CHECK 3 function
#   check_outlier_filter           CHECK 4 function
#   check_asset_class              CHECK 5 function
#   run_integrity_gate             Full gate: runs all 5 checks, returns GateVerdict
#
# CLASSIFICATION
# --------------
# P0 — Pure analysis and strategy research platform.
# Stateless, deterministic predicate.  Does not call ctrl.update(), does not
# emit events, does not trigger execution.  The CALLER is responsible for
# emitting FM events and updating meta_uncertainty based on the returned
# GateVerdict.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, math, typing
#   internal:  jarvis.core.data_layer (VALID_ASSET_CLASSES, VALID_SESSION_TAGS)
#   PROHIBITED: numpy, logging, random, file IO, network IO, datetime.now()
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly (rolling history as list).
# DET-03  No side effects.
# DET-04  Arithmetic: only comparisons, abs, median, MAD.
# DET-05  No datetime.now() / time.time().
# DET-06  Fixed literals (thresholds) are not parametrised.
# DET-07  Same inputs = bit-identical outputs.
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from jarvis.core.data_layer import VALID_ASSET_CLASSES, VALID_SESSION_TAGS

__all__ = [
    "VALID_OPERATING_MODES",
    "GAP_MULTIPLIERS",
    "OUTLIER_Z_THRESHOLD",
    "OUTLIER_WINDOW",
    "OUTLIER_QUALITY_PENALTY",
    "SPREAD_ANOMALY_FACTOR",
    "VALID_SESSION_TAGS_PER_ASSET_CLASS",
    "CheckResult",
    "GateVerdict",
    "IntegrityViolation",
    "check_missing_data",
    "check_timestamp_continuity",
    "check_spread_anomaly",
    "check_outlier_filter",
    "check_asset_class",
    "run_integrity_gate",
]


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

VALID_OPERATING_MODES: Tuple[str, ...] = (
    "historical",
    "live_analytical",
    "hybrid",
)

# Per-asset-class gap threshold multipliers (applied to timeframe_seconds).
# FAS S37 Stage 0 CHECK 2.
GAP_MULTIPLIERS: dict = {
    "crypto":      2,
    "forex":       5,
    "indices":     1,
    "commodities": 3,
    "rates":       2,
}

# Robust z-score threshold for outlier detection.  FAS S37 CHECK 4.
OUTLIER_Z_THRESHOLD: float = 5.0

# Rolling window size for outlier z-score computation.  FAS S37 CHECK 4.
OUTLIER_WINDOW: int = 20

# Quality score reduction on outlier detection.  FAS S37 CHECK 4.
OUTLIER_QUALITY_PENALTY: float = 0.30

# Spread anomaly factor: spread_bps must be < max_spread * this.  FAS CHECK 3.
SPREAD_ANOMALY_FACTOR: float = 2.0

# Valid session tags per asset class.  FAS S37 CHECK 5.
VALID_SESSION_TAGS_PER_ASSET_CLASS: dict = {
    "crypto":      frozenset({"CRYPTO_24_7"}),
    "forex":       frozenset({"LONDON", "NEW_YORK", "TOKYO", "SYDNEY"}),
    "indices":     frozenset({"LONDON", "NEW_YORK", "TOKYO", "PRE_MARKET",
                              "POST_MARKET", "AUCTION"}),
    "commodities": frozenset({"LONDON", "NEW_YORK", "TOKYO"}),
    "rates":       frozenset({"LONDON", "NEW_YORK", "TOKYO"}),
}


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class IntegrityViolation:
    """
    Describes a single integrity check violation.

    Fields:
        check_name:      Which check failed (e.g. "missing_data").
        failure_mode:    FM code triggered (e.g. "FM-03", "FM-06").
        field_name:      Specific field that failed, or "" for general.
        message:         Human-readable description.
    """
    check_name:   str
    failure_mode: str
    field_name:   str
    message:      str


@dataclass(frozen=True)
class CheckResult:
    """
    Result of a single integrity check.

    Fields:
        passed:          True if the check passed without issue.
        degraded:        True if the check passed but quality was reduced.
        violations:      List of IntegrityViolation (empty if passed).
        quality_penalty: Amount to subtract from quality_score (0.0 if none).
    """
    passed:          bool
    degraded:        bool
    violations:      List[IntegrityViolation]
    quality_penalty: float


@dataclass(frozen=True)
class GateVerdict:
    """
    Overall result of the Stage 0 integrity gate.

    Fields:
        admitted:            True if the data object is admitted to the pipeline.
        operating_mode:      The mode used for this evaluation.
        quality_score_adj:   Adjusted quality_score after all penalties.
        is_stale:            True if timestamp continuity detected a gap.
        spread_flagged:      True if spread anomaly was detected.
        violations:          All violations across all 5 checks.
        checks_passed:       Number of checks that passed (0-5).
        checks_total:        Always 5.
        reason:              Human-readable summary.
    """
    admitted:          bool
    operating_mode:    str
    quality_score_adj: float
    is_stale:          bool
    spread_flagged:    bool
    violations:        List[IntegrityViolation]
    checks_passed:     int
    checks_total:      int = 5
    reason:            str = ""


# =============================================================================
# SECTION 3 -- VALIDATION HELPERS
# =============================================================================

def _validate_operating_mode(operating_mode: str) -> None:
    """Raise TypeError/ValueError if operating_mode is invalid."""
    if not isinstance(operating_mode, str):
        raise TypeError(
            f"operating_mode must be a string, got {type(operating_mode).__name__}"
        )
    if operating_mode not in VALID_OPERATING_MODES:
        raise ValueError(
            f"operating_mode must be one of {VALID_OPERATING_MODES}, "
            f"got {operating_mode!r}"
        )


def _median(values: List[float]) -> float:
    """Compute median of a list of floats. List must be non-empty."""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0
    return sorted_vals[mid]


def _mad(values: List[float], med: float) -> float:
    """Compute Median Absolute Deviation from a precomputed median."""
    deviations = [abs(v - med) for v in values]
    return _median(deviations)


# =============================================================================
# SECTION 4 -- CHECK FUNCTIONS
# =============================================================================

def check_missing_data(
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float,
) -> CheckResult:
    """
    CHECK 1 -- MISSING DATA.

    All OHLCV fields must be finite and > 0.
    Returns CheckResult with violations for each invalid field.

    Args:
        open_, high, low, close, volume: OHLCV values.

    Returns:
        CheckResult. passed=True if all fields valid.
    """
    violations: List[IntegrityViolation] = []
    fields = {
        "open": open_, "high": high, "low": low,
        "close": close, "volume": volume,
    }
    for name, val in fields.items():
        if val is None:
            violations.append(IntegrityViolation(
                check_name="missing_data",
                failure_mode="FM-03",
                field_name=name,
                message=f"{name} is None",
            ))
        elif not isinstance(val, (int, float)):
            violations.append(IntegrityViolation(
                check_name="missing_data",
                failure_mode="FM-03",
                field_name=name,
                message=f"{name} is not numeric: {type(val).__name__}",
            ))
        elif not math.isfinite(val):
            violations.append(IntegrityViolation(
                check_name="missing_data",
                failure_mode="FM-03",
                field_name=name,
                message=f"{name} is NaN or Inf: {val!r}",
            ))
        elif val <= 0:
            violations.append(IntegrityViolation(
                check_name="missing_data",
                failure_mode="FM-03",
                field_name=name,
                message=f"{name} must be > 0, got {val!r}",
            ))

    return CheckResult(
        passed=len(violations) == 0,
        degraded=False,
        violations=violations,
        quality_penalty=0.0,
    )


def check_timestamp_continuity(
    prev_sequence_id: Optional[int],
    curr_sequence_id: int,
    time_gap_seconds: float,
    timeframe_seconds: float,
    asset_class: str,
) -> CheckResult:
    """
    CHECK 2 -- TIMESTAMP CONTINUITY.

    sequence_id must be monotonically increasing. Time gap must not exceed
    the asset-class-specific threshold (GAP_MULTIPLIERS[asset_class] * timeframe_seconds).

    Args:
        prev_sequence_id:   Previous sequence_id, or None for first tick.
        curr_sequence_id:   Current sequence_id.
        time_gap_seconds:   Time gap between ticks in seconds.
        timeframe_seconds:  Expected seconds per candle.
        asset_class:        One of VALID_ASSET_CLASSES.

    Returns:
        CheckResult. is_stale indicated via violations if gap exceeded.
    """
    violations: List[IntegrityViolation] = []

    # Sequence regression check
    if prev_sequence_id is not None and curr_sequence_id <= prev_sequence_id:
        violations.append(IntegrityViolation(
            check_name="timestamp_continuity",
            failure_mode="FM-03",
            field_name="sequence_id",
            message=(
                f"sequence_id regression: curr={curr_sequence_id} "
                f"<= prev={prev_sequence_id}"
            ),
        ))

    # Gap threshold check
    multiplier = GAP_MULTIPLIERS.get(asset_class, 2)
    max_gap = multiplier * timeframe_seconds
    if time_gap_seconds > max_gap:
        violations.append(IntegrityViolation(
            check_name="timestamp_continuity",
            failure_mode="FM-03",
            field_name="time_gap",
            message=(
                f"time gap {time_gap_seconds}s exceeds {asset_class} threshold "
                f"{max_gap}s ({multiplier} * {timeframe_seconds}s)"
            ),
        ))

    return CheckResult(
        passed=len(violations) == 0,
        degraded=False,
        violations=violations,
        quality_penalty=0.0,
    )


def check_spread_anomaly(
    spread_bps: float,
    max_entry_spread_bps: float,
) -> CheckResult:
    """
    CHECK 3 -- SPREAD ANOMALY DETECTION.

    spread_bps must be < max_entry_spread_bps * SPREAD_ANOMALY_FACTOR.
    On failure, object is passed but flagged (FM-06). No new entries permitted.

    Args:
        spread_bps:          Current spread in basis points.
        max_entry_spread_bps: Maximum acceptable entry spread (from strategy config).

    Returns:
        CheckResult. passed=True even on anomaly (object admitted but flagged).
        degraded=True if anomaly detected.
    """
    if not isinstance(spread_bps, (int, float)) or not math.isfinite(spread_bps):
        return CheckResult(
            passed=False,
            degraded=False,
            violations=[IntegrityViolation(
                check_name="spread_anomaly",
                failure_mode="FM-03",
                field_name="spread_bps",
                message=f"spread_bps is not finite: {spread_bps!r}",
            )],
            quality_penalty=0.0,
        )

    threshold = max_entry_spread_bps * SPREAD_ANOMALY_FACTOR
    if spread_bps >= threshold:
        return CheckResult(
            passed=True,
            degraded=True,
            violations=[IntegrityViolation(
                check_name="spread_anomaly",
                failure_mode="FM-06",
                field_name="spread_bps",
                message=(
                    f"spread_bps {spread_bps} >= threshold {threshold} "
                    f"({max_entry_spread_bps} * {SPREAD_ANOMALY_FACTOR})"
                ),
            )],
            quality_penalty=0.0,
        )

    return CheckResult(
        passed=True,
        degraded=False,
        violations=[],
        quality_penalty=0.0,
    )


def check_outlier_filter(
    close: float,
    rolling_closes: List[float],
) -> CheckResult:
    """
    CHECK 4 -- OUTLIER FILTER (Robust Z-Score).

    close price must satisfy: |z_score| < OUTLIER_Z_THRESHOLD
    where z_score = (close - rolling_median) / rolling_MAD

    If insufficient history (< OUTLIER_WINDOW), the check passes (cannot compute).

    Args:
        close:           Current close price.
        rolling_closes:  List of recent close prices (up to OUTLIER_WINDOW).

    Returns:
        CheckResult. degraded=True if outlier detected (quality reduced).
        quality_penalty set to OUTLIER_QUALITY_PENALTY if outlier.
    """
    # Insufficient history -- cannot compute, pass
    if len(rolling_closes) < OUTLIER_WINDOW:
        return CheckResult(
            passed=True,
            degraded=False,
            violations=[],
            quality_penalty=0.0,
        )

    # Use last OUTLIER_WINDOW values
    window = rolling_closes[-OUTLIER_WINDOW:]
    med = _median(window)
    mad_val = _mad(window, med)

    # MAD == 0 means all values identical; any different close is an outlier
    if mad_val == 0.0:
        if close != med:
            return CheckResult(
                passed=True,
                degraded=True,
                violations=[IntegrityViolation(
                    check_name="outlier_filter",
                    failure_mode="FM-03",
                    field_name="close",
                    message=(
                        f"close {close} deviates from constant series "
                        f"(median={med}, MAD=0)"
                    ),
                )],
                quality_penalty=OUTLIER_QUALITY_PENALTY,
            )
        return CheckResult(
            passed=True,
            degraded=False,
            violations=[],
            quality_penalty=0.0,
        )

    z_score = abs(close - med) / mad_val

    if z_score >= OUTLIER_Z_THRESHOLD:
        return CheckResult(
            passed=True,
            degraded=True,
            violations=[IntegrityViolation(
                check_name="outlier_filter",
                failure_mode="FM-03",
                field_name="close",
                message=(
                    f"|z_score| = {z_score:.4f} >= {OUTLIER_Z_THRESHOLD} "
                    f"(close={close}, median={med}, MAD={mad_val:.6f})"
                ),
            )],
            quality_penalty=OUTLIER_QUALITY_PENALTY,
        )

    return CheckResult(
        passed=True,
        degraded=False,
        violations=[],
        quality_penalty=0.0,
    )


def check_asset_class(
    asset_class: str,
    session_tag: str,
) -> CheckResult:
    """
    CHECK 5 -- ASSET CLASS VALIDATION.

    asset_class must be in VALID_ASSET_CLASSES.
    session_tag must be valid for the declared asset_class.

    Args:
        asset_class:  Asset class string.
        session_tag:  Session tag string.

    Returns:
        CheckResult. passed=False if asset_class unknown or session invalid.
    """
    violations: List[IntegrityViolation] = []

    if asset_class not in VALID_ASSET_CLASSES:
        violations.append(IntegrityViolation(
            check_name="asset_class",
            failure_mode="FM-03",
            field_name="asset_class",
            message=f"asset_class {asset_class!r} not in {sorted(VALID_ASSET_CLASSES)}",
        ))
        return CheckResult(
            passed=False,
            degraded=False,
            violations=violations,
            quality_penalty=0.0,
        )

    # Validate session_tag for asset_class
    if session_tag not in VALID_SESSION_TAGS:
        violations.append(IntegrityViolation(
            check_name="asset_class",
            failure_mode="FM-03",
            field_name="session_tag",
            message=f"session_tag {session_tag!r} not in VALID_SESSION_TAGS",
        ))
    else:
        valid_tags = VALID_SESSION_TAGS_PER_ASSET_CLASS.get(asset_class, frozenset())
        if session_tag not in valid_tags:
            violations.append(IntegrityViolation(
                check_name="asset_class",
                failure_mode="FM-03",
                field_name="session_tag",
                message=(
                    f"session_tag {session_tag!r} not valid for "
                    f"asset_class {asset_class!r} "
                    f"(valid: {sorted(valid_tags)})"
                ),
            ))

    return CheckResult(
        passed=len(violations) == 0,
        degraded=False,
        violations=violations,
        quality_penalty=0.0,
    )


# =============================================================================
# SECTION 5 -- GATE ORCHESTRATOR
# =============================================================================

def run_integrity_gate(
    operating_mode: str,
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float,
    quality_score: float,
    spread_bps: float,
    max_entry_spread_bps: float,
    asset_class: str,
    session_tag: str,
    prev_sequence_id: Optional[int],
    curr_sequence_id: int,
    time_gap_seconds: float,
    timeframe_seconds: float,
    rolling_closes: Optional[List[float]] = None,
) -> GateVerdict:
    """
    Full Stage 0 integrity gate.  Runs all 5 checks and returns GateVerdict.

    In MODE_HISTORICAL: always returns admitted=True (data pre-validated).
    In MODE_LIVE_ANALYTICAL / MODE_HYBRID: runs all 5 checks.

    The caller is responsible for:
      - Emitting FM-03 / FM-06 events based on violations
      - Updating meta_uncertainty via ctrl.update()
      - Setting is_stale on the data object

    Args:
        operating_mode:        One of VALID_OPERATING_MODES.
        open_, high, low, close, volume: OHLCV values.
        quality_score:         Current quality_score [0.0, 1.0].
        spread_bps:            Current spread in basis points.
        max_entry_spread_bps:  Max acceptable entry spread (strategy config).
        asset_class:           Asset class string.
        session_tag:           Session tag string.
        prev_sequence_id:      Previous sequence_id (None for first tick).
        curr_sequence_id:      Current sequence_id.
        time_gap_seconds:      Time gap between ticks in seconds.
        timeframe_seconds:     Expected seconds per candle.
        rolling_closes:        Recent close prices for outlier detection.

    Returns:
        GateVerdict with admission decision and all violations.

    Raises:
        TypeError:  If operating_mode is not a string.
        ValueError: If operating_mode is not valid.
    """
    _validate_operating_mode(operating_mode)

    # Historical mode: bypass gate entirely
    if operating_mode == "historical":
        return GateVerdict(
            admitted=True,
            operating_mode=operating_mode,
            quality_score_adj=quality_score,
            is_stale=False,
            spread_flagged=False,
            violations=[],
            checks_passed=5,
            reason="historical mode: data pre-validated in store",
        )

    if rolling_closes is None:
        rolling_closes = []

    # Run all 5 checks
    c1 = check_missing_data(open_, high, low, close, volume)
    c2 = check_timestamp_continuity(
        prev_sequence_id, curr_sequence_id,
        time_gap_seconds, timeframe_seconds, asset_class,
    )
    c3 = check_spread_anomaly(spread_bps, max_entry_spread_bps)
    c4 = check_outlier_filter(close, rolling_closes)
    c5 = check_asset_class(asset_class, session_tag)

    checks = [c1, c2, c3, c4, c5]

    # Aggregate violations
    all_violations: List[IntegrityViolation] = []
    for c in checks:
        all_violations.extend(c.violations)

    # Count passed checks
    checks_passed = sum(1 for c in checks if c.passed)

    # Compute adjusted quality score
    total_penalty = sum(c.quality_penalty for c in checks)
    quality_adj = quality_score - total_penalty

    # Determine staleness (CHECK 2 gap violations)
    is_stale = any(
        v.check_name == "timestamp_continuity" and v.field_name == "time_gap"
        for v in all_violations
    )

    # Determine spread flag (CHECK 3 FM-06)
    spread_flagged = c3.degraded

    # Admission decision:
    # - CHECK 1 fail -> reject (missing data)
    # - CHECK 2 fail -> reject (sequence regression)
    # - CHECK 3 fail -> reject only if non-finite spread
    # - CHECK 4 -> always admitted (degraded only), but if quality < 0.5 -> reject
    # - CHECK 5 fail -> reject (unknown asset class)
    hard_fail = not c1.passed or not c5.passed
    if not c2.passed:
        hard_fail = True
    if not c3.passed:
        hard_fail = True

    # Quality gate: if adjusted quality < 0.5 after penalties -> reject
    quality_gate_fail = quality_adj < 0.5

    admitted = not hard_fail and not quality_gate_fail

    # Build reason
    if admitted and not all_violations:
        reason = "all 5 checks passed"
    elif admitted:
        degraded_names = [v.check_name for v in all_violations]
        reason = f"admitted with warnings: {', '.join(degraded_names)}"
    else:
        failed_names = sorted({v.check_name for v in all_violations})
        reason = f"rejected: {', '.join(failed_names)}"
        if quality_gate_fail:
            reason += f" (quality_score {quality_adj:.2f} < 0.5)"

    return GateVerdict(
        admitted=admitted,
        operating_mode=operating_mode,
        quality_score_adj=quality_adj,
        is_stale=is_stale,
        spread_flagged=spread_flagged,
        violations=all_violations,
        checks_passed=checks_passed,
        reason=reason,
    )
