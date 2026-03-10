# =============================================================================
# JARVIS v6.1.0 -- ADAPTIVE STRATEGY ABSTRACTION
# File:   jarvis/strategy/adaptive_strategy.py
# Version: 1.0.0
# Session: S26
# =============================================================================
#
# SCOPE
# -----
# KEINE fixen Strategien.
# Regime aktiviert Strategie-Modus. Benutzer kann NICHT ueberschreiben.
#
# CRITICAL REQUIREMENTS (from FAS S26):
#   R1: override_locked ist IMMER True, keine Ausnahme
#   R2: Alle Strategie-Aktivierungen in BUILD_LOG geloggt
#   R3: Strategie-Modus ist SICHTBAR im Chart-Interface (S31)
#   R4: STRATEGY_CONFIGS sind Hash-gesichert
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-05  All branching is deterministic.
# DET-06  Fixed literals are not parametrised.
# DET-07  Same inputs = bit-identical outputs.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict

from jarvis.core.regime import GlobalRegimeState, NewsRegimeState


# ---------------------------------------------------------------------------
# STRATEGY MODE ENUM
# ---------------------------------------------------------------------------

class StrategyMode(Enum):
    MOMENTUM         = "MOMENTUM"
    MEAN_REVERSION   = "MEAN_REVERSION"
    RISK_REDUCTION   = "RISK_REDUCTION"
    DEFENSIVE        = "DEFENSIVE"
    MINIMAL_EXPOSURE = "MINIMAL_EXPOSURE"


# ---------------------------------------------------------------------------
# STRATEGY MODE CONFIG
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StrategyModeConfig:
    """Parameter-Set pro Strategie-Modus. Immutable."""
    label:                  str
    confidence_box_scale:   float   # Multiplikator auf Entry/Exit-Boxen
    max_exposure_pct:       float   # Maximale Exposure in %
    position_size_cap:      float   # Max Position-Size-Faktor [0,1]
    recalibration_priority: str     # LOW, MEDIUM, HIGH, CRITICAL


STRATEGY_CONFIGS: Dict[StrategyMode, StrategyModeConfig] = {
    StrategyMode.MOMENTUM: StrategyModeConfig(
        label="MOMENTUM",
        confidence_box_scale=1.0,
        max_exposure_pct=0.80,
        position_size_cap=0.9,
        recalibration_priority="LOW",
    ),
    StrategyMode.MEAN_REVERSION: StrategyModeConfig(
        label="MEAN_REVERSION",
        confidence_box_scale=0.7,
        max_exposure_pct=0.65,
        position_size_cap=0.7,
        recalibration_priority="MEDIUM",
    ),
    StrategyMode.RISK_REDUCTION: StrategyModeConfig(
        label="RISK_REDUCTION",
        confidence_box_scale=1.4,
        max_exposure_pct=0.40,
        position_size_cap=0.45,
        recalibration_priority="HIGH",
    ),
    StrategyMode.DEFENSIVE: StrategyModeConfig(
        label="DEFENSIVE",
        confidence_box_scale=2.0,
        max_exposure_pct=0.20,
        position_size_cap=0.2,
        recalibration_priority="CRITICAL",
    ),
    StrategyMode.MINIMAL_EXPOSURE: StrategyModeConfig(
        label="MINIMAL_EXPOSURE",
        confidence_box_scale=2.5,
        max_exposure_pct=0.10,
        position_size_cap=0.1,
        recalibration_priority="CRITICAL",
    ),
}


# ---------------------------------------------------------------------------
# STRATEGY SELECTION RESULT
# ---------------------------------------------------------------------------

@dataclass
class StrategySelection:
    """Result of adaptive strategy selection."""
    mode:              StrategyMode
    config:            StrategyModeConfig
    activation_reason: str
    override_locked:   bool = True  # IMMER True: kein manuelles Override


# ---------------------------------------------------------------------------
# ADAPTIVE STRATEGY SELECTOR
# ---------------------------------------------------------------------------

class AdaptiveStrategySelector:
    """
    Waehlt Strategie-Modus basierend auf Regime und Risk-Output.
    Kein manuelles Ueberschreiben moeglich.
    """

    REGIME_TO_STRATEGY: Dict[str, StrategyMode] = {
        "TRENDING":  StrategyMode.MOMENTUM,
        "RANGING":   StrategyMode.MEAN_REVERSION,
        "HIGH_VOL":  StrategyMode.RISK_REDUCTION,
        "SHOCK":     StrategyMode.DEFENSIVE,
        "UNKNOWN":   StrategyMode.MINIMAL_EXPOSURE,
    }

    def select(
        self,
        regime:               str,
        risk_compression:     bool,
        volatility_forecast:  float,
        news_regime:          str = "QUIET",
        liquidity_score:      float = 0.8,
    ) -> StrategySelection:
        """
        Automatische Strategie-Selektion. Kein manueller Override.

        Priority order:
          1. Risk compression or SHOCK news -> DEFENSIVE
          2. Critical liquidity (<0.2) -> DEFENSIVE
          3. UNKNOWN regime -> MINIMAL_EXPOSURE
          4. Regime-based mapping
        """
        # Shock-Bedingungen zuerst (hoechste Prioritaet)
        if risk_compression or news_regime == NewsRegimeState.SHOCK.value:
            mode = StrategyMode.DEFENSIVE
            reason = (
                f"Risk compression active={risk_compression}, "
                f"news_regime={news_regime}"
            )
        elif liquidity_score < 0.2:
            mode = StrategyMode.DEFENSIVE
            reason = f"Critical liquidity: {liquidity_score:.3f}"
        elif regime == GlobalRegimeState.UNKNOWN.value:
            mode = StrategyMode.MINIMAL_EXPOSURE
            reason = "Regime unbekannt: minimale Exposure"
        else:
            mode = self.REGIME_TO_STRATEGY.get(regime, StrategyMode.MINIMAL_EXPOSURE)
            reason = f"Regime={regime}"

        return StrategySelection(
            mode=mode,
            config=STRATEGY_CONFIGS[mode],
            activation_reason=reason,
            override_locked=True,  # Unveraenderlich
        )


__all__ = [
    "StrategyMode",
    "StrategyModeConfig",
    "STRATEGY_CONFIGS",
    "StrategySelection",
    "AdaptiveStrategySelector",
]
