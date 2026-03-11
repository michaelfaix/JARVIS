# =============================================================================
# jarvis/api/main.py — FastAPI Application Entry Point
#
# Authority: FAS v6.0.1, S14
#
# Creates the FastAPI application instance with CORS middleware,
# mounts the API router, and configures the WebSocket stream endpoint.
#
# CLASSIFICATION: Tier 6 — ANALYSIS AND STRATEGY RESEARCH TOOL.
# This is a BOUNDARY layer — no computational logic here.
#
# Usage:
#   uvicorn jarvis.api.main:app --reload --port 8000
# =============================================================================

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .ws import websocket_stream

__all__ = ["app"]

# =============================================================================
# APPLICATION
# =============================================================================

app = FastAPI(
    title="JARVIS MASP API",
    version="7.0.0",
    description="JARVIS Multi-Asset Strategy Platform — Analysis & Research API",
)

# =============================================================================
# CORS MIDDLEWARE
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# MOUNT ROUTES
# =============================================================================

app.include_router(router, prefix="/api/v1")
app.add_api_websocket_route("/api/v1/stream/{symbol}", websocket_stream)
