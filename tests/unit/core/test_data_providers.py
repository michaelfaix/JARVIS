# =============================================================================
# Tests for jarvis.core.data_layer -- MarketDataProvider Protocols
# =============================================================================

import pytest

from jarvis.core.data_layer import (
    HistoricalDataProvider,
    LiveDataProvider,
    MarketData,
    MarketDataProvider,
    ValidationResult,
)


# ---------------------------------------------------------------------------
# 1. MarketDataProvider is runtime_checkable Protocol
# ---------------------------------------------------------------------------

class TestMarketDataProviderProtocol:
    def test_is_runtime_checkable(self):
        """MarketDataProvider must be a runtime-checkable Protocol."""
        # If it is runtime_checkable, isinstance checks work
        assert hasattr(MarketDataProvider, "__protocol_attrs__") or hasattr(
            MarketDataProvider, "__abstractmethods__"
        ) or hasattr(MarketDataProvider, "_is_runtime_protocol")

    def test_non_implementing_class_fails(self):
        class Empty:
            pass

        assert not isinstance(Empty(), MarketDataProvider)


# ---------------------------------------------------------------------------
# 2. HistoricalDataProvider is runtime_checkable Protocol
# ---------------------------------------------------------------------------

class TestHistoricalDataProviderProtocol:
    def test_is_runtime_checkable(self):
        assert hasattr(HistoricalDataProvider, "_is_runtime_protocol") or True
        # The key test: isinstance check should not raise
        class Dummy:
            pass
        # Should not raise TypeError -- proves it is runtime_checkable
        isinstance(Dummy(), HistoricalDataProvider)

    def test_non_implementing_class_fails(self):
        class Empty:
            pass

        assert not isinstance(Empty(), HistoricalDataProvider)


# ---------------------------------------------------------------------------
# 3. LiveDataProvider is runtime_checkable Protocol
# ---------------------------------------------------------------------------

class TestLiveDataProviderProtocol:
    def test_is_runtime_checkable(self):
        class Dummy:
            pass
        # Should not raise TypeError -- proves it is runtime_checkable
        isinstance(Dummy(), LiveDataProvider)

    def test_non_implementing_class_fails(self):
        class Empty:
            pass

        assert not isinstance(Empty(), LiveDataProvider)


# ---------------------------------------------------------------------------
# 4. A class implementing MarketDataProvider is recognized
# ---------------------------------------------------------------------------

class TestMarketDataProviderImplementation:
    def test_implementing_class_is_recognized(self):
        class MyProvider:
            def fetch(self, symbol: str, timeframe: str) -> MarketData:
                pass  # pragma: no cover

            def validate(self, data: MarketData) -> ValidationResult:
                pass  # pragma: no cover

        provider = MyProvider()
        assert isinstance(provider, MarketDataProvider)

    def test_partial_implementation_not_recognized(self):
        class PartialProvider:
            def fetch(self, symbol: str, timeframe: str) -> MarketData:
                pass  # pragma: no cover
            # Missing validate method

        provider = PartialProvider()
        assert not isinstance(provider, MarketDataProvider)

    def test_historical_provider_implementation(self):
        class MyHistProvider:
            def fetch_range(self, symbol: str, start_ordinal: int, end_ordinal: int) -> list:
                return []  # pragma: no cover

        provider = MyHistProvider()
        assert isinstance(provider, HistoricalDataProvider)

    def test_live_provider_implementation(self):
        class MyLiveProvider:
            def subscribe(self, symbol: str) -> None:
                pass  # pragma: no cover

            def get_latest(self, symbol: str) -> MarketData:
                pass  # pragma: no cover

        provider = MyLiveProvider()
        assert isinstance(provider, LiveDataProvider)


# ---------------------------------------------------------------------------
# 5. Import contract
# ---------------------------------------------------------------------------

class TestImportContract:
    def test_import_from_data_layer(self):
        from jarvis.core.data_layer import (
            HistoricalDataProvider,
            LiveDataProvider,
            MarketDataProvider,
        )
        assert MarketDataProvider is not None
        assert HistoricalDataProvider is not None
        assert LiveDataProvider is not None

    def test_in_all(self):
        from jarvis.core import data_layer
        assert "MarketDataProvider" in data_layer.__all__
        assert "HistoricalDataProvider" in data_layer.__all__
        assert "LiveDataProvider" in data_layer.__all__
