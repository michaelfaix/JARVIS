# =============================================================================
# jarvis/intelligence/ood_engine.py -- Asset-Conditional OOD Engine (Phase MA-4)
#
# Detects out-of-distribution conditions with asset-class-aware thresholds.
# 4-component scoring: distribution + event + macro + regime.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   ood_engine.py -> jarvis.core.regime (AssetClass, GlobalRegimeState,
#                    CorrelationRegimeState, HierarchicalRegime)
#   ood_engine.py -> jarvis.intelligence.ood_config (AssetOODConfig,
#                    get_ood_config, classify_severity, REGIME_OOD_WEIGHT)
#   ood_engine.py -> (stdlib only otherwise)
#
# DETERMINISM GUARANTEES: DET-01 through DET-07 enforced.
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly. No module-level mutable reads.
#   DET-03  No side effects.
#   DET-05  Same inputs -> same outputs.
#   DET-06  Fixed literals not parameterizable.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01: No numpy. Pure stdlib math.
#   PROHIBITED-02: No file I/O.
#   PROHIBITED-03: No logging/print.
#   PROHIBITED-05: No global mutable state.
#   PROHIBITED-08: No new Enum definitions.
#   PROHIBITED-09: No string-based regime branching (uses Enum instances).
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from jarvis.core.regime import (
    AssetClass,
    AssetRegimeState,
    CorrelationRegimeState,
    GlobalRegimeState,
    HierarchicalRegime,
)
from jarvis.intelligence.ood_config import (
    AssetOODConfig,
    REGIME_OOD_WEIGHT,
    classify_severity,
    get_ood_config,
)


# =============================================================================
# SECTION 1 -- RESULT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class OODComponentScores:
    """Individual OOD component scores.

    Attributes:
        distribution: Feature-space anomaly score [0, 1].
        event: Price-action event score [0, 1].
        macro: Macro event sensitivity score [0, 1].
        regime: Regime transition score [0, 1].
    """
    distribution: float
    event: float
    macro: float
    regime: float


@dataclass(frozen=True)
class OODResult:
    """Complete OOD detection result.

    Attributes:
        is_ood: True if total score exceeds asset-specific threshold.
        score: Combined OOD score [0, 1].
        severity: CRITICAL | HIGH | MEDIUM | LOW.
        components: Individual component scores.
        asset_class: Asset class this result applies to.
        threshold: Asset-specific threshold used.
        result_hash: SHA-256[:16] of content for determinism verification.
    """
    is_ood: bool
    score: float
    severity: str
    components: OODComponentScores
    asset_class: AssetClass
    threshold: float
    result_hash: str


# =============================================================================
# SECTION 2 -- PURE MATH HELPERS (stdlib only, DET-01)
# =============================================================================

def _clip(value: float, lo: float, hi: float) -> float:
    """Clip value to [lo, hi]."""
    return max(lo, min(hi, value))


def _zscore_ood(
    features: List[float],
    reference_mean: List[float],
    reference_std: List[float],
) -> float:
    """Compute distribution OOD score from z-scores of feature vector.

    For each feature with non-zero reference std, compute abs(z-score).
    Return the fraction of features with |z| > 2.0, scaled to [0, 1].

    Args:
        features: Current feature vector.
        reference_mean: Historical mean per feature.
        reference_std: Historical std per feature.

    Returns:
        Distribution OOD score [0, 1].
    """
    n = min(len(features), len(reference_mean), len(reference_std))
    if n == 0:
        return 0.0

    outlier_count = 0
    active_count = 0
    total_z = 0.0

    for i in range(n):
        std = reference_std[i]
        if std < 1e-15:
            continue
        active_count += 1
        z = abs((features[i] - reference_mean[i]) / std)
        total_z += min(z, 10.0)  # cap extreme z-scores
        if z > 2.0:
            outlier_count += 1

    if active_count == 0:
        return 0.0

    # Blend: fraction of outliers (0.6) + mean z-score normalized (0.4)
    outlier_fraction = outlier_count / active_count
    mean_z_normalized = _clip((total_z / active_count) / 5.0, 0.0, 1.0)

    return _clip(0.6 * outlier_fraction + 0.4 * mean_z_normalized, 0.0, 1.0)


# =============================================================================
# SECTION 3 -- ASSET-CONDITIONAL OOD DETECTOR
# =============================================================================

class AssetConditionalOOD:
    """Asset-class-aware OOD detection.

    Detects out-of-distribution conditions using 4 components:
    1. Distribution OOD: Feature-space anomaly (z-score based).
    2. Event OOD: Price-action anomaly (flash crash, vol spike, liquidity drain).
    3. Macro OOD: Macro event sensitivity (calendar-based, passed explicitly).
    4. Regime OOD: Regime transition/crisis detection.

    All inputs are explicit parameters (DET-02).
    No internal state retained between calls (DET-03, PROHIBITED-05).
    """

    def detect(
        self,
        *,
        asset_class: AssetClass,
        features: List[float],
        reference_mean: List[float],
        reference_std: List[float],
        recent_return: float,
        current_volatility: float,
        historical_volatility: float,
        liquidity_score: float,
        macro_event_scores: Dict[str, float],
        regime: HierarchicalRegime,
    ) -> OODResult:
        """Detect OOD condition for a specific asset class.

        Args:
            asset_class: Asset class to evaluate.
            features: Current 99-dim feature vector.
            reference_mean: Historical mean per feature dimension.
            reference_std: Historical std per feature dimension.
            recent_return: Most recent return (signed, e.g., -0.10 = -10%).
            current_volatility: Current annualized volatility.
            historical_volatility: Historical baseline annualized volatility.
            liquidity_score: Current liquidity quality [0, 1].
                1.0 = full liquidity, 0.0 = no liquidity.
            macro_event_scores: Dict mapping event type -> importance [0, 1].
                Only include upcoming/active events. Empty dict = no events.
            regime: Current HierarchicalRegime for regime OOD detection.

        Returns:
            OODResult with is_ood decision, score, severity, and components.
        """
        config = get_ood_config(asset_class)

        # 1. Distribution OOD (feature space)
        dist_ood = _zscore_ood(features, reference_mean, reference_std)

        # 2. Event OOD (price action)
        event_ood = self._event_ood(
            recent_return, current_volatility, historical_volatility,
            liquidity_score, config,
        )

        # 3. Macro OOD (calendar events)
        macro_ood = self._macro_ood(macro_event_scores, config)

        # 4. Regime OOD (regime transitions)
        regime_ood = self._regime_ood(regime, asset_class)

        # Combine with asset-specific weighting
        total_ood = (
            config.distribution_weight * dist_ood
            + config.event_weight * event_ood
            + config.macro_weight * macro_ood
            + REGIME_OOD_WEIGHT * regime_ood
        )
        total_ood = _clip(total_ood, 0.0, 1.0)

        is_ood = total_ood > config.ood_threshold
        severity = classify_severity(total_ood)

        components = OODComponentScores(
            distribution=round(dist_ood, 8),
            event=round(event_ood, 8),
            macro=round(macro_ood, 8),
            regime=round(regime_ood, 8),
        )

        # Deterministic hash
        payload = {
            "asset_class": asset_class.value,
            "is_ood": is_ood,
            "score": round(total_ood, 8),
            "severity": severity,
            "distribution": components.distribution,
            "event": components.event,
            "macro": components.macro,
            "regime": components.regime,
        }
        result_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]

        return OODResult(
            is_ood=is_ood,
            score=round(total_ood, 8),
            severity=severity,
            components=components,
            asset_class=asset_class,
            threshold=config.ood_threshold,
            result_hash=result_hash,
        )

    # -----------------------------------------------------------------
    # COMPONENT DETECTORS
    # -----------------------------------------------------------------

    def _event_ood(
        self,
        recent_return: float,
        current_volatility: float,
        historical_volatility: float,
        liquidity_score: float,
        config: AssetOODConfig,
    ) -> float:
        """Detect event-based OOD from price action.

        Three sub-signals combined:
        1. Flash crash: |return| vs asset-specific threshold.
        2. Vol spike: current_vol / historical_vol vs threshold.
        3. Liquidity drain: 1 - liquidity_score vs threshold.

        Returns:
            Event OOD score [0, 1].
        """
        # Flash crash detection
        abs_return = abs(recent_return)
        if config.flash_crash_threshold > 0:
            flash_score = _clip(abs_return / config.flash_crash_threshold, 0.0, 1.0)
        else:
            flash_score = 1.0 if abs_return > 0 else 0.0

        # Volatility spike detection
        if historical_volatility > 1e-15:
            vol_ratio = current_volatility / historical_volatility
            vol_score = _clip(
                (vol_ratio - 1.0) / (config.volatility_spike_threshold - 1.0)
                if config.volatility_spike_threshold > 1.0
                else vol_ratio - 1.0,
                0.0,
                1.0,
            )
        else:
            vol_score = 0.0

        # Liquidity drain detection
        liquidity_drop = 1.0 - _clip(liquidity_score, 0.0, 1.0)
        if config.liquidity_drain_threshold > 0:
            drain_score = _clip(
                liquidity_drop / config.liquidity_drain_threshold, 0.0, 1.0
            )
        else:
            drain_score = 1.0 if liquidity_drop > 0 else 0.0

        # Equal weighting of the three sub-signals
        return (flash_score + vol_score + drain_score) / 3.0

    def _macro_ood(
        self,
        macro_event_scores: Dict[str, float],
        config: AssetOODConfig,
    ) -> float:
        """Compute macro OOD score from event importance and asset sensitivity.

        For each active macro event, the contribution is:
            event_importance * asset_sensitivity

        Returns the maximum across all active events (FAS: max, not sum).

        Returns:
            Macro OOD score [0, 1].
        """
        if not macro_event_scores:
            return 0.0

        max_score = 0.0
        for event_type, importance in macro_event_scores.items():
            sensitivity = config.macro_sensitivity.get(event_type, 0.0)
            score = _clip(importance, 0.0, 1.0) * _clip(sensitivity, 0.0, 1.0)
            max_score = max(max_score, score)

        return max_score

    def _regime_ood(
        self,
        regime: HierarchicalRegime,
        asset_class: AssetClass,
    ) -> float:
        """Compute regime-based OOD score.

        FAS regime OOD signals:
        - Global CRISIS -> 1.0
        - Correlation BREAKDOWN -> 0.8
        - Asset SHOCK -> 0.9
        - Global RISK_OFF + asset HIGH_VOLATILITY -> 0.5
        - Otherwise -> 0.0

        Uses Enum comparison (PROHIBITED-09 compliant).

        Returns:
            Regime OOD score [0, 1].
        """
        score = 0.0

        # Global crisis
        if regime.global_regime == GlobalRegimeState.CRISIS:
            score = max(score, 1.0)

        # Correlation breakdown
        if regime.correlation_regime == CorrelationRegimeState.BREAKDOWN:
            score = max(score, 0.8)

        # Asset-specific shock
        asset_regime = regime.asset_regimes.get(asset_class)
        if asset_regime == AssetRegimeState.SHOCK:
            score = max(score, 0.9)

        # Risk-off + high volatility
        if (regime.global_regime == GlobalRegimeState.RISK_OFF
                and asset_regime == AssetRegimeState.HIGH_VOLATILITY):
            score = max(score, 0.5)

        return score
