# =============================================================================
# jarvis/systems/mode_controller.py
# Authority: FAS v6.0.1 -- S17.5, lines 14869-14909
# =============================================================================
#
# SCOPE
# -----
# Operational mode controller for runtime behavior.  Distinct from
# SystemMode (data-source modes in core/system_mode.py).  This controls
# runtime operational posture: NORMAL → DEFENSIVE → HOLD → EMERGENCY.
#
# Public symbols:
#   OperationalMode            Enum: NORMAL, DEFENSIVE, HOLD, EMERGENCY
#   TRANSITION_TABLE           Canonical transition mapping
#   ModeTransitionResult       Frozen dataclass for transition result
#   ModeController             Stateless controller class
#
# GOVERNANCE
# ----------
# Mode transitions are advisory.  EMERGENCY mode requires manual_recovery
# trigger to exit.  No mode bypasses Risk Engine or Failure Modes.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, enum, typing
#   external:  NONE
#   internal:  NONE
#   PROHIBITED: logging, random, file IO, network IO, datetime.now(), numpy
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-06  Fixed literals (TRANSITION_TABLE) not parametrisable.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique
from typing import Dict, FrozenSet, Optional, Tuple

__all__ = [
    "OperationalMode",
    "TRANSITION_TABLE",
    "ModeTransitionResult",
    "ModeController",
]


# =============================================================================
# SECTION 1 -- ENUM
# =============================================================================

@unique
class OperationalMode(Enum):
    """
    Runtime operational mode for the JARVIS platform.

    NORMAL:     Normal operation — all analytical layers active.
    DEFENSIVE:  Reduced risk, heightened caution — exposure capped.
    HOLD:       Position hold — minimal strategy changes.
    EMERGENCY:  Critical failure — minimal functionality, manual recovery needed.
    """
    NORMAL = "normal"
    DEFENSIVE = "defensive"
    HOLD = "hold"
    EMERGENCY = "emergency"


# =============================================================================
# SECTION 2 -- TRANSITION TABLE (DET-06: fixed literals)
# =============================================================================

TRANSITION_TABLE: Dict[Tuple[OperationalMode, str], OperationalMode] = {
    # From NORMAL
    (OperationalMode.NORMAL, "ood_detected"): OperationalMode.DEFENSIVE,
    (OperationalMode.NORMAL, "high_uncertainty"): OperationalMode.DEFENSIVE,
    (OperationalMode.NORMAL, "drawdown_warning"): OperationalMode.DEFENSIVE,
    (OperationalMode.NORMAL, "critical_failure"): OperationalMode.EMERGENCY,

    # From DEFENSIVE
    (OperationalMode.DEFENSIVE, "ood_cleared"): OperationalMode.NORMAL,
    (OperationalMode.DEFENSIVE, "uncertainty_spike"): OperationalMode.HOLD,
    (OperationalMode.DEFENSIVE, "drawdown_exceeded"): OperationalMode.EMERGENCY,

    # From HOLD
    (OperationalMode.HOLD, "stability_restored"): OperationalMode.DEFENSIVE,
    (OperationalMode.HOLD, "critical_failure"): OperationalMode.EMERGENCY,

    # From EMERGENCY
    (OperationalMode.EMERGENCY, "manual_recovery"): OperationalMode.HOLD,
}
"""Canonical transition table: (current_mode, trigger) → new_mode."""

VALID_TRIGGERS: FrozenSet[str] = frozenset({
    "ood_detected",
    "ood_cleared",
    "high_uncertainty",
    "uncertainty_spike",
    "drawdown_warning",
    "drawdown_exceeded",
    "critical_failure",
    "stability_restored",
    "manual_recovery",
})
"""All recognised trigger strings."""


# =============================================================================
# SECTION 3 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class ModeTransitionResult:
    """
    Result of a mode transition attempt.

    Fields:
        previous_mode:  Mode before transition attempt.
        trigger:        Trigger string that was applied.
        new_mode:       Mode after transition (same as previous if rejected).
        accepted:       True if transition was valid and applied.
        reason:         Human-readable explanation.
    """
    previous_mode: OperationalMode
    trigger: str
    new_mode: OperationalMode
    accepted: bool
    reason: str


# =============================================================================
# SECTION 4 -- CONTROLLER
# =============================================================================

class ModeController:
    """
    Stateless operational mode controller.

    Evaluates transition requests against TRANSITION_TABLE.
    Does not hold state — caller manages current mode.
    """

    def transition(
        self,
        current_mode: OperationalMode,
        trigger: str,
    ) -> ModeTransitionResult:
        """
        Attempt a mode transition.

        Args:
            current_mode: Current operational mode.
            trigger:      Trigger string (e.g. "ood_detected").

        Returns:
            ModeTransitionResult with accepted/rejected status.

        Raises:
            TypeError: If arguments have wrong types.
        """
        if not isinstance(current_mode, OperationalMode):
            raise TypeError(
                f"current_mode must be an OperationalMode, "
                f"got {type(current_mode).__name__}"
            )
        if not isinstance(trigger, str):
            raise TypeError(
                f"trigger must be a string, "
                f"got {type(trigger).__name__}"
            )

        new_mode = TRANSITION_TABLE.get((current_mode, trigger))

        if new_mode is not None:
            return ModeTransitionResult(
                previous_mode=current_mode,
                trigger=trigger,
                new_mode=new_mode,
                accepted=True,
                reason=(
                    f"{current_mode.value} -> {new_mode.value} "
                    f"on trigger '{trigger}'"
                ),
            )
        else:
            return ModeTransitionResult(
                previous_mode=current_mode,
                trigger=trigger,
                new_mode=current_mode,
                accepted=False,
                reason=(
                    f"No transition from {current_mode.value} "
                    f"on trigger '{trigger}'"
                ),
            )

    def get_available_triggers(
        self,
        current_mode: OperationalMode,
    ) -> FrozenSet[str]:
        """
        Return all triggers that produce a valid transition from current_mode.

        Args:
            current_mode: Current operational mode.

        Returns:
            Frozenset of valid trigger strings.
        """
        if not isinstance(current_mode, OperationalMode):
            raise TypeError(
                f"current_mode must be an OperationalMode, "
                f"got {type(current_mode).__name__}"
            )
        triggers = set()
        for (mode, trigger), _ in TRANSITION_TABLE.items():
            if mode == current_mode:
                triggers.add(trigger)
        return frozenset(triggers)

    def is_valid_trigger(
        self,
        current_mode: OperationalMode,
        trigger: str,
    ) -> bool:
        """Check whether a trigger produces a valid transition."""
        if not isinstance(current_mode, OperationalMode):
            raise TypeError(
                f"current_mode must be an OperationalMode, "
                f"got {type(current_mode).__name__}"
            )
        if not isinstance(trigger, str):
            raise TypeError(
                f"trigger must be a string, "
                f"got {type(trigger).__name__}"
            )
        return (current_mode, trigger) in TRANSITION_TABLE
