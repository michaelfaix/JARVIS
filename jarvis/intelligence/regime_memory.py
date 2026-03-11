# =============================================================================
# jarvis/intelligence/regime_memory.py -- Multi-Asset Regime Memory (Phase MA-3)
#
# Extended regime memory for multi-asset context-aware decisions.
# Stores per-asset and cross-asset regime histories with transition tracking.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   regime_memory.py -> jarvis.core.regime (HierarchicalRegime, GlobalRegimeState,
#                       AssetRegimeState, CorrelationRegimeState, AssetClass)
#   regime_memory.py -> (stdlib only otherwise)
#
# DETERMINISM GUARANTEES:
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly (timestamps are parameters).
#   DET-03  No external side effects (no logging, no file I/O).
#   DET-05  Same sequence of updates -> same internal state.
#   DET-06  Fixed literals not parameterizable.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01: No numpy.
#   PROHIBITED-02: No file I/O.
#   PROHIBITED-03: No logging/print.
#   PROHIBITED-04: No os.environ.
#   PROHIBITED-05: Stateful by design (deque histories); no module-level state.
#   PROHIBITED-08: No new Regime-Enum definitions.
#   PROHIBITED-09: No string-based regime branching (uses Enum instances).
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from jarvis.core.regime import (
    AssetClass,
    AssetRegimeState,
    CorrelationRegimeState,
    GlobalRegimeState,
    HierarchicalRegime,
)


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

# FAS: Default lookback for regime history (days)
DEFAULT_LOOKBACK_DAYS: int = 365

# FAS: Hourly granularity -> entries per day
ENTRIES_PER_DAY: int = 24

# Asset class attribute name mapping for history deques
_ASSET_HISTORY_KEYS: Tuple[AssetClass, ...] = (
    AssetClass.CRYPTO,
    AssetClass.FOREX,
    AssetClass.INDICES,
    AssetClass.COMMODITIES,
    AssetClass.RATES,
)


# =============================================================================
# SECTION 2 -- TRANSITION RECORD DATACLASS
# =============================================================================

@dataclass(frozen=True)
class RegimeTransitionRecord:
    """Record of a single regime transition event.

    Attributes:
        dimension: Which regime dimension changed (e.g., "global", "crypto", "correlation").
        from_state: Previous state value string.
        to_state: New state value string.
        timestamp: UTC ISO-8601 timestamp of the transition.
        sequence_id: Sequence ID from the triggering HierarchicalRegime.
    """
    dimension: str
    from_state: str
    to_state: str
    timestamp: str
    sequence_id: int


@dataclass(frozen=True)
class BreakdownAlert:
    """Alert generated when correlation transitions to BREAKDOWN.

    Attributes:
        timestamp: UTC ISO-8601 timestamp.
        sequence_id: Sequence ID from the triggering HierarchicalRegime.
        previous_state: Previous correlation state value.
    """
    timestamp: str
    sequence_id: int
    previous_state: str


# =============================================================================
# SECTION 3 -- MULTI-ASSET REGIME MEMORY
# =============================================================================

class MultiAssetRegimeMemory:
    """Extended regime memory for multi-asset context-aware decisions.

    Stores separate deque-based histories for:
    - Global regime (GlobalRegimeState)
    - Per-asset-class regimes (AssetRegimeState)
    - Correlation regime (CorrelationRegimeState)

    Tracks transitions and counts per dimension.
    Generates BreakdownAlert when correlation transitions to BREAKDOWN.

    FAS: lookback_days=365, hourly granularity -> maxlen=365*24=8760.

    This class is intentionally stateful (regime history accumulator).
    It is NOT a computation-layer module -- it is a memory/context service.
    Instances are NOT shared as module-level singletons (PROHIBITED-05).
    """

    def __init__(self, lookback_days: int = DEFAULT_LOOKBACK_DAYS) -> None:
        self.lookback_days: int = lookback_days
        maxlen = lookback_days * ENTRIES_PER_DAY

        # Separate histories per FAS
        self.global_history: deque = deque(maxlen=maxlen)
        self.asset_histories: Dict[AssetClass, deque] = {
            ac: deque(maxlen=maxlen) for ac in _ASSET_HISTORY_KEYS
        }
        self.correlation_history: deque = deque(maxlen=maxlen)

        # Transition tracking
        self.last_transition: Dict[str, RegimeTransitionRecord] = {}
        self.transition_counts: Dict[str, int] = defaultdict(int)
        self.transition_log: deque = deque(maxlen=maxlen)

        # Breakdown alerts (returned via update, not logged per PROHIBITED-03)
        self._pending_alerts: List[BreakdownAlert] = []

    # -----------------------------------------------------------------
    # PUBLIC API
    # -----------------------------------------------------------------

    def update(self, regime: HierarchicalRegime) -> List[BreakdownAlert]:
        """Update all regime histories from a HierarchicalRegime snapshot.

        Args:
            regime: Current HierarchicalRegime (frozen dataclass from regime.py).

        Returns:
            List of BreakdownAlert objects if correlation breakdown detected.
            Empty list otherwise.
        """
        self._pending_alerts = []

        # 1. Global history
        self.global_history.append(regime.global_regime)

        # 2. Per-asset histories
        for asset_class, asset_regime in regime.asset_regimes.items():
            if asset_class in self.asset_histories:
                self.asset_histories[asset_class].append(asset_regime)

        # 3. Correlation history
        self.correlation_history.append(regime.correlation_regime)

        # 4. Detect transitions
        self._detect_transitions(regime)

        return list(self._pending_alerts)

    def get_global_history(self) -> List[GlobalRegimeState]:
        """Return global regime history as a list."""
        return list(self.global_history)

    def get_asset_history(self, asset_class: AssetClass) -> List[AssetRegimeState]:
        """Return asset-class regime history as a list."""
        if asset_class not in self.asset_histories:
            return []
        return list(self.asset_histories[asset_class])

    def get_correlation_history(self) -> List[CorrelationRegimeState]:
        """Return correlation regime history as a list."""
        return list(self.correlation_history)

    def get_transition_count(self, transition_key: str) -> int:
        """Return count for a specific transition key."""
        return self.transition_counts.get(transition_key, 0)

    def get_last_transition(self, dimension: str) -> Optional[RegimeTransitionRecord]:
        """Return the most recent transition for a given dimension."""
        return self.last_transition.get(dimension)

    def get_transition_log(self) -> List[RegimeTransitionRecord]:
        """Return full transition log as a list."""
        return list(self.transition_log)

    def get_regime_persistence(self, dimension: str) -> int:
        """Count consecutive identical states at tail of a dimension's history.

        Args:
            dimension: "global", an AssetClass value string, or "correlation".

        Returns:
            Number of consecutive identical states at end of history.
            0 if history is empty.
        """
        history = self._get_history_for_dimension(dimension)
        if not history:
            return 0

        current = history[-1]
        count = 0
        for state in reversed(history):
            if state == current:
                count += 1
            else:
                break
        return count

    def get_state_distribution(self, dimension: str) -> Dict[str, float]:
        """Compute relative frequency distribution of states in a dimension.

        Args:
            dimension: "global", an AssetClass value string, or "correlation".

        Returns:
            Dict mapping state value strings to relative frequencies [0.0, 1.0].
            Empty dict if no history.
        """
        history = self._get_history_for_dimension(dimension)
        if not history:
            return {}

        counts: Dict[str, int] = defaultdict(int)
        for state in history:
            counts[state.value] += 1

        total = len(history)
        return {k: v / total for k, v in sorted(counts.items())}

    @property
    def total_updates(self) -> int:
        """Total number of updates (global history length)."""
        return len(self.global_history)

    # -----------------------------------------------------------------
    # INTERNAL METHODS
    # -----------------------------------------------------------------

    def _detect_transitions(self, regime: HierarchicalRegime) -> None:
        """Detect regime state changes across all dimensions."""
        # Global regime transitions
        if len(self.global_history) > 1:
            prev_global = self.global_history[-2]
            curr_global = regime.global_regime

            if prev_global != curr_global:
                key = f"global_{prev_global.value}_to_{curr_global.value}"
                record = RegimeTransitionRecord(
                    dimension="global",
                    from_state=prev_global.value,
                    to_state=curr_global.value,
                    timestamp=regime.timestamp,
                    sequence_id=regime.sequence_id,
                )
                self.transition_counts[key] += 1
                self.last_transition["global"] = record
                self.transition_log.append(record)

        # Per-asset regime transitions
        for asset_class in _ASSET_HISTORY_KEYS:
            history = self.asset_histories[asset_class]
            if len(history) > 1 and asset_class in regime.asset_regimes:
                prev_asset = history[-2]
                curr_asset = regime.asset_regimes[asset_class]

                if prev_asset != curr_asset:
                    dim = asset_class.value
                    key = f"{dim}_{prev_asset.value}_to_{curr_asset.value}"
                    record = RegimeTransitionRecord(
                        dimension=dim,
                        from_state=prev_asset.value,
                        to_state=curr_asset.value,
                        timestamp=regime.timestamp,
                        sequence_id=regime.sequence_id,
                    )
                    self.transition_counts[key] += 1
                    self.last_transition[dim] = record
                    self.transition_log.append(record)

        # Correlation regime transitions
        if len(self.correlation_history) > 1:
            prev_corr = self.correlation_history[-2]
            curr_corr = regime.correlation_regime

            if prev_corr != curr_corr:
                key = f"correlation_{prev_corr.value}_to_{curr_corr.value}"
                record = RegimeTransitionRecord(
                    dimension="correlation",
                    from_state=prev_corr.value,
                    to_state=curr_corr.value,
                    timestamp=regime.timestamp,
                    sequence_id=regime.sequence_id,
                )
                self.transition_counts[key] += 1
                self.last_transition["correlation"] = record
                self.transition_log.append(record)

                # FAS: Correlation breakdown -> CRITICAL alert
                if curr_corr == CorrelationRegimeState.BREAKDOWN:
                    self._pending_alerts.append(BreakdownAlert(
                        timestamp=regime.timestamp,
                        sequence_id=regime.sequence_id,
                        previous_state=prev_corr.value,
                    ))

    def _get_history_for_dimension(self, dimension: str) -> deque:
        """Resolve dimension string to the corresponding history deque."""
        if dimension == "global":
            return self.global_history
        if dimension == "correlation":
            return self.correlation_history
        # Try asset class lookup
        for ac in _ASSET_HISTORY_KEYS:
            if ac.value == dimension:
                return self.asset_histories[ac]
        return deque()
