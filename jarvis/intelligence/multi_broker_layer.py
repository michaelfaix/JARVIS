# =============================================================================
# JARVIS v6.1.0 -- MULTI-SOURCE MARKET DATA RESEARCH LAYER
# File:   jarvis/intelligence/multi_broker_layer.py
# Version: 1.0.0
# Session: S25
# =============================================================================
#
# SCOPE
# -----
# Daten von mehreren Brokern = bessere Datenbasis.
# ABER: Execution Layer strikt getrennt.
# Kein direkter, ungesicherter Brokerzugriff.
#
# Zweck:
#   - Spread-Vergleich zwischen Brokern
#   - Liquiditaetsunterschiede erkennen
#   - Datenpunkte cross-validieren
#   - Best-of-Data-Feed-Auswahl
#
# CLASSIFICATION: P0 — ANALYSIS AND STRATEGY RESEARCH TOOL.
#
# ISOLATION (KRITISCH — P0 ENFORCEMENT):
#   R1: KEIN Interface zum Execution Layer, keinen Broker-Order-Kanal
#   R2: Kein Trade-Routing. Nur Daten-Aggregation und Qualitaets-Analyse.
#   R3: API-Credentials NIEMALS in diesem Layer (nur in gesichertem Vault)
#   R4: Veraltete Quotes (>10s) werden ignoriert, nicht als Fehler behandelt
#   R5: Outputs gehen NUR an Intelligence Layer und Feature Registry
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
from typing import Dict, List, Optional

import numpy as np


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class BrokerQuote:
    """Single broker quote snapshot."""
    broker_id:   str
    bid:         float
    ask:         float
    timestamp:   float      # Unix-Timestamp
    volume:      Optional[float] = None


@dataclass
class MultiBrokerAssessment:
    """Aggregated multi-broker assessment output."""
    best_bid:          float             # Bester Bid aller Broker
    best_ask:          float             # Bester Ask aller Broker
    avg_spread:        float             # Durchschnittlicher Spread
    min_spread:        float             # Minimaler Spread
    spread_dispersion: float             # Spread-Streuung (Qualitaetsindikator)
    liquidity_map:     Dict[str, float]  # Broker-ID -> Liquiditaets-Score
    preferred_source:  str               # Broker mit bestem Spread+Liquiditaet
    data_quality:      float             # Quote-Qualitaet [0,1]


# ---------------------------------------------------------------------------
# MULTI-SOURCE DATA LAYER
# ---------------------------------------------------------------------------

class MultiSourceDataLayer:
    """
    Layer: Multi-Source Market Data Research Aggregation.
    ISOLIERT von jedem Execution-Layer. Kein Broker-Interface fuer Orders.
    Kein Trade-Routing. Nur Daten-Aggregation und Qualitaets-Analyse.
    Zweck: Spread-Research, Liquiditaets-Forschung, Datenqualitaets-Bewertung.
    """

    MAX_QUOTE_AGE_SECONDS = 10.0  # Quotes aelter als 10s werden ignoriert

    def aggregate(
        self,
        quotes: List[BrokerQuote],
        now_ts: float,
    ) -> MultiBrokerAssessment:
        """
        Aggregiert Broker-Quotes zu strukturiertem Output.
        Ignoriert veraltete Quotes (>MAX_QUOTE_AGE_SECONDS).
        """
        if not quotes:
            raise ValueError("Keine Broker-Quotes vorhanden")

        # Frische Quotes filtern
        fresh = [
            q for q in quotes
            if abs(now_ts - q.timestamp) <= self.MAX_QUOTE_AGE_SECONDS
            and np.isfinite(q.bid) and np.isfinite(q.ask)
            and q.ask > q.bid > 0
        ]

        if not fresh:
            raise ValueError("Keine gueltigen/frischen Broker-Quotes")

        bids = np.array([q.bid for q in fresh])
        asks = np.array([q.ask for q in fresh])
        spreads = asks - bids

        best_bid = float(np.max(bids))
        best_ask = float(np.min(asks))
        avg_spread = float(np.mean(spreads))
        min_spread = float(np.min(spreads))
        spread_dispersion = float(np.std(spreads))

        # Liquiditaets-Map
        liq_map: Dict[str, float] = {}
        for q in fresh:
            spread_score = float(np.clip(
                1.0 - (q.ask - q.bid) / max(avg_spread, 1e-10), 0.0, 1.0
            ))
            vol_score = 0.5
            if q.volume is not None and np.isfinite(q.volume) and q.volume > 0:
                all_vols = [x.volume for x in fresh if x.volume]
                if all_vols:
                    vol_score = float(np.clip(
                        q.volume / max(np.mean(all_vols), 1e-10), 0.0, 1.0
                    ))
            liq_map[q.broker_id] = 0.6 * spread_score + 0.4 * vol_score

        preferred = max(liq_map, key=lambda k: liq_map[k]) if liq_map else "UNKNOWN"

        # Daten-Qualitaet: basierend auf Anzahl frischer Quotes und Spread-Konsistenz
        freshness_score = float(np.clip(len(fresh) / max(len(quotes), 1), 0.0, 1.0))
        consistency     = float(np.clip(
            1.0 - spread_dispersion / max(avg_spread, 1e-10), 0.0, 1.0
        ))
        data_quality = 0.5 * freshness_score + 0.5 * consistency

        return MultiBrokerAssessment(
            best_bid=best_bid,
            best_ask=best_ask,
            avg_spread=avg_spread,
            min_spread=min_spread,
            spread_dispersion=spread_dispersion,
            liquidity_map=liq_map,
            preferred_source=preferred,
            data_quality=data_quality,
        )


__all__ = [
    "BrokerQuote",
    "MultiBrokerAssessment",
    "MultiSourceDataLayer",
]
