# =============================================================================
# JARVIS v6.1.0 -- CONFIDENCE REFRESH POLICY
# File:   jarvis/confidence/confidence_refresh.py
# Version: 1.0.0
# Session: S26-S37
# =============================================================================
#
# SCOPE
# -----
# Determines whether the confidence engine should recompute based on
# operating mode and state changes.
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-05  All branching is deterministic.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No file IO, no logging, no random, no global mutable state.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceRefreshState:
    """
    Immutable snapshot of the fields relevant to confidence refresh decisions.

    Fields:
        regime:           Current regime identifier (e.g. "RISK_ON").
        risk_mode:        Current risk mode (e.g. "NORMAL", "ELEVATED").
        strategy_mode:    Current strategy mode (e.g. "MOMENTUM").
        ood_status:       Out-of-distribution status flag.
        meta_uncertainty: Meta-uncertainty value in [0.0, 1.0].
    """

    regime: str
    risk_mode: str
    strategy_mode: str
    ood_status: bool
    meta_uncertainty: float


def should_refresh_confidence(
    prev_state: ConfidenceRefreshState,
    curr_state: ConfidenceRefreshState,
    operating_mode: str,
) -> bool:
    """
    Returns True if the confidence engine should recompute.

    HISTORICAL mode: always True (batch recompute).
    LIVE / HYBRID: only on defined state changes.

    Args:
        prev_state:     Previous ConfidenceRefreshState snapshot.
        curr_state:     Current ConfidenceRefreshState snapshot.
        operating_mode: One of "historical", "live_analytical", "hybrid".

    Returns:
        True if confidence should be recomputed, False otherwise.
    """
    if operating_mode == "historical":
        return True

    # Live / Hybrid: only on genuine state changes
    return any([
        prev_state.regime != curr_state.regime,
        prev_state.risk_mode != curr_state.risk_mode,
        prev_state.strategy_mode != curr_state.strategy_mode,
        prev_state.ood_status != curr_state.ood_status,
        prev_state.meta_uncertainty != curr_state.meta_uncertainty,
    ])


__all__ = [
    "ConfidenceRefreshState",
    "should_refresh_confidence",
]
