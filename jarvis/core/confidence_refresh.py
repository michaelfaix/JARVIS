# =============================================================================
# jarvis/core/confidence_refresh.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, CONFIDENCE REFRESH LOGIC
# ARCHITECTURE.md Section 14
# =============================================================================
#
# SCOPE
# -----
# Mode-aware confidence refresh gate.  Determines whether the Confidence
# Engine should recompute its ConfidenceBundle based on analytical state
# changes between two consecutive snapshots.
#
# Public symbols:
#   VALID_OPERATING_MODES       Tuple of permitted mode strings
#   REFRESH_TRIGGER_FIELDS      Tuple of state fields compared for triggers
#   RefreshTrigger              Frozen dataclass describing a single trigger
#   RefreshDecision             Frozen dataclass: should_refresh + triggers
#   ConfidenceStateSnapshot     Frozen dataclass holding the 5 compared fields
#   should_refresh_confidence   Gate function (returns bool)
#   identify_refresh_triggers   Returns list of RefreshTrigger with details
#   evaluate_refresh            Returns full RefreshDecision
#
# CLASSIFICATION
# --------------
# P0 — Pure analysis and strategy research platform.
# This module is a stateless, deterministic predicate.  It does not
# call ctrl.update(), does not emit events, does not trigger execution.
#
# CONFIDENCE MAY ONLY UPDATE WHEN (live/hybrid):
#   1. regime_change:             regime value changed
#   2. volatility_state_change:   risk_mode changed (proxy for vol_regime)
#   3. strategy_weight_change:    strategy_mode changed
#   4. ood_trigger:               ood_status changed
#   5. failure_mode_trigger:      meta_uncertainty changed (FM impact)
#
# NOT PERMITTED:
#   - Recalculate on every tick without state change
#   - Spike confidence upward without state trigger
#   - Override Risk Engine output
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, typing
#   internal:  NONE
#   PROHIBITED: numpy, logging, random, file IO, network IO, datetime.now()
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  No arithmetic beyond equality comparison.
# DET-05  No datetime.now() / time.time().
# DET-06  Fixed literals are not parametrised.
# DET-07  Same inputs = bit-identical outputs.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

__all__ = [
    "VALID_OPERATING_MODES",
    "REFRESH_TRIGGER_FIELDS",
    "RefreshTrigger",
    "RefreshDecision",
    "ConfidenceStateSnapshot",
    "should_refresh_confidence",
    "identify_refresh_triggers",
    "evaluate_refresh",
]


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

VALID_OPERATING_MODES: Tuple[str, ...] = (
    "historical",
    "live_analytical",
    "hybrid",
)

REFRESH_TRIGGER_FIELDS: Tuple[str, ...] = (
    "regime",
    "risk_mode",
    "strategy_mode",
    "ood_status",
    "meta_uncertainty",
)


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class ConfidenceStateSnapshot:
    """
    Minimal frozen snapshot of the state fields relevant to confidence
    refresh evaluation.  Matches the five fields compared in
    should_refresh_confidence() per FAS S37.

    Fields:
        regime:           Current regime label (e.g. "RISK_ON").
        risk_mode:        Current risk mode (e.g. "NORMAL", "ELEVATED").
        strategy_mode:    Current strategy mode identifier.
        ood_status:       Out-of-distribution status (e.g. True/False).
        meta_uncertainty: Current meta-uncertainty value [0.0, 1.0].
    """
    regime:           str
    risk_mode:        str
    strategy_mode:    str
    ood_status:       bool
    meta_uncertainty: float


@dataclass(frozen=True)
class RefreshTrigger:
    """
    Describes a single state change that triggered a confidence refresh.

    Fields:
        field_name:  Name of the changed field (one of REFRESH_TRIGGER_FIELDS).
        prev_value:  Value in the previous snapshot.
        curr_value:  Value in the current snapshot.
    """
    field_name: str
    prev_value: object
    curr_value: object

    def __post_init__(self) -> None:
        if self.field_name not in REFRESH_TRIGGER_FIELDS:
            raise ValueError(
                f"field_name must be one of {REFRESH_TRIGGER_FIELDS}, "
                f"got {self.field_name!r}"
            )


@dataclass(frozen=True)
class RefreshDecision:
    """
    Complete result of a confidence refresh evaluation.

    Fields:
        should_refresh:  Whether the confidence engine should recompute.
        operating_mode:  The operating mode used for evaluation.
        triggers:        List of RefreshTrigger instances that fired.
                         Empty if should_refresh is False or mode is historical
                         (historical always refreshes regardless of triggers).
        reason:          Human-readable summary of the decision.
    """
    should_refresh: bool
    operating_mode: str
    triggers:       List[RefreshTrigger]
    reason:         str


# =============================================================================
# SECTION 3 -- VALIDATION
# =============================================================================

def _validate_operating_mode(operating_mode: str) -> None:
    """Raise ValueError if operating_mode is not a valid mode string."""
    if not isinstance(operating_mode, str):
        raise TypeError(
            f"operating_mode must be a string, got {type(operating_mode).__name__}"
        )
    if operating_mode not in VALID_OPERATING_MODES:
        raise ValueError(
            f"operating_mode must be one of {VALID_OPERATING_MODES}, "
            f"got {operating_mode!r}"
        )


def _validate_snapshot(snapshot: object, name: str) -> None:
    """Raise TypeError/AttributeError if snapshot lacks required fields."""
    if snapshot is None:
        raise TypeError(f"{name} must not be None")
    for field_name in REFRESH_TRIGGER_FIELDS:
        if not hasattr(snapshot, field_name):
            raise AttributeError(
                f"{name} is missing required field {field_name!r}"
            )


# =============================================================================
# SECTION 4 -- GATE FUNCTIONS
# =============================================================================

def should_refresh_confidence(
    prev_state: object,
    curr_state: object,
    operating_mode: str,
) -> bool:
    """
    Returns True if the confidence engine should recompute.

    In HISTORICAL mode: always returns True (batch recompute on every step).
    In LIVE_ANALYTICAL / HYBRID: returns True only when a genuine
    analytical state change has occurred in one of the five monitored
    fields.

    Args:
        prev_state:      Previous state snapshot.  Must have attributes:
                         regime, risk_mode, strategy_mode, ood_status,
                         meta_uncertainty.
        curr_state:      Current state snapshot (same attribute requirements).
        operating_mode:  One of "historical", "live_analytical", "hybrid".

    Returns:
        True if confidence should be recomputed, False otherwise.

    Raises:
        TypeError:        If operating_mode is not a string, or if
                          prev_state/curr_state is None.
        ValueError:       If operating_mode is not a valid mode.
        AttributeError:   If prev_state/curr_state lacks a required field.
    """
    _validate_operating_mode(operating_mode)
    _validate_snapshot(prev_state, "prev_state")
    _validate_snapshot(curr_state, "curr_state")

    if operating_mode == "historical":
        return True

    # Live / Hybrid: only on genuine state changes
    return any([
        prev_state.regime          != curr_state.regime,
        prev_state.risk_mode       != curr_state.risk_mode,
        prev_state.strategy_mode   != curr_state.strategy_mode,
        prev_state.ood_status      != curr_state.ood_status,
        prev_state.meta_uncertainty != curr_state.meta_uncertainty,
    ])


def identify_refresh_triggers(
    prev_state: object,
    curr_state: object,
) -> List[RefreshTrigger]:
    """
    Identify which state fields changed between two snapshots.

    Returns a list of RefreshTrigger for each field that differs.
    Returns an empty list if no fields changed.

    Does NOT check operating_mode -- this is a pure comparison function.

    Args:
        prev_state:  Previous state snapshot.
        curr_state:  Current state snapshot.

    Returns:
        List of RefreshTrigger instances for changed fields.

    Raises:
        TypeError:       If prev_state or curr_state is None.
        AttributeError:  If snapshots lack required fields.
    """
    _validate_snapshot(prev_state, "prev_state")
    _validate_snapshot(curr_state, "curr_state")

    triggers: List[RefreshTrigger] = []
    for field_name in REFRESH_TRIGGER_FIELDS:
        prev_val = getattr(prev_state, field_name)
        curr_val = getattr(curr_state, field_name)
        if prev_val != curr_val:
            triggers.append(RefreshTrigger(
                field_name=field_name,
                prev_value=prev_val,
                curr_value=curr_val,
            ))
    return triggers


def evaluate_refresh(
    prev_state: object,
    curr_state: object,
    operating_mode: str,
) -> RefreshDecision:
    """
    Full evaluation combining should_refresh_confidence and
    identify_refresh_triggers into a single RefreshDecision.

    Args:
        prev_state:      Previous state snapshot.
        curr_state:      Current state snapshot.
        operating_mode:  One of "historical", "live_analytical", "hybrid".

    Returns:
        RefreshDecision with should_refresh, triggers, and reason.

    Raises:
        TypeError:       If inputs have wrong types.
        ValueError:      If operating_mode is invalid.
        AttributeError:  If snapshots lack required fields.
    """
    _validate_operating_mode(operating_mode)
    _validate_snapshot(prev_state, "prev_state")
    _validate_snapshot(curr_state, "curr_state")

    if operating_mode == "historical":
        return RefreshDecision(
            should_refresh=True,
            operating_mode=operating_mode,
            triggers=[],
            reason="historical mode: batch recompute on every step",
        )

    triggers = identify_refresh_triggers(prev_state, curr_state)

    if triggers:
        field_names = ", ".join(t.field_name for t in triggers)
        return RefreshDecision(
            should_refresh=True,
            operating_mode=operating_mode,
            triggers=triggers,
            reason=f"state change detected in: {field_names}",
        )

    return RefreshDecision(
        should_refresh=False,
        operating_mode=operating_mode,
        triggers=[],
        reason="no analytical state change detected",
    )
