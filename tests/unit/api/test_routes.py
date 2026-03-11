# =============================================================================
# tests/unit/api/test_routes.py — Route tests for S14 API using TestClient
#
# Tests cover:
#   - GET /health: returns 200 + version
#   - POST /predict: valid features, missing features, forced deep path
#   - POST /feedback: valid request, invalid action
#   - GET /status: returns all fields
#   - GET /metrics: returns all components
#   - Predict disabled (NOTFALL mode): returns 503
# =============================================================================

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from jarvis.api.routes import router, set_system_zustand
from jarvis.api.ws import websocket_stream
from jarvis.systems.degradation_ctrl import SystemZustand


@pytest.fixture
def app():
    """Create a fresh FastAPI app with the router included."""
    application = FastAPI()
    application.include_router(router)

    @application.websocket("/stream/{symbol}")
    async def ws_endpoint(websocket, symbol: str):
        await websocket_stream(websocket, symbol)

    return application


@pytest.fixture
def client(app):
    """Create a TestClient for the app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_system_state():
    """Reset system state to NORMAL before each test."""
    set_system_zustand(SystemZustand(
        ece=0.0,
        ood_score=0.0,
        datenverlust_ratio=0.0,
        entscheidungs_count=100,
        aktive_rekalibrierung=False,
        meta_unsicherheit_u=0.0,
    ))
    yield


# =============================================================================
# Health
# =============================================================================

class TestHealth:
    """Tests for GET /health."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, client):
        data = client.get("/health").json()
        assert data["status"] == "ok"

    def test_health_returns_version(self, client):
        data = client.get("/health").json()
        assert data["version"] == "6.2.0"


# =============================================================================
# Predict
# =============================================================================

class TestPredict:
    """Tests for POST /predict."""

    def test_predict_valid_features(self, client):
        response = client.post("/predict", json={
            "features": {"momentum": 0.3, "volatility": 0.1, "trend_strength": 0.2},
        })
        assert response.status_code == 200

    def test_predict_response_has_mu(self, client):
        data = client.post("/predict", json={
            "features": {"momentum": 0.3},
        }).json()
        assert "mu" in data

    def test_predict_response_has_sigma(self, client):
        data = client.post("/predict", json={
            "features": {"momentum": 0.3},
        }).json()
        assert "sigma" in data

    def test_predict_response_has_confidence(self, client):
        data = client.post("/predict", json={
            "features": {"momentum": 0.3},
        }).json()
        assert "confidence" in data

    def test_predict_response_has_uncertainty(self, client):
        data = client.post("/predict", json={
            "features": {"momentum": 0.3},
        }).json()
        assert "uncertainty" in data
        u = data["uncertainty"]
        assert "aleatoric" in u
        assert "epistemic_model" in u
        assert "epistemic_data" in u
        assert "total" in u

    def test_predict_response_has_regime(self, client):
        data = client.post("/predict", json={
            "features": {"x": 1.0},
            "regime": "CRISIS",
        }).json()
        assert data["regime"] == "CRISIS"

    def test_predict_response_has_ood_fields(self, client):
        data = client.post("/predict", json={
            "features": {"x": 1.0},
        }).json()
        assert "is_ood" in data
        assert "ood_score" in data

    def test_predict_response_has_quality_score(self, client):
        data = client.post("/predict", json={
            "features": {"x": 1.0},
        }).json()
        assert "quality_score" in data

    def test_predict_forced_deep_path(self, client):
        data = client.post("/predict", json={
            "features": {"momentum": 0.01},
            "force_deep_path": True,
        }).json()
        assert data["deep_path_used"] is True

    def test_predict_missing_features_key(self, client):
        response = client.post("/predict", json={})
        assert response.status_code == 422

    def test_predict_invalid_meta_uncertainty(self, client):
        response = client.post("/predict", json={
            "features": {"x": 1.0},
            "meta_uncertainty": 5.0,
        })
        assert response.status_code == 422

    def test_predict_empty_features(self, client):
        response = client.post("/predict", json={
            "features": {},
        })
        assert response.status_code == 200

    def test_predict_default_regime_is_risk_on(self, client):
        data = client.post("/predict", json={
            "features": {"x": 1.0},
        }).json()
        assert data["regime"] == "RISK_ON"


# =============================================================================
# Predict Disabled
# =============================================================================

class TestPredictDisabled:
    """Tests for prediction when system is in NOTFALL mode."""

    def test_notfall_returns_503(self, client):
        set_system_zustand(SystemZustand(
            ece=0.0,
            ood_score=0.9,  # > OOD_NOTFALL_THRESHOLD (0.8) -> NOTFALL
            datenverlust_ratio=0.0,
            entscheidungs_count=100,
            aktive_rekalibrierung=False,
            meta_unsicherheit_u=0.0,
        ))
        response = client.post("/predict", json={
            "features": {"x": 1.0},
        })
        assert response.status_code == 503

    def test_kaltstart_returns_503(self, client):
        set_system_zustand(SystemZustand(
            ece=0.0,
            ood_score=0.0,
            datenverlust_ratio=0.0,
            entscheidungs_count=10,  # < KALTSTART_ENTSCHEIDUNGS_MINIMUM (50)
            aktive_rekalibrierung=False,
            meta_unsicherheit_u=0.0,
        ))
        response = client.post("/predict", json={
            "features": {"x": 1.0},
        })
        assert response.status_code == 503

    def test_konfidenz_kollaps_returns_503(self, client):
        set_system_zustand(SystemZustand(
            ece=0.0,
            ood_score=0.0,
            datenverlust_ratio=0.0,
            entscheidungs_count=100,
            aktive_rekalibrierung=False,
            meta_unsicherheit_u=0.8,  # > META_U_KOLLAPS (0.7)
        ))
        response = client.post("/predict", json={
            "features": {"x": 1.0},
        })
        assert response.status_code == 503


# =============================================================================
# Feedback
# =============================================================================

class TestFeedback:
    """Tests for POST /feedback."""

    def test_feedback_valid(self, client):
        response = client.post("/feedback", json={
            "prediction_id": "pred-001",
            "benutzer_aktion": "GEFOLGT",
            "ergebnis": "ERFOLG",
            "konfidenz": 0.8,
            "tatsaechliches_ergebnis": 0.5,
            "vorhersage_fehler": 0.1,
        })
        assert response.status_code == 200

    def test_feedback_returns_prediction_id(self, client):
        data = client.post("/feedback", json={
            "prediction_id": "pred-002",
            "benutzer_aktion": "IGNORIERT",
            "ergebnis": "NEUTRAL",
        }).json()
        assert data["prediction_id"] == "pred-002"

    def test_feedback_returns_label(self, client):
        data = client.post("/feedback", json={
            "prediction_id": "pred-003",
            "benutzer_aktion": "GEFOLGT",
            "ergebnis": "ERFOLG",
            "konfidenz": 0.9,
            "vorhersage_fehler": 0.05,
        }).json()
        assert "label_wert" in data
        assert "label_unsicherheit" in data
        assert data["accepted"] is True

    def test_feedback_invalid_action(self, client):
        response = client.post("/feedback", json={
            "prediction_id": "pred-004",
            "benutzer_aktion": "INVALID",
            "ergebnis": "ERFOLG",
        })
        assert response.status_code == 422

    def test_feedback_invalid_outcome(self, client):
        response = client.post("/feedback", json={
            "prediction_id": "pred-005",
            "benutzer_aktion": "GEFOLGT",
            "ergebnis": "INVALID",
        })
        assert response.status_code == 422

    def test_feedback_gegenteil_fehler(self, client):
        data = client.post("/feedback", json={
            "prediction_id": "pred-006",
            "benutzer_aktion": "GEGENTEIL",
            "ergebnis": "FEHLER",
            "konfidenz": 0.5,
            "vorhersage_fehler": 0.2,
        }).json()
        assert data["accepted"] is True


# =============================================================================
# Status
# =============================================================================

class TestStatus:
    """Tests for GET /status."""

    def test_status_returns_200(self, client):
        response = client.get("/status")
        assert response.status_code == 200

    def test_status_has_modus(self, client):
        data = client.get("/status").json()
        assert "modus" in data
        assert data["modus"] == "NORMAL"

    def test_status_has_all_fields(self, client):
        data = client.get("/status").json()
        assert "vorhersagen_aktiv" in data
        assert "konfidenz_multiplikator" in data
        assert "ece" in data
        assert "ood_score" in data
        assert "meta_unsicherheit" in data
        assert "entscheidungs_count" in data

    def test_status_reflects_state_change(self, client):
        set_system_zustand(SystemZustand(
            ece=0.06,  # > ECE_KRISE_THRESHOLD
            ood_score=0.0,
            datenverlust_ratio=0.0,
            entscheidungs_count=100,
            aktive_rekalibrierung=False,
            meta_unsicherheit_u=0.0,
        ))
        data = client.get("/status").json()
        assert data["modus"] == "KRISE"
        assert data["ece"] == 0.06


# =============================================================================
# Metrics
# =============================================================================

class TestMetrics:
    """Tests for GET /metrics."""

    def test_metrics_returns_200(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_has_all_components(self, client):
        data = client.get("/metrics").json()
        assert "quality_score" in data
        assert "calibration_component" in data
        assert "confidence_component" in data
        assert "stability_component" in data
        assert "data_quality_component" in data
        assert "regime_component" in data

    def test_metrics_quality_score_in_range(self, client):
        data = client.get("/metrics").json()
        assert 0.0 <= data["quality_score"] <= 1.0

    def test_metrics_components_in_range(self, client):
        data = client.get("/metrics").json()
        for key in [
            "calibration_component", "confidence_component",
            "stability_component", "data_quality_component",
            "regime_component",
        ]:
            assert 0.0 <= data[key] <= 1.0, f"{key} out of [0, 1]: {data[key]}"
