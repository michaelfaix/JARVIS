# =============================================================================
# JARVIS v6.1.0 -- DECISION QUALITY ENGINE
# File:   jarvis/intelligence/decision_quality_engine.py
# Version: 1.0.0
# =============================================================================
#
# SCOPE
# -----
# Capstone Phase 3 component. Computes a composite quality score for the
# current analytical decision cycle by aggregating:
#   - regime stability
#   - regime duration stress (from RegimeDurationModel)
#   - signal fragility (from SignalFragilityAnalyzer)
#   - correlation risk
#   - overfit risk
#   - epistemic uncertainty
#   - streak instability (from DecisionContextSnapshot)
#   - regime misalignment (from DecisionContextSnapshot)
#   - repeated failure penalty (from DecisionContextSnapshot)
#
# Determines adaptive selectivity threshold via AdaptiveSelectivityModel
# and evaluates whether the composite quality passes that threshold.
#
# CLASSIFICATION: Phase 3 — Decision Quality Maximization.
# Sub-component of P8 (Confidence Engine).
# Output is purely analytical — no execution semantics.
#
# PUBLIC SYMBOLS
# --------------
#   QUALITY_SCORE_CAP_UNDER_UNCERTAINTY  float constant (0.60)
#   QUALITY_SCORE_MIN_FLOOR              float constant (0.05)
#   DecisionQualityBundle                frozen dataclass — computation output
#   DecisionQualityEngine                engine class — compute() method
#
# GOVERNANCE CONSTRAINTS
# ----------------------
#   - DETERMINISTIC: identical snapshot inputs => identical output.
#   - SNAPSHOT-ONLY: never accesses live buffers.
#   - NO STATE MUTATION: never calls ctrl.update().
#   - NO EVENT EMISSION: never emits analytical events.
#   - NO EXECUTION SEMANTICS: output is purely analytical.
#   - FORBIDDEN: broker concepts, execution triggers, direct FM overrides,
#     Risk Engine threshold overrides, random number generation.
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
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet

from jarvis.confidence.adaptive_selectivity_model import AdaptiveSelectivityModel
from jarvis.core.decision_context_state import DecisionContextSnapshot
from jarvis.core.regime import CorrelationRegimeState
from jarvis.intelligence.regime_duration_model import RegimeDurationResult
from jarvis.strategy.signal_fragility_analyzer import SignalFragilityResult


# ---------------------------------------------------------------------------
# CONSTANTS — fixed per DET-06
# ---------------------------------------------------------------------------

QUALITY_SCORE_CAP_UNDER_UNCERTAINTY: float = 0.60
"""
When total_uncertainty > 0.5, composite_quality_score is capped at this
value regardless of other sub-scores.
Prevents optimistic quality ratings during high epistemic uncertainty.
"""

QUALITY_SCORE_MIN_FLOOR: float = 0.05
"""
composite_quality_score is always >= this floor.
Prevents division-by-zero and degenerate downstream calculations.
Does not represent a "good" signal — floor exists for numerical stability.
"""


# ---------------------------------------------------------------------------
# CORRELATION RISK MAPPING
# ---------------------------------------------------------------------------

_CORRELATION_RISK_MAP = {
    CorrelationRegimeState.NORMAL: 0.0,
    CorrelationRegimeState.DIVERGENCE: 0.0,
    CorrelationRegimeState.COUPLED: 0.40,
    CorrelationRegimeState.BREAKDOWN: 0.85,
}


# ---------------------------------------------------------------------------
# DECISION QUALITY BUNDLE (frozen)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DecisionQualityBundle:
    """
    Frozen output of DecisionQualityEngine.
    Contains all sub-scores and the composite quality assessment.

    All fields deterministically computed from snapshot inputs.
    No randomness. No execution semantics.
    """
    regime_stability_score: float
    regime_duration_stress_score: float
    signal_fragility_score: float
    correlation_risk_modifier: float
    overfit_risk_modifier: float
    uncertainty_modifier: float
    streak_instability: float
    regime_misalignment: float
    repeated_failure_penalty: float
    composite_quality_score: float
    selectivity_threshold: float
    signal_passes_selectivity: bool


# ---------------------------------------------------------------------------
# HELPER: clip to [0, 1]
# ---------------------------------------------------------------------------

def _clip01(v: float) -> float:
    return max(0.0, min(1.0, v))


# ---------------------------------------------------------------------------
# DECISION QUALITY ENGINE
# ---------------------------------------------------------------------------

class DecisionQualityEngine:
    """
    Capstone Phase 3 engine computing composite decision quality.

    Aggregates regime stability, duration stress, signal fragility,
    correlation risk, overfit risk, uncertainty, streak instability,
    regime misalignment, and repeated failure penalty into a single
    composite quality score. Determines adaptive selectivity threshold
    and evaluates pass/fail.

    Performance budget: < 20 ms per cycle (including all sub-calls).
    """

    # --- Composite quality weights (must sum to 1.0) ---
    W_REGIME_STABILITY: float = 0.20
    W_DURATION_STRESS: float = 0.15
    W_SIGNAL_FRAGILITY: float = 0.20
    W_CORRELATION_RISK: float = 0.15
    W_OVERFIT_RISK: float = 0.10
    W_UNCERTAINTY: float = 0.10
    W_STREAK_INSTABILITY: float = 0.05
    W_REGIME_MISALIGNMENT: float = 0.03
    W_REPEATED_FAILURE_PENALTY: float = 0.02

    # --- Helper windows ---
    STREAK_WINDOW: int = 10
    MISALIGNMENT_WINDOW: int = 20
    FAILURE_WINDOW: int = 10
    LOSS_THRESHOLD: float = 0.60

    def __init__(self) -> None:
        self._selectivity_model = AdaptiveSelectivityModel()

    # -----------------------------------------------------------------
    # MAIN COMPUTE
    # -----------------------------------------------------------------

    def compute(
        self,
        regime_transition_diagonal_mean: float,
        duration_result: RegimeDurationResult,
        fragility_result: SignalFragilityResult,
        correlation_regime: CorrelationRegimeState,
        overfitting_risk_score: float,
        total_uncertainty: float,
        decision_snapshot: DecisionContextSnapshot,
        active_failure_modes: FrozenSet[str],
    ) -> DecisionQualityBundle:
        """
        Compute DecisionQualityBundle from all snapshot inputs.

        Args:
            regime_transition_diagonal_mean:
                Mean of diagonal of RegimeTransitionMatrix (stability
                proxy). Range [0.0, 1.0]. Higher = more stable.
            duration_result:
                Output of RegimeDurationModel for current cycle.
            fragility_result:
                Output of SignalFragilityAnalyzer for current strategy.
            correlation_regime:
                Current cross-asset correlation regime (enum).
            overfitting_risk_score:
                OverfittingReport.overfitting_risk_score. [0.0, 1.0].
            total_uncertainty:
                UncertaintyBundle.total_uncertainty. [0.0, 1.0].
            decision_snapshot:
                Frozen snapshot of DecisionContextState.
            active_failure_modes:
                Set of active failure mode identifiers.

        Returns:
            DecisionQualityBundle (frozen, deterministic).
        """
        # --- Sub-score: regime stability ---
        regime_stability: float = _clip01(regime_transition_diagonal_mean)

        # --- Sub-score: duration stress ---
        z_abs: float = abs(duration_result.duration_z_score)
        duration_stress: float = _clip01(z_abs / 5.0)
        if duration_result.transition_acceleration_flag:
            duration_stress = _clip01(duration_stress + 0.30)

        # --- Sub-score: signal fragility ---
        signal_fragility: float = _clip01(fragility_result.fragility_index)

        # --- Sub-score: correlation risk ---
        correlation_risk: float = _CORRELATION_RISK_MAP.get(
            correlation_regime, 0.40
        )

        # --- Sub-score: overfit risk ---
        overfit_risk: float = _clip01(overfitting_risk_score)

        # --- Sub-score: uncertainty ---
        uncertainty: float = _clip01(total_uncertainty)

        # --- Sub-scores from decision context ---
        streak_inst: float = self._streak_instability(decision_snapshot)
        regime_misal: float = self._regime_misalignment(decision_snapshot)
        repeated_fail: float = self._repeated_failure_penalty(
            decision_snapshot
        )

        # --- Composite quality score (weighted aggregate) ---
        raw_quality: float = (
            self.W_REGIME_STABILITY * regime_stability
            + self.W_DURATION_STRESS * (1.0 - duration_stress)
            + self.W_SIGNAL_FRAGILITY * (1.0 - signal_fragility)
            + self.W_CORRELATION_RISK * (1.0 - correlation_risk)
            + self.W_OVERFIT_RISK * (1.0 - overfit_risk)
            + self.W_UNCERTAINTY * (1.0 - uncertainty)
            + self.W_STREAK_INSTABILITY * (1.0 - streak_inst)
            + self.W_REGIME_MISALIGNMENT * (1.0 - regime_misal)
            + self.W_REPEATED_FAILURE_PENALTY * (1.0 - repeated_fail)
        )

        composite: float = _clip01(raw_quality)

        # Apply uncertainty cap
        if uncertainty > 0.50:
            composite = min(composite, QUALITY_SCORE_CAP_UNDER_UNCERTAINTY)

        # Apply floor
        composite = max(composite, QUALITY_SCORE_MIN_FLOOR)

        # --- Selectivity threshold ---
        selectivity_result = self._selectivity_model.compute_threshold(
            regime_stability_score=regime_stability,
            total_uncertainty=uncertainty,
            correlation_regime=correlation_regime,
            active_failure_modes=active_failure_modes,
            transition_acceleration_flag=(
                duration_result.transition_acceleration_flag
            ),
        )

        passes: bool = composite >= selectivity_result.resolved_threshold

        return DecisionQualityBundle(
            regime_stability_score=regime_stability,
            regime_duration_stress_score=duration_stress,
            signal_fragility_score=signal_fragility,
            correlation_risk_modifier=correlation_risk,
            overfit_risk_modifier=overfit_risk,
            uncertainty_modifier=uncertainty,
            streak_instability=streak_inst,
            regime_misalignment=regime_misal,
            repeated_failure_penalty=repeated_fail,
            composite_quality_score=composite,
            selectivity_threshold=selectivity_result.resolved_threshold,
            signal_passes_selectivity=passes,
        )

    # -----------------------------------------------------------------
    # DECISION CONTEXT HELPERS (pure functions)
    # -----------------------------------------------------------------

    def _streak_instability(
        self,
        snapshot: DecisionContextSnapshot,
    ) -> float:
        """
        Outcome transition rate in recent window. Pure function.
        Range [0.0, 1.0]. 0 = all same, 1 = all differ.
        """
        records = snapshot.records
        recent = records[-self.STREAK_WINDOW:]
        if len(recent) < 2:
            return 0.0
        outcomes = [r.outcome for r in recent]
        transitions: int = sum(
            1 for a, b in zip(outcomes, outcomes[1:]) if a != b
        )
        return float(transitions / (len(recent) - 1))

    def _regime_misalignment(
        self,
        snapshot: DecisionContextSnapshot,
    ) -> float:
        """
        Fraction of recent decisions in a different regime than current.
        Pure function. Range [0.0, 1.0].
        """
        records = snapshot.records
        recent = records[-self.MISALIGNMENT_WINDOW:]
        if not recent:
            return 0.0
        current_regime: str = records[-1].regime_at_decision
        misaligned: int = sum(
            1 for r in recent if r.regime_at_decision != current_regime
        )
        return float(misaligned / len(recent))

    def _repeated_failure_penalty(
        self,
        snapshot: DecisionContextSnapshot,
    ) -> float:
        """
        Penalty when recent LOSS rate exceeds threshold. Pure function.
        Range [0.0, 1.0]. 0 = loss rate <= 60%, scales to 1.0 at 100%.
        """
        records = snapshot.records
        recent = records[-self.FAILURE_WINDOW:]
        if not recent:
            return 0.0
        losses: int = sum(1 for r in recent if r.outcome == "LOSS")
        loss_rate: float = float(losses / len(recent))
        if loss_rate <= self.LOSS_THRESHOLD:
            return 0.0
        denominator: float = max(1.0 - self.LOSS_THRESHOLD, 1e-9)
        return float(min(1.0, (loss_rate - self.LOSS_THRESHOLD) / denominator))


__all__ = [
    "QUALITY_SCORE_CAP_UNDER_UNCERTAINTY",
    "QUALITY_SCORE_MIN_FLOOR",
    "DecisionQualityBundle",
    "DecisionQualityEngine",
]
