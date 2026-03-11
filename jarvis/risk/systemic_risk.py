# =============================================================================
# jarvis/risk/systemic_risk.py -- Systemic Risk Monitor (Phase MA-5)
#
# Monitors cross-asset contagion, correlation regime classification,
# portfolio fragility, tail dependency stress, and concentration risk.
#
# Analytical-only. No execution. No capital modification.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   systemic_risk.py -> jarvis.core.regime (AssetClass, CorrelationRegimeState)
#   systemic_risk.py -> (stdlib + math only)
#
# DETERMINISM GUARANTEES: DET-01 through DET-07 enforced.
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly.
#   DET-03  No side effects (functions are pure; no caching).
#   DET-05  Same inputs -> same outputs.
#   DET-06  Fixed literals not parameterizable.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01: No numpy, no scipy. Pure stdlib math.
#   PROHIBITED-02: No file I/O.
#   PROHIBITED-03: No logging/print.
#   PROHIBITED-05: No global mutable state.
#   PROHIBITED-08: No new Enum definitions.
#   PROHIBITED-09: No string-based regime branching.
#
# GOVERNANCE: Correlation spikes may ONLY:
#   - Reduce ConfidenceBundle.Q via confidence_penalty
#   - Trigger FM-04 if CORR_FM04_THRESHOLD exceeded
#   - Reduce WeightPosteriorModel via weight_penalty
#   - Update Visual Output heatmap
# Correlation spikes may NOT:
#   - Auto-liquidate positions
#   - Modify PortfolioState.positions
#   - Override strategy weights
#   - Trigger execution
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from jarvis.core.regime import AssetClass, CorrelationRegimeState


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

# Correlation regime thresholds
CORR_LOW_THRESHOLD: float = 0.40     # < 0.40 -> NORMAL (legacy: DECOUPLED)
CORR_MEDIUM_THRESHOLD: float = 0.65  # 0.40-0.65 -> COUPLED; >= 0.65 -> BREAKDOWN

# FM-04 trigger threshold
CORR_FM04_THRESHOLD: float = 0.85

# Tail dependency stress multipliers (deterministic)
TAIL_STRESS_MULTIPLIERS: Dict[str, float] = {
    "MILD": 1.30,
    "MODERATE": 1.60,
    "SEVERE": 2.00,
    "EXTREME": 2.50,
}

# Recovery scenario thresholds
RECOVERY_FAST_THRESHOLD: float = 0.70
RECOVERY_SLOW_THRESHOLD: float = 0.85

# Fragility band thresholds
FRAGILITY_LOW_THRESHOLD: float = 0.30
FRAGILITY_HIGH_THRESHOLD: float = 0.60

# Fragility confidence penalty factor
FRAGILITY_CONFIDENCE_PENALTY_FACTOR: float = 0.20

# Concentration band thresholds
CONCENTRATION_LOW_THRESHOLD: float = 0.25
CONCENTRATION_HIGH_THRESHOLD: float = 0.50

# Concentration weight penalty factor
CONCENTRATION_WEIGHT_PENALTY_FACTOR: float = 0.30


# =============================================================================
# SECTION 2 -- RESULT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class CorrelationRegimeResult:
    """Correlation regime classification result.

    Attributes:
        state: Canonical CorrelationRegimeState enum.
        mean_pairwise_corr: Mean of upper-triangle absolute correlations.
        max_pairwise_corr: Maximum single-pair absolute correlation.
        n_pairs: Number of asset pairs.
        fm04_triggered: Whether mean correlation exceeds FM-04 threshold.
        result_hash: SHA-256[:16] for determinism verification.
    """
    state: CorrelationRegimeState
    mean_pairwise_corr: float
    max_pairwise_corr: float
    n_pairs: int
    fm04_triggered: bool
    result_hash: str


@dataclass(frozen=True)
class PortfolioFragilityIndex:
    """Portfolio fragility (correlation concentration) index.

    Attributes:
        hhi_correlation: HHI of mean correlations [0, 1].
        fragility_band: "LOW", "MEDIUM", or "HIGH".
        dominant_asset_id: Asset with highest mean correlation.
        dominant_corr: Dominant asset's mean correlation.
        confidence_penalty: Confidence Q reduction (hhi * 0.20).
        result_hash: SHA-256[:16] for determinism verification.
    """
    hhi_correlation: float
    fragility_band: str
    dominant_asset_id: str
    dominant_corr: float
    confidence_penalty: float
    result_hash: str


@dataclass(frozen=True)
class TailDependencyStressResult:
    """Tail dependency stress test result.

    Attributes:
        base_mean_corr: Current mean pairwise correlation.
        stressed_mean_corr: Stressed correlation (base * multiplier).
        stress_multiplier: Applied multiplier.
        fm04_triggered_base: FM-04 at base correlation.
        fm04_triggered_stress: FM-04 at stressed correlation.
        confidence_impact: Expected confidence Q reduction under stress.
        recovery_scenario: "FAST", "SLOW", or "PERSISTENT".
        result_hash: SHA-256[:16] for determinism verification.
    """
    base_mean_corr: float
    stressed_mean_corr: float
    stress_multiplier: float
    fm04_triggered_base: bool
    fm04_triggered_stress: bool
    confidence_impact: float
    recovery_scenario: str
    result_hash: str


@dataclass(frozen=True)
class ConcentrationRiskScore:
    """Asset class concentration risk score.

    Attributes:
        hhi_weight: HHI of weight fractions [0, 1].
        concentration_band: "LOW", "MEDIUM", or "HIGH".
        dominant_class: Asset class with largest weight.
        dominant_weight: Dominant class weight fraction.
        weight_penalty: Penalty to weight posterior [0, 0.30].
        result_hash: SHA-256[:16] for determinism verification.
    """
    hhi_weight: float
    concentration_band: str
    dominant_class: str
    dominant_weight: float
    weight_penalty: float
    result_hash: str


# =============================================================================
# SECTION 3 -- PURE MATH HELPERS
# =============================================================================

def _upper_triangle_values(
    matrix: Tuple[Tuple[float, ...], ...],
    n: int,
) -> List[float]:
    """Extract upper-triangle values (excluding diagonal) from NxN matrix.

    Args:
        matrix: NxN matrix as tuple of tuples.
        n: Matrix dimension.

    Returns:
        List of upper-triangle absolute values.
    """
    values = []
    for i in range(n):
        for j in range(i + 1, n):
            if i < len(matrix) and j < len(matrix[i]):
                values.append(abs(matrix[i][j]))
    return values


def _mean_corr_per_asset(
    matrix: Tuple[Tuple[float, ...], ...],
    n: int,
) -> List[float]:
    """Compute mean absolute correlation for each asset with all others.

    Args:
        matrix: NxN correlation matrix.
        n: Number of assets.

    Returns:
        List of mean correlations (one per asset).
    """
    means = []
    for i in range(n):
        total = 0.0
        count = 0
        for j in range(n):
            if i != j and i < len(matrix) and j < len(matrix[i]):
                total += abs(matrix[i][j])
                count += 1
        means.append(total / count if count > 0 else 0.0)
    return means


def _compute_hash(payload: dict) -> str:
    """Compute SHA-256[:16] hash from payload dict."""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]


# =============================================================================
# SECTION 4 -- SYSTEMIC RISK FUNCTIONS
# =============================================================================

def classify_correlation_regime(
    *,
    corr_matrix: Tuple[Tuple[float, ...], ...],
    n_assets: int,
) -> CorrelationRegimeResult:
    """Classify correlation regime from current correlation matrix.

    Deterministic threshold-based classification:
      mean_corr < 0.40  -> NORMAL
      mean_corr < 0.65  -> COUPLED
      mean_corr >= 0.65 -> BREAKDOWN

    Args:
        corr_matrix: NxN correlation matrix (tuple of tuples).
        n_assets: Number of assets.

    Returns:
        CorrelationRegimeResult with canonical enum state.
    """
    if n_assets < 2:
        payload = {"state": "NORMAL", "mean": 0.0, "max": 0.0, "n": 0, "fm04": False}
        return CorrelationRegimeResult(
            state=CorrelationRegimeState.NORMAL,
            mean_pairwise_corr=0.0,
            max_pairwise_corr=0.0,
            n_pairs=0,
            fm04_triggered=False,
            result_hash=_compute_hash(payload),
        )

    upper = _upper_triangle_values(corr_matrix, n_assets)
    n_pairs = len(upper)

    if n_pairs == 0:
        mean_corr = 0.0
        max_corr = 0.0
    else:
        mean_corr = sum(upper) / n_pairs
        max_corr = max(upper)

    # Classify state
    if mean_corr < CORR_LOW_THRESHOLD:
        state = CorrelationRegimeState.NORMAL
    elif mean_corr < CORR_MEDIUM_THRESHOLD:
        state = CorrelationRegimeState.COUPLED
    else:
        state = CorrelationRegimeState.BREAKDOWN

    fm04 = mean_corr > CORR_FM04_THRESHOLD

    payload = {
        "state": state.value,
        "mean": round(mean_corr, 8),
        "max": round(max_corr, 8),
        "n": n_pairs,
        "fm04": fm04,
    }

    return CorrelationRegimeResult(
        state=state,
        mean_pairwise_corr=mean_corr,
        max_pairwise_corr=max_corr,
        n_pairs=n_pairs,
        fm04_triggered=fm04,
        result_hash=_compute_hash(payload),
    )


def compute_portfolio_fragility(
    *,
    corr_matrix: Tuple[Tuple[float, ...], ...],
    asset_ids: List[str],
) -> PortfolioFragilityIndex:
    """Compute Herfindahl-style correlation concentration index.

    HHI_corr = sum_i(mean_corr_i^2) / n_assets

    Args:
        corr_matrix: NxN correlation matrix.
        asset_ids: Ordered list of asset identifiers.

    Returns:
        PortfolioFragilityIndex with HHI, band, and confidence penalty.
    """
    n = len(asset_ids)

    if n < 2:
        payload = {"hhi": 0.0, "band": "LOW", "dom": "", "dom_corr": 0.0, "pen": 0.0}
        return PortfolioFragilityIndex(
            hhi_correlation=0.0,
            fragility_band="LOW",
            dominant_asset_id=asset_ids[0] if n == 1 else "",
            dominant_corr=0.0,
            confidence_penalty=0.0,
            result_hash=_compute_hash(payload),
        )

    mean_corrs = _mean_corr_per_asset(corr_matrix, n)

    # HHI: sum of squared mean correlations, normalized by n
    hhi = sum(mc ** 2 for mc in mean_corrs) / n

    # Dominant asset
    max_idx = 0
    max_corr = mean_corrs[0]
    for i in range(1, n):
        if mean_corrs[i] > max_corr:
            max_corr = mean_corrs[i]
            max_idx = i
    dominant_id = asset_ids[max_idx]

    # Band classification
    if hhi < FRAGILITY_LOW_THRESHOLD:
        band = "LOW"
    elif hhi < FRAGILITY_HIGH_THRESHOLD:
        band = "MEDIUM"
    else:
        band = "HIGH"

    # Confidence penalty (clipped to [0, 0.20])
    penalty = min(hhi * FRAGILITY_CONFIDENCE_PENALTY_FACTOR, 0.20)

    payload = {
        "hhi": round(hhi, 8),
        "band": band,
        "dom": dominant_id,
        "dom_corr": round(max_corr, 8),
        "pen": round(penalty, 8),
    }

    return PortfolioFragilityIndex(
        hhi_correlation=hhi,
        fragility_band=band,
        dominant_asset_id=dominant_id,
        dominant_corr=max_corr,
        confidence_penalty=penalty,
        result_hash=_compute_hash(payload),
    )


def simulate_tail_stress(
    *,
    current_corr_regime: CorrelationRegimeResult,
    stress_scenario: str = "MODERATE",
) -> TailDependencyStressResult:
    """Apply deterministic stress multiplier to current correlation state.

    Args:
        current_corr_regime: Current correlation regime result.
        stress_scenario: One of "MILD", "MODERATE", "SEVERE", "EXTREME".

    Returns:
        TailDependencyStressResult with stressed values.
    """
    multiplier = TAIL_STRESS_MULTIPLIERS.get(stress_scenario, 1.60)
    base = current_corr_regime.mean_pairwise_corr

    # Apply stress: clip to [0, 1]
    stressed = max(0.0, min(1.0, base * multiplier))

    fm04_base = current_corr_regime.fm04_triggered
    fm04_stress = stressed > CORR_FM04_THRESHOLD

    # Confidence impact
    if fm04_stress:
        confidence_impact = stressed * 0.30
    else:
        confidence_impact = stressed * 0.10

    # Recovery scenario
    if stressed < RECOVERY_FAST_THRESHOLD:
        recovery = "FAST"
    elif stressed < RECOVERY_SLOW_THRESHOLD:
        recovery = "SLOW"
    else:
        recovery = "PERSISTENT"

    payload = {
        "base": round(base, 8),
        "stressed": round(stressed, 8),
        "mult": round(multiplier, 8),
        "fm04_b": fm04_base,
        "fm04_s": fm04_stress,
        "ci": round(confidence_impact, 8),
        "rec": recovery,
    }

    return TailDependencyStressResult(
        base_mean_corr=base,
        stressed_mean_corr=stressed,
        stress_multiplier=multiplier,
        fm04_triggered_base=fm04_base,
        fm04_triggered_stress=fm04_stress,
        confidence_impact=confidence_impact,
        recovery_scenario=recovery,
        result_hash=_compute_hash(payload),
    )


def compute_concentration_risk(
    *,
    weights_by_class: Dict[str, float],
) -> ConcentrationRiskScore:
    """HHI-based concentration measure over simulated asset class weights.

    HHI_weight = sum_k(w_k^2) where w_k = normalized weight fraction.

    Args:
        weights_by_class: Dict mapping asset class name -> weight (raw).

    Returns:
        ConcentrationRiskScore with HHI, band, and weight penalty.
    """
    if not weights_by_class:
        payload = {"hhi": 0.0, "band": "LOW", "dom": "", "dom_w": 0.0, "pen": 0.0}
        return ConcentrationRiskScore(
            hhi_weight=0.0,
            concentration_band="LOW",
            dominant_class="",
            dominant_weight=0.0,
            weight_penalty=0.0,
            result_hash=_compute_hash(payload),
        )

    # Normalize weights
    total = sum(abs(v) for v in weights_by_class.values())
    if total <= 0.0:
        n = len(weights_by_class)
        fracs = {k: 1.0 / n for k in weights_by_class}
    else:
        fracs = {k: abs(v) / total for k, v in weights_by_class.items()}

    # HHI
    hhi = sum(w ** 2 for w in fracs.values())

    # Dominant class
    dominant_class = max(fracs, key=fracs.get)
    dominant_weight = fracs[dominant_class]

    # Band classification
    if hhi < CONCENTRATION_LOW_THRESHOLD:
        band = "LOW"
    elif hhi < CONCENTRATION_HIGH_THRESHOLD:
        band = "MEDIUM"
    else:
        band = "HIGH"

    # Weight penalty (clipped to [0, 0.30])
    penalty = min(hhi * CONCENTRATION_WEIGHT_PENALTY_FACTOR, 0.30)

    payload = {
        "hhi": round(hhi, 8),
        "band": band,
        "dom": dominant_class,
        "dom_w": round(dominant_weight, 8),
        "pen": round(penalty, 8),
    }

    return ConcentrationRiskScore(
        hhi_weight=hhi,
        concentration_band=band,
        dominant_class=dominant_class,
        dominant_weight=dominant_weight,
        weight_penalty=penalty,
        result_hash=_compute_hash(payload),
    )
