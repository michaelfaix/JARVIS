# =============================================================================
# Tests for jarvis/intelligence/news_layer.py (S24)
# =============================================================================

import hashlib
from datetime import datetime, timedelta

import numpy as np
import pytest

from jarvis.core.regime import NewsRegimeState
from jarvis.intelligence.news_layer import (
    NewsEvent,
    NewsIntelligenceLayer,
    NewsLayerOutput,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

NOW = datetime(2026, 3, 10, 12, 0, 0)
SOURCES = ["reuters", "bloomberg", "fed"]


@pytest.fixture
def layer():
    return NewsIntelligenceLayer(whitelisted_sources=SOURCES)


def _make_event(layer, source="reuters", category="ECONOMIC", headline="Test headline",
                sentiment=-0.5, ts=None):
    ts = ts or NOW
    return layer.process_event(source, ts, category, headline, sentiment)


# ---------------------------------------------------------------------------
# CONSTRUCTOR
# ---------------------------------------------------------------------------

class TestConstructor:
    def test_valid_sources(self):
        nl = NewsIntelligenceLayer(["reuters"])
        assert nl.whitelisted_sources == ["reuters"]

    def test_empty_sources_raises(self):
        with pytest.raises(ValueError, match="whitelisted"):
            NewsIntelligenceLayer([])

    def test_multiple_sources(self):
        nl = NewsIntelligenceLayer(["a", "b", "c"])
        assert len(nl.whitelisted_sources) == 3


# ---------------------------------------------------------------------------
# PROCESS EVENT — BASIC
# ---------------------------------------------------------------------------

class TestProcessEventBasic:
    def test_returns_news_event(self, layer):
        ev = _make_event(layer)
        assert isinstance(ev, NewsEvent)

    def test_processed_flag(self, layer):
        ev = _make_event(layer)
        assert ev.processed is True

    def test_source_preserved(self, layer):
        ev = _make_event(layer, source="bloomberg")
        assert ev.source == "bloomberg"

    def test_timestamp_preserved(self, layer):
        ts = datetime(2026, 1, 1, 0, 0, 0)
        ev = _make_event(layer, ts=ts)
        assert ev.timestamp == ts

    def test_category_preserved(self, layer):
        ev = _make_event(layer, category="CENTRAL_BANK")
        assert ev.category == "CENTRAL_BANK"


# ---------------------------------------------------------------------------
# PROCESS EVENT — WHITELIST
# ---------------------------------------------------------------------------

class TestWhitelist:
    def test_whitelisted_source_accepted(self, layer):
        ev = _make_event(layer, source="reuters")
        assert ev is not None

    def test_non_whitelisted_returns_none(self, layer):
        ev = _make_event(layer, source="unknown_source")
        assert ev is None

    def test_all_whitelisted_accepted(self, layer):
        for src in SOURCES:
            ev = _make_event(layer, source=src)
            assert ev is not None


# ---------------------------------------------------------------------------
# PROCESS EVENT — HEADLINE HASH (R2: no original text)
# ---------------------------------------------------------------------------

class TestHeadlineHash:
    def test_headline_hash_is_sha256_prefix(self, layer):
        ev = _make_event(layer, headline="Breaking news")
        expected = hashlib.sha256("Breaking news".encode("utf-8")).hexdigest()[:16]
        assert ev.headline_hash == expected

    def test_different_headlines_different_hashes(self, layer):
        ev1 = _make_event(layer, headline="Headline A")
        ev2 = _make_event(layer, headline="Headline B")
        assert ev1.headline_hash != ev2.headline_hash

    def test_event_id_is_sha256_prefix(self, layer):
        ev = _make_event(layer, source="reuters", headline="Test")
        headline_hash = hashlib.sha256("Test".encode("utf-8")).hexdigest()[:16]
        expected_id = hashlib.sha256(
            f"reuters{NOW.isoformat()}{headline_hash}".encode()
        ).hexdigest()[:16]
        assert ev.event_id == expected_id

    def test_hash_length_16(self, layer):
        ev = _make_event(layer)
        assert len(ev.headline_hash) == 16
        assert len(ev.event_id) == 16


# ---------------------------------------------------------------------------
# PROCESS EVENT — CATEGORY
# ---------------------------------------------------------------------------

class TestCategory:
    def test_valid_categories(self, layer):
        for cat in ["CENTRAL_BANK", "GEOPOLITICAL", "ECONOMIC", "EARNINGS", "OTHER"]:
            ev = _make_event(layer, category=cat)
            assert ev.category == cat

    def test_unknown_category_mapped_to_other(self, layer):
        ev = _make_event(layer, category="NONSENSE")
        assert ev.category == "OTHER"


# ---------------------------------------------------------------------------
# PROCESS EVENT — SENTIMENT
# ---------------------------------------------------------------------------

class TestSentiment:
    def test_sentiment_preserved(self, layer):
        ev = _make_event(layer, sentiment=-0.3)
        assert ev.sentiment_score == pytest.approx(-0.3)

    def test_sentiment_clipped_high(self, layer):
        ev = _make_event(layer, sentiment=5.0)
        assert ev.sentiment_score == pytest.approx(1.0)

    def test_sentiment_clipped_low(self, layer):
        ev = _make_event(layer, sentiment=-5.0)
        assert ev.sentiment_score == pytest.approx(-1.0)

    def test_zero_sentiment(self, layer):
        ev = _make_event(layer, sentiment=0.0)
        assert ev.sentiment_score == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# PROCESS EVENT — IMPACT SCORE
# ---------------------------------------------------------------------------

class TestImpactScore:
    def test_impact_range(self, layer):
        for cat in ["CENTRAL_BANK", "GEOPOLITICAL", "ECONOMIC", "EARNINGS", "OTHER"]:
            for sent in [-1.0, -0.5, 0.0, 0.5, 1.0]:
                ev = _make_event(layer, category=cat, sentiment=sent)
                assert 0.0 <= ev.impact_score <= 1.0

    def test_negative_sentiment_increases_impact(self, layer):
        ev_neg = _make_event(layer, category="ECONOMIC", sentiment=-0.8)
        ev_pos = _make_event(layer, category="ECONOMIC", sentiment=0.8)
        assert ev_neg.impact_score >= ev_pos.impact_score

    def test_central_bank_highest_base_impact(self, layer):
        ev_cb = _make_event(layer, category="CENTRAL_BANK", sentiment=0.0)
        ev_ot = _make_event(layer, category="OTHER", sentiment=0.0)
        assert ev_cb.impact_score > ev_ot.impact_score

    def test_impact_formula(self, layer):
        # category=ECONOMIC -> base=0.6, sentiment=-0.5
        # impact = clip(0.6 * (1.0 + max(0.5, 0.0)), 0, 1) = clip(0.6*1.5, 0, 1) = 0.9
        ev = _make_event(layer, category="ECONOMIC", sentiment=-0.5)
        assert ev.impact_score == pytest.approx(0.9)

    def test_positive_sentiment_no_boost(self, layer):
        # sentiment=0.5 -> max(-0.5, 0.0) = 0.0 -> impact = base * 1.0
        ev = _make_event(layer, category="ECONOMIC", sentiment=0.5)
        assert ev.impact_score == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# PROCESS EVENT — SHOCK PROBABILITY
# ---------------------------------------------------------------------------

class TestShockProb:
    def test_shock_range(self, layer):
        for sent in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            ev = _make_event(layer, sentiment=sent)
            assert 0.0 <= ev.shock_prob <= 1.0

    def test_positive_sentiment_zero_shock(self, layer):
        ev = _make_event(layer, sentiment=0.5)
        assert ev.shock_prob == pytest.approx(0.0)

    def test_negative_sentiment_positive_shock(self, layer):
        ev = _make_event(layer, category="CENTRAL_BANK", sentiment=-0.8)
        assert ev.shock_prob > 0.0

    def test_shock_formula(self, layer):
        # CENTRAL_BANK base=0.9, sentiment=-0.8
        # impact = clip(0.9*(1+0.8), 0, 1) = clip(1.62, 0, 1) = 1.0
        # shock = clip(1.0 * 0.8, 0, 1) = 0.8
        ev = _make_event(layer, category="CENTRAL_BANK", sentiment=-0.8)
        assert ev.shock_prob == pytest.approx(0.8)

    def test_zero_sentiment_zero_shock(self, layer):
        ev = _make_event(layer, sentiment=0.0)
        assert ev.shock_prob == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# AGGREGATE — BASIC
# ---------------------------------------------------------------------------

class TestAggregateBasic:
    def test_returns_output(self, layer):
        ev = _make_event(layer)
        result = layer.aggregate([ev], now=NOW)
        assert isinstance(result, NewsLayerOutput)

    def test_empty_events(self, layer):
        result = layer.aggregate([], now=NOW)
        assert result.recent_events == []
        assert result.aggregate_impact == 0.0
        assert result.shock_probability == 0.0
        assert result.news_regime == NewsRegimeState.QUIET
        assert result.sentiment_drift == 0.0

    def test_recent_events_included(self, layer):
        ev = _make_event(layer, ts=NOW - timedelta(hours=1))
        result = layer.aggregate([ev], now=NOW)
        assert len(result.recent_events) == 1

    def test_aggregate_impact_range(self, layer):
        events = [_make_event(layer, sentiment=s) for s in [-1.0, -0.5, 0.0, 0.5]]
        result = layer.aggregate(events, now=NOW)
        assert 0.0 <= result.aggregate_impact <= 1.0

    def test_sentiment_drift_range(self, layer):
        events = [_make_event(layer, sentiment=s) for s in [-1.0, -0.5, 0.0, 0.5]]
        result = layer.aggregate(events, now=NOW)
        assert -1.0 <= result.sentiment_drift <= 1.0


# ---------------------------------------------------------------------------
# AGGREGATE — TIME FILTERING
# ---------------------------------------------------------------------------

class TestAggregateTimeFiltering:
    def test_old_events_excluded(self, layer):
        old = _make_event(layer, ts=NOW - timedelta(hours=48))
        recent = _make_event(layer, ts=NOW - timedelta(hours=1))
        result = layer.aggregate([old, recent], lookback_hours=24.0, now=NOW)
        assert len(result.recent_events) == 1

    def test_boundary_event_included(self, layer):
        boundary = _make_event(layer, ts=NOW - timedelta(hours=24))
        result = layer.aggregate([boundary], lookback_hours=24.0, now=NOW)
        assert len(result.recent_events) == 1

    def test_just_past_boundary_excluded(self, layer):
        old = _make_event(layer, ts=NOW - timedelta(hours=24, seconds=1))
        result = layer.aggregate([old], lookback_hours=24.0, now=NOW)
        assert len(result.recent_events) == 0
        assert result.news_regime == NewsRegimeState.QUIET

    def test_custom_lookback(self, layer):
        ev = _make_event(layer, ts=NOW - timedelta(hours=5))
        r1 = layer.aggregate([ev], lookback_hours=6.0, now=NOW)
        r2 = layer.aggregate([ev], lookback_hours=4.0, now=NOW)
        assert len(r1.recent_events) == 1
        assert len(r2.recent_events) == 0

    def test_unprocessed_events_excluded(self, layer):
        ev = _make_event(layer)
        ev.processed = False
        result = layer.aggregate([ev], now=NOW)
        assert len(result.recent_events) == 0


# ---------------------------------------------------------------------------
# AGGREGATE — NEWS REGIME
# ---------------------------------------------------------------------------

class TestNewsRegime:
    def test_quiet_few_events(self, layer):
        events = [_make_event(layer, sentiment=0.5)]  # positive -> low impact, no shock
        result = layer.aggregate(events, now=NOW)
        assert result.news_regime == NewsRegimeState.QUIET

    def test_shock_regime(self, layer):
        # Force shock_prob >= 0.7
        ev = _make_event(layer, category="CENTRAL_BANK", sentiment=-0.9)
        assert ev.shock_prob >= 0.7
        result = layer.aggregate([ev], now=NOW)
        assert result.news_regime == NewsRegimeState.SHOCK

    def test_high_impact_regime(self, layer):
        # High impact but no shock: positive sentiment, high base impact
        # CENTRAL_BANK with sentiment=0 -> impact=0.9, shock=0
        events = [_make_event(layer, category="CENTRAL_BANK", sentiment=0.0)]
        result = layer.aggregate(events, now=NOW)
        assert result.aggregate_impact > 0.6
        if result.shock_probability < 0.7:
            assert result.news_regime == NewsRegimeState.HIGH_IMPACT

    def test_active_regime_many_events(self, layer):
        # > 5 events, low impact, no shock
        events = [_make_event(layer, category="OTHER", sentiment=0.5,
                              headline=f"News {i}", ts=NOW - timedelta(minutes=i))
                  for i in range(6)]
        result = layer.aggregate(events, now=NOW)
        if result.shock_probability < 0.7 and result.aggregate_impact <= 0.6:
            assert result.news_regime == NewsRegimeState.ACTIVE

    def test_quiet_when_5_or_fewer_low_impact(self, layer):
        events = [_make_event(layer, category="OTHER", sentiment=0.5,
                              headline=f"News {i}")
                  for i in range(5)]
        result = layer.aggregate(events, now=NOW)
        if result.shock_probability < 0.7 and result.aggregate_impact <= 0.6:
            assert result.news_regime == NewsRegimeState.QUIET

    def test_shock_priority_over_high_impact(self, layer):
        ev = _make_event(layer, category="CENTRAL_BANK", sentiment=-1.0)
        result = layer.aggregate([ev], now=NOW)
        assert result.news_regime == NewsRegimeState.SHOCK


# ---------------------------------------------------------------------------
# AGGREGATE — METRICS
# ---------------------------------------------------------------------------

class TestAggregateMetrics:
    def test_aggregate_impact_is_mean(self, layer):
        e1 = _make_event(layer, category="ECONOMIC", sentiment=0.0)   # impact=0.6
        e2 = _make_event(layer, category="EARNINGS", sentiment=0.0,
                         headline="H2")  # impact=0.5
        result = layer.aggregate([e1, e2], now=NOW)
        assert result.aggregate_impact == pytest.approx((0.6 + 0.5) / 2.0)

    def test_shock_probability_is_max(self, layer):
        e1 = _make_event(layer, category="CENTRAL_BANK", sentiment=-0.9)
        e2 = _make_event(layer, category="OTHER", sentiment=0.5, headline="H2")
        result = layer.aggregate([e1, e2], now=NOW)
        assert result.shock_probability == pytest.approx(e1.shock_prob)

    def test_sentiment_drift_is_mean(self, layer):
        e1 = _make_event(layer, sentiment=-0.6)
        e2 = _make_event(layer, sentiment=0.4, headline="H2")
        result = layer.aggregate([e1, e2], now=NOW)
        assert result.sentiment_drift == pytest.approx((-0.6 + 0.4) / 2.0)


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

class TestConstants:
    def test_impact_categories(self):
        assert NewsIntelligenceLayer.IMPACT_CATEGORIES == {
            "CENTRAL_BANK":  0.9,
            "GEOPOLITICAL":  0.7,
            "ECONOMIC":      0.6,
            "EARNINGS":      0.5,
            "OTHER":         0.2,
        }

    def test_shock_prob_threshold(self):
        assert NewsIntelligenceLayer.SHOCK_PROB_THRESHOLD == 0.7


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------

class TestDataClasses:
    def test_news_event_fields(self):
        ev = NewsEvent(
            event_id="abc", source="reuters", timestamp=NOW,
            category="ECONOMIC", headline_hash="def",
            sentiment_score=-0.5, impact_score=0.8,
            shock_prob=0.3, processed=True,
        )
        assert ev.event_id == "abc"
        assert ev.processed is True

    def test_news_event_default_processed(self):
        ev = NewsEvent(
            event_id="x", source="s", timestamp=NOW,
            category="OTHER", headline_hash="h",
            sentiment_score=0.0, impact_score=0.1, shock_prob=0.0,
        )
        assert ev.processed is False

    def test_news_layer_output_fields(self):
        out = NewsLayerOutput(
            recent_events=[], aggregate_impact=0.0,
            shock_probability=0.0, news_regime=NewsRegimeState.QUIET,
            sentiment_drift=0.0,
        )
        assert out.news_regime == NewsRegimeState.QUIET


# ---------------------------------------------------------------------------
# DETERMINISM
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_process_event_deterministic(self, layer):
        e1 = _make_event(layer, headline="Same text", sentiment=-0.5)
        e2 = _make_event(layer, headline="Same text", sentiment=-0.5)
        assert e1.event_id == e2.event_id
        assert e1.headline_hash == e2.headline_hash
        assert e1.impact_score == e2.impact_score
        assert e1.shock_prob == e2.shock_prob

    def test_aggregate_deterministic(self, layer):
        events = [_make_event(layer, headline=f"H{i}", sentiment=-0.3 * i)
                  for i in range(3)]
        r1 = layer.aggregate(events, now=NOW)
        r2 = layer.aggregate(events, now=NOW)
        assert r1.aggregate_impact == r2.aggregate_impact
        assert r1.shock_probability == r2.shock_probability
        assert r1.news_regime == r2.news_regime
        assert r1.sentiment_drift == r2.sentiment_drift


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_unicode_headline(self, layer):
        ev = _make_event(layer, headline="Börsenkrach ⚠️ €500M Verlust")
        assert ev is not None
        assert len(ev.headline_hash) == 16

    def test_empty_headline(self, layer):
        ev = _make_event(layer, headline="")
        assert ev is not None

    def test_very_long_headline(self, layer):
        ev = _make_event(layer, headline="X" * 10000)
        assert ev is not None
        assert len(ev.headline_hash) == 16

    def test_extreme_negative_sentiment(self, layer):
        ev = _make_event(layer, category="CENTRAL_BANK", sentiment=-1.0)
        # base=0.9, impact = clip(0.9*(1+1), 0, 1) = clip(1.8, 0, 1) = 1.0
        assert ev.impact_score == pytest.approx(1.0)
        # shock = clip(1.0*1.0, 0, 1) = 1.0
        assert ev.shock_prob == pytest.approx(1.0)

    def test_all_events_old(self, layer):
        events = [_make_event(layer, ts=NOW - timedelta(days=30))]
        result = layer.aggregate(events, now=NOW)
        assert result.news_regime == NewsRegimeState.QUIET
        assert len(result.recent_events) == 0

    def test_single_source_layer(self):
        nl = NewsIntelligenceLayer(["only"])
        ev = nl.process_event("only", NOW, "ECONOMIC", "test", -0.1)
        assert ev is not None
        ev2 = nl.process_event("other", NOW, "ECONOMIC", "test", -0.1)
        assert ev2 is None
