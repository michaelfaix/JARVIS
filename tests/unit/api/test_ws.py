# =============================================================================
# tests/unit/api/test_ws.py — WebSocket tests for S14 API
#
# Tests cover:
#   - StreamManager: connect, disconnect, connection_count, broadcast
#   - WebSocket endpoint: connect to /stream/BTC, send/receive, disconnect
# =============================================================================

import pytest
from fastapi import FastAPI, WebSocket
from starlette.testclient import TestClient

from jarvis.api.ws import StreamManager, websocket_stream


@pytest.fixture
def app():
    """Create a FastAPI app with the WebSocket endpoint."""
    application = FastAPI()

    @application.websocket("/stream/{symbol}")
    async def ws_endpoint(websocket: WebSocket, symbol: str):
        await websocket_stream(websocket, symbol)

    return application


@pytest.fixture
def client(app):
    return TestClient(app)


# =============================================================================
# StreamManager unit tests
# =============================================================================

class TestStreamManager:
    """Tests for the StreamManager class."""

    def test_initial_connection_count_zero(self):
        mgr = StreamManager()
        assert mgr.get_connection_count("BTC") == 0

    def test_connection_count_unknown_symbol(self):
        mgr = StreamManager()
        assert mgr.get_connection_count("ETH") == 0

    @pytest.mark.anyio
    async def test_connect_increments_count(self):
        """Verify internal state after simulated connect."""
        mgr = StreamManager()
        # Simulate by directly manipulating _connections
        # (actual WebSocket accept needs a real connection)
        mgr._connections["BTC"] = ["ws1"]
        assert mgr.get_connection_count("BTC") == 1

    @pytest.mark.anyio
    async def test_disconnect_decrements_count(self):
        """Verify disconnect removes the correct connection."""
        mgr = StreamManager()
        mgr._connections["BTC"] = ["ws1", "ws2"]
        await mgr.disconnect("ws1", "BTC")
        assert mgr.get_connection_count("BTC") == 1

    @pytest.mark.anyio
    async def test_disconnect_nonexistent_symbol(self):
        """Disconnect on unknown symbol should not raise."""
        mgr = StreamManager()
        await mgr.disconnect("ws1", "UNKNOWN")
        assert mgr.get_connection_count("UNKNOWN") == 0

    @pytest.mark.anyio
    async def test_broadcast_empty_connections(self):
        """Broadcast to symbol with no connections should not raise."""
        mgr = StreamManager()
        await mgr.broadcast("BTC", {"price": 65000.0})

    def test_multiple_symbols(self):
        """Connection counts are per-symbol."""
        mgr = StreamManager()
        mgr._connections["BTC"] = ["ws1", "ws2"]
        mgr._connections["ETH"] = ["ws3"]
        assert mgr.get_connection_count("BTC") == 2
        assert mgr.get_connection_count("ETH") == 1


# =============================================================================
# WebSocket endpoint tests
# =============================================================================

class TestWebSocketEndpoint:
    """Tests for the /stream/{symbol} WebSocket endpoint."""

    def test_connect_to_stream(self, client):
        with client.websocket_connect("/stream/BTC") as ws:
            ws.send_text("hello")
            data = ws.receive_json()
            assert data["status"] == "received"
            assert data["symbol"] == "BTC"

    def test_connect_to_different_symbol(self, client):
        with client.websocket_connect("/stream/ETH") as ws:
            ws.send_text("ping")
            data = ws.receive_json()
            assert data["symbol"] == "ETH"

    def test_multiple_messages(self, client):
        with client.websocket_connect("/stream/SPY") as ws:
            for i in range(3):
                ws.send_text(f"msg-{i}")
                data = ws.receive_json()
                assert data["status"] == "received"
                assert data["symbol"] == "SPY"

    def test_disconnect_graceful(self, client):
        """Connection should close gracefully after context manager exit."""
        with client.websocket_connect("/stream/BTC") as ws:
            ws.send_text("test")
            ws.receive_json()
        # No exception after exit = graceful disconnect
