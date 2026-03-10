# =============================================================================
# JARVIS v6.1.0 -- MARKET MICROSTRUCTURE LAYER
# File:   jarvis/intelligence/microstructure_layer.py
# Version: 1.0.0
# Session: S19
# =============================================================================
#
# SCOPE
# -----
# Microstructure verbessert Entry-Timing-Praezision.
# Analysiert: Order Flow, Bid-Ask-Druck, Liquiditaets-Absorption,
# Spoofing-Heuristiken, Rauschen, Microstructure-Volatility.
#
# Kein direktes Trading. Nur Eingabe in Risk Engine + Strategy Selector.
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
class OrderBookSnapshot:
    """Momentaufnahme des Order Books."""
    timestamp:     float           # Unix-Timestamp
    bid_prices:    List[float]     # Absteigende Bids [best_bid, ...]
    bid_volumes:   List[float]     # Volumina pro Bid-Level
    ask_prices:    List[float]     # Aufsteigende Asks [best_ask, ...]
    ask_volumes:   List[float]     # Volumina pro Ask-Level


@dataclass
class MicrostructureResult:
    """
    Output des Microstructure Layers.
    Alle Werte geclipt und finite.
    """
    order_flow_imbalance:    float   # OFI in [-1, 1]: -1=Sell-Druck, 1=Buy-Druck
    bid_ask_pressure:        float   # BAP in [0, 1]: 0=Sell, 1=Buy dominant
    liquidity_absorption:    float   # [0, 1]: 0=niemand schluckt Druck, 1=sofort absorbiert
    spoofing_probability:    float   # [0, 1]: Wahrscheinlichkeit fuer Spoofing-Aktivitaet
    noise_filter_score:      float   # [0, 1]: 0=reines Rauschen, 1=echtes Signal
    microstructure_vol_idx:  float   # Microstructure Volatility Index >= 0
    timing_quality:          float   # [0, 1]: Kombinierter Entry-Timing Score
    regime_hint:             str     # ACCUMULATION, DISTRIBUTION, EQUILIBRIUM, NOISE


# ---------------------------------------------------------------------------
# MARKET MICROSTRUCTURE LAYER
# ---------------------------------------------------------------------------

class MarketMicrostructureLayer:
    """
    Layer: Market Microstructure Analysis.
    Verbessert Entry-Timing durch Order-Book-Analyse.
    Darf NIEMALS direkt in Execution-Layer schreiben.
    """

    # Mindest-Levels fuer valide Analyse
    MIN_ORDER_BOOK_LEVELS = 3
    SPOOFING_VOLUME_RATIO = 5.0   # Verdaechtiges Volumen-Verhaeltnis
    NOISE_HALFLIFE_TICKS  = 10    # EWMA-Halflife fuer Rauschen-Filterung

    def compute_order_flow_imbalance(
        self,
        bid_volumes: List[float],
        ask_volumes: List[float],
        n_levels: int = 5,
    ) -> float:
        """
        Order Flow Imbalance (OFI): Asymmetrie zwischen Bid und Ask Volumen.
        OFI = (BidVol - AskVol) / (BidVol + AskVol)
        Gibt Wert in [-1, 1] zurueck.
        """
        levels = min(n_levels, len(bid_volumes), len(ask_volumes))
        if levels < 1:
            raise ValueError("Keine Order-Book-Levels fuer OFI-Berechnung")

        bid_vol = float(np.sum(bid_volumes[:levels]))
        ask_vol = float(np.sum(ask_volumes[:levels]))
        total   = bid_vol + ask_vol

        if total < 1e-10:
            return 0.0

        ofi = (bid_vol - ask_vol) / total
        return float(np.clip(ofi, -1.0, 1.0))

    def compute_bid_ask_pressure(
        self,
        snapshot: OrderBookSnapshot,
        n_levels: int = 5,
    ) -> float:
        """
        Bid-Ask-Pressure: Gewichtetes Volumen nahe Best Bid/Ask.
        Normiert auf [0, 1]: 0.5 = ausgeglichen.
        """
        levels = min(n_levels, len(snapshot.bid_volumes), len(snapshot.ask_volumes))
        if levels < self.MIN_ORDER_BOOK_LEVELS:
            return 0.5

        # Gewichte: Level 1 (best) hat hoechstes Gewicht
        weights = np.array([1.0 / (i + 1) for i in range(levels)])
        weights /= weights.sum()

        bid_weighted = float(np.sum(weights * np.array(snapshot.bid_volumes[:levels])))
        ask_weighted = float(np.sum(weights * np.array(snapshot.ask_volumes[:levels])))
        total = bid_weighted + ask_weighted

        if total < 1e-10:
            return 0.5

        return float(np.clip(bid_weighted / total, 0.0, 1.0))

    def detect_liquidity_absorption(
        self,
        price_changes: List[float],
        volume_changes: List[float],
        window: int = 20,
    ) -> float:
        """
        Liquidity Absorption: Hohe Volumina ohne Preis-Bewegung = Absorption.
        Score nahe 1 = Markt absorbiert Druck gut.
        """
        if len(price_changes) < window or len(volume_changes) < window:
            raise ValueError(f"Mindestens {window} Ticks fuer Absorptions-Analyse")

        price_arr  = np.array(price_changes[-window:], dtype=float)
        volume_arr = np.array(volume_changes[-window:], dtype=float)

        if not np.all(np.isfinite(price_arr)) or not np.all(np.isfinite(volume_arr)):
            raise ValueError("Preis oder Volumen enthalten NaN/Inf")

        price_std  = float(np.std(price_arr))
        volume_std = float(np.std(volume_arr))

        if volume_std < 1e-10:
            return 0.5

        # Hohe Vol, niedrige Preis-Reaktion = hohe Absorption
        sensitivity = price_std / volume_std
        absorption  = float(np.clip(1.0 - sensitivity / max(sensitivity, 1e-10), 0.0, 1.0))
        return absorption

    def estimate_spoofing_probability(
        self,
        snapshot: OrderBookSnapshot,
        historical_snapshots: List[OrderBookSnapshot],
        cancel_threshold_ms: float = 500.0,
    ) -> float:
        """
        Spoofing Heuristik: Grosse Orders erscheinen/verschwinden schnell.
        Gibt Spoofing-Wahrscheinlichkeit in [0, 1] zurueck.
        """
        if len(historical_snapshots) < 2:
            return 0.0

        # Vergleich Top-Level-Volumina ueber Snapshots
        volume_changes = []
        for prev, curr in zip(historical_snapshots[:-1], historical_snapshots[1:]):
            if not prev.bid_volumes or not curr.bid_volumes:
                continue
            prev_best_bid_vol = prev.bid_volumes[0]
            curr_best_bid_vol = curr.bid_volumes[0]
            if prev_best_bid_vol > 1e-10:
                change = abs(curr_best_bid_vol - prev_best_bid_vol) / prev_best_bid_vol
                volume_changes.append(change)

        if not volume_changes:
            return 0.0

        mean_change = float(np.mean(volume_changes))
        # Hohe mittlere Aenderung = verdaechtig
        spoof_score = float(np.clip(
            mean_change / self.SPOOFING_VOLUME_RATIO, 0.0, 1.0
        ))
        return spoof_score

    def filter_noise(
        self,
        tick_returns: List[float],
        halflife: Optional[int] = None,
    ) -> float:
        """
        Rauschen-Filter via EWMA-Glaettung.
        Score nahe 1 = wenig Rauschen = valides Signal.
        """
        halflife = halflife or self.NOISE_HALFLIFE_TICKS
        if len(tick_returns) < 3:
            return 0.5

        arr = np.array(tick_returns, dtype=float)
        if not np.all(np.isfinite(arr)):
            return 0.5

        decay = float(np.exp(-np.log(2.0) / max(halflife, 1)))
        weights = np.array([decay ** i for i in range(len(arr) - 1, -1, -1)])
        weights /= weights.sum()

        ewma = float(np.abs(np.sum(weights * arr)))
        raw_std = float(np.std(arr))

        if raw_std < 1e-10:
            return 1.0

        # Signal-zu-Rauschen: EWMA-Signal vs. Gesamtschwankung
        snr = ewma / raw_std
        return float(np.clip(snr, 0.0, 1.0))

    def compute_microstructure_vol(
        self,
        tick_returns: List[float],
        window: int = 30,
    ) -> float:
        """
        Microstructure Volatility Index: RMS der Tick-Returns (annualisiert).
        """
        if len(tick_returns) < window:
            raise ValueError(f"Mindestens {window} Tick-Returns erforderlich")

        arr = np.array(tick_returns[-window:], dtype=float)
        if not np.all(np.isfinite(arr)):
            raise ValueError("Tick-Returns enthalten NaN/Inf")

        rms = float(np.sqrt(np.mean(arr ** 2)))
        # Annualisierung: ~23400 Ticks pro Tag (1-Sekunden-Ticks)
        return rms * np.sqrt(23400.0)

    def assess(
        self,
        snapshot:              OrderBookSnapshot,
        historical_snapshots:  List[OrderBookSnapshot],
        tick_returns:          List[float],
        price_changes:         List[float],
        volume_changes:        List[float],
    ) -> MicrostructureResult:
        """
        Vollstaendige Microstructure-Analyse.
        Gibt MicrostructureResult zurueck. Kein Silent-Fail.
        """
        ofi = self.compute_order_flow_imbalance(
            snapshot.bid_volumes, snapshot.ask_volumes
        )
        bap = self.compute_bid_ask_pressure(snapshot)

        absorption = 0.5
        try:
            absorption = self.detect_liquidity_absorption(price_changes, volume_changes)
        except ValueError:
            pass

        spoof_prob = self.estimate_spoofing_probability(snapshot, historical_snapshots)
        noise_score = self.filter_noise(tick_returns)

        ms_vol = 0.0
        try:
            ms_vol = self.compute_microstructure_vol(tick_returns)
        except ValueError:
            pass

        # Timing Quality: Kombination aller Signale
        # Gut: hohe Absorption, niedriges Spoofing, gutes Signal-Rauschen
        timing = float(np.clip(
            absorption * noise_score * (1.0 - spoof_prob), 0.0, 1.0
        ))

        # Regime Hint
        if abs(ofi) > 0.6 and absorption > 0.6:
            regime_hint = "ACCUMULATION" if ofi > 0 else "DISTRIBUTION"
        elif noise_score < 0.3:
            regime_hint = "NOISE"
        else:
            regime_hint = "EQUILIBRIUM"

        return MicrostructureResult(
            order_flow_imbalance=ofi,
            bid_ask_pressure=bap,
            liquidity_absorption=absorption,
            spoofing_probability=float(np.clip(spoof_prob, 0.0, 1.0)),
            noise_filter_score=float(np.clip(noise_score, 0.0, 1.0)),
            microstructure_vol_idx=float(max(ms_vol, 0.0)),
            timing_quality=timing,
            regime_hint=regime_hint,
        )


__all__ = [
    "OrderBookSnapshot",
    "MicrostructureResult",
    "MarketMicrostructureLayer",
]
