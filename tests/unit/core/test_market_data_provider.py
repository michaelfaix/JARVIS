# tests/unit/core/test_market_data_provider.py
# Coverage target: jarvis/core/market_data_provider.py -> 95%+
# Tests both providers, buffer management, sequence enforcement, rolling
# window limits, edge cases, and determinism.

import pytest

from jarvis.core.data_layer import (
    OHLCV,
    MarketData,
    SequenceError,
)
from jarvis.core.market_data_provider import (
    MAX_BUFFER_SIZE,
    CandleRecord,
    HistoricalDataProvider,
    LiveDataProvider,
    _buffer_key,
)


# =============================================================================
# Helpers
# =============================================================================

def _md(
    symbol: str = "BTC/USDT",
    timeframe: str = "H1",
    seq: int = 1,
    close: float = 100.0,
    data_source: str = "historical",
) -> MarketData:
    """Build a valid MarketData with sensible defaults."""
    high = close + 5.0
    low = close - 5.0 if close > 5.0 else 0.01
    opn = close - 1.0 if close > 1.0 else 0.5
    return MarketData(
        symbol=symbol,
        asset_class="crypto",
        timeframe=timeframe,
        timestamp_utc=1000 + seq,
        ohlcv=OHLCV(open=opn, high=high, low=low, close=close, volume=100.0),
        quality_score=0.9,
        sequence_id=seq,
        data_source=data_source,
        provider_id="test",
    )


# =============================================================================
# Constants
# =============================================================================

class TestConstants:
    def test_max_buffer_size(self):
        assert MAX_BUFFER_SIZE == 500


# =============================================================================
# CandleRecord
# =============================================================================

class TestCandleRecord:
    def test_construction(self):
        md = _md()
        cr = CandleRecord("BTC/USDT_H1", md)
        assert cr.key == "BTC/USDT_H1"
        assert cr.market_data == md

    def test_equality(self):
        md = _md()
        cr1 = CandleRecord("BTC/USDT_H1", md)
        cr2 = CandleRecord("BTC/USDT_H1", md)
        assert cr1 == cr2

    def test_inequality_key(self):
        md = _md()
        cr1 = CandleRecord("BTC/USDT_H1", md)
        cr2 = CandleRecord("ETH/USDT_H1", md)
        assert cr1 != cr2

    def test_inequality_wrong_type(self):
        md = _md()
        cr = CandleRecord("BTC/USDT_H1", md)
        assert cr != "not a record"


# =============================================================================
# _buffer_key
# =============================================================================

class TestBufferKey:
    def test_standard_key(self):
        assert _buffer_key("BTC/USDT", "H1") == "BTC/USDT_H1"

    def test_different_inputs(self):
        assert _buffer_key("ETH/USD", "M5") == "ETH/USD_M5"


# =============================================================================
# HistoricalDataProvider -- Construction
# =============================================================================

class TestHistoricalConstruction:
    def test_default_mode_tag(self):
        p = HistoricalDataProvider()
        assert p.mode_tag == "historical"

    def test_hybrid_backfill_mode_tag(self):
        p = HistoricalDataProvider(mode_tag="hybrid_backfill")
        assert p.mode_tag == "hybrid_backfill"

    def test_invalid_mode_tag_raises(self):
        with pytest.raises(ValueError, match="mode_tag"):
            HistoricalDataProvider(mode_tag="live")

    def test_initial_empty(self):
        p = HistoricalDataProvider()
        assert p.symbols == []
        assert p.depth("BTC/USDT", "H1") == 0


# =============================================================================
# HistoricalDataProvider -- load()
# =============================================================================

class TestHistoricalLoad:
    def test_load_single_candle(self):
        p = HistoricalDataProvider()
        md = _md(seq=1)
        result = p.load(md)
        assert result == md
        assert p.depth("BTC/USDT", "H1") == 1

    def test_load_multiple_candles(self):
        p = HistoricalDataProvider()
        for i in range(1, 6):
            p.load(_md(seq=i))
        assert p.depth("BTC/USDT", "H1") == 5

    def test_load_non_market_data_raises(self):
        p = HistoricalDataProvider()
        with pytest.raises(TypeError, match="MarketData"):
            p.load("not market data")

    def test_load_none_raises(self):
        p = HistoricalDataProvider()
        with pytest.raises(TypeError, match="MarketData"):
            p.load(None)

    def test_sequence_regression_raises(self):
        p = HistoricalDataProvider()
        p.load(_md(seq=5))
        with pytest.raises(SequenceError):
            p.load(_md(seq=3))

    def test_sequence_duplicate_raises(self):
        p = HistoricalDataProvider()
        p.load(_md(seq=5))
        with pytest.raises(SequenceError):
            p.load(_md(seq=5))

    def test_rolling_window_cap(self):
        p = HistoricalDataProvider()
        for i in range(1, MAX_BUFFER_SIZE + 100):
            p.load(_md(seq=i))
        assert p.depth("BTC/USDT", "H1") == MAX_BUFFER_SIZE

    def test_oldest_evicted_first(self):
        p = HistoricalDataProvider()
        for i in range(1, MAX_BUFFER_SIZE + 10):
            p.load(_md(seq=i, close=float(i)))
        latest = p.get_latest("BTC/USDT", "H1")
        assert latest is not None
        assert latest.ohlcv.close == float(MAX_BUFFER_SIZE + 9)

    def test_multiple_symbols(self):
        p = HistoricalDataProvider()
        p.load(_md(symbol="BTC/USDT", seq=1))
        p.load(_md(symbol="ETH/USDT", seq=1))
        assert p.depth("BTC/USDT", "H1") == 1
        assert p.depth("ETH/USDT", "H1") == 1
        assert len(p.symbols) == 2


# =============================================================================
# HistoricalDataProvider -- get_latest()
# =============================================================================

class TestHistoricalGetLatest:
    def test_returns_last_loaded(self):
        p = HistoricalDataProvider()
        p.load(_md(seq=1, close=100.0))
        p.load(_md(seq=2, close=200.0))
        latest = p.get_latest("BTC/USDT", "H1")
        assert latest is not None
        assert latest.ohlcv.close == 200.0

    def test_returns_none_if_empty(self):
        p = HistoricalDataProvider()
        assert p.get_latest("BTC/USDT", "H1") is None

    def test_returns_none_wrong_symbol(self):
        p = HistoricalDataProvider()
        p.load(_md(symbol="BTC/USDT", seq=1))
        assert p.get_latest("ETH/USDT", "H1") is None


# =============================================================================
# HistoricalDataProvider -- get_candles()
# =============================================================================

class TestHistoricalGetCandles:
    def test_returns_all(self):
        p = HistoricalDataProvider()
        for i in range(1, 6):
            p.load(_md(seq=i))
        candles = p.get_candles("BTC/USDT", "H1")
        assert len(candles) == 5

    def test_returns_last_n(self):
        p = HistoricalDataProvider()
        for i in range(1, 11):
            p.load(_md(seq=i))
        candles = p.get_candles("BTC/USDT", "H1", last_n=3)
        assert len(candles) == 3
        assert candles[0].sequence_id == 8

    def test_empty_for_unknown_key(self):
        p = HistoricalDataProvider()
        assert p.get_candles("UNKNOWN", "H1") == []

    def test_fifo_order(self):
        p = HistoricalDataProvider()
        for i in range(1, 4):
            p.load(_md(seq=i, close=float(i * 100)))
        candles = p.get_candles("BTC/USDT", "H1")
        assert candles[0].ohlcv.close == 100.0
        assert candles[2].ohlcv.close == 300.0


# =============================================================================
# HistoricalDataProvider -- get_rolling_closes()
# =============================================================================

class TestHistoricalRollingCloses:
    def test_returns_closes(self):
        p = HistoricalDataProvider()
        for i in range(1, 6):
            p.load(_md(seq=i, close=float(i * 10)))
        closes = p.get_rolling_closes("BTC/USDT", "H1", window=3)
        assert closes == [30.0, 40.0, 50.0]

    def test_returns_all_if_fewer_than_window(self):
        p = HistoricalDataProvider()
        p.load(_md(seq=1, close=100.0))
        closes = p.get_rolling_closes("BTC/USDT", "H1", window=20)
        assert closes == [100.0]

    def test_empty_for_unknown_key(self):
        p = HistoricalDataProvider()
        assert p.get_rolling_closes("UNKNOWN", "H1") == []


# =============================================================================
# LiveDataProvider -- Construction
# =============================================================================

class TestLiveConstruction:
    def test_default_mode_tag(self):
        p = LiveDataProvider()
        assert p.mode_tag == "live"

    def test_hybrid_live_mode_tag(self):
        p = LiveDataProvider(mode_tag="hybrid_live")
        assert p.mode_tag == "hybrid_live"

    def test_invalid_mode_tag_raises(self):
        with pytest.raises(ValueError, match="mode_tag"):
            LiveDataProvider(mode_tag="historical")

    def test_initial_empty(self):
        p = LiveDataProvider()
        assert p.symbols == []
        assert p.ingest_count == 0


# =============================================================================
# LiveDataProvider -- ingest()
# =============================================================================

class TestLiveIngest:
    def test_ingest_single(self):
        p = LiveDataProvider()
        md = _md(seq=1, data_source="live")
        result = p.ingest(md)
        assert result == md
        assert p.depth("BTC/USDT", "H1") == 1
        assert p.ingest_count == 1

    def test_ingest_multiple(self):
        p = LiveDataProvider()
        for i in range(1, 6):
            p.ingest(_md(seq=i, data_source="live"))
        assert p.depth("BTC/USDT", "H1") == 5
        assert p.ingest_count == 5

    def test_ingest_non_market_data_raises(self):
        p = LiveDataProvider()
        with pytest.raises(TypeError, match="MarketData"):
            p.ingest({"close": 100.0})

    def test_ingest_none_raises(self):
        p = LiveDataProvider()
        with pytest.raises(TypeError, match="MarketData"):
            p.ingest(None)

    def test_sequence_regression_raises(self):
        p = LiveDataProvider()
        p.ingest(_md(seq=5, data_source="live"))
        with pytest.raises(SequenceError):
            p.ingest(_md(seq=3, data_source="live"))

    def test_rolling_window_cap(self):
        p = LiveDataProvider()
        for i in range(1, MAX_BUFFER_SIZE + 100):
            p.ingest(_md(seq=i, data_source="live"))
        assert p.depth("BTC/USDT", "H1") == MAX_BUFFER_SIZE

    def test_multiple_symbols_independent(self):
        p = LiveDataProvider()
        p.ingest(_md(symbol="BTC/USDT", seq=1, data_source="live"))
        p.ingest(_md(symbol="ETH/USDT", seq=1, data_source="live"))
        assert p.depth("BTC/USDT", "H1") == 1
        assert p.depth("ETH/USDT", "H1") == 1
        assert len(p.symbols) == 2
        assert p.ingest_count == 2

    def test_ingest_count_cumulative(self):
        p = LiveDataProvider()
        p.ingest(_md(symbol="BTC/USDT", seq=1, data_source="live"))
        p.ingest(_md(symbol="BTC/USDT", seq=2, data_source="live"))
        p.ingest(_md(symbol="ETH/USDT", seq=1, data_source="live"))
        assert p.ingest_count == 3


# =============================================================================
# LiveDataProvider -- get_latest()
# =============================================================================

class TestLiveGetLatest:
    def test_returns_last_ingested(self):
        p = LiveDataProvider()
        p.ingest(_md(seq=1, close=100.0, data_source="live"))
        p.ingest(_md(seq=2, close=200.0, data_source="live"))
        latest = p.get_latest("BTC/USDT", "H1")
        assert latest is not None
        assert latest.ohlcv.close == 200.0

    def test_returns_none_if_empty(self):
        p = LiveDataProvider()
        assert p.get_latest("BTC/USDT", "H1") is None


# =============================================================================
# LiveDataProvider -- get_candles()
# =============================================================================

class TestLiveGetCandles:
    def test_returns_all(self):
        p = LiveDataProvider()
        for i in range(1, 4):
            p.ingest(_md(seq=i, data_source="live"))
        candles = p.get_candles("BTC/USDT", "H1")
        assert len(candles) == 3

    def test_returns_last_n(self):
        p = LiveDataProvider()
        for i in range(1, 11):
            p.ingest(_md(seq=i, data_source="live"))
        candles = p.get_candles("BTC/USDT", "H1", last_n=3)
        assert len(candles) == 3
        assert candles[0].sequence_id == 8

    def test_empty_for_unknown(self):
        p = LiveDataProvider()
        assert p.get_candles("UNKNOWN", "H1") == []


# =============================================================================
# LiveDataProvider -- get_rolling_closes()
# =============================================================================

class TestLiveRollingCloses:
    def test_returns_closes(self):
        p = LiveDataProvider()
        for i in range(1, 6):
            p.ingest(_md(seq=i, close=float(i * 10), data_source="live"))
        closes = p.get_rolling_closes("BTC/USDT", "H1", window=3)
        assert closes == [30.0, 40.0, 50.0]

    def test_empty_for_unknown(self):
        p = LiveDataProvider()
        assert p.get_rolling_closes("UNKNOWN", "H1") == []


# =============================================================================
# Sequence independence across symbols
# =============================================================================

class TestSequenceIndependence:
    def test_different_symbols_independent_sequences(self):
        p = LiveDataProvider()
        p.ingest(_md(symbol="BTC/USDT", seq=1, data_source="live"))
        p.ingest(_md(symbol="ETH/USDT", seq=1, data_source="live"))
        p.ingest(_md(symbol="BTC/USDT", seq=2, data_source="live"))
        p.ingest(_md(symbol="ETH/USDT", seq=2, data_source="live"))
        assert p.depth("BTC/USDT", "H1") == 2
        assert p.depth("ETH/USDT", "H1") == 2

    def test_different_timeframes_independent_sequences(self):
        p = LiveDataProvider()
        p.ingest(_md(timeframe="H1", seq=1, data_source="live"))
        p.ingest(_md(timeframe="M5", seq=1, data_source="live"))
        assert p.depth("BTC/USDT", "H1") == 1
        assert p.depth("BTC/USDT", "M5") == 1

    def test_regression_in_one_does_not_affect_other(self):
        p = LiveDataProvider()
        p.ingest(_md(symbol="BTC/USDT", seq=5, data_source="live"))
        p.ingest(_md(symbol="ETH/USDT", seq=1, data_source="live"))
        # BTC regression should not block ETH
        with pytest.raises(SequenceError):
            p.ingest(_md(symbol="BTC/USDT", seq=3, data_source="live"))
        # ETH still works
        p.ingest(_md(symbol="ETH/USDT", seq=2, data_source="live"))
        assert p.depth("ETH/USDT", "H1") == 2


# =============================================================================
# Properties
# =============================================================================

class TestProperties:
    def test_historical_depth_zero(self):
        p = HistoricalDataProvider()
        assert p.depth("X", "H1") == 0

    def test_live_depth_zero(self):
        p = LiveDataProvider()
        assert p.depth("X", "H1") == 0

    def test_historical_symbols_tracks_loaded(self):
        p = HistoricalDataProvider()
        p.load(_md(symbol="AAA", seq=1))
        p.load(_md(symbol="BBB", seq=1))
        syms = p.symbols
        assert "AAA" in syms
        assert "BBB" in syms

    def test_live_symbols_tracks_ingested(self):
        p = LiveDataProvider()
        p.ingest(_md(symbol="X", seq=1, data_source="live"))
        assert "X" in p.symbols


# =============================================================================
# Determinism
# =============================================================================

class TestDeterminism:
    def test_same_sequence_same_state(self):
        p1 = LiveDataProvider()
        p2 = LiveDataProvider()
        for i in range(1, 6):
            md = _md(seq=i, close=float(i * 10), data_source="live")
            p1.ingest(md)
            p2.ingest(md)
        c1 = p1.get_rolling_closes("BTC/USDT", "H1")
        c2 = p2.get_rolling_closes("BTC/USDT", "H1")
        assert c1 == c2
        assert p1.ingest_count == p2.ingest_count

    def test_historical_deterministic(self):
        p1 = HistoricalDataProvider()
        p2 = HistoricalDataProvider()
        for i in range(1, 6):
            md = _md(seq=i, close=float(i * 10))
            p1.load(md)
            p2.load(md)
        c1 = p1.get_candles("BTC/USDT", "H1")
        c2 = p2.get_candles("BTC/USDT", "H1")
        assert len(c1) == len(c2)
        for a, b in zip(c1, c2):
            assert a == b


# =============================================================================
# Edge cases
# =============================================================================

class TestEdgeCases:
    def test_first_sequence_id_zero(self):
        p = LiveDataProvider()
        p.ingest(_md(seq=0, data_source="live"))
        assert p.depth("BTC/USDT", "H1") == 1

    def test_get_candles_last_n_larger_than_buffer(self):
        p = LiveDataProvider()
        p.ingest(_md(seq=1, data_source="live"))
        candles = p.get_candles("BTC/USDT", "H1", last_n=100)
        assert len(candles) == 1

    def test_get_candles_last_n_zero_returns_all(self):
        p = LiveDataProvider()
        for i in range(1, 4):
            p.ingest(_md(seq=i, data_source="live"))
        # last_n=0 should not trigger the > 0 branch, returns all
        candles = p.get_candles("BTC/USDT", "H1", last_n=0)
        assert len(candles) == 3

    def test_get_candles_last_n_none_returns_all(self):
        p = HistoricalDataProvider()
        for i in range(1, 4):
            p.load(_md(seq=i))
        candles = p.get_candles("BTC/USDT", "H1", last_n=None)
        assert len(candles) == 3

    def test_buffer_is_copy(self):
        p = LiveDataProvider()
        p.ingest(_md(seq=1, data_source="live"))
        candles = p.get_candles("BTC/USDT", "H1")
        candles.clear()
        assert p.depth("BTC/USDT", "H1") == 1
