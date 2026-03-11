# =============================================================================
# jarvis/api/ws.py — S14 API Layer WebSocket Handler
#
# Authority: FAS v6.0.1, S14
#
# WebSocket support for streaming predictions per symbol.
# Manages connections and broadcasts data to subscribers.
#
# CLASSIFICATION: Tier 6 — ANALYSIS AND STRATEGY RESEARCH TOOL.
#
# DEPENDENCIES
# ------------
#   external: fastapi (WebSocket, WebSocketDisconnect)
# =============================================================================

from __future__ import annotations

from fastapi import WebSocket, WebSocketDisconnect

__all__ = [
    "StreamManager",
    "stream_manager",
    "websocket_stream",
]


# =============================================================================
# SECTION 1 -- STREAM MANAGER
# =============================================================================

class StreamManager:
    """Manages WebSocket connections for streaming predictions."""

    def __init__(self) -> None:
        self._connections: dict = {}  # symbol -> list of WebSocket

    async def connect(self, websocket: WebSocket, symbol: str) -> None:
        """Accept and register a WebSocket connection for a symbol."""
        await websocket.accept()
        if symbol not in self._connections:
            self._connections[symbol] = []
        self._connections[symbol].append(websocket)

    async def disconnect(self, websocket: WebSocket, symbol: str) -> None:
        """Remove a WebSocket connection for a symbol."""
        if symbol in self._connections:
            self._connections[symbol] = [
                ws for ws in self._connections[symbol] if ws != websocket
            ]

    async def broadcast(self, symbol: str, data: dict) -> None:
        """Broadcast data to all connections for a symbol."""
        if symbol in self._connections:
            for ws in self._connections[symbol]:
                try:
                    await ws.send_json(data)
                except Exception:
                    pass

    def get_connection_count(self, symbol: str) -> int:
        """Return the number of active connections for a symbol."""
        return len(self._connections.get(symbol, []))


# Module-level singleton instance
stream_manager = StreamManager()


# =============================================================================
# SECTION 2 -- WEBSOCKET ENDPOINT HANDLER
# =============================================================================

async def websocket_stream(websocket: WebSocket, symbol: str) -> None:
    """
    WebSocket endpoint handler for /stream/{symbol}.

    Accepts the connection, then loops receiving messages and
    echoing back acknowledgments until the client disconnects.
    """
    await stream_manager.connect(websocket, symbol)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"status": "received", "symbol": symbol})
    except WebSocketDisconnect:
        await stream_manager.disconnect(websocket, symbol)
