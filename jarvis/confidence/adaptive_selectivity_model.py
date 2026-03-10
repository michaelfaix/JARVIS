# =============================================================================
# JARVIS v6.1.0 -- ADAPTIVE SELECTIVITY MODEL
# File:   jarvis/confidence/adaptive_selectivity_model.py
# Version: 1.0.0
# =============================================================================
#
# SCOPE
# -----
# Deterministic computation of the adaptive selectivity threshold.
# Adjusts the minimum composite quality score required for a strategy
# signal to be considered analytically valid, based on current market
# stress indicators.
#
# CLASSIFICATION: Phase 3 — Decision Quality sub-component.
# Output feeds ONLY DecisionQualityEngine.
# May NOT directly alter Risk Engine thresholds or Failure Modes.
#
# PUBLIC SYMBOLS
# --------------
#   BASE_SELECTIVITY_THRESHOLD    float constant (0.55)
#   THRESHOLD_CEILING             float constant (0.92)
#   AdaptiveSelectivityResult     frozen dataclass — computation output
#   AdaptiveSelectivityModel      stateless model — compute_threshold()
#
# GOVERNANCE CONSTRAINTS
# ----------------------
#   - THRESHOLD MONOTONICITY: resolved_threshold >= BASE always.
#   - DETERMINISTIC MAPPING: identical inputs => identical threshold.
#   - CANNOT OVERRIDE FAILURE MODES: FM-01..FM-06 unchanged.
#   - CANNOT OVERRIDE RISK ENGINE: threshold adjustments advisory only.
#   - NO STATE MUTATION: never calls ctrl.update().
#   - SNAPSHOT-ONLY: all inputs passed as frozen values.
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
#   No Failure Mode override
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

from jarvis.core.regime import CorrelationRegimeState


# ---------------------------------------------------------------------------
# CONSTANTS — fixed per DET-06
# ---------------------------------------------------------------------------

BASE_SELECTIVITY_THRESHOLD: float = 0.55
"""
Minimum composite quality score required for analytical validity.
AdaptiveSelectivityModel may only increase this value; it may never
fall below BASE_SELECTIVITY_THRESHOLD.
"""

THRESHOLD_CEILING: float = 0.92
"""
Upper bound for the resolved selectivity threshold.
Prevents threshold from reaching 1.0 (which would block all signals).
"""


# ---------------------------------------------------------------------------
# ADAPTIVE SELECTIVITY RESULT (frozen)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AdaptiveSelectivityResult:
    """
    Frozen result of AdaptiveSelectivityModel.
    Contains the resolved selectivity threshold for this evaluation cycle.
    Threshold is always >= BASE_SELECTIVITY_THRESHOLD.

    Attributes:
        resolved_threshold:
            Selectivity threshold for the current cycle.
            Range: [BASE_SELECTIVITY_THRESHOLD, THRESHOLD_CEILING].
            Higher = more selective; fewer signals pass.

        adjustment_reason:
            Human-readable description of which factors increased
            the threshold. For Visual Output and audit trail only.

        base_used:
            BASE_SELECTIVITY_THRESHOLD used in this computation.
            Must always equal the registered constant (0.55).
    """
    resolved_threshold: float
    adjustment_reason: str
    base_used: float


# ---------------------------------------------------------------------------
# ADAPTIVE SELECTIVITY MODEL (stateless)
# ---------------------------------------------------------------------------

class AdaptiveSelectivityModel:
    """
    Deterministic adaptive selectivity threshold computation.

    Adjusts the minimum composite quality score required for a strategy
    signal to be considered analytically valid. Adjustment is always
    upward (additive penalties on top of BASE_SELECTIVITY_THRESHOLD).

    Stateless: all inputs passed explicitly to compute_threshold().
    No internal buffers, no mutable state, no side effects.

    Performance budget: < 2 ms per call.
    """

    # --- Class constants (fixed per DET-06) ---
    BASE: float = BASE_SELECTIVITY_THRESHOLD

    PENALTY_LOW_REGIME_STABILITY: float = 0.10
    """Applied when regime_stability_score < 0.40."""

    PENALTY_HIGH_UNCERTAINTY: float = 0.08
    """Applied when total_uncertainty > 0.50."""

    PENALTY_CORRELATION_STRESS: float = 0.07
    """Applied when correlation_regime == BREAKDOWN (crisis coupling)."""

    PENALTY_PER_ACTIVE_FM: float = 0.05
    """Per active failure mode (capped at 3 FMs)."""

    PENALTY_DURATION_STRESS: float = 0.05
    """Applied when transition_acceleration_flag is True."""

    THRESHOLD_CEILING: float = THRESHOLD_CEILING

    # --- Thresholds for penalty activation ---
    REGIME_STABILITY_THRESHOLD: float = 0.40
    UNCERTAINTY_THRESHOLD: float = 0.50
    MAX_FM_COUNT: int = 3

    def compute_threshold(
        self,
        regime_stability_score: float,
        total_uncertainty: float,
        correlation_regime: CorrelationRegimeState,
        active_failure_modes: FrozenSet[str],
        transition_acceleration_flag: bool,
    ) -> AdaptiveSelectivityResult:
        """
        Deterministically compute the adaptive selectivity threshold.

        Args:
            regime_stability_score:
                Regime stability in [0.0, 1.0]. Lower = less stable.
            total_uncertainty:
                Total uncertainty in [0.0, 1.0]. Higher = more uncertain.
            correlation_regime:
                Current correlation regime state (CorrelationRegimeState enum).
            active_failure_modes:
                Frozen set of active failure mode identifiers
                (e.g., frozenset({"FM-01", "FM-04"})).
            transition_acceleration_flag:
                From RegimeDurationResult. True when regime duration is
                significantly outside historical norms.

        Returns:
            AdaptiveSelectivityResult (frozen, deterministic).

        Raises:
            TypeError: if correlation_regime is not CorrelationRegimeState.
        """
        if not isinstance(correlation_regime, CorrelationRegimeState):
            raise TypeError(
                f"correlation_regime must be a CorrelationRegimeState; "
                f"got {type(correlation_regime).__name__}"
            )

        penalty: float = 0.0
        reasons: list[str] = []

        # 1. Low regime stability
        if regime_stability_score < self.REGIME_STABILITY_THRESHOLD:
            penalty += self.PENALTY_LOW_REGIME_STABILITY
            reasons.append(
                f"LOW_REGIME_STABILITY({regime_stability_score:.3f})"
            )

        # 2. High uncertainty
        if total_uncertainty > self.UNCERTAINTY_THRESHOLD:
            penalty += self.PENALTY_HIGH_UNCERTAINTY
            reasons.append(
                f"HIGH_UNCERTAINTY({total_uncertainty:.3f})"
            )

        # 3. Correlation stress (BREAKDOWN = crisis coupling)
        if correlation_regime == CorrelationRegimeState.BREAKDOWN:
            penalty += self.PENALTY_CORRELATION_STRESS
            reasons.append("CORRELATION_STRESS(BREAKDOWN)")

        # 4. Active failure modes (capped at MAX_FM_COUNT)
        fm_count: int = min(len(active_failure_modes), self.MAX_FM_COUNT)
        if fm_count > 0:
            fm_penalty: float = fm_count * self.PENALTY_PER_ACTIVE_FM
            penalty += fm_penalty
            reasons.append(
                f"ACTIVE_FM_COUNT({fm_count}, penalty={fm_penalty:.3f})"
            )

        # 5. Duration stress
        if transition_acceleration_flag:
            penalty += self.PENALTY_DURATION_STRESS
            reasons.append("DURATION_STRESS_FLAG(True)")

        # --- Resolve threshold ---
        raw_threshold: float = self.BASE + penalty
        resolved: float = float(
            max(self.BASE, min(raw_threshold, self.THRESHOLD_CEILING))
        )

        reason_str: str = "; ".join(reasons) if reasons else "NO_ADJUSTMENT"

        return AdaptiveSelectivityResult(
            resolved_threshold=resolved,
            adjustment_reason=reason_str,
            base_used=self.BASE,
        )


__all__ = [
    "BASE_SELECTIVITY_THRESHOLD",
    "THRESHOLD_CEILING",
    "AdaptiveSelectivityResult",
    "AdaptiveSelectivityModel",
]
