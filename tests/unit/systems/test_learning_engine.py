# =============================================================================
# tests/unit/systems/test_learning_engine.py
# Tests for jarvis/systems/learning_engine.py (S12 Learning Engine)
# =============================================================================

import math

import pytest

from jarvis.systems.learning_engine import (
    USER_WEIGHT,
    MARKET_WEIGHT,
    ONLINE_UPDATE_THRESHOLD,
    BIAS_CHECK_INTERVAL,
    BIAS_THRESHOLD,
    PREDICTION_ERROR_FLOOR,
    BenutzerAktion,
    Ergebnis,
    BenutzerFeedback,
    MarktFeedback,
    Label,
    BiasReport,
    HybridesLabeling,
    OnlineLearner,
    BiasMonitor,
)


# =============================================================================
# HELPERS
# =============================================================================

def _make_user_fb(
    aktion=BenutzerAktion.GEFOLGT,
    ergebnis=Ergebnis.ERFOLG,
    konfidenz=0.8,
    prediction_id="pred-001",
):
    return BenutzerFeedback(
        prediction_id=prediction_id,
        benutzer_aktion=aktion,
        ergebnis=ergebnis,
        konfidenz=konfidenz,
    )


def _make_markt_fb(
    tatsaechliches_ergebnis=0.5,
    vorhersage_fehler=0.1,
    prediction_id="pred-001",
):
    return MarktFeedback(
        prediction_id=prediction_id,
        tatsaechliches_ergebnis=tatsaechliches_ergebnis,
        vorhersage_fehler=vorhersage_fehler,
    )


# =============================================================================
# SECTION 1 -- BENUTZER AKTION ENUM
# =============================================================================

class TestBenutzerAktion:
    def test_gefolgt_value(self):
        assert BenutzerAktion.GEFOLGT.value == "GEFOLGT"

    def test_ignoriert_value(self):
        assert BenutzerAktion.IGNORIERT.value == "IGNORIERT"

    def test_gegenteil_value(self):
        assert BenutzerAktion.GEGENTEIL.value == "GEGENTEIL"

    def test_enum_membership(self):
        assert len(BenutzerAktion) == 3
        members = {m.value for m in BenutzerAktion}
        assert members == {"GEFOLGT", "IGNORIERT", "GEGENTEIL"}


# =============================================================================
# SECTION 2 -- ERGEBNIS ENUM
# =============================================================================

class TestErgebnis:
    def test_erfolg_value(self):
        assert Ergebnis.ERFOLG.value == "ERFOLG"

    def test_neutral_value(self):
        assert Ergebnis.NEUTRAL.value == "NEUTRAL"

    def test_fehler_value(self):
        assert Ergebnis.FEHLER.value == "FEHLER"

    def test_enum_membership(self):
        assert len(Ergebnis) == 3


# =============================================================================
# SECTION 3 -- BENUTZER FEEDBACK DATACLASS
# =============================================================================

class TestBenutzerFeedback:
    def test_frozen(self):
        fb = _make_user_fb()
        with pytest.raises(AttributeError):
            fb.konfidenz = 0.5

    def test_valid_construction(self):
        fb = _make_user_fb(konfidenz=0.9)
        assert fb.konfidenz == 0.9
        assert fb.benutzer_aktion == BenutzerAktion.GEFOLGT
        assert fb.ergebnis == Ergebnis.ERFOLG

    def test_konfidenz_zero(self):
        fb = _make_user_fb(konfidenz=0.0)
        assert fb.konfidenz == 0.0

    def test_konfidenz_one(self):
        fb = _make_user_fb(konfidenz=1.0)
        assert fb.konfidenz == 1.0

    def test_konfidenz_out_of_range_high(self):
        with pytest.raises(ValueError, match="konfidenz"):
            _make_user_fb(konfidenz=1.1)

    def test_konfidenz_out_of_range_low(self):
        with pytest.raises(ValueError, match="konfidenz"):
            _make_user_fb(konfidenz=-0.1)

    def test_konfidenz_nan(self):
        with pytest.raises(ValueError, match="konfidenz"):
            _make_user_fb(konfidenz=float("nan"))

    def test_konfidenz_inf(self):
        with pytest.raises(ValueError, match="konfidenz"):
            _make_user_fb(konfidenz=float("inf"))


# =============================================================================
# SECTION 4 -- MARKT FEEDBACK DATACLASS
# =============================================================================

class TestMarktFeedback:
    def test_frozen(self):
        fb = _make_markt_fb()
        with pytest.raises(AttributeError):
            fb.vorhersage_fehler = 0.5

    def test_valid_construction(self):
        fb = _make_markt_fb(tatsaechliches_ergebnis=0.7, vorhersage_fehler=0.3)
        assert fb.tatsaechliches_ergebnis == 0.7
        assert fb.vorhersage_fehler == 0.3

    def test_negative_vorhersage_fehler(self):
        with pytest.raises(ValueError, match="vorhersage_fehler"):
            _make_markt_fb(vorhersage_fehler=-0.1)

    def test_nan_vorhersage_fehler(self):
        with pytest.raises(ValueError, match="vorhersage_fehler"):
            _make_markt_fb(vorhersage_fehler=float("nan"))


# =============================================================================
# SECTION 5 -- LABEL DATACLASS
# =============================================================================

class TestLabel:
    def test_frozen(self):
        label = Label(wert=0.5, unsicherheit=0.3)
        with pytest.raises(AttributeError):
            label.wert = 0.1

    def test_valid_construction(self):
        label = Label(wert=-0.5, unsicherheit=0.7)
        assert label.wert == -0.5
        assert label.unsicherheit == 0.7

    def test_wert_range_min(self):
        label = Label(wert=-1.0, unsicherheit=0.5)
        assert label.wert == -1.0

    def test_wert_range_max(self):
        label = Label(wert=1.0, unsicherheit=0.5)
        assert label.wert == 1.0

    def test_wert_out_of_range(self):
        with pytest.raises(ValueError, match="wert"):
            Label(wert=1.1, unsicherheit=0.5)

    def test_unsicherheit_out_of_range(self):
        with pytest.raises(ValueError, match="unsicherheit"):
            Label(wert=0.0, unsicherheit=1.1)

    def test_unsicherheit_negative(self):
        with pytest.raises(ValueError, match="unsicherheit"):
            Label(wert=0.0, unsicherheit=-0.1)


# =============================================================================
# SECTION 6 -- BIAS REPORT DATACLASS
# =============================================================================

class TestBiasReport:
    def test_frozen(self):
        report = BiasReport(
            experten_bias=0.0, markt_bias=0.0,
            regime_bias=0.0, is_biased=False, dominant_bias="NONE",
        )
        with pytest.raises(AttributeError):
            report.is_biased = True

    def test_is_biased_false(self):
        report = BiasReport(
            experten_bias=0.05, markt_bias=0.05,
            regime_bias=0.05, is_biased=False, dominant_bias="NONE",
        )
        assert report.is_biased is False

    def test_is_biased_true(self):
        report = BiasReport(
            experten_bias=0.2, markt_bias=0.0,
            regime_bias=0.0, is_biased=True, dominant_bias="EXPERTEN",
        )
        assert report.is_biased is True

    def test_invalid_dominant_bias(self):
        with pytest.raises(ValueError, match="dominant_bias"):
            BiasReport(
                experten_bias=0.0, markt_bias=0.0,
                regime_bias=0.0, is_biased=False, dominant_bias="INVALID",
            )

    def test_valid_dominant_bias_values(self):
        for dom in ("EXPERTEN", "MARKT", "REGIME", "NONE"):
            report = BiasReport(
                experten_bias=0.0, markt_bias=0.0,
                regime_bias=0.0, is_biased=False, dominant_bias=dom,
            )
            assert report.dominant_bias == dom

    def test_nan_experten_bias(self):
        with pytest.raises(ValueError):
            BiasReport(
                experten_bias=float("nan"), markt_bias=0.0,
                regime_bias=0.0, is_biased=False, dominant_bias="NONE",
            )


# =============================================================================
# SECTION 7 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_weights_sum_to_one(self):
        assert abs(USER_WEIGHT + MARKET_WEIGHT - 1.0) < 1e-9

    def test_user_weight(self):
        assert USER_WEIGHT == 0.6

    def test_market_weight(self):
        assert MARKET_WEIGHT == 0.4

    def test_online_update_threshold(self):
        assert ONLINE_UPDATE_THRESHOLD == 100

    def test_bias_check_interval(self):
        assert BIAS_CHECK_INTERVAL == 500

    def test_bias_threshold(self):
        assert BIAS_THRESHOLD == 0.1

    def test_prediction_error_floor(self):
        assert PREDICTION_ERROR_FLOOR == 1e-10


# =============================================================================
# SECTION 8 -- HYBRIDES LABELING
# =============================================================================

class TestHybridesLabeling:
    def setup_method(self):
        self.labeler = HybridesLabeling()

    def test_gefolgt_erfolg(self):
        label = self.labeler.create_label(
            _make_user_fb(BenutzerAktion.GEFOLGT, Ergebnis.ERFOLG, 0.8),
            _make_markt_fb(vorhersage_fehler=0.1),
        )
        # user_signal = +1.0, market_signal = -0.1
        # wert = 0.6*1.0 + 0.4*(-0.1) = 0.56
        assert abs(label.wert - 0.56) < 1e-9

    def test_gefolgt_fehler(self):
        label = self.labeler.create_label(
            _make_user_fb(BenutzerAktion.GEFOLGT, Ergebnis.FEHLER, 0.8),
            _make_markt_fb(vorhersage_fehler=0.1),
        )
        # user_signal = -0.5, market_signal = -0.1
        # wert = 0.6*(-0.5) + 0.4*(-0.1) = -0.34
        assert abs(label.wert - (-0.34)) < 1e-9

    def test_ignoriert(self):
        label = self.labeler.create_label(
            _make_user_fb(BenutzerAktion.IGNORIERT, Ergebnis.ERFOLG, 0.5),
            _make_markt_fb(vorhersage_fehler=0.0),
        )
        # user_signal = 0.0, market_signal = 0.0
        # wert = 0.0
        assert abs(label.wert) < 1e-9

    def test_gegenteil_erfolg(self):
        label = self.labeler.create_label(
            _make_user_fb(BenutzerAktion.GEGENTEIL, Ergebnis.ERFOLG, 0.9),
            _make_markt_fb(vorhersage_fehler=0.0),
        )
        # user_signal = -1.0, market_signal = 0.0
        # wert = 0.6*(-1.0) + 0.4*(0.0) = -0.6
        assert abs(label.wert - (-0.6)) < 1e-9

    def test_gegenteil_fehler(self):
        label = self.labeler.create_label(
            _make_user_fb(BenutzerAktion.GEGENTEIL, Ergebnis.FEHLER, 0.9),
            _make_markt_fb(vorhersage_fehler=0.0),
        )
        # user_signal = +0.5, market_signal = 0.0
        # wert = 0.6*0.5 = 0.3
        assert abs(label.wert - 0.3) < 1e-9

    def test_neutral_outcome_gefolgt(self):
        label = self.labeler.create_label(
            _make_user_fb(BenutzerAktion.GEFOLGT, Ergebnis.NEUTRAL, 0.8),
            _make_markt_fb(vorhersage_fehler=0.0),
        )
        # user_signal = 0.5, market_signal = 0.0
        # wert = 0.6*0.5 = 0.3
        assert abs(label.wert - 0.3) < 1e-9

    def test_neutral_outcome_gegenteil(self):
        label = self.labeler.create_label(
            _make_user_fb(BenutzerAktion.GEGENTEIL, Ergebnis.NEUTRAL, 0.8),
            _make_markt_fb(vorhersage_fehler=0.0),
        )
        # user_signal = -0.5, market_signal = 0.0
        # wert = 0.6*(-0.5) = -0.3
        assert abs(label.wert - (-0.3)) < 1e-9

    def test_confidence_effect_on_uncertainty(self):
        label_high = self.labeler.create_label(
            _make_user_fb(konfidenz=0.9),
            _make_markt_fb(vorhersage_fehler=0.1),
        )
        label_low = self.labeler.create_label(
            _make_user_fb(konfidenz=0.1),
            _make_markt_fb(vorhersage_fehler=0.1),
        )
        # Higher confidence -> lower uncertainty
        assert label_high.unsicherheit < label_low.unsicherheit

    def test_uncertainty_calculation(self):
        label = self.labeler.create_label(
            _make_user_fb(konfidenz=0.8),
            _make_markt_fb(vorhersage_fehler=0.2),
        )
        # unsicherheit = 1.0 - 0.8 * (1.0 - 0.2) = 1.0 - 0.64 = 0.36
        assert abs(label.unsicherheit - 0.36) < 1e-9

    def test_zero_confidence_uncertainty(self):
        label = self.labeler.create_label(
            _make_user_fb(konfidenz=0.0),
            _make_markt_fb(vorhersage_fehler=0.5),
        )
        # unsicherheit = 1.0 - 0.0 * 0.5 = 1.0
        assert abs(label.unsicherheit - 1.0) < 1e-9

    def test_large_market_error(self):
        label = self.labeler.create_label(
            _make_user_fb(BenutzerAktion.GEFOLGT, Ergebnis.ERFOLG, 0.5),
            _make_markt_fb(vorhersage_fehler=2.0),
        )
        # market_signal = -2.0 clamped to -1.0
        # wert = 0.6*1.0 + 0.4*(-1.0) = 0.2
        assert abs(label.wert - 0.2) < 1e-9


# =============================================================================
# SECTION 9 -- ONLINE LEARNER
# =============================================================================

class TestOnlineLearner:
    def setup_method(self):
        self.learner = OnlineLearner()

    def test_process_feedback_returns_label(self):
        label = self.learner.process_feedback(
            _make_user_fb(), _make_markt_fb()
        )
        assert isinstance(label, Label)

    def test_should_update_initially_false(self):
        assert self.learner.should_update() is False

    def test_should_update_at_threshold(self):
        for _ in range(ONLINE_UPDATE_THRESHOLD):
            self.learner.process_feedback(_make_user_fb(), _make_markt_fb())
        assert self.learner.should_update() is True

    def test_should_update_below_threshold(self):
        for _ in range(ONLINE_UPDATE_THRESHOLD - 1):
            self.learner.process_feedback(_make_user_fb(), _make_markt_fb())
        assert self.learner.should_update() is False

    def test_get_recent_labels_empty(self):
        labels = self.learner.get_recent_labels()
        assert labels == ()

    def test_get_recent_labels_returns_tuple(self):
        self.learner.process_feedback(_make_user_fb(), _make_markt_fb())
        labels = self.learner.get_recent_labels(5)
        assert isinstance(labels, tuple)
        assert len(labels) == 1

    def test_get_recent_labels_limit(self):
        for _ in range(10):
            self.learner.process_feedback(_make_user_fb(), _make_markt_fb())
        labels = self.learner.get_recent_labels(3)
        assert len(labels) == 3

    def test_get_mean_label_value_empty(self):
        assert self.learner.get_mean_label_value() == 0.0

    def test_get_mean_label_value(self):
        self.learner.process_feedback(
            _make_user_fb(BenutzerAktion.GEFOLGT, Ergebnis.ERFOLG, 0.8),
            _make_markt_fb(vorhersage_fehler=0.0),
        )
        # wert should be 0.6*1.0 + 0.4*0.0 = 0.6
        mean_val = self.learner.get_mean_label_value()
        assert abs(mean_val - 0.6) < 1e-9

    def test_get_mean_uncertainty_empty(self):
        assert self.learner.get_mean_uncertainty() == 1.0

    def test_get_mean_uncertainty(self):
        self.learner.process_feedback(
            _make_user_fb(konfidenz=1.0),
            _make_markt_fb(vorhersage_fehler=0.0),
        )
        # unsicherheit = 1.0 - 1.0 * 1.0 = 0.0
        mean_unc = self.learner.get_mean_uncertainty()
        assert abs(mean_unc - 0.0) < 1e-9

    def test_mark_updated_resets_counter(self):
        for _ in range(ONLINE_UPDATE_THRESHOLD):
            self.learner.process_feedback(_make_user_fb(), _make_markt_fb())
        assert self.learner.should_update() is True
        self.learner.mark_updated()
        assert self.learner.should_update() is False

    def test_mark_updated_allows_next_threshold(self):
        for _ in range(ONLINE_UPDATE_THRESHOLD):
            self.learner.process_feedback(_make_user_fb(), _make_markt_fb())
        self.learner.mark_updated()
        for _ in range(ONLINE_UPDATE_THRESHOLD):
            self.learner.process_feedback(_make_user_fb(), _make_markt_fb())
        assert self.learner.should_update() is True

    def test_get_recent_labels_zero_n(self):
        self.learner.process_feedback(_make_user_fb(), _make_markt_fb())
        labels = self.learner.get_recent_labels(0)
        assert labels == ()


# =============================================================================
# SECTION 10 -- BIAS MONITOR
# =============================================================================

class TestBiasMonitor:
    def setup_method(self):
        self.monitor = BiasMonitor()

    def test_should_check_initially_false(self):
        assert self.monitor.should_check() is False

    def test_should_check_at_interval(self):
        for _ in range(BIAS_CHECK_INTERVAL):
            self.monitor.record(_make_user_fb(), _make_markt_fb())
        assert self.monitor.should_check() is True

    def test_detect_bias_no_data(self):
        report = self.monitor.detect_bias()
        assert report.is_biased is False
        assert report.dominant_bias == "NONE"
        assert report.experten_bias == 0.0
        assert report.markt_bias == 0.0
        assert report.regime_bias == 0.0

    def test_detect_bias_no_bias(self):
        # All GEFOLGT + ERFOLG with small error -> some bias likely
        for _ in range(10):
            self.monitor.record(
                _make_user_fb(BenutzerAktion.GEFOLGT, Ergebnis.NEUTRAL, 0.5),
                _make_markt_fb(vorhersage_fehler=0.05),
            )
            self.monitor.record(
                _make_user_fb(BenutzerAktion.GEGENTEIL, Ergebnis.NEUTRAL, 0.5),
                _make_markt_fb(vorhersage_fehler=0.05),
            )
        report = self.monitor.detect_bias()
        # Both GEFOLGT and GEGENTEIL have NEUTRAL (score=0), so expert bias = 0
        assert abs(report.experten_bias) < 1e-9
        assert report.markt_bias == pytest.approx(0.05, abs=1e-9)

    def test_detect_bias_with_expert_bias(self):
        # GEFOLGT always succeeds, GEGENTEIL always fails
        for _ in range(10):
            self.monitor.record(
                _make_user_fb(BenutzerAktion.GEFOLGT, Ergebnis.ERFOLG, 0.8),
                _make_markt_fb(vorhersage_fehler=0.05),
            )
            self.monitor.record(
                _make_user_fb(BenutzerAktion.GEGENTEIL, Ergebnis.FEHLER, 0.8),
                _make_markt_fb(vorhersage_fehler=0.05),
            )
        report = self.monitor.detect_bias()
        # GEFOLGT mean = 1.0, GEGENTEIL mean = -1.0, bias = 2.0
        assert abs(report.experten_bias - 2.0) < 1e-9
        assert report.is_biased is True
        assert report.dominant_bias == "EXPERTEN"

    def test_detect_bias_with_market_bias(self):
        for _ in range(10):
            self.monitor.record(
                _make_user_fb(BenutzerAktion.IGNORIERT, Ergebnis.NEUTRAL, 0.5),
                _make_markt_fb(vorhersage_fehler=0.5),
            )
        report = self.monitor.detect_bias()
        # market_bias = mean(0.5) = 0.5 > BIAS_THRESHOLD
        assert abs(report.markt_bias - 0.5) < 1e-9
        assert report.is_biased is True

    def test_detect_bias_with_regime_bias(self):
        # Two regimes with very different error rates
        for _ in range(10):
            self.monitor.record(
                _make_user_fb(BenutzerAktion.IGNORIERT, Ergebnis.NEUTRAL, 0.5),
                _make_markt_fb(vorhersage_fehler=0.01),
                regime="RISK_ON",
            )
            self.monitor.record(
                _make_user_fb(BenutzerAktion.IGNORIERT, Ergebnis.NEUTRAL, 0.5),
                _make_markt_fb(vorhersage_fehler=0.9),
                regime="CRISIS",
            )
        report = self.monitor.detect_bias()
        # regime_bias = |0.01 - 0.9| = 0.89
        assert abs(report.regime_bias - 0.89) < 1e-9
        assert report.is_biased is True

    def test_dominant_bias_selection_markt(self):
        # Only market bias (IGNORIERT so no expert data split)
        for _ in range(10):
            self.monitor.record(
                _make_user_fb(BenutzerAktion.IGNORIERT, Ergebnis.NEUTRAL, 0.5),
                _make_markt_fb(vorhersage_fehler=0.8),
            )
        report = self.monitor.detect_bias()
        assert report.dominant_bias == "MARKT"

    def test_dominant_bias_regime(self):
        # Regime bias dominant
        for _ in range(5):
            self.monitor.record(
                _make_user_fb(BenutzerAktion.IGNORIERT, Ergebnis.NEUTRAL, 0.5),
                _make_markt_fb(vorhersage_fehler=0.0),
                regime="RISK_ON",
            )
            self.monitor.record(
                _make_user_fb(BenutzerAktion.IGNORIERT, Ergebnis.NEUTRAL, 0.5),
                _make_markt_fb(vorhersage_fehler=1.0),
                regime="CRISIS",
            )
        report = self.monitor.detect_bias()
        # markt_bias = mean(0.0, 1.0, 0.0, 1.0, ...) = 0.5
        # regime_bias = |0.0 - 1.0| = 1.0
        # regime is dominant
        assert report.dominant_bias == "REGIME"

    def test_record_increments_samples(self):
        self.monitor.record(_make_user_fb(), _make_markt_fb())
        assert self.monitor._total_samples == 1

    def test_single_regime_no_regime_bias(self):
        for _ in range(10):
            self.monitor.record(
                _make_user_fb(), _make_markt_fb(), regime="RISK_ON"
            )
        report = self.monitor.detect_bias()
        assert report.regime_bias == 0.0


# =============================================================================
# SECTION 11 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_same_feedback_same_label(self):
        labeler = HybridesLabeling()
        fb_u = _make_user_fb(BenutzerAktion.GEFOLGT, Ergebnis.ERFOLG, 0.75)
        fb_m = _make_markt_fb(vorhersage_fehler=0.15)
        label1 = labeler.create_label(fb_u, fb_m)
        label2 = labeler.create_label(fb_u, fb_m)
        assert label1.wert == label2.wert
        assert label1.unsicherheit == label2.unsicherheit

    def test_same_sequence_same_bias_report(self):
        def build_monitor():
            m = BiasMonitor()
            for i in range(20):
                m.record(
                    _make_user_fb(
                        BenutzerAktion.GEFOLGT, Ergebnis.ERFOLG, 0.8,
                        prediction_id=f"p-{i}",
                    ),
                    _make_markt_fb(vorhersage_fehler=0.1 * (i % 5)),
                    regime="RISK_ON" if i % 2 == 0 else "CRISIS",
                )
            return m.detect_bias()

        r1 = build_monitor()
        r2 = build_monitor()
        assert r1.experten_bias == r2.experten_bias
        assert r1.markt_bias == r2.markt_bias
        assert r1.regime_bias == r2.regime_bias
        assert r1.is_biased == r2.is_biased
        assert r1.dominant_bias == r2.dominant_bias


# =============================================================================
# SECTION 12 -- NUMERICAL SAFETY
# =============================================================================

class TestNumericalSafety:
    def test_nan_konfidenz_rejected(self):
        with pytest.raises(ValueError):
            _make_user_fb(konfidenz=float("nan"))

    def test_inf_konfidenz_rejected(self):
        with pytest.raises(ValueError):
            _make_user_fb(konfidenz=float("inf"))

    def test_extreme_prediction_error(self):
        labeler = HybridesLabeling()
        label = labeler.create_label(
            _make_user_fb(konfidenz=0.5),
            _make_markt_fb(vorhersage_fehler=1e10),
        )
        # market_signal clamped to -1.0
        # wert = 0.6*1.0 + 0.4*(-1.0) = 0.2
        assert math.isfinite(label.wert)
        assert -1.0 <= label.wert <= 1.0
        assert math.isfinite(label.unsicherheit)
        assert 0.0 <= label.unsicherheit <= 1.0

    def test_zero_prediction_error(self):
        labeler = HybridesLabeling()
        label = labeler.create_label(
            _make_user_fb(konfidenz=1.0),
            _make_markt_fb(vorhersage_fehler=0.0),
        )
        assert math.isfinite(label.wert)
        assert math.isfinite(label.unsicherheit)


# =============================================================================
# SECTION 13 -- IMPORT CONTRACT
# =============================================================================

class TestImportContract:
    def test_all_symbols_importable(self):
        import jarvis.systems.learning_engine as mod
        for name in mod.__all__:
            assert hasattr(mod, name), f"{name} in __all__ but not in module"

    def test_all_list_not_empty(self):
        import jarvis.systems.learning_engine as mod
        assert len(mod.__all__) > 0

    def test_all_expected_exports(self):
        import jarvis.systems.learning_engine as mod
        expected = {
            "USER_WEIGHT", "MARKET_WEIGHT", "ONLINE_UPDATE_THRESHOLD",
            "BIAS_CHECK_INTERVAL", "BIAS_THRESHOLD", "PREDICTION_ERROR_FLOOR",
            "BenutzerAktion", "Ergebnis",
            "BenutzerFeedback", "MarktFeedback", "Label", "BiasReport",
            "HybridesLabeling", "OnlineLearner", "BiasMonitor",
        }
        assert set(mod.__all__) == expected


# =============================================================================
# SECTION 14 -- EDGE CASES
# =============================================================================

class TestEdgeCases:
    def test_empty_monitor_detect_bias(self):
        monitor = BiasMonitor()
        report = monitor.detect_bias()
        assert report.experten_bias == 0.0
        assert report.markt_bias == 0.0
        assert report.regime_bias == 0.0
        assert report.is_biased is False

    def test_single_feedback_monitor(self):
        monitor = BiasMonitor()
        monitor.record(_make_user_fb(), _make_markt_fb(), regime="RISK_ON")
        report = monitor.detect_bias()
        assert isinstance(report, BiasReport)
        # Only one regime -> regime_bias = 0.0
        assert report.regime_bias == 0.0

    def test_all_same_outcomes(self):
        monitor = BiasMonitor()
        for _ in range(20):
            monitor.record(
                _make_user_fb(BenutzerAktion.GEFOLGT, Ergebnis.ERFOLG, 0.5),
                _make_markt_fb(vorhersage_fehler=0.1),
            )
            monitor.record(
                _make_user_fb(BenutzerAktion.GEGENTEIL, Ergebnis.ERFOLG, 0.5),
                _make_markt_fb(vorhersage_fehler=0.1),
            )
        report = monitor.detect_bias()
        # GEFOLGT mean = 1.0, GEGENTEIL mean = 1.0, bias = 0.0
        assert abs(report.experten_bias) < 1e-9

    def test_only_ignoriert_no_expert_bias(self):
        monitor = BiasMonitor()
        for _ in range(10):
            monitor.record(
                _make_user_fb(BenutzerAktion.IGNORIERT, Ergebnis.ERFOLG, 0.5),
                _make_markt_fb(vorhersage_fehler=0.05),
            )
        report = monitor.detect_bias()
        assert report.experten_bias == 0.0

    def test_online_learner_fresh_instance(self):
        l1 = OnlineLearner()
        l2 = OnlineLearner()
        l1.process_feedback(_make_user_fb(), _make_markt_fb())
        # l2 should be unaffected
        assert l2.get_mean_label_value() == 0.0
        assert len(l2.get_recent_labels()) == 0
