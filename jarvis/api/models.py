# =============================================================================
# jarvis/api/models.py — S14 API Layer Pydantic Models
#
# Authority: FAS v6.0.1, S14 (Lines ~4400-4700)
#
# Request/response models for the FastAPI-based prediction API.
# All models use Pydantic v2 BaseModel with strict validation.
#
# CLASSIFICATION: Tier 6 — ANALYSIS AND STRATEGY RESEARCH TOOL.
#   This is a BOUNDARY layer — DET constraints apply to underlying logic,
#   not to request/response serialization.
#
# DEPENDENCIES
# ------------
#   external: pydantic (BaseModel, Field)
#   stdlib:   enum
# =============================================================================

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field

__all__ = [
    "RegimeInput",
    "VorhersageAnfrage",
    "UnsicherheitsOutput",
    "VorhersageAntwort",
    "FeedbackAnfrage",
    "FeedbackAntwort",
    "SystemStatusAntwort",
    "MetricsAntwort",
    "HealthAntwort",
]


# =============================================================================
# SECTION 1 -- ENUMS
# =============================================================================

class RegimeInput(str, Enum):
    """Regime input enum for API requests. Maps to GlobalRegimeState values."""
    RISK_ON = "RISK_ON"
    RISK_OFF = "RISK_OFF"
    CRISIS = "CRISIS"
    TRANSITION = "TRANSITION"
    UNKNOWN = "UNKNOWN"


# =============================================================================
# SECTION 2 -- REQUEST MODELS
# =============================================================================

class VorhersageAnfrage(BaseModel):
    """Prediction request."""
    features: Dict[str, float]
    regime: RegimeInput = RegimeInput.RISK_ON
    meta_uncertainty: float = Field(default=0.2, ge=0.0, le=1.0)
    force_deep_path: bool = False


class FeedbackAnfrage(BaseModel):
    """Feedback request."""
    prediction_id: str
    benutzer_aktion: str = Field(..., pattern=r"^(GEFOLGT|IGNORIERT|GEGENTEIL)$")
    ergebnis: str = Field(..., pattern=r"^(ERFOLG|NEUTRAL|FEHLER)$")
    konfidenz: float = Field(default=0.5, ge=0.0, le=1.0)
    tatsaechliches_ergebnis: float = 0.0
    vorhersage_fehler: float = Field(default=0.0, ge=0.0)


# =============================================================================
# SECTION 3 -- RESPONSE MODELS
# =============================================================================

class UnsicherheitsOutput(BaseModel):
    """Uncertainty breakdown in response."""
    aleatoric: float
    epistemic_model: float
    epistemic_data: float
    total: float


class VorhersageAntwort(BaseModel):
    """Prediction response."""
    mu: float
    sigma: float
    confidence: float
    deep_path_used: bool
    uncertainty: UnsicherheitsOutput
    quality_score: float
    regime: str
    is_ood: bool
    ood_score: float


class FeedbackAntwort(BaseModel):
    """Feedback response."""
    prediction_id: str
    label_wert: float
    label_unsicherheit: float
    accepted: bool


class SystemStatusAntwort(BaseModel):
    """System status response."""
    modus: str
    vorhersagen_aktiv: bool
    konfidenz_multiplikator: float
    ece: float
    ood_score: float
    meta_unsicherheit: float
    entscheidungs_count: int


class MetricsAntwort(BaseModel):
    """Metrics response."""
    quality_score: float
    calibration_component: float
    confidence_component: float
    stability_component: float
    data_quality_component: float
    regime_component: float


class HealthAntwort(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "6.2.0"
