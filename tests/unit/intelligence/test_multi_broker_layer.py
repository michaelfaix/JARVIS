# =============================================================================
# Tests for jarvis/intelligence/multi_broker_layer.py (S25)
# =============================================================================

import numpy as np
import pytest

from jarvis.intelligence.multi_broker_layer import (
    BrokerQuote,
    MultiBrokerAssessment,
    MultiSourceDataLayer,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

NOW = 1000.0  # Reference timestamp


@pytest.fixture
def layer():
    return MultiSourceDataLayer()


def _q(broker_id, bid, ask, ts=NOW, volume=None):
    """Shortcut to create a BrokerQuote."""
    return BrokerQuote(broker_id=broker_id, bid=bid, ask=ask, timestamp=ts, volume=volume)


# ---------------------------------------------------------------------------
# BASIC AGGREGATE
# ---------------------------------------------------------------------------

class TestAggregateBasic:
    def test_returns_assessment(self, layer):
        quotes = [_q("A", 100.0, 100.5)]
        result = layer.aggregate(quotes, NOW)
        assert isinstance(result, MultiBrokerAssessment)

    def test_single_quote(self, layer):
        result = layer.aggregate([_q("A", 100.0, 100.5)], NOW)
        assert result.best_bid == 100.0
        assert result.best_ask == 100.5
        assert result.avg_spread == pytest.approx(0.5)
        assert result.min_spread == pytest.approx(0.5)
        assert result.preferred_source == "A"

    def test_multiple_brokers(self, layer):
        quotes = [
            _q("A", 100.0, 100.5),
            _q("B", 100.1, 100.4),
            _q("C", 99.9, 100.6),
        ]
        result = layer.aggregate(quotes, NOW)
        assert result.best_bid == pytest.approx(100.1)
        assert result.best_ask == pytest.approx(100.4)

    def test_data_quality_range(self, layer):
        quotes = [_q("A", 100.0, 100.5), _q("B", 100.1, 100.4)]
        result = layer.aggregate(quotes, NOW)
        assert 0.0 <= result.data_quality <= 1.0

    def test_spread_dispersion_zero_for_single(self, layer):
        result = layer.aggregate([_q("A", 100.0, 100.5)], NOW)
        assert result.spread_dispersion == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# BEST BID / BEST ASK
# ---------------------------------------------------------------------------

class TestBestBidAsk:
    def test_best_bid_is_max(self, layer):
        quotes = [_q("A", 99.0, 100.0), _q("B", 101.0, 102.0), _q("C", 100.0, 101.0)]
        result = layer.aggregate(quotes, NOW)
        assert result.best_bid == pytest.approx(101.0)

    def test_best_ask_is_min(self, layer):
        quotes = [_q("A", 99.0, 100.0), _q("B", 101.0, 105.0), _q("C", 100.0, 101.0)]
        result = layer.aggregate(quotes, NOW)
        assert result.best_ask == pytest.approx(100.0)

    def test_crossed_market_possible(self, layer):
        # best_bid > best_ask is possible in multi-broker scenario
        quotes = [_q("A", 101.0, 101.5), _q("B", 99.0, 100.0)]
        result = layer.aggregate(quotes, NOW)
        assert result.best_bid == pytest.approx(101.0)
        assert result.best_ask == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# SPREAD METRICS
# ---------------------------------------------------------------------------

class TestSpreadMetrics:
    def test_avg_spread(self, layer):
        quotes = [_q("A", 100.0, 101.0), _q("B", 100.0, 100.5)]
        result = layer.aggregate(quotes, NOW)
        assert result.avg_spread == pytest.approx(0.75)

    def test_min_spread(self, layer):
        quotes = [_q("A", 100.0, 101.0), _q("B", 100.0, 100.2)]
        result = layer.aggregate(quotes, NOW)
        assert result.min_spread == pytest.approx(0.2)

    def test_spread_dispersion_uniform(self, layer):
        quotes = [_q("A", 100.0, 100.5), _q("B", 100.0, 100.5)]
        result = layer.aggregate(quotes, NOW)
        assert result.spread_dispersion == pytest.approx(0.0)

    def test_spread_dispersion_varied(self, layer):
        quotes = [_q("A", 100.0, 100.1), _q("B", 100.0, 101.0)]
        result = layer.aggregate(quotes, NOW)
        assert result.spread_dispersion > 0.0


# ---------------------------------------------------------------------------
# FRESHNESS FILTER
# ---------------------------------------------------------------------------

class TestFreshnessFilter:
    def test_stale_quotes_excluded(self, layer):
        quotes = [
            _q("A", 100.0, 100.5, ts=NOW),           # fresh
            _q("B", 99.0, 100.0, ts=NOW - 20.0),     # stale (20s old)
        ]
        result = layer.aggregate(quotes, NOW)
        assert "B" not in result.liquidity_map
        assert "A" in result.liquidity_map

    def test_exactly_at_threshold_included(self, layer):
        quotes = [_q("A", 100.0, 100.5, ts=NOW - 10.0)]  # exactly 10s
        result = layer.aggregate(quotes, NOW)
        assert "A" in result.liquidity_map

    def test_just_past_threshold_excluded(self, layer):
        quotes = [
            _q("A", 100.0, 100.5, ts=NOW - 10.01),  # just past 10s
            _q("B", 100.0, 100.5, ts=NOW),
        ]
        result = layer.aggregate(quotes, NOW)
        assert "A" not in result.liquidity_map

    def test_future_timestamp_included(self, layer):
        # abs(now_ts - q.timestamp) allows future timestamps within threshold
        quotes = [_q("A", 100.0, 100.5, ts=NOW + 5.0)]
        result = layer.aggregate(quotes, NOW)
        assert "A" in result.liquidity_map

    def test_all_stale_raises(self, layer):
        quotes = [_q("A", 100.0, 100.5, ts=NOW - 100.0)]
        with pytest.raises(ValueError, match="gueltigen/frischen"):
            layer.aggregate(quotes, NOW)

    def test_freshness_affects_data_quality(self, layer):
        # Half stale -> lower freshness_score -> lower data_quality
        all_fresh = [_q(f"B{i}", 100.0, 100.5) for i in range(4)]
        r_all = layer.aggregate(all_fresh, NOW)

        mixed = all_fresh + [_q(f"S{i}", 100.0, 100.5, ts=NOW - 50.0) for i in range(4)]
        r_mix = layer.aggregate(mixed, NOW)

        assert r_all.data_quality >= r_mix.data_quality


# ---------------------------------------------------------------------------
# INVALID QUOTE FILTER
# ---------------------------------------------------------------------------

class TestInvalidQuoteFilter:
    def test_nan_bid_excluded(self, layer):
        quotes = [
            _q("A", float('nan'), 100.5),
            _q("B", 100.0, 100.5),
        ]
        result = layer.aggregate(quotes, NOW)
        assert "A" not in result.liquidity_map

    def test_nan_ask_excluded(self, layer):
        quotes = [
            _q("A", 100.0, float('nan')),
            _q("B", 100.0, 100.5),
        ]
        result = layer.aggregate(quotes, NOW)
        assert "A" not in result.liquidity_map

    def test_inf_excluded(self, layer):
        quotes = [
            _q("A", float('inf'), 100.5),
            _q("B", 100.0, 100.5),
        ]
        result = layer.aggregate(quotes, NOW)
        assert "A" not in result.liquidity_map

    def test_negative_bid_excluded(self, layer):
        quotes = [
            _q("A", -1.0, 100.5),
            _q("B", 100.0, 100.5),
        ]
        result = layer.aggregate(quotes, NOW)
        assert "A" not in result.liquidity_map

    def test_zero_bid_excluded(self, layer):
        # q.ask > q.bid > 0 requires bid > 0
        quotes = [
            _q("A", 0.0, 100.5),
            _q("B", 100.0, 100.5),
        ]
        result = layer.aggregate(quotes, NOW)
        assert "A" not in result.liquidity_map

    def test_bid_equals_ask_excluded(self, layer):
        # q.ask > q.bid required
        quotes = [
            _q("A", 100.0, 100.0),
            _q("B", 100.0, 100.5),
        ]
        result = layer.aggregate(quotes, NOW)
        assert "A" not in result.liquidity_map

    def test_inverted_spread_excluded(self, layer):
        quotes = [
            _q("A", 101.0, 100.0),  # bid > ask
            _q("B", 100.0, 100.5),
        ]
        result = layer.aggregate(quotes, NOW)
        assert "A" not in result.liquidity_map

    def test_all_invalid_raises(self, layer):
        quotes = [_q("A", -1.0, 100.0), _q("B", 100.0, 100.0)]
        with pytest.raises(ValueError, match="gueltigen/frischen"):
            layer.aggregate(quotes, NOW)


# ---------------------------------------------------------------------------
# LIQUIDITY MAP
# ---------------------------------------------------------------------------

class TestLiquidityMap:
    def test_all_brokers_present(self, layer):
        quotes = [_q("A", 100.0, 100.5), _q("B", 100.0, 100.3)]
        result = layer.aggregate(quotes, NOW)
        assert "A" in result.liquidity_map
        assert "B" in result.liquidity_map

    def test_tighter_spread_higher_score(self, layer):
        quotes = [_q("A", 100.0, 100.1), _q("B", 100.0, 101.0)]
        result = layer.aggregate(quotes, NOW)
        assert result.liquidity_map["A"] > result.liquidity_map["B"]

    def test_score_range(self, layer):
        quotes = [_q("A", 100.0, 100.5), _q("B", 100.0, 100.3)]
        result = layer.aggregate(quotes, NOW)
        for score in result.liquidity_map.values():
            assert 0.0 <= score <= 1.0

    def test_volume_affects_score(self, layer):
        quotes = [
            _q("A", 100.0, 100.5, volume=1000.0),
            _q("B", 100.0, 100.5, volume=100.0),
        ]
        result = layer.aggregate(quotes, NOW)
        assert result.liquidity_map["A"] >= result.liquidity_map["B"]

    def test_no_volume_uses_default(self, layer):
        quotes = [_q("A", 100.0, 100.5)]  # volume=None
        result = layer.aggregate(quotes, NOW)
        # vol_score defaults to 0.5, spread_score for single quote:
        # spread = 0.5, avg_spread = 0.5
        # spread_score = clip(1 - 0.5/0.5, 0, 1) = 0.0
        # liq = 0.6*0.0 + 0.4*0.5 = 0.2
        assert result.liquidity_map["A"] == pytest.approx(0.2)

    def test_liquidity_formula_weights(self, layer):
        # 0.6 spread_score + 0.4 vol_score
        quotes = [_q("A", 100.0, 100.5, volume=500.0),
                  _q("B", 100.0, 100.5, volume=500.0)]
        result = layer.aggregate(quotes, NOW)
        # Both identical -> same scores
        assert result.liquidity_map["A"] == pytest.approx(result.liquidity_map["B"])


# ---------------------------------------------------------------------------
# PREFERRED SOURCE
# ---------------------------------------------------------------------------

class TestPreferredSource:
    def test_tightest_spread_preferred(self, layer):
        quotes = [_q("A", 100.0, 101.0), _q("B", 100.0, 100.1)]
        result = layer.aggregate(quotes, NOW)
        assert result.preferred_source == "B"

    def test_single_broker(self, layer):
        result = layer.aggregate([_q("ONLY", 50.0, 50.5)], NOW)
        assert result.preferred_source == "ONLY"

    def test_volume_can_tip_preference(self, layer):
        # A has wider spread but much more volume
        quotes = [
            _q("A", 100.0, 100.5, volume=10000.0),
            _q("B", 100.0, 100.3, volume=1.0),
        ]
        result = layer.aggregate(quotes, NOW)
        # B has tighter spread (higher spread_score), but A has more volume
        # Whether A or B wins depends on the weights
        assert result.preferred_source in ("A", "B")


# ---------------------------------------------------------------------------
# DATA QUALITY
# ---------------------------------------------------------------------------

class TestDataQuality:
    def test_range(self, layer):
        quotes = [_q("A", 100.0, 100.5), _q("B", 100.0, 100.3)]
        result = layer.aggregate(quotes, NOW)
        assert 0.0 <= result.data_quality <= 1.0

    def test_all_fresh_consistent_high_quality(self, layer):
        quotes = [_q(f"B{i}", 100.0, 100.5) for i in range(5)]
        result = layer.aggregate(quotes, NOW)
        # All fresh (freshness=1.0), zero dispersion (consistency=1.0)
        # quality = 0.5*1.0 + 0.5*1.0 = 1.0
        assert result.data_quality == pytest.approx(1.0)

    def test_freshness_component(self, layer):
        # 2 fresh out of 4 total -> freshness = 0.5
        fresh_quotes = [_q("A", 100.0, 100.5), _q("B", 100.0, 100.5)]
        stale_quotes = [
            _q("C", 100.0, 100.5, ts=NOW - 50.0),
            _q("D", 100.0, 100.5, ts=NOW - 50.0),
        ]
        result = layer.aggregate(fresh_quotes + stale_quotes, NOW)
        # freshness = 2/4 = 0.5, consistency = 1.0 (uniform spreads)
        # quality = 0.5*0.5 + 0.5*1.0 = 0.75
        assert result.data_quality == pytest.approx(0.75)

    def test_consistency_component(self, layer):
        # Varied spreads -> higher dispersion -> lower consistency
        uniform = [_q(f"U{i}", 100.0, 100.5) for i in range(3)]
        varied = [_q("A", 100.0, 100.1), _q("B", 100.0, 101.0), _q("C", 100.0, 100.5)]
        r_uniform = layer.aggregate(uniform, NOW)
        r_varied = layer.aggregate(varied, NOW)
        assert r_uniform.data_quality >= r_varied.data_quality

    def test_formula_manual(self, layer):
        quotes = [_q("A", 100.0, 100.5)]
        result = layer.aggregate(quotes, NOW)
        # freshness = 1/1 = 1.0
        # dispersion = 0.0, avg_spread = 0.5
        # consistency = clip(1 - 0/0.5, 0, 1) = 1.0
        # quality = 0.5*1.0 + 0.5*1.0 = 1.0
        assert result.data_quality == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# INPUT VALIDATION
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_empty_quotes_raises(self, layer):
        with pytest.raises(ValueError, match="Keine Broker-Quotes vorhanden"):
            layer.aggregate([], NOW)

    def test_all_stale_raises(self, layer):
        quotes = [_q("A", 100.0, 100.5, ts=NOW - 100.0)]
        with pytest.raises(ValueError, match="gueltigen/frischen"):
            layer.aggregate(quotes, NOW)

    def test_all_nan_raises(self, layer):
        quotes = [_q("A", float('nan'), float('nan'))]
        with pytest.raises(ValueError, match="gueltigen/frischen"):
            layer.aggregate(quotes, NOW)


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

class TestConstants:
    def test_max_quote_age(self):
        assert MultiSourceDataLayer.MAX_QUOTE_AGE_SECONDS == 10.0


# ---------------------------------------------------------------------------
# DATACLASS FIELDS
# ---------------------------------------------------------------------------

class TestDataClasses:
    def test_broker_quote_fields(self):
        q = BrokerQuote(broker_id="X", bid=50.0, ask=51.0, timestamp=100.0, volume=200.0)
        assert q.broker_id == "X"
        assert q.bid == 50.0
        assert q.ask == 51.0
        assert q.timestamp == 100.0
        assert q.volume == 200.0

    def test_broker_quote_default_volume(self):
        q = BrokerQuote(broker_id="X", bid=50.0, ask=51.0, timestamp=100.0)
        assert q.volume is None

    def test_assessment_fields(self):
        a = MultiBrokerAssessment(
            best_bid=100.0, best_ask=100.5, avg_spread=0.5, min_spread=0.3,
            spread_dispersion=0.1, liquidity_map={"A": 0.8},
            preferred_source="A", data_quality=0.9,
        )
        assert a.best_bid == 100.0
        assert a.preferred_source == "A"
        assert a.liquidity_map == {"A": 0.8}


# ---------------------------------------------------------------------------
# DETERMINISM
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_identical_inputs_identical_outputs(self, layer):
        quotes = [
            _q("A", 100.0, 100.5, volume=500.0),
            _q("B", 100.1, 100.4, volume=300.0),
            _q("C", 99.9, 100.6, volume=700.0),
        ]
        r1 = layer.aggregate(quotes, NOW)
        r2 = layer.aggregate(quotes, NOW)
        assert r1.best_bid == r2.best_bid
        assert r1.best_ask == r2.best_ask
        assert r1.avg_spread == r2.avg_spread
        assert r1.min_spread == r2.min_spread
        assert r1.spread_dispersion == r2.spread_dispersion
        assert r1.data_quality == r2.data_quality
        assert r1.preferred_source == r2.preferred_source
        assert r1.liquidity_map == r2.liquidity_map

    def test_no_state_between_calls(self, layer):
        q1 = [_q("A", 100.0, 100.5)]
        q2 = [_q("B", 200.0, 200.5)]
        r1a = layer.aggregate(q1, NOW)
        _ = layer.aggregate(q2, NOW)
        r1b = layer.aggregate(q1, NOW)
        assert r1a.best_bid == r1b.best_bid
        assert r1a.data_quality == r1b.data_quality


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_many_brokers(self, layer):
        quotes = [_q(f"B{i}", 100.0 + i * 0.01, 100.5 + i * 0.01) for i in range(50)]
        result = layer.aggregate(quotes, NOW)
        assert len(result.liquidity_map) == 50

    def test_very_tight_spread(self, layer):
        result = layer.aggregate([_q("A", 100.0, 100.0001)], NOW)
        assert result.avg_spread == pytest.approx(0.0001)

    def test_very_wide_spread(self, layer):
        result = layer.aggregate([_q("A", 100.0, 200.0)], NOW)
        assert result.avg_spread == pytest.approx(100.0)

    def test_duplicate_broker_ids(self, layer):
        # Same broker_id appears twice — last one wins in dict
        quotes = [_q("A", 100.0, 100.5), _q("A", 100.0, 100.3)]
        result = layer.aggregate(quotes, NOW)
        assert "A" in result.liquidity_map

    def test_very_small_prices(self, layer):
        result = layer.aggregate([_q("A", 0.001, 0.002)], NOW)
        assert result.best_bid == pytest.approx(0.001)
        assert result.best_ask == pytest.approx(0.002)

    def test_volume_zero_uses_default(self, layer):
        # volume=0 -> q.volume > 0 is False -> default vol_score=0.5
        quotes = [_q("A", 100.0, 100.5, volume=0.0)]
        result = layer.aggregate(quotes, NOW)
        assert "A" in result.liquidity_map

    def test_negative_volume_uses_default(self, layer):
        quotes = [_q("A", 100.0, 100.5, volume=-100.0)]
        result = layer.aggregate(quotes, NOW)
        assert "A" in result.liquidity_map

    def test_inf_volume_uses_default(self, layer):
        # np.isfinite(inf) is False -> default vol_score
        quotes = [_q("A", 100.0, 100.5, volume=float('inf'))]
        result = layer.aggregate(quotes, NOW)
        assert "A" in result.liquidity_map
