# =============================================================================
# jarvis/confidence/failure_impact.py
# Authority: FAS v6.0.1 -- S17.5, lines 6149-6180
# =============================================================================
#
# SCOPE
# -----
# Failure Mode impact application on ConfidenceBundle fields.
# Confidence can ONLY decrease (mu, Q, R, S).  U (uncertainty) can ONLY
# increase.  sigma2 is untouched by failure impacts.
#
# Public symbols:
#   IMPACT_TABLE               FM-01..FM-06 → {field: delta}
#   ConfidenceBundle           Frozen dataclass {mu, sigma2, Q, S, U, R}
#   FailureImpactResult        Frozen result of impact application
#   apply_failure_mode_impacts Pure function — apply impacts to bundle
#
# GOVERNANCE
# ----------
# Confidence may NEVER increase through failure mode impacts.
# U (uncertainty) may NEVER decrease.  All outputs clipped to [0, 1].
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, typing
#   external:  NONE
#   internal:  NONE
#   PROHIBITED: logging, random, file IO, network IO, datetime.now(), numpy
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-06  Fixed literals (IMPACT_TABLE) not parametrisable.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

__all__ = [
    "IMPACT_TABLE",
    "ConfidenceBundle",
    "FailureImpactResult",
    "apply_failure_mode_impacts",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

IMPACT_TABLE: Dict[str, Dict[str, float]] = {
    "FM-01": {"R": -0.40, "Q": -0.40},
    "FM-02": {"S": -0.30, "Q": -0.20},
    "FM-03": {"mu": -0.20, "U": +0.15},
    "FM-04": {"Q": -0.50, "R": -0.20},
    "FM-05": {"S": -0.10},
    "FM-06": {"mu": -0.15, "S": -0.10},
}
"""Canonical impact table: failure mode → {field: delta}.

Negative deltas reduce confidence fields (mu, Q, R, S).
Positive delta on U increases uncertainty.
"""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class ConfidenceBundle:
    """
    Confidence state vector for the decision quality system.

    Fields:
        mu:     Information quality [0, 1].
        sigma2: Total uncertainty [0, 1].
        Q:      Contextual coherence / Bayesian posterior confidence [0, 1].
        S:      Selectivity / signal strength [0, 1].
        U:      Uncertainty penalty [0, 1].
        R:      Regime confidence [0, 1].
    """
    mu: float
    sigma2: float
    Q: float
    S: float
    U: float
    R: float


@dataclass(frozen=True)
class FailureImpactResult:
    """
    Result of applying failure mode impacts to a ConfidenceBundle.

    Fields:
        original:       The input bundle (unchanged).
        updated:        The output bundle with impacts applied.
        applied_modes:  Failure modes that were recognised and applied.
        ignored_modes:  Failure modes not found in IMPACT_TABLE.
    """
    original: ConfidenceBundle
    updated: ConfidenceBundle
    applied_modes: tuple
    ignored_modes: tuple


# =============================================================================
# SECTION 3 -- IMPACT APPLICATION
# =============================================================================

def _clip(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clip value to [lo, hi] without numpy."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def apply_failure_mode_impacts(
    bundle: ConfidenceBundle,
    active_modes: List[str],
) -> FailureImpactResult:
    """
    Apply failure mode confidence impacts to a ConfidenceBundle.

    Rules:
        - Confidence fields (mu, Q, R, S) can ONLY decrease.
        - Uncertainty field (U) can ONLY increase.
        - sigma2 is never modified by failure impacts.
        - All outputs clipped to [0.0, 1.0].
        - Unrecognised failure modes are ignored (tracked in result).
        - Impacts are applied in order of active_modes.

    Args:
        bundle:       Input ConfidenceBundle (frozen).
        active_modes: List of failure mode identifiers (e.g. ["FM-01", "FM-04"]).

    Returns:
        FailureImpactResult with original and updated bundles.

    Raises:
        TypeError: If bundle is not a ConfidenceBundle or active_modes is not a list.
    """
    if not isinstance(bundle, ConfidenceBundle):
        raise TypeError(
            f"bundle must be a ConfidenceBundle, "
            f"got {type(bundle).__name__}"
        )
    if not isinstance(active_modes, list):
        raise TypeError(
            f"active_modes must be a list, "
            f"got {type(active_modes).__name__}"
        )

    # Working copies of field values
    mu = float(bundle.mu)
    sigma2 = float(bundle.sigma2)
    Q = float(bundle.Q)
    S = float(bundle.S)
    U = float(bundle.U)
    R = float(bundle.R)

    applied: list = []
    ignored: list = []

    fields = {"mu": mu, "Q": Q, "S": S, "U": U, "R": R}

    for mode in active_modes:
        if not isinstance(mode, str):
            raise TypeError(
                f"each mode must be a string, "
                f"got {type(mode).__name__}"
            )
        impact = IMPACT_TABLE.get(mode)
        if impact is None:
            ignored.append(mode)
            continue

        applied.append(mode)
        for field, delta in impact.items():
            current = fields[field]
            if field == "U":
                # Uncertainty can only increase
                new_val = _clip(current + abs(delta))
            else:
                # Confidence fields can only decrease
                new_val = _clip(current + delta)  # delta is negative
            fields[field] = new_val

    updated = ConfidenceBundle(
        mu=_clip(fields["mu"]),
        sigma2=_clip(sigma2),
        Q=_clip(fields["Q"]),
        S=_clip(fields["S"]),
        U=_clip(fields["U"]),
        R=_clip(fields["R"]),
    )

    return FailureImpactResult(
        original=bundle,
        updated=updated,
        applied_modes=tuple(applied),
        ignored_modes=tuple(ignored),
    )
