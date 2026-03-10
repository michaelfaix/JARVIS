# =============================================================================
# jarvis/chart/chart_contract.py — Chart Data Contract (S32)
#
# Alle Daten die das Chart-Interface benoetigt.
# Wird von ChartDataBuilder aus System-Outputs zusammengestellt.
#
# P0 ENFORCEMENT:
#   - KEINE "BUY" / "SELL" Labels
#   - KEINE Order-Routing-Felder
#   - KEINE Broker-Connect-Felder
#   - Nur Wahrscheinlichkeitsbereiche und Marktstruktur-Daten
#
# R3: meta_uncertainty_pct IMMER sichtbar
# R4: risk_compression_active IMMER im Header sichtbar
# R5: timeframe_label IMMER sichtbar
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChartOverlay:
    """All data the chart interface needs.

    Built by ChartDataBuilder from system outputs.
    Contains NO order-type fields (P0 enforcement).
    """

    # Entry Confidence Box
    entry_box_lower: float  # Lower bound in price units
    entry_box_upper: float  # Upper bound in price units
    entry_confidence_pct: float  # Confidence in % (0-100)

    # Exit Risk Corridor
    exit_corridor_soft: float  # Soft exit level
    exit_corridor_hard: float  # Hard exit level (risk boundary)
    exit_confidence_pct: float  # Exit confidence in %

    # Expected Move
    expected_move_pct: float  # Expected move in %

    # Volatility Adjusted Stop
    vol_stop_price: float  # Stop price (vol-adjusted)
    vol_stop_distance_pct: float  # Stop distance in % from current price

    # Regime Label (ASCII)
    regime_label: str  # e.g. "TRENDING", "RANGING", "HIGH_VOL", "SHOCK"

    # Strategy Mode Label (ASCII)
    strategy_mode_label: str  # e.g. "MOMENTUM", "DEFENSIVE", "RISK_REDUCTION"

    # Meta-Uncertainty Level
    meta_uncertainty_pct: float  # Meta-uncertainty in % (0=certain, 100=max uncertain)
    uncertainty_band: str  # "LOW", "MODERATE", "HIGH", "EXTREME"

    # Timeframe Label
    timeframe_label: str  # e.g. "5m", "15m", "1h"

    # Risk Compression Indicator
    risk_compression_active: bool
