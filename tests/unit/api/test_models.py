# =============================================================================
# tests/unit/api/test_models.py — Pydantic model validation tests for S14 API
#
# Tests cover:
#   - VorhersageAnfrage: valid creation, defaults, validation
#   - VorhersageAntwort: all fields present
#   - FeedbackAnfrage: valid actions/outcomes, konfidenz range, invalid rejected
#   - FeedbackAntwort: all fields
#   - SystemStatusAntwort: all fields
#   - MetricsAntwort: all fields
#   - RegimeInput: all 5 values
#   - HealthAntwort: default values
#   - UnsicherheitsOutput: all fields
# =============================================================================

import pytest
from pydantic import ValidationError

from jarvis.api.models import (
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


# =============================================================================
# RegimeInput
# =============================================================================

class TestRegimeInput:
    """Tests for RegimeInput enum."""

    def test_risk_on(self):
        assert RegimeInput.RISK_ON.value == "RISK_ON"

    def test_risk_off(self):
        assert RegimeInput.RISK_OFF.value == "RISK_OFF"

    def test_crisis(self):
        assert RegimeInput.CRISIS.value == "CRISIS"

    def test_transition(self):
        assert RegimeInput.TRANSITION.value == "TRANSITION"

    def test_unknown(self):
        assert RegimeInput.UNKNOWN.value == "UNKNOWN"

    def test_all_five_members(self):
        assert len(RegimeInput) == 5

    def test_is_string_enum(self):
        assert isinstance(RegimeInput.RISK_ON, str)
        assert RegimeInput.RISK_ON == "RISK_ON"


# =============================================================================
# VorhersageAnfrage
# =============================================================================

class TestVorhersageAnfrage:
    """Tests for VorhersageAnfrage (prediction request)."""

    def test_valid_creation(self):
        req = VorhersageAnfrage(features={"momentum": 0.5, "volatility": 0.1})
        assert req.features == {"momentum": 0.5, "volatility": 0.1}
        assert req.regime == RegimeInput.RISK_ON
        assert req.meta_uncertainty == 0.2
        assert req.force_deep_path is False

    def test_default_regime(self):
        req = VorhersageAnfrage(features={"x": 1.0})
        assert req.regime == RegimeInput.RISK_ON

    def test_custom_regime(self):
        req = VorhersageAnfrage(features={"x": 1.0}, regime=RegimeInput.CRISIS)
        assert req.regime == RegimeInput.CRISIS

    def test_meta_uncertainty_default(self):
        req = VorhersageAnfrage(features={"x": 1.0})
        assert req.meta_uncertainty == 0.2

    def test_meta_uncertainty_valid_zero(self):
        req = VorhersageAnfrage(features={"x": 1.0}, meta_uncertainty=0.0)
        assert req.meta_uncertainty == 0.0

    def test_meta_uncertainty_valid_one(self):
        req = VorhersageAnfrage(features={"x": 1.0}, meta_uncertainty=1.0)
        assert req.meta_uncertainty == 1.0

    def test_meta_uncertainty_too_low(self):
        with pytest.raises(ValidationError):
            VorhersageAnfrage(features={"x": 1.0}, meta_uncertainty=-0.1)

    def test_meta_uncertainty_too_high(self):
        with pytest.raises(ValidationError):
            VorhersageAnfrage(features={"x": 1.0}, meta_uncertainty=1.1)

    def test_force_deep_path_true(self):
        req = VorhersageAnfrage(features={"x": 1.0}, force_deep_path=True)
        assert req.force_deep_path is True

    def test_empty_features(self):
        req = VorhersageAnfrage(features={})
        assert req.features == {}


# =============================================================================
# UnsicherheitsOutput
# =============================================================================

class TestUnsicherheitsOutput:
    """Tests for UnsicherheitsOutput."""

    def test_valid_creation(self):
        u = UnsicherheitsOutput(
            aleatoric=0.1, epistemic_model=0.05,
            epistemic_data=0.02, total=0.12,
        )
        assert u.aleatoric == 0.1
        assert u.epistemic_model == 0.05
        assert u.epistemic_data == 0.02
        assert u.total == 0.12


# =============================================================================
# VorhersageAntwort
# =============================================================================

class TestVorhersageAntwort:
    """Tests for VorhersageAntwort (prediction response)."""

    def test_all_fields_present(self):
        resp = VorhersageAntwort(
            mu=0.5, sigma=0.1, confidence=0.8,
            deep_path_used=False,
            uncertainty=UnsicherheitsOutput(
                aleatoric=0.05, epistemic_model=0.03,
                epistemic_data=0.01, total=0.06,
            ),
            quality_score=0.9,
            regime="RISK_ON",
            is_ood=False,
            ood_score=0.1,
        )
        assert resp.mu == 0.5
        assert resp.sigma == 0.1
        assert resp.confidence == 0.8
        assert resp.deep_path_used is False
        assert resp.uncertainty.aleatoric == 0.05
        assert resp.quality_score == 0.9
        assert resp.regime == "RISK_ON"
        assert resp.is_ood is False
        assert resp.ood_score == 0.1

    def test_deep_path_used_true(self):
        resp = VorhersageAntwort(
            mu=0.0, sigma=0.5, confidence=0.3,
            deep_path_used=True,
            uncertainty=UnsicherheitsOutput(
                aleatoric=0.3, epistemic_model=0.2,
                epistemic_data=0.0, total=0.4,
            ),
            quality_score=0.4,
            regime="CRISIS",
            is_ood=True,
            ood_score=0.8,
        )
        assert resp.deep_path_used is True
        assert resp.is_ood is True


# =============================================================================
# FeedbackAnfrage
# =============================================================================

class TestFeedbackAnfrage:
    """Tests for FeedbackAnfrage (feedback request)."""

    def test_valid_gefolgt_erfolg(self):
        fb = FeedbackAnfrage(
            prediction_id="pred-001",
            benutzer_aktion="GEFOLGT",
            ergebnis="ERFOLG",
        )
        assert fb.prediction_id == "pred-001"
        assert fb.benutzer_aktion == "GEFOLGT"
        assert fb.ergebnis == "ERFOLG"
        assert fb.konfidenz == 0.5
        assert fb.tatsaechliches_ergebnis == 0.0
        assert fb.vorhersage_fehler == 0.0

    def test_valid_ignoriert_neutral(self):
        fb = FeedbackAnfrage(
            prediction_id="pred-002",
            benutzer_aktion="IGNORIERT",
            ergebnis="NEUTRAL",
        )
        assert fb.benutzer_aktion == "IGNORIERT"
        assert fb.ergebnis == "NEUTRAL"

    def test_valid_gegenteil_fehler(self):
        fb = FeedbackAnfrage(
            prediction_id="pred-003",
            benutzer_aktion="GEGENTEIL",
            ergebnis="FEHLER",
        )
        assert fb.benutzer_aktion == "GEGENTEIL"
        assert fb.ergebnis == "FEHLER"

    def test_invalid_action_rejected(self):
        with pytest.raises(ValidationError):
            FeedbackAnfrage(
                prediction_id="pred-004",
                benutzer_aktion="INVALID",
                ergebnis="ERFOLG",
            )

    def test_invalid_outcome_rejected(self):
        with pytest.raises(ValidationError):
            FeedbackAnfrage(
                prediction_id="pred-005",
                benutzer_aktion="GEFOLGT",
                ergebnis="INVALID",
            )

    def test_konfidenz_range_valid_zero(self):
        fb = FeedbackAnfrage(
            prediction_id="pred-006",
            benutzer_aktion="GEFOLGT",
            ergebnis="ERFOLG",
            konfidenz=0.0,
        )
        assert fb.konfidenz == 0.0

    def test_konfidenz_range_valid_one(self):
        fb = FeedbackAnfrage(
            prediction_id="pred-007",
            benutzer_aktion="GEFOLGT",
            ergebnis="ERFOLG",
            konfidenz=1.0,
        )
        assert fb.konfidenz == 1.0

    def test_konfidenz_too_low(self):
        with pytest.raises(ValidationError):
            FeedbackAnfrage(
                prediction_id="pred-008",
                benutzer_aktion="GEFOLGT",
                ergebnis="ERFOLG",
                konfidenz=-0.1,
            )

    def test_konfidenz_too_high(self):
        with pytest.raises(ValidationError):
            FeedbackAnfrage(
                prediction_id="pred-009",
                benutzer_aktion="GEFOLGT",
                ergebnis="ERFOLG",
                konfidenz=1.1,
            )

    def test_vorhersage_fehler_negative_rejected(self):
        with pytest.raises(ValidationError):
            FeedbackAnfrage(
                prediction_id="pred-010",
                benutzer_aktion="GEFOLGT",
                ergebnis="ERFOLG",
                vorhersage_fehler=-0.1,
            )


# =============================================================================
# FeedbackAntwort
# =============================================================================

class TestFeedbackAntwort:
    """Tests for FeedbackAntwort (feedback response)."""

    def test_all_fields(self):
        resp = FeedbackAntwort(
            prediction_id="pred-001",
            label_wert=0.6,
            label_unsicherheit=0.3,
            accepted=True,
        )
        assert resp.prediction_id == "pred-001"
        assert resp.label_wert == 0.6
        assert resp.label_unsicherheit == 0.3
        assert resp.accepted is True


# =============================================================================
# SystemStatusAntwort
# =============================================================================

class TestSystemStatusAntwort:
    """Tests for SystemStatusAntwort."""

    def test_all_fields(self):
        resp = SystemStatusAntwort(
            modus="NORMAL",
            vorhersagen_aktiv=True,
            konfidenz_multiplikator=1.0,
            ece=0.02,
            ood_score=0.1,
            meta_unsicherheit=0.15,
            entscheidungs_count=500,
        )
        assert resp.modus == "NORMAL"
        assert resp.vorhersagen_aktiv is True
        assert resp.konfidenz_multiplikator == 1.0
        assert resp.ece == 0.02
        assert resp.ood_score == 0.1
        assert resp.meta_unsicherheit == 0.15
        assert resp.entscheidungs_count == 500


# =============================================================================
# MetricsAntwort
# =============================================================================

class TestMetricsAntwort:
    """Tests for MetricsAntwort."""

    def test_all_fields(self):
        resp = MetricsAntwort(
            quality_score=0.85,
            calibration_component=0.95,
            confidence_component=0.9,
            stability_component=0.8,
            data_quality_component=0.7,
            regime_component=0.6,
        )
        assert resp.quality_score == 0.85
        assert resp.calibration_component == 0.95
        assert resp.confidence_component == 0.9
        assert resp.stability_component == 0.8
        assert resp.data_quality_component == 0.7
        assert resp.regime_component == 0.6


# =============================================================================
# HealthAntwort
# =============================================================================

class TestHealthAntwort:
    """Tests for HealthAntwort."""

    def test_default_values(self):
        resp = HealthAntwort()
        assert resp.status == "ok"
        assert resp.version == "6.2.0"

    def test_custom_values(self):
        resp = HealthAntwort(status="degraded", version="7.0.0")
        assert resp.status == "degraded"
        assert resp.version == "7.0.0"
