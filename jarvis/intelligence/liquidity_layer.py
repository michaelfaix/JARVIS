# =============================================================================
# JARVIS v6.1.0 -- LIQUIDITY LAYER
# File:   jarvis/intelligence/liquidity_layer.py
# Version: 1.0.0
# Session: S21
# =============================================================================
#
# SCOPE
# -----
# Bewertet Marktliquiditaet fuer Risikokorrektur.
# Schlechte Liquiditaet -> erhoehter Slippage -> groessere Confidence Boxen.
#
# Ergebnis wird als Multiplikator auf Confidence Zones angewendet.
#
# CLASSIFICATION: P0 — ANALYSIS AND STRATEGY RESEARCH TOOL.
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  Deterministic arithmetic only.
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
from typing import List, Optional

import numpy as np


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class LiquidityAssessment:
    """Output des Liquidity Layers."""
    bid_ask_spread:    float   # Aktueller Spread (in Basispoints)
    spread_percentile: float   # Spread vs. Historisch (0=eng, 1=weit)
    volume_ratio:      float   # Aktuell/Durchschnitt-Volumen
    market_depth:      float   # Relative Markttiefe (0=gering, 1=hoch)
    liquidity_score:   float   # Gesamt-Score [0,1]: 0=illiquide, 1=sehr liquide
    slippage_estimate: float   # Geschaetzter Slippage in % fuer Standardposition
    regime_impact:     str     # NEGLIGIBLE, MODERATE, SIGNIFICANT, CRITICAL


# ---------------------------------------------------------------------------
# LIQUIDITY LAYER
# ---------------------------------------------------------------------------

class LiquidityLayer:
    """
    Layer 3: Liquidity Assessment.
    Ergebnis wird als Multiplikator auf Confidence Zones angewendet.
    """

    SPREAD_THRESHOLD_MODERATE   = 0.001   # 10 Basispoints
    SPREAD_THRESHOLD_CRITICAL   = 0.005   # 50 Basispoints
    VOLUME_RATIO_LOW_THRESHOLD  = 0.5
    VOLUME_RATIO_HIGH_THRESHOLD = 2.0

    def assess(
        self,
        current_spread: float,
        historical_spreads: List[float],
        current_volume: float,
        avg_volume: float,
        order_book_depth: Optional[float] = None,
    ) -> LiquidityAssessment:
        """
        Vollstaendiges Liquidity Assessment.
        Wirft ValueError bei negativen/NaN-Werten.
        """
        for name, val in [("current_spread", current_spread),
                          ("current_volume", current_volume),
                          ("avg_volume", avg_volume)]:
            if not np.isfinite(val) or val < 0:
                raise ValueError(f"Ungaeltiger Wert: {name}={val}")

        if len(historical_spreads) < 10:
            raise ValueError("Mindestens 10 historische Spreads erforderlich")

        spread_arr = np.array(historical_spreads)
        if not np.all(np.isfinite(spread_arr)):
            raise ValueError("Historische Spreads enthalten NaN/Inf")

        spread_pct = float(np.mean(spread_arr <= current_spread))
        vol_ratio  = float(current_volume / max(avg_volume, 1e-10))
        depth      = float(np.clip(order_book_depth, 0.0, 1.0)) if order_book_depth is not None else 0.5

        # Liquidity Score: gewichtet
        spread_score = float(np.clip(1.0 - spread_pct, 0.0, 1.0))
        vol_score    = float(np.clip(vol_ratio / self.VOLUME_RATIO_HIGH_THRESHOLD, 0.0, 1.0))
        liquidity_score = 0.4 * spread_score + 0.35 * vol_score + 0.25 * depth
        liquidity_score = float(np.clip(liquidity_score, 0.0, 1.0))

        # Slippage-Schaetzung
        slippage_estimate = current_spread * (1.0 + (1.0 - liquidity_score))

        # Regime Impact
        if liquidity_score < 0.2:
            regime_impact = "CRITICAL"
        elif liquidity_score < 0.4:
            regime_impact = "SIGNIFICANT"
        elif liquidity_score < 0.65:
            regime_impact = "MODERATE"
        else:
            regime_impact = "NEGLIGIBLE"

        return LiquidityAssessment(
            bid_ask_spread=current_spread,
            spread_percentile=spread_pct,
            volume_ratio=vol_ratio,
            market_depth=depth,
            liquidity_score=liquidity_score,
            slippage_estimate=slippage_estimate,
            regime_impact=regime_impact,
        )


__all__ = [
    "LiquidityAssessment",
    "LiquidityLayer",
]
