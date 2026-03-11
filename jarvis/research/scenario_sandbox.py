# =============================================================================
# jarvis/research/scenario_sandbox.py
# Authority: FAS v6.0.1 -- S26-S30, lines 9913-10051
# =============================================================================
#
# SCOPE
# -----
# Scenario sandbox engine for analytical stress testing.  Simulates
# regime shifts, volatility spikes, and correlation shocks.  Produces
# ScenarioResult objects — pure analytical data, no state mutation.
#
# Public symbols:
#   SCENARIO_TYPES                 Supported scenario type strings
#   CORR_FM04_THRESHOLD            FM-04 correlation threshold (0.85)
#   VOL_FM02_THRESHOLD             FM-02 NVU threshold (3.0)
#   MODE_MAP                       Regime → strategy mode mapping
#   ScenarioConfig                 Frozen dataclass for scenario input
#   ScenarioResult                 Frozen dataclass for scenario output
#   ScenarioSandboxEngine          Engine class
#
# ISOLATION RULES
# ---------------
# R1: Reads ONLY immutable snapshots — no live state references.
# R2: NEVER calls ctrl.update() — no state mutation.
# R3: Cloned strategy objects only — no registry modification.
# R4: Returns ScenarioResult only — no Order/broker references.
# R5: No live feed access — inputs from snapshots and explicit params.
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
# DET-06  Fixed literals not parametrisable.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

__all__ = [
    "SCENARIO_TYPES",
    "CORR_FM04_THRESHOLD",
    "VOL_FM02_THRESHOLD",
    "MODE_MAP",
    "ScenarioConfig",
    "ScenarioResult",
    "ScenarioSandboxEngine",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

SCENARIO_TYPES: List[str] = [
    "regime_shift",
    "vol_spike",
    "corr_shock",
    "confidence_shift",
    "ev_shift",
]
"""Supported scenario types."""

CORR_FM04_THRESHOLD: float = 0.85
"""FM-04 correlation threshold — shock above this triggers FM-04."""

VOL_FM02_THRESHOLD: float = 3.0
"""FM-02 NVU threshold — spike above this triggers FM-02."""

MODE_MAP: Dict[str, str] = {
    "TRENDING": "MOMENTUM",
    "RANGING": "MEAN_REVERSION",
    "HIGH_VOL": "RISK_REDUCTION",
    "SHOCK": "DEFENSIVE",
    "UNKNOWN": "MINIMAL_EXPOSURE",
}
"""Regime → expected strategy mode mapping."""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class ScenarioConfig:
    """
    Scenario configuration input.

    Fields:
        scenario_id:   Unique scenario identifier.
        scenario_type: One of SCENARIO_TYPES.
        magnitude:     Intensity [0.0, 1.0].
        duration_bars: Simulated duration in bars.
        asset_scope:   Affected asset identifiers.
    """
    scenario_id: str
    scenario_type: str
    magnitude: float
    duration_bars: int
    asset_scope: tuple


@dataclass(frozen=True)
class ScenarioResult:
    """
    Scenario simulation result — pure analytical data.

    Fields:
        scenario_id:            Unique identifier.
        regime_impact:          Expected regime under scenario.
        confidence_delta:       Delta to Q [clipped to -1.0, 0.0].
        strategy_mode_shift:    Expected strategy mode change.
        expected_vol_change:    Hypothetical vol change (percent).
        portfolio_heat_change:  Simulated exposure change [-1, 1].
        ev_shift:               Expected Value shift (basis points).
        recovery_bars_estimate: Estimated recovery time (bars).
        notes:                  Analytical explanation.
    """
    scenario_id: str
    regime_impact: str
    confidence_delta: float
    strategy_mode_shift: str
    expected_vol_change: float
    portfolio_heat_change: float
    ev_shift: float
    recovery_bars_estimate: int
    notes: str


# =============================================================================
# SECTION 3 -- HELPERS
# =============================================================================

def _clip(value: float, lo: float, hi: float) -> float:
    """Clip value to [lo, hi] without numpy."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


# =============================================================================
# SECTION 4 -- ENGINE
# =============================================================================

class ScenarioSandboxEngine:
    """
    Scenario sandbox engine for analytical stress testing.

    Simulates regime shifts, volatility spikes, and correlation shocks.
    Returns ScenarioResult objects only — no state mutation.

    Stateless: all inputs passed explicitly.  No ctrl reference accepted.
    """

    def simulate_regime_shift(
        self,
        from_regime: str,
        to_regime: str,
        current_confidence: float,
        magnitude: float = 0.5,
    ) -> ScenarioResult:
        """
        Simulate a regime shift and compute analytical impacts.

        Args:
            from_regime:        Current regime string.
            to_regime:          Target regime string.
            current_confidence: Current Q value [0, 1].
            magnitude:          Shift intensity [0.0, 1.0].

        Returns:
            ScenarioResult.

        Raises:
            TypeError:  If arguments have wrong types.
            ValueError: If magnitude not in [0.0, 1.0].
        """
        if not isinstance(from_regime, str):
            raise TypeError(
                f"from_regime must be a string, "
                f"got {type(from_regime).__name__}"
            )
        if not isinstance(to_regime, str):
            raise TypeError(
                f"to_regime must be a string, "
                f"got {type(to_regime).__name__}"
            )
        if not isinstance(current_confidence, (int, float)):
            raise TypeError(
                f"current_confidence must be numeric, "
                f"got {type(current_confidence).__name__}"
            )
        if not isinstance(magnitude, (int, float)):
            raise TypeError(
                f"magnitude must be numeric, "
                f"got {type(magnitude).__name__}"
            )
        if not (0.0 <= magnitude <= 1.0):
            raise ValueError(
                f"magnitude must be in [0.0, 1.0], got {magnitude}"
            )

        confidence_delta = _clip(-magnitude * 0.4, -1.0, 0.0)
        strategy_mode = MODE_MAP.get(to_regime, "MINIMAL_EXPOSURE")
        expected_vol_change = magnitude * 0.3
        portfolio_heat_change = _clip(-magnitude * 0.2, -1.0, 1.0)
        ev_shift = -magnitude * 50.0
        recovery_bars = int(magnitude * 20)

        return ScenarioResult(
            scenario_id=f"REGIME_SHIFT_{from_regime}_TO_{to_regime}",
            regime_impact=to_regime,
            confidence_delta=confidence_delta,
            strategy_mode_shift=strategy_mode,
            expected_vol_change=expected_vol_change,
            portfolio_heat_change=portfolio_heat_change,
            ev_shift=ev_shift,
            recovery_bars_estimate=recovery_bars,
            notes=(
                f"Regime shift from {from_regime} to {to_regime} "
                f"at magnitude {magnitude:.2f}. "
                f"Confidence delta: {confidence_delta:.3f}"
            ),
        )

    def simulate_vol_spike(
        self,
        current_nvu: float,
        spike_factor: float = 3.0,
    ) -> ScenarioResult:
        """
        Simulate a volatility spike (NVU-based).

        Args:
            current_nvu:  Current NVU-normalized volatility (> 0).
            spike_factor: Multiplication factor (>= 1.0).

        Returns:
            ScenarioResult.

        Raises:
            TypeError:  If arguments have wrong types.
            ValueError: If spike_factor < 1.0 or current_nvu <= 0.
        """
        if not isinstance(current_nvu, (int, float)):
            raise TypeError(
                f"current_nvu must be numeric, "
                f"got {type(current_nvu).__name__}"
            )
        if not isinstance(spike_factor, (int, float)):
            raise TypeError(
                f"spike_factor must be numeric, "
                f"got {type(spike_factor).__name__}"
            )
        if current_nvu <= 0:
            raise ValueError(
                f"current_nvu must be > 0, got {current_nvu}"
            )
        if spike_factor < 1.0:
            raise ValueError(
                f"spike_factor must be >= 1.0, got {spike_factor}"
            )

        simulated_nvu = current_nvu * spike_factor
        triggers_fm02 = simulated_nvu > VOL_FM02_THRESHOLD

        if triggers_fm02:
            regime_impact = "HIGH_VOL"
            confidence_delta = -0.3
            strategy_mode = "RISK_REDUCTION"
            portfolio_heat_change = -0.5
            ev_shift = -80.0
            recovery_bars = 10
        else:
            regime_impact = "ELEVATED_VOL"
            confidence_delta = -0.1
            strategy_mode = "MEAN_REVERSION"
            portfolio_heat_change = -0.15
            ev_shift = -20.0
            recovery_bars = 3

        expected_vol_change = (spike_factor - 1.0) * 100.0

        return ScenarioResult(
            scenario_id=f"VOL_SPIKE_NVU_{simulated_nvu:.1f}",
            regime_impact=regime_impact,
            confidence_delta=confidence_delta,
            strategy_mode_shift=strategy_mode,
            expected_vol_change=expected_vol_change,
            portfolio_heat_change=portfolio_heat_change,
            ev_shift=ev_shift,
            recovery_bars_estimate=recovery_bars,
            notes=(
                f"NVU spike from {current_nvu:.2f} to {simulated_nvu:.2f}. "
                f"FM-02: {triggers_fm02}"
            ),
        )

    def simulate_correlation_shock(
        self,
        n_assets: int,
        shock_correlation: float = 0.90,
    ) -> ScenarioResult:
        """
        Simulate a correlation shock (all assets converge).

        Args:
            n_assets:          Number of assets affected.
            shock_correlation: Target pairwise correlation [0, 1].

        Returns:
            ScenarioResult.

        Raises:
            TypeError:  If arguments have wrong types.
            ValueError: If n_assets < 1 or shock_correlation out of range.
        """
        if not isinstance(n_assets, int):
            raise TypeError(
                f"n_assets must be int, "
                f"got {type(n_assets).__name__}"
            )
        if not isinstance(shock_correlation, (int, float)):
            raise TypeError(
                f"shock_correlation must be numeric, "
                f"got {type(shock_correlation).__name__}"
            )
        if n_assets < 1:
            raise ValueError(
                f"n_assets must be >= 1, got {n_assets}"
            )
        if not (0.0 <= shock_correlation <= 1.0):
            raise ValueError(
                f"shock_correlation must be in [0.0, 1.0], "
                f"got {shock_correlation}"
            )

        triggers_fm04 = shock_correlation > CORR_FM04_THRESHOLD

        if triggers_fm04:
            confidence_delta = -0.5
        else:
            confidence_delta = -0.2

        strategy_mode = "DEFENSIVE"
        regime_impact = "SHOCK"
        expected_vol_change = 20.0 * shock_correlation
        portfolio_heat_change = _clip(
            -shock_correlation * 0.6, -1.0, 1.0
        )
        ev_shift = -100.0 * shock_correlation
        recovery_bars = int(20 * shock_correlation)

        return ScenarioResult(
            scenario_id=f"CORR_SHOCK_{shock_correlation:.2f}",
            regime_impact=regime_impact,
            confidence_delta=confidence_delta,
            strategy_mode_shift=strategy_mode,
            expected_vol_change=expected_vol_change,
            portfolio_heat_change=portfolio_heat_change,
            ev_shift=ev_shift,
            recovery_bars_estimate=recovery_bars,
            notes=(
                f"Correlation shock to {shock_correlation:.2f} "
                f"across {n_assets} assets. FM-04: {triggers_fm04}"
            ),
        )
