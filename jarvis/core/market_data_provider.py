# =============================================================================
# jarvis/core/market_data_provider.py
# Authority: FAS v6.0.1 -- S03 DATA INGESTION, S37 SYSTEM ADDENDUM Stage 0/1
# ARCHITECTURE.md Section 11 (Stages 0-1)
# =============================================================================
#
# SCOPE
# -----
# Unified market data provider abstraction.  All downstream layers consume
# MarketData / EnhancedMarketData objects through this interface.  They must
# never know whether data is historical or live.
#
# Providers:
#   MarketDataProviderBase    Abstract base with common rolling-buffer logic.
#   HistoricalDataProvider    Batch access to pre-validated historical data.
#   LiveDataProvider          Rolling-buffer ingestion with integrity gate.
#
# INVARIANTS
# ----------
# 1. No downstream layer may branch on data_source field.
# 2. LiveDataProvider is READ-ONLY -- no execution, no broker API.
# 3. Rolling buffer max 500 candles per symbol/timeframe.
# 4. All incoming live data passes through the integrity gate.
# 5. sequence_id is monotonically increasing per symbol/timeframe.
#
# WRITE PERMISSIONS
# -----------------
#   market_data_provider.py writes to: EnhancedMarketData (construction only)
#   FORBIDDEN from writing: Any state object
#
# DEPENDENCIES
# ------------
#   stdlib:    typing, dataclasses
#   internal:  jarvis.core.data_layer (MarketData, OHLCV, VALID_ASSET_CLASSES,
#              VALID_TIMEFRAMES, VALID_SESSION_TAGS, VALID_DATA_SOURCES,
#              check_sequence, SequenceError)
#   PROHIBITED: numpy, logging, random, file IO, network IO, datetime.now()
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects beyond internal buffer state.
# DET-05  No datetime.now() / time.time().
# DET-07  Same sequence of ingest() calls = identical buffer state.
# =============================================================================

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from jarvis.core.data_layer import (
    OHLCV,
    MarketData,
    VALID_ASSET_CLASSES,
    VALID_DATA_SOURCES,
    VALID_TIMEFRAMES,
    SequenceError,
    check_sequence,
)

__all__ = [
    "MAX_BUFFER_SIZE",
    "CandleRecord",
    "HistoricalDataProvider",
    "LiveDataProvider",
]


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

# Maximum rolling buffer size per symbol/timeframe (FAS: 500).
MAX_BUFFER_SIZE: int = 500


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

class CandleRecord:
    """
    Lightweight validated candle record for provider buffers.

    Wraps a MarketData object with the buffer key for lookup.
    Immutable after construction (uses __slots__, no __dict__).
    """
    __slots__ = ("key", "market_data")

    def __init__(self, key: str, market_data: MarketData) -> None:
        self.key = key
        self.market_data = market_data

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CandleRecord):
            return NotImplemented
        return self.key == other.key and self.market_data == other.market_data


# =============================================================================
# SECTION 3 -- BUFFER KEY HELPER
# =============================================================================

def _buffer_key(symbol: str, timeframe: str) -> str:
    """Build canonical buffer key from symbol and timeframe."""
    return f"{symbol}_{timeframe}"


# =============================================================================
# SECTION 4 -- HISTORICAL DATA PROVIDER
# =============================================================================

class HistoricalDataProvider:
    """
    Provider for pre-validated historical data.

    Used in MODE_HISTORICAL and the backfill phase of MODE_HYBRID.
    Data is loaded into the provider by the caller via load().
    No integrity gate -- data is pre-validated in store.

    data_source is set to 'historical' or 'hybrid_backfill' depending
    on mode_tag (configured at construction).
    """

    def __init__(self, mode_tag: str = "historical") -> None:
        """
        Initialize historical provider.

        Args:
            mode_tag: Data source tag ('historical' or 'hybrid_backfill').

        Raises:
            ValueError: If mode_tag is not a valid data source.
        """
        if mode_tag not in ("historical", "hybrid_backfill"):
            raise ValueError(
                f"mode_tag must be 'historical' or 'hybrid_backfill', "
                f"got {mode_tag!r}"
            )
        self._mode_tag: str = mode_tag
        self._buffers: Dict[str, List[MarketData]] = {}
        self._sequence_counters: Dict[str, int] = {}

    def load(self, market_data: MarketData) -> MarketData:
        """
        Load a single pre-validated MarketData object into the provider.

        Enforces monotonic sequence_id per symbol/timeframe.
        Applies MAX_BUFFER_SIZE rolling window.

        Args:
            market_data: Pre-validated MarketData instance.

        Returns:
            The loaded MarketData object.

        Raises:
            TypeError:      If market_data is not a MarketData instance.
            SequenceError:  If sequence_id is not monotonically increasing.
        """
        if not isinstance(market_data, MarketData):
            raise TypeError(
                f"market_data must be a MarketData instance, "
                f"got {type(market_data).__name__}"
            )

        key = _buffer_key(market_data.symbol, market_data.timeframe)

        # Sequence check
        prev_seq = self._sequence_counters.get(key)
        if prev_seq is not None:
            check_sequence(prev_seq, market_data.sequence_id)
        self._sequence_counters[key] = market_data.sequence_id

        # Buffer management
        if key not in self._buffers:
            self._buffers[key] = []
        self._buffers[key].append(market_data)
        if len(self._buffers[key]) > MAX_BUFFER_SIZE:
            self._buffers[key] = self._buffers[key][-MAX_BUFFER_SIZE:]

        return market_data

    def get_latest(self, symbol: str, timeframe: str) -> Optional[MarketData]:
        """
        Return the most recent candle for a symbol/timeframe.

        Returns None if no data has been loaded for this key.
        """
        key = _buffer_key(symbol, timeframe)
        buf = self._buffers.get(key)
        if not buf:
            return None
        return buf[-1]

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        last_n: Optional[int] = None,
    ) -> List[MarketData]:
        """
        Return candles for a symbol/timeframe.

        Args:
            symbol:    Asset symbol.
            timeframe: Timeframe string.
            last_n:    If provided, return only the last N candles.

        Returns:
            List of MarketData (oldest first).  Empty if no data.
        """
        key = _buffer_key(symbol, timeframe)
        buf = self._buffers.get(key, [])
        if last_n is not None and last_n > 0:
            return list(buf[-last_n:])
        return list(buf)

    def get_rolling_closes(
        self,
        symbol: str,
        timeframe: str,
        window: int = 20,
    ) -> List[float]:
        """
        Return the last `window` close prices for outlier detection.

        Args:
            symbol:    Asset symbol.
            timeframe: Timeframe string.
            window:    Number of recent closes to return.

        Returns:
            List of close prices (oldest first).
        """
        key = _buffer_key(symbol, timeframe)
        buf = self._buffers.get(key, [])
        return [md.ohlcv.close for md in buf[-window:]]

    @property
    def mode_tag(self) -> str:
        """Data source tag for this provider."""
        return self._mode_tag

    @property
    def symbols(self) -> List[str]:
        """List of unique symbols currently in buffer."""
        seen = []
        for key in self._buffers:
            sym = key.rsplit("_", 1)[0]
            if sym not in seen:
                seen.append(sym)
        return seen

    def depth(self, symbol: str, timeframe: str) -> int:
        """Number of candles in buffer for a symbol/timeframe."""
        key = _buffer_key(symbol, timeframe)
        return len(self._buffers.get(key, []))


# =============================================================================
# SECTION 5 -- LIVE DATA PROVIDER
# =============================================================================

class LiveDataProvider:
    """
    Provider for live market data with integrity gate integration.

    Used in MODE_LIVE_ANALYTICAL and live phase of MODE_HYBRID.
    All incoming data must be pre-validated by the integrity gate
    before being passed to ingest().

    data_source is set to 'live' or 'hybrid_live' depending on mode_tag.

    Rolling buffer: max MAX_BUFFER_SIZE (500) candles per symbol/timeframe.
    """

    def __init__(self, mode_tag: str = "live") -> None:
        """
        Initialize live provider.

        Args:
            mode_tag: Data source tag ('live' or 'hybrid_live').

        Raises:
            ValueError: If mode_tag is not valid.
        """
        if mode_tag not in ("live", "hybrid_live"):
            raise ValueError(
                f"mode_tag must be 'live' or 'hybrid_live', "
                f"got {mode_tag!r}"
            )
        self._mode_tag: str = mode_tag
        self._buffers: Dict[str, List[MarketData]] = {}
        self._sequence_counters: Dict[str, int] = {}
        self._ingest_count: int = 0

    def ingest(self, market_data: MarketData) -> MarketData:
        """
        Ingest a single validated candle into the rolling buffer.

        The caller MUST have passed this data through the integrity gate
        (live_data_integrity_gate.run_integrity_gate) BEFORE calling ingest().
        This method does NOT run the gate itself -- it trusts the caller.

        Enforces monotonic sequence_id per symbol/timeframe.
        Applies MAX_BUFFER_SIZE rolling window.

        Args:
            market_data: Validated MarketData instance.

        Returns:
            The ingested MarketData object.

        Raises:
            TypeError:     If market_data is not a MarketData instance.
            SequenceError: If sequence_id is not monotonically increasing.
        """
        if not isinstance(market_data, MarketData):
            raise TypeError(
                f"market_data must be a MarketData instance, "
                f"got {type(market_data).__name__}"
            )

        key = _buffer_key(market_data.symbol, market_data.timeframe)

        # Sequence check
        prev_seq = self._sequence_counters.get(key)
        if prev_seq is not None:
            check_sequence(prev_seq, market_data.sequence_id)
        self._sequence_counters[key] = market_data.sequence_id

        # Buffer management
        if key not in self._buffers:
            self._buffers[key] = []
        self._buffers[key].append(market_data)
        if len(self._buffers[key]) > MAX_BUFFER_SIZE:
            self._buffers[key] = self._buffers[key][-MAX_BUFFER_SIZE:]

        self._ingest_count += 1
        return market_data

    def get_latest(self, symbol: str, timeframe: str) -> Optional[MarketData]:
        """
        Return the most recent candle for a symbol/timeframe.

        Returns None if no data has been ingested for this key.
        """
        key = _buffer_key(symbol, timeframe)
        buf = self._buffers.get(key)
        if not buf:
            return None
        return buf[-1]

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        last_n: Optional[int] = None,
    ) -> List[MarketData]:
        """
        Return candles from the rolling buffer.

        Args:
            symbol:    Asset symbol.
            timeframe: Timeframe string.
            last_n:    If provided, return only the last N candles.

        Returns:
            List of MarketData (oldest first).  Empty if no data.
        """
        key = _buffer_key(symbol, timeframe)
        buf = self._buffers.get(key, [])
        if last_n is not None and last_n > 0:
            return list(buf[-last_n:])
        return list(buf)

    def get_rolling_closes(
        self,
        symbol: str,
        timeframe: str,
        window: int = 20,
    ) -> List[float]:
        """
        Return the last `window` close prices for outlier detection.

        Args:
            symbol:    Asset symbol.
            timeframe: Timeframe string.
            window:    Number of recent closes to return.

        Returns:
            List of close prices (oldest first).
        """
        key = _buffer_key(symbol, timeframe)
        buf = self._buffers.get(key, [])
        return [md.ohlcv.close for md in buf[-window:]]

    @property
    def mode_tag(self) -> str:
        """Data source tag for this provider."""
        return self._mode_tag

    @property
    def ingest_count(self) -> int:
        """Total number of candles ingested across all symbols."""
        return self._ingest_count

    @property
    def symbols(self) -> List[str]:
        """List of unique symbols currently in buffer."""
        seen = []
        for key in self._buffers:
            sym = key.rsplit("_", 1)[0]
            if sym not in seen:
                seen.append(sym)
        return seen

    def depth(self, symbol: str, timeframe: str) -> int:
        """Number of candles in buffer for a symbol/timeframe."""
        key = _buffer_key(symbol, timeframe)
        return len(self._buffers.get(key, []))
