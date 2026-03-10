# =============================================================================
# JARVIS v6.1.0 -- STRATEGY OBJECT SCHEMA (KANONISCH)
# File:   jarvis/core/strategy_schema.py
# Version: 1.0.0
# Session: S26
# =============================================================================
#
# Alle Strategien im System werden durch exakt dieses Schema repraesentiert.
# Keine Strategie darf instanziiert, gewichtet, selektiert oder evaluiert
# werden ausserhalb dieser Struktur.
#
# CLASSIFICATION: P0 — ANALYSIS AND STRATEGY RESEARCH TOOL.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

import numpy as np


# ---------------------------------------------------------------------------
# SCHEMA VERSION
# ---------------------------------------------------------------------------

STRATEGY_SCHEMA_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# ENUMS
# ---------------------------------------------------------------------------

class StrategyType(Enum):
    MOMENTUM          = "momentum"
    MEAN_REVERSION    = "mean_reversion"
    BREAKOUT          = "breakout"
    CARRY             = "carry"
    VOLATILITY_SELL   = "volatility_sell"
    DEFENSIVE         = "defensive"
    MINIMAL_EXPOSURE  = "minimal_exposure"


class RegimeSensitivity(Enum):
    HIGH    = "high"    # Only active in specific regime
    MEDIUM  = "medium"  # Reduced weight outside target regime
    LOW     = "low"     # Active across all regimes


class VolatilitySensitivity(Enum):
    EXPANDS   = "expands"    # Increases allocation in high vol
    CONTRACTS = "contracts"  # Reduces allocation in high vol
    NEUTRAL   = "neutral"    # Unaffected by vol level


class SessionSensitivity(Enum):
    LIQUID_ONLY  = "liquid_only"   # Disabled during illiquid sessions
    ADAPTIVE     = "adaptive"      # Reduces size during illiquid sessions
    SESSION_FREE = "session_free"  # Asset is 24/7 (crypto)


# ---------------------------------------------------------------------------
# SUB-MODELS
# ---------------------------------------------------------------------------

@dataclass
class EntryModel:
    signal_type:           str    # "momentum_cross", "mean_rev_zscore", etc.
    signal_threshold:      float  # Minimum signal strength to trigger
    confirmation_bars:     int    # Bars signal must persist before entry
    max_entry_spread_bps:  float  # Max spread at entry (bps); 0 = no limit


@dataclass
class ExitModel:
    stop_loss_atr_multiple:   float  # Stop = N * ATR from entry
    take_profit_atr_multiple: float  # TP = N * ATR from entry; 0 = no TP
    time_exit_bars:           int    # Force exit after N bars; 0 = disabled
    trailing_stop:            bool   # Enable trailing stop
    regime_exit:              bool   # Exit immediately on regime change


@dataclass
class RiskModel:
    base_risk_per_trade:   float  # Fraction of capital at risk; max 0.02
    max_position_size:     float  # Hard cap on position as fraction of capital
    kelly_fraction:        float  # Kelly multiplier in [0, 1]
    confidence_floor:      float  # Minimum confidence to allow any sizing
    var_contribution_cap:  float  # Max contribution to portfolio VaR


@dataclass
class WeightModel:
    base_weight:          float            # Default portfolio weight in [0, 1]
    regime_weight_map:    Dict[str, float] # Per-regime weight override
    volatility_scalar_fn: str              # Name of registered scalar function
    min_weight:           float            # Floor; never go below this
    max_weight:           float            # Ceiling; never exceed this


# ---------------------------------------------------------------------------
# STRATEGY OBJECT (FROZEN)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StrategyObject:
    """
    Kanonische Repraesentation aller Strategien in JARVIS.
    Immutable nach Konstruktion.
    Adaptive Weighting darf NUR ueber das Weight_Model operieren.
    """
    # Identity
    Strategy_ID:               str
    Strategy_Type:             StrategyType

    # Models
    Entry_Model:               EntryModel
    Exit_Model:                ExitModel
    Risk_Model:                RiskModel
    Weight_Model:              WeightModel

    # Regime and Environment Sensitivity
    Regime_Sensitivity:        RegimeSensitivity
    Volatility_Sensitivity:    VolatilitySensitivity
    Session_Sensitivity:       SessionSensitivity

    # Temporal Profile
    Timeframe_Profile:         str   # "M5", "H1", "H4", "D1", or "MULTI"
    Expected_Holding_Duration: int   # Expected bars held; informs exit model

    # Metadata
    target_regime:             str   # Primary regime this strategy targets
    asset_class_scope:         List[str]  # ["crypto"], ["forex"], ["all"], etc.
    version:                   str   # Schema version; must match STRATEGY_SCHEMA_VERSION

    def validate(self) -> bool:
        """
        Strukturelle Validierung. Wirft ValueError bei Verletzung.
        """
        if not (0 < self.Risk_Model.base_risk_per_trade <= 0.02):
            raise ValueError(
                f"base_risk_per_trade {self.Risk_Model.base_risk_per_trade} out of (0, 0.02]"
            )
        if not (0.0 <= self.Risk_Model.confidence_floor <= 1.0):
            raise ValueError("confidence_floor out of [0, 1]")
        if not (0.0 <= self.Weight_Model.base_weight <= 1.0):
            raise ValueError("base_weight out of [0, 1]")
        if not (self.Weight_Model.min_weight <= self.Weight_Model.base_weight
                <= self.Weight_Model.max_weight):
            raise ValueError("weight bounds inconsistent")
        if self.Expected_Holding_Duration <= 0:
            raise ValueError("Expected_Holding_Duration must be positive")
        return True


# ---------------------------------------------------------------------------
# ADAPTIVE WEIGHTING (canonical function)
# ---------------------------------------------------------------------------

def apply_adaptive_weight(obj: StrategyObject, current_regime: str) -> float:
    """
    Adaptive Weighting NUR ueber Weight_Model.
    Direkte weight-Zuweisung ist VERBOTEN.
    """
    w = obj.Weight_Model.regime_weight_map.get(
        current_regime,
        obj.Weight_Model.base_weight,
    )
    return float(np.clip(w, obj.Weight_Model.min_weight, obj.Weight_Model.max_weight))


__all__ = [
    "STRATEGY_SCHEMA_VERSION",
    "StrategyType",
    "RegimeSensitivity",
    "VolatilitySensitivity",
    "SessionSensitivity",
    "EntryModel",
    "ExitModel",
    "RiskModel",
    "WeightModel",
    "StrategyObject",
    "apply_adaptive_weight",
]
