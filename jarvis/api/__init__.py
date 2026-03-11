# =============================================================================
# jarvis/api/__init__.py — S14 API Layer Package
#
# Authority: FAS v6.0.1, S14
#
# Public API surface for the FastAPI-based prediction API.
# =============================================================================

from .models import (
    FeedbackAnfrage,
    FeedbackAntwort,
    HealthAntwort,
    MetricsAntwort,
    RegimeInput,
    SystemStatusAntwort,
    UnsicherheitsOutput,
    VorhersageAnfrage,
    VorhersageAntwort,
)
from .routes import router
from .ws import StreamManager, stream_manager, websocket_stream

__all__ = [
    # Models
    "RegimeInput",
    "VorhersageAnfrage",
    "UnsicherheitsOutput",
    "VorhersageAntwort",
    "FeedbackAnfrage",
    "FeedbackAntwort",
    "SystemStatusAntwort",
    "MetricsAntwort",
    "HealthAntwort",
    # Router
    "router",
    # WebSocket
    "StreamManager",
    "stream_manager",
    "websocket_stream",
]
