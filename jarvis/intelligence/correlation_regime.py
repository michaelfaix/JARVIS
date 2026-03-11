# =============================================================================
# jarvis/intelligence/correlation_regime.py -- Correlation Regime Detector (Phase MA-3)
#
# Tier 3 of the 3-Tier Hierarchical Regime System.
# Detects cross-asset correlation structure:
#   normal | divergence | convergence | breakdown
#
# Breakdown triggers CRITICAL alert -> immediate portfolio risk reduction.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   correlation_regime.py -> jarvis.core.regime (CorrelationRegimeState)
#   correlation_regime.py -> (stdlib only otherwise)
#
# DETERMINISM GUARANTEES: DET-01 through DET-07 enforced.
# PROHIBITED ACTIONS: PROHIBITED-01 through PROHIBITED-10 absent.
#   PROHIBITED-01: No numpy. Pure stdlib math for correlation.
#   PROHIBITED-02: No file I/O.
#   PROHIBITED-08: No new Regime-Enum definitions.
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from jarvis.core.regime import CorrelationRegimeState


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

# FAS: Correlation breakdown threshold
BREAKDOWN_THRESHOLD: float = 0.8

# FAS: Convergence/divergence sensitivity relative to historical average
CONVERGENCE_DELTA: float = 0.2
DIVERGENCE_DELTA: float = 0.2

# FAS: Rolling correlation window (days)
CORRELATION_WINDOW: int = 30

# Alert levels
ALERT_CRITICAL: str = "CRITICAL"
ALERT_HIGH: str = "HIGH"
ALERT_NORMAL: str = "NORMAL"
ALERT_LOW: str = "LOW"

# Internal state strings (metadata, not Enums per PROHIBITED-08)
CORRELATION_STATES: Tuple[str, ...] = ("normal", "divergence", "convergence", "breakdown")

# FAS state -> canonical CorrelationRegimeState
_STATE_TO_CANONICAL: Dict[str, CorrelationRegimeState] = {
    "normal":      CorrelationRegimeState.NORMAL,
    "divergence":  CorrelationRegimeState.DIVERGENCE,
    "convergence": CorrelationRegimeState.COUPLED,
    "breakdown":   CorrelationRegimeState.BREAKDOWN,
}

# FAS state -> alert level
_STATE_TO_ALERT: Dict[str, str] = {
    "normal":      ALERT_NORMAL,
    "divergence":  ALERT_LOW,
    "convergence": ALERT_HIGH,
    "breakdown":   ALERT_CRITICAL,
}


# =============================================================================
# SECTION 2 -- RESULT DATACLASS
# =============================================================================

@dataclass(frozen=True)
class CorrelationRegimeResult:
    """Tier 3 correlation regime detection result.

    Attributes:
        state: Internal state string (normal/divergence/convergence/breakdown).
        canonical_state: Mapped CorrelationRegimeState for downstream.
        average_correlation: Mean pairwise correlation.
        historical_average: Baseline average correlation.
        alert_level: CRITICAL | HIGH | NORMAL | LOW.
        pair_correlations: Dict of (asset_a, asset_b) -> correlation.
        num_assets: Number of assets in the correlation matrix.
    """
    state: str
    canonical_state: CorrelationRegimeState
    average_correlation: float
    historical_average: float
    alert_level: str
    pair_correlations: Dict[Tuple[str, str], float]
    num_assets: int


# =============================================================================
# SECTION 3 -- PURE MATH HELPERS (stdlib only, DET-01)
# =============================================================================

def _mean(values: List[float]) -> float:
    """Arithmetic mean. Returns 0.0 for empty list."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def _pearson_correlation(xs: List[float], ys: List[float]) -> float:
    """Pearson correlation coefficient. Pure stdlib.

    Returns 0.0 if either series has zero variance or lengths differ.
    """
    n = len(xs)
    if n < 2 or n != len(ys):
        return 0.0

    mean_x = _mean(xs)
    mean_y = _mean(ys)

    cov = 0.0
    var_x = 0.0
    var_y = 0.0

    for i in range(n):
        dx = xs[i] - mean_x
        dy = ys[i] - mean_y
        cov += dx * dy
        var_x += dx * dx
        var_y += dy * dy

    if var_x < 1e-15 or var_y < 1e-15:
        return 0.0

    r = cov / math.sqrt(var_x * var_y)
    # Clip to [-1, 1] for numerical safety
    return max(-1.0, min(1.0, r))


def compute_pairwise_correlations(
    returns: Dict[str, List[float]],
) -> Dict[Tuple[str, str], float]:
    """Compute pairwise Pearson correlations between all asset return series.

    Args:
        returns: Dict mapping asset names to return series (lists of floats).
                 All series should have the same length.

    Returns:
        Dict mapping (asset_a, asset_b) pairs to correlation values.
        Only upper-triangle pairs are included (a < b alphabetically).
    """
    assets = sorted(returns.keys())
    pairs: Dict[Tuple[str, str], float] = {}

    for i in range(len(assets)):
        for j in range(i + 1, len(assets)):
            a, b = assets[i], assets[j]
            corr = _pearson_correlation(returns[a], returns[b])
            pairs[(a, b)] = corr

    return pairs


def compute_average_correlation(
    pair_correlations: Dict[Tuple[str, str], float],
) -> float:
    """Compute average of all pairwise correlations.

    Returns 0.0 if no pairs.
    """
    if not pair_correlations:
        return 0.0
    return _mean(list(pair_correlations.values()))


# =============================================================================
# SECTION 4 -- CORRELATION REGIME DETECTOR
# =============================================================================

class CorrelationRegimeDetector:
    """Tier 3: Cross-asset correlation regime detector.

    Detects correlation structure from pairwise return correlations.
    Compares current average correlation to historical baseline.

    FAS thresholds:
        breakdown:   avg_corr > 0.8
        convergence: avg_corr > hist_avg + 0.2
        divergence:  avg_corr < hist_avg - 0.2
        normal:      otherwise

    All inputs are explicit parameters (DET-02).
    No internal state retained between calls (DET-03, PROHIBITED-05).
    """

    def detect(
        self,
        *,
        returns: Dict[str, List[float]],
        historical_average: float,
    ) -> CorrelationRegimeResult:
        """Detect correlation regime from asset return series.

        Args:
            returns: Dict mapping asset names to return series.
                     Each series should cover at least CORRELATION_WINDOW days.
            historical_average: Historical baseline average correlation.

        Returns:
            CorrelationRegimeResult with state, alert, and pair correlations.
        """
        pair_corrs = compute_pairwise_correlations(returns)
        avg_corr = compute_average_correlation(pair_corrs)
        num_assets = len(returns)

        state = self._classify(avg_corr, historical_average)

        return CorrelationRegimeResult(
            state=state,
            canonical_state=_STATE_TO_CANONICAL[state],
            average_correlation=avg_corr,
            historical_average=historical_average,
            alert_level=_STATE_TO_ALERT[state],
            pair_correlations=pair_corrs,
            num_assets=num_assets,
        )

    def detect_from_matrix(
        self,
        *,
        pair_correlations: Dict[Tuple[str, str], float],
        historical_average: float,
        num_assets: int,
    ) -> CorrelationRegimeResult:
        """Detect correlation regime from pre-computed pair correlations.

        Args:
            pair_correlations: Pre-computed (asset_a, asset_b) -> correlation.
            historical_average: Historical baseline average correlation.
            num_assets: Number of assets.

        Returns:
            CorrelationRegimeResult.
        """
        avg_corr = compute_average_correlation(pair_correlations)
        state = self._classify(avg_corr, historical_average)

        return CorrelationRegimeResult(
            state=state,
            canonical_state=_STATE_TO_CANONICAL[state],
            average_correlation=avg_corr,
            historical_average=historical_average,
            alert_level=_STATE_TO_ALERT[state],
            pair_correlations=pair_correlations,
            num_assets=num_assets,
        )

    def _classify(self, avg_corr: float, historical_average: float) -> str:
        """Classify correlation regime state.

        FAS priority order:
        1. avg_corr > 0.8 -> breakdown (CRITICAL)
        2. avg_corr > hist_avg + 0.2 -> convergence (HIGH)
        3. avg_corr < hist_avg - 0.2 -> divergence (LOW)
        4. else -> normal (NORMAL)
        """
        if avg_corr > BREAKDOWN_THRESHOLD:
            return "breakdown"
        if avg_corr > historical_average + CONVERGENCE_DELTA:
            return "convergence"
        if avg_corr < historical_average - DIVERGENCE_DELTA:
            return "divergence"
        return "normal"
