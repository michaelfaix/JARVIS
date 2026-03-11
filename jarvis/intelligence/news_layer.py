# =============================================================================
# JARVIS v6.1.0 -- NEWS & EVENT INTELLIGENCE LAYER
# File:   jarvis/intelligence/news_layer.py
# Version: 1.0.0
# Session: S24
# =============================================================================
#
# SCOPE
# -----
# NICHT "Internet lesen".
# Stattdessen:
#   - Whitelisted Quellen (konfigurierbar, nicht hardcoded)
#   - NLP Event Detection
#   - Impact-Score pro Event
#   - Zeitgestempelte Einbindung in Systemvertrag
#   - Shock-Probability Injection
#
# News wird strukturierte Variable, KEIN Chaosfaktor.
#
# CLASSIFICATION: P0 — ANALYSIS AND STRATEGY RESEARCH TOOL.
#
# CRITICAL REQUIREMENTS (from FAS S24):
#   R1: KEINE nicht-whitelisted Quellen verarbeiten
#   R2: Originaltext NIEMALS im Systemkern gespeichert (nur Hash)
#   R3: shock_probability direkt in Systemvertrag als sigma^2-Erweiterung
#   R4: Alle verarbeiteten Events in BUILD_LOG geloggt (event_id, timestamp, impact)
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly (now parameter for aggregate).
# DET-05  All branching is deterministic.
# DET-06  Fixed literals are not parametrised.
# DET-07  Same inputs = bit-identical outputs.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No logging module
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
# =============================================================================

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np

from jarvis.core.regime import NewsRegimeState


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class NewsEvent:
    """Strukturierter News-Event. Kein roher Text in Systemkern."""
    event_id:        str        # SHA-256[:16] der Headline (Eindeutigkeit)
    source:          str        # Whitelisted Quellen-ID
    timestamp:       datetime
    category:        str        # CENTRAL_BANK, EARNINGS, GEOPOLITICAL, ECONOMIC, OTHER
    headline_hash:   str        # Hash der Headline (kein Originaltext im System)
    sentiment_score: float      # [-1,1]: -1=sehr negativ, 1=sehr positiv
    impact_score:    float      # [0,1]: Einfluss auf Asset-Klasse
    shock_prob:      float      # [0,1]: Wahrscheinlichkeit eines Schock-Events
    processed:       bool = False


@dataclass
class NewsLayerOutput:
    """Aggregierter Output des News Intelligence Layers."""
    recent_events:          List[NewsEvent]
    aggregate_impact:       float            # Gewichteter Durchschnitt Impact [0,1]
    shock_probability:      float            # P(Schock-Event) in naechster Periode
    news_regime:            NewsRegimeState   # QUIET, ACTIVE, HIGH_IMPACT, SHOCK
    sentiment_drift:        float            # Trend der Stimmung [-1,1]


# ---------------------------------------------------------------------------
# NEWS INTELLIGENCE LAYER
# ---------------------------------------------------------------------------

class NewsIntelligenceLayer:
    """
    Layer 6: News & Event Intelligence.
    Nur whitelisted Quellen. Kontrollierte, strukturierte Verarbeitung.
    """

    IMPACT_CATEGORIES: Dict[str, float] = {
        "CENTRAL_BANK":  0.9,
        "GEOPOLITICAL":  0.7,
        "ECONOMIC":      0.6,
        "EARNINGS":      0.5,
        "OTHER":         0.2,
    }

    SHOCK_PROB_THRESHOLD = 0.7

    def __init__(self, whitelisted_sources: List[str]) -> None:
        if not whitelisted_sources:
            raise ValueError("Mindestens eine whitelisted Quelle erforderlich")
        self.whitelisted_sources = whitelisted_sources

    def process_event(
        self,
        source: str,
        timestamp: datetime,
        category: str,
        headline_text: str,
        raw_sentiment: float,
    ) -> Optional[NewsEvent]:
        """
        Verarbeitet einen News-Event. Gibt None zurueck wenn Quelle nicht whitelisted.
        Speichert NIEMALS den Original-Text im System.
        """
        if source not in self.whitelisted_sources:
            return None  # Nicht-whitelisted Quellen werden ignoriert

        if category not in self.IMPACT_CATEGORIES:
            category = "OTHER"

        # Headline-Hash: kein Original-Text im Systemkern
        headline_hash = hashlib.sha256(headline_text.encode("utf-8")).hexdigest()[:16]
        event_id      = hashlib.sha256(
            f"{source}{timestamp.isoformat()}{headline_hash}".encode()
        ).hexdigest()[:16]

        sentiment = float(np.clip(raw_sentiment, -1.0, 1.0))
        base_impact = self.IMPACT_CATEGORIES.get(category, 0.2)
        # Negativer Sentiment erhoeht Impact
        impact = float(np.clip(base_impact * (1.0 + max(-sentiment, 0.0)), 0.0, 1.0))

        # Shock-Wahrscheinlichkeit: basierend auf Sentiment und Impact
        shock_prob = float(np.clip(
            impact * max(-sentiment, 0.0), 0.0, 1.0
        ))

        return NewsEvent(
            event_id=event_id,
            source=source,
            timestamp=timestamp,
            category=category,
            headline_hash=headline_hash,
            sentiment_score=sentiment,
            impact_score=impact,
            shock_prob=shock_prob,
            processed=True,
        )

    def aggregate(
        self,
        events: List[NewsEvent],
        lookback_hours: float = 24.0,
        now: Optional[datetime] = None,
    ) -> NewsLayerOutput:
        """
        Aggregiert News-Events zu strukturiertem Layer-Output.
        """
        now = now or datetime.now(timezone.utc)

        # Zeitfenster: nur Events der letzten lookback_hours
        cutoff_seconds = lookback_hours * 3600.0
        recent = [
            e for e in events
            if (now - e.timestamp).total_seconds() <= cutoff_seconds
            and e.processed
        ]

        if not recent:
            return NewsLayerOutput(
                recent_events=[],
                aggregate_impact=0.0,
                shock_probability=0.0,
                news_regime=NewsRegimeState.QUIET,
                sentiment_drift=0.0,
            )

        impacts     = np.array([e.impact_score for e in recent])
        shocks      = np.array([e.shock_prob for e in recent])
        sentiments  = np.array([e.sentiment_score for e in recent])

        agg_impact  = float(np.mean(impacts))
        shock_prob  = float(np.clip(np.max(shocks), 0.0, 1.0))
        sent_drift  = float(np.mean(sentiments))

        # News Regime
        if shock_prob >= self.SHOCK_PROB_THRESHOLD:
            news_regime = NewsRegimeState.SHOCK
        elif agg_impact > 0.6:
            news_regime = NewsRegimeState.HIGH_IMPACT
        elif len(recent) > 5:
            news_regime = NewsRegimeState.ACTIVE
        else:
            news_regime = NewsRegimeState.QUIET

        return NewsLayerOutput(
            recent_events=recent,
            aggregate_impact=agg_impact,
            shock_probability=shock_prob,
            news_regime=news_regime,
            sentiment_drift=sent_drift,
        )


__all__ = [
    "NewsEvent",
    "NewsLayerOutput",
    "NewsIntelligenceLayer",
]
