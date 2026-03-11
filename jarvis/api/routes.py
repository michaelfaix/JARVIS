# =============================================================================
# jarvis/api/routes.py — S14 API Layer Routes
#
# Authority: FAS v6.0.1, S14 (Lines ~4400-4700)
#
# FastAPI router with endpoints for prediction, feedback, status, metrics.
# This is a BOUNDARY layer — mutable in-memory state is acceptable here
# (not in computational layers).
#
# CLASSIFICATION: Tier 6 — ANALYSIS AND STRATEGY RESEARCH TOOL.
#
# DEPENDENCIES
# ------------
#   external: fastapi (APIRouter, HTTPException)
#   internal: jarvis.systems.degradation_ctrl (DegradationsController, SystemZustand)
#             jarvis.systems.quality_scorer (QualityScorer)
#             jarvis.systems.learning_engine (OnlineLearner, BenutzerFeedback,
#                 MarktFeedback, BenutzerAktion, Ergebnis)
#             jarvis.models.fast_path (FastPathEnsemble)
#             jarvis.models.uncertainty (UncertaintyLayer)
#             jarvis.models.ood_detection (OODEnsemble)
# =============================================================================

from __future__ import annotations

import math

from fastapi import APIRouter, HTTPException

from jarvis.systems.degradation_ctrl import (
    DegradationsController,
    SystemZustand,
)
from jarvis.systems.quality_scorer import QualityScorer
from jarvis.systems.learning_engine import (
    BenutzerAktion,
    BenutzerFeedback,
    Ergebnis,
    MarktFeedback,
    OnlineLearner,
)
from jarvis.models.fast_path import FastPathEnsemble
from jarvis.models.uncertainty import UncertaintyLayer
from jarvis.models.ood_detection import OODEnsemble

from .models import (
    FeedbackAnfrage,
    FeedbackAntwort,
    HealthAntwort,
    MetricsAntwort,
    SystemStatusAntwort,
    UnsicherheitsOutput,
    VorhersageAnfrage,
    VorhersageAntwort,
)

__all__ = [
    "router",
]


# =============================================================================
# SECTION 1 -- IN-MEMORY STATE (API boundary — acceptable per FAS S14)
# =============================================================================

_system_zustand = SystemZustand(
    ece=0.0,
    ood_score=0.0,
    datenverlust_ratio=0.0,
    entscheidungs_count=100,
    aktive_rekalibrierung=False,
    meta_unsicherheit_u=0.0,
)

_quality_scorer = QualityScorer()
_degradation_ctrl = DegradationsController()
_online_learner = OnlineLearner()
_prediction_counter: int = 0


def _get_system_zustand() -> SystemZustand:
    """Return the current system state. Separated for testability."""
    return _system_zustand


def set_system_zustand(zustand: SystemZustand) -> None:
    """
    Update the module-level system state.

    Used by the API layer to inject state changes (e.g. for testing
    or external health updates). Not a computational function.
    """
    global _system_zustand
    _system_zustand = zustand


# =============================================================================
# SECTION 2 -- ROUTER
# =============================================================================

router = APIRouter()


@router.get("/health")
def health() -> HealthAntwort:
    """Health check endpoint. Always returns 200."""
    return HealthAntwort()


@router.post("/predict")
def predict(anfrage: VorhersageAnfrage) -> VorhersageAntwort:
    """
    Run prediction pipeline.

    1. Check if predictions are safe (DegradationsController)
    2. Run FastPathEnsemble
    3. Compute uncertainty
    4. Check OOD (simplified — uses fast path sigma as proxy)
    5. Compute quality score
    6. Return VorhersageAntwort

    Raises HTTPException(503) if predictions are disabled.
    """
    global _prediction_counter

    zustand = _get_system_zustand()

    # Step 1: Check degradation controller
    if not _degradation_ctrl.is_predictions_safe(zustand):
        result = _degradation_ctrl.evaluate(zustand)
        raise HTTPException(
            status_code=503,
            detail=f"Predictions disabled: {result.grund}",
        )

    # Step 2: Run fast path ensemble
    ensemble = FastPathEnsemble(base_seed=42)
    fast_result = ensemble.predict(anfrage.features)

    deep_path_used = anfrage.force_deep_path or fast_result.deep_triggered

    # Step 3: Compute uncertainty decomposition
    from jarvis.models.fast_path import Prediction

    # Create predictions tuple for uncertainty layer
    pred = Prediction(mu=fast_result.mu, sigma=fast_result.sigma, confidence=0.5)
    uncertainty_layer = UncertaintyLayer()
    breakdown = uncertainty_layer.decompose((pred,))

    # Step 4: OOD check (simplified — based on sigma threshold)
    ood_score = min(1.0, fast_result.sigma * 2.0)
    is_ood = ood_score > 0.5

    # Step 5: Quality score
    quality = _quality_scorer.compute_quality(
        ece=zustand.ece,
        sigma=fast_result.sigma,
    )

    # Step 6: Confidence from inverse sigma
    confidence = 1.0 / (1.0 + fast_result.sigma) if math.isfinite(fast_result.sigma) else 0.5

    _prediction_counter += 1

    return VorhersageAntwort(
        mu=fast_result.mu,
        sigma=fast_result.sigma,
        confidence=confidence,
        deep_path_used=deep_path_used,
        uncertainty=UnsicherheitsOutput(
            aleatoric=breakdown.aleatoric,
            epistemic_model=breakdown.epistemic_model,
            epistemic_data=breakdown.epistemic_data,
            total=breakdown.total,
        ),
        quality_score=quality.total,
        regime=anfrage.regime.value,
        is_ood=is_ood,
        ood_score=ood_score,
    )


@router.post("/feedback")
def feedback(anfrage: FeedbackAnfrage) -> FeedbackAntwort:
    """
    Process user/market feedback via OnlineLearner.

    Creates BenutzerFeedback + MarktFeedback from the request,
    passes them to the OnlineLearner, and returns the hybrid label.
    """
    benutzer_fb = BenutzerFeedback(
        prediction_id=anfrage.prediction_id,
        benutzer_aktion=BenutzerAktion(anfrage.benutzer_aktion),
        ergebnis=Ergebnis(anfrage.ergebnis),
        konfidenz=anfrage.konfidenz,
    )
    markt_fb = MarktFeedback(
        prediction_id=anfrage.prediction_id,
        tatsaechliches_ergebnis=anfrage.tatsaechliches_ergebnis,
        vorhersage_fehler=anfrage.vorhersage_fehler,
    )

    label = _online_learner.process_feedback(benutzer_fb, markt_fb)

    return FeedbackAntwort(
        prediction_id=anfrage.prediction_id,
        label_wert=label.wert,
        label_unsicherheit=label.unsicherheit,
        accepted=True,
    )


@router.get("/status")
def status() -> SystemStatusAntwort:
    """Return current system status from DegradationsController."""
    zustand = _get_system_zustand()
    result = _degradation_ctrl.evaluate(zustand)

    return SystemStatusAntwort(
        modus=result.modus.value,
        vorhersagen_aktiv=result.konfiguration.vorhersagen_aktiv,
        konfidenz_multiplikator=result.konfiguration.konfidenz_multiplikator,
        ece=zustand.ece,
        ood_score=zustand.ood_score,
        meta_unsicherheit=zustand.meta_unsicherheit_u,
        entscheidungs_count=zustand.entscheidungs_count,
    )


@router.get("/metrics")
def metrics() -> MetricsAntwort:
    """Return current quality metrics from QualityScorer."""
    zustand = _get_system_zustand()
    quality = _quality_scorer.compute_quality(ece=zustand.ece)

    return MetricsAntwort(
        quality_score=quality.total,
        calibration_component=quality.calibration_component,
        confidence_component=quality.confidence_component,
        stability_component=quality.stability_component,
        data_quality_component=quality.data_quality_component,
        regime_component=quality.regime_component,
    )
