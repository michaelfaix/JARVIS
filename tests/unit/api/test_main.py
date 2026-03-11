# =============================================================================
# tests/unit/api/test_main.py — Tests for FastAPI application entry point
# =============================================================================

from fastapi import FastAPI
from fastapi.testclient import TestClient

from jarvis.api.main import app


class TestApp:
    """Tests for the FastAPI application instance."""

    def test_app_is_fastapi_instance(self):
        assert isinstance(app, FastAPI)

    def test_app_title(self):
        assert app.title == "JARVIS MASP API"

    def test_app_version(self):
        assert app.version == "7.0.0"

    def test_health_endpoint(self):
        client = TestClient(app)
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_cors_localhost_any_port(self):
        client = TestClient(app)
        for port in [3000, 3001, 3002, 8080]:
            origin = f"http://localhost:{port}"
            resp = client.options(
                "/api/v1/health",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                },
            )
            assert resp.headers.get("access-control-allow-origin") == origin, (
                f"CORS should allow {origin}"
            )

    def test_status_endpoint(self):
        client = TestClient(app)
        resp = client.get("/api/v1/status")
        assert resp.status_code == 200

    def test_metrics_endpoint(self):
        client = TestClient(app)
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200
