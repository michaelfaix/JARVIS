# =============================================================================
# jarvis/risk/portfolio_heatmap.py -- Portfolio Heatmap Engine (Phase MA-5)
#
# Analytical visualization layer for portfolio risk monitoring.
# Enforces live update policy: updates only on confirmed triggers,
# NOT on every tick or price update.
#
# P0: Purely analytical. No execution. No orders.
# Output goes ONLY to Visual Output Layer (P9).
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   portfolio_heatmap.py -> jarvis.core.regime (AssetClass,
#                           CorrelationRegimeState, GlobalRegimeState,
#                           HierarchicalRegime)
#   portfolio_heatmap.py -> jarvis.risk.portfolio_risk (PortfolioRiskResult)
#   portfolio_heatmap.py -> (stdlib + math only)
#
# DETERMINISM GUARANTEES: DET-01, DET-02, DET-05, DET-06 enforced.
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly to build_snapshot.
#   DET-05  Same inputs -> same outputs (for build_snapshot).
#   DET-06  Fixed literals not parameterizable.
#
# NOTE: PortfolioHeatmapEngine is stateful by design (caches last snapshot
# for delta detection in should_update). This is a service layer, not a
# computation layer. State is internal to the engine instance.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01: No numpy, no scipy. Pure stdlib math.
#   PROHIBITED-02: No file I/O.
#   PROHIBITED-03: No logging/print.
#   PROHIBITED-08: No new Enum definitions.
#   PROHIBITED-09: No string-based regime branching.
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
    CorrelationRegimeState,
    GlobalRegimeState,
    HierarchicalRegime,
)
from jarvis.risk.portfolio_risk import PortfolioRiskResult


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

# Exposure delta thresholds for update triggers
EXPOSURE_DELTA_THRESHOLD: float = 0.05       # 5% gross exposure change
NET_EXPOSURE_DELTA_THRESHOLD: float = 0.03   # 3% net exposure change

# Correlation delta thresholds for update triggers
CORRELATION_DELTA_THRESHOLD: float = 0.05    # Mean pairwise correlation delta
CORRELATION_SINGLE_THRESHOLD: float = 0.10   # Single pair correlation delta

# Heat score weights
HEAT_VOL_WEIGHT: float = 0.5
HEAT_CORR_WEIGHT: float = 0.5

# Trigger reason strings
TRIGGER_NEW_CANDLE: str = "NEW_CONFIRMED_CANDLE"
TRIGGER_REGIME_TRANSITION: str = "REGIME_TRANSITION"
TRIGGER_FAILURE_MODE: str = "FAILURE_MODE_STATUS_CHANGE"
TRIGGER_EXPOSURE_DELTA: str = "EXPOSURE_DELTA_THRESHOLD"
TRIGGER_CORRELATION_SHIFT: str = "CORRELATION_REGIME_SHIFT"
TRIGGER_NONE: str = "NO_TRIGGER"


# =============================================================================
# SECTION 2 -- RESULT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class HeatmapCell:
    """Per-asset heatmap cell.

    Attributes:
        asset_id: Asset symbol.
        asset_class: Asset class.
        simulated_weight: Simulated portfolio weight [0, 1].
        vol_percentile: Volatility percentile [0, 1].
        correlation_mean: Mean correlation with rest of portfolio.
        failure_modes: Active FM codes for this asset.
        heat_score: Composite heat [0, 1]; 1 = hottest.
    """
    asset_id: str
    asset_class: AssetClass
    simulated_weight: float
    vol_percentile: float
    correlation_mean: float
    failure_modes: Tuple[str, ...]
    heat_score: float


@dataclass(frozen=True)
class PortfolioHeatmapSnapshot:
    """Portfolio-level heatmap snapshot.

    Attributes:
        cells: Per-asset heatmap cells.
        global_heat: Portfolio-level heat [0, 1].
        diversification_ratio: Portfolio diversification ratio.
        active_failure_modes: All active FM codes.
        regime: Current global regime state.
        correlation_regime: Current correlation regime.
        trigger_reason: Why this update was triggered.
        num_assets: Number of assets.
        result_hash: SHA-256[:16] for determinism verification.
    """
    cells: Dict[str, HeatmapCell]
    global_heat: float
    diversification_ratio: float
    active_failure_modes: Tuple[str, ...]
    regime: GlobalRegimeState
    correlation_regime: CorrelationRegimeState
    trigger_reason: str
    num_assets: int
    result_hash: str


# =============================================================================
# SECTION 3 -- PURE HELPERS
# =============================================================================

def _compute_vol_percentile(
    asset_vol: float,
    all_vols: List[float],
) -> float:
    """Compute percentile rank of asset vol within portfolio vols.

    Args:
        asset_vol: This asset's annualized volatility.
        all_vols: All asset volatilities in portfolio.

    Returns:
        Percentile [0, 1].
    """
    if not all_vols or len(all_vols) < 2:
        return 0.5

    count_below = sum(1 for v in all_vols if v < asset_vol)
    return count_below / (len(all_vols) - 1) if len(all_vols) > 1 else 0.5


def _compute_asset_corr_mean(
    matrix: Tuple[Tuple[float, ...], ...],
    asset_idx: int,
    n: int,
) -> float:
    """Compute mean absolute correlation of asset with all others.

    Args:
        matrix: NxN correlation matrix.
        asset_idx: Index of the asset.
        n: Number of assets.

    Returns:
        Mean absolute off-diagonal correlation.
    """
    if n < 2:
        return 0.0

    total = 0.0
    count = 0
    for j in range(n):
        if j != asset_idx and asset_idx < len(matrix) and j < len(matrix[asset_idx]):
            total += abs(matrix[asset_idx][j])
            count += 1

    return total / count if count > 0 else 0.0


def _compute_heat_score(vol_percentile: float, corr_mean: float) -> float:
    """Compute composite heat score.

    heat = 0.5 * vol_percentile + 0.5 * corr_mean, clipped to [0, 1].

    Args:
        vol_percentile: Volatility percentile [0, 1].
        corr_mean: Mean correlation with rest of portfolio.

    Returns:
        Heat score [0, 1].
    """
    raw = HEAT_VOL_WEIGHT * vol_percentile + HEAT_CORR_WEIGHT * corr_mean
    return max(0.0, min(1.0, raw))


def _matrix_delta(
    a: Tuple[Tuple[float, ...], ...],
    b: Tuple[Tuple[float, ...], ...],
    n: int,
) -> Tuple[float, float]:
    """Compute mean and max absolute delta of upper-triangle values.

    Args:
        a: First NxN correlation matrix.
        b: Second NxN correlation matrix.
        n: Matrix dimension.

    Returns:
        (mean_delta, max_delta) of upper-triangle absolute differences.
    """
    deltas = []
    for i in range(n):
        for j in range(i + 1, n):
            val_a = a[i][j] if i < len(a) and j < len(a[i]) else 0.0
            val_b = b[i][j] if i < len(b) and j < len(b[i]) else 0.0
            deltas.append(abs(val_a - val_b))

    if not deltas:
        return 0.0, 0.0

    return sum(deltas) / len(deltas), max(deltas)


# =============================================================================
# SECTION 4 -- PORTFOLIO HEATMAP ENGINE
# =============================================================================

class PortfolioHeatmapEngine:
    """Portfolio Heatmap Engine with Live Update Policy enforcement.

    READ-ONLY access to portfolio state.
    No execution. No orders. Pure analytical display output.

    Stateful: caches last snapshot state for delta detection.
    """

    def __init__(self) -> None:
        self._last_corr_matrix: Optional[Tuple[Tuple[float, ...], ...]] = None
        self._last_gross_exp: float = 0.0
        self._last_net_exp: float = 0.0
        self._last_regime: Optional[GlobalRegimeState] = None
        self._last_fm_states: Tuple[str, ...] = ()
        self._last_n_assets: int = 0

    def should_update(
        self,
        *,
        new_candle_confirmed: bool,
        current_corr_matrix: Tuple[Tuple[float, ...], ...],
        n_assets: int,
        current_gross_exp: float,
        current_net_exp: float,
        current_regime: GlobalRegimeState,
        active_failure_modes: Tuple[str, ...],
        regime_transition_flag: bool,
    ) -> Tuple[bool, str]:
        """Check whether heatmap should update per Live Update Policy.

        Priority order:
        1. NEW_CONFIRMED_CANDLE
        2. REGIME_TRANSITION
        3. FAILURE_MODE_STATUS_CHANGE
        4. EXPOSURE_DELTA_THRESHOLD
        5. CORRELATION_REGIME_SHIFT
        6. NO_TRIGGER

        Args:
            new_candle_confirmed: Whether a new candle has closed.
            current_corr_matrix: Current correlation matrix.
            n_assets: Number of assets.
            current_gross_exp: Current gross exposure fraction.
            current_net_exp: Current net exposure fraction.
            current_regime: Current global regime state.
            active_failure_modes: Currently active FM codes.
            regime_transition_flag: Whether a regime transition is in progress.

        Returns:
            (should_update, trigger_reason) tuple.
        """
        # 1. New candle
        if new_candle_confirmed:
            return True, TRIGGER_NEW_CANDLE

        # 2. Regime transition
        if regime_transition_flag or (
            self._last_regime is not None and current_regime != self._last_regime
        ):
            return True, TRIGGER_REGIME_TRANSITION

        # 3. Failure mode status change
        if active_failure_modes != self._last_fm_states:
            return True, TRIGGER_FAILURE_MODE

        # 4. Exposure delta
        gross_delta = abs(current_gross_exp - self._last_gross_exp)
        net_delta = abs(current_net_exp - self._last_net_exp)
        if gross_delta > EXPOSURE_DELTA_THRESHOLD:
            return True, TRIGGER_EXPOSURE_DELTA
        if net_delta > NET_EXPOSURE_DELTA_THRESHOLD:
            return True, TRIGGER_EXPOSURE_DELTA

        # 5. Correlation shift
        if (
            self._last_corr_matrix is not None
            and n_assets >= 2
            and self._last_n_assets == n_assets
        ):
            mean_d, max_d = _matrix_delta(
                self._last_corr_matrix, current_corr_matrix, n_assets,
            )
            if mean_d > CORRELATION_DELTA_THRESHOLD:
                return True, TRIGGER_CORRELATION_SHIFT
            if max_d > CORRELATION_SINGLE_THRESHOLD:
                return True, TRIGGER_CORRELATION_SHIFT

        # 6. No trigger
        return False, TRIGGER_NONE

    def build_snapshot(
        self,
        *,
        portfolio_risk: PortfolioRiskResult,
        active_failure_modes: Tuple[str, ...],
        trigger_reason: str,
        gross_exposure: float,
        net_exposure: float,
    ) -> PortfolioHeatmapSnapshot:
        """Build a new heatmap snapshot from current portfolio risk.

        All inputs are immutable snapshots. No live state references.

        Args:
            portfolio_risk: Current portfolio risk result (read-only).
            active_failure_modes: Currently active FM codes.
            trigger_reason: Why this update was triggered.
            gross_exposure: Current gross exposure fraction.
            net_exposure: Current net exposure fraction.

        Returns:
            PortfolioHeatmapSnapshot with per-asset heat scores.
        """
        asset_risks = portfolio_risk.asset_risks
        corr_matrix = portfolio_risk.correlation_result.matrix
        regime = portfolio_risk.regime
        symbols = sorted(asset_risks.keys())
        n = len(symbols)

        # Collect all volatilities for percentile calculation
        all_vols = [asset_risks[s].volatility.annualized for s in symbols]

        # Total notional for weight computation
        total_notional = portfolio_risk.total_notional

        # Build cells
        cells: Dict[str, HeatmapCell] = {}
        for idx, sym in enumerate(symbols):
            ar = asset_risks[sym]
            weight = ar.notional / total_notional if total_notional > 0.0 else 0.0
            vol_pct = _compute_vol_percentile(ar.volatility.annualized, all_vols)
            corr_mean = _compute_asset_corr_mean(corr_matrix, idx, n)
            heat = _compute_heat_score(vol_pct, corr_mean)

            cells[sym] = HeatmapCell(
                asset_id=sym,
                asset_class=ar.asset_class,
                simulated_weight=weight,
                vol_percentile=vol_pct,
                correlation_mean=corr_mean,
                failure_modes=active_failure_modes,
                heat_score=heat,
            )

        # Global heat
        if cells:
            global_heat = sum(c.heat_score for c in cells.values()) / len(cells)
        else:
            global_heat = 0.0

        # Diversification ratio
        div_ratio = portfolio_risk.diversification_benefit

        # Hash
        payload = {
            "global_heat": round(global_heat, 8),
            "div_ratio": round(div_ratio, 8),
            "n": n,
            "trigger": trigger_reason,
            "regime": regime.global_regime.value,
            "corr_regime": regime.correlation_regime.value,
        }
        result_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]

        snapshot = PortfolioHeatmapSnapshot(
            cells=cells,
            global_heat=global_heat,
            diversification_ratio=div_ratio,
            active_failure_modes=active_failure_modes,
            regime=regime.global_regime,
            correlation_regime=regime.correlation_regime,
            trigger_reason=trigger_reason,
            num_assets=n,
            result_hash=result_hash,
        )

        # Cache state for next delta detection
        self._last_corr_matrix = corr_matrix
        self._last_gross_exp = gross_exposure
        self._last_net_exp = net_exposure
        self._last_regime = regime.global_regime
        self._last_fm_states = active_failure_modes
        self._last_n_assets = n

        return snapshot
