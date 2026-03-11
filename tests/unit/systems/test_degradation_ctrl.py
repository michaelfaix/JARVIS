# =============================================================================
# tests/unit/systems/test_degradation_ctrl.py
# Tests for jarvis/systems/degradation_ctrl.py (S13 Degradation Controller)
# =============================================================================

import math

import pytest

from jarvis.systems.degradation_ctrl import (
    # Enums
    SystemModus,
    # Dataclasses
    SystemZustand,
    ModusKonfiguration,
    DegradationResult,
    # Constants
    MODUS_KONFIGURATIONEN,
    ECE_KONSERVATIV_THRESHOLD,
    ECE_KRISE_THRESHOLD,
    OOD_ERHOEHTE_THRESHOLD,
    OOD_KRISE_THRESHOLD,
    OOD_NOTFALL_THRESHOLD,
    META_U_KONSERVATIV,
    META_U_KRISE,
    META_U_KOLLAPS,
    DATENVERLUST_MINIMAL_THRESHOLD,
    DATENVERLUST_NOTFALL_THRESHOLD,
    KALTSTART_ENTSCHEIDUNGS_MINIMUM,
    # Class
    DegradationsController,
)


# =============================================================================
# HELPERS
# =============================================================================

def _healthy_zustand(**overrides) -> SystemZustand:
    """Return a healthy SystemZustand with all values in NORMAL range."""
    defaults = dict(
        ece=0.01,
        ood_score=0.1,
        datenverlust_ratio=0.05,
        entscheidungs_count=100,
        aktive_rekalibrierung=False,
        meta_unsicherheit_u=0.1,
    )
    defaults.update(overrides)
    return SystemZustand(**defaults)


# =============================================================================
# SECTION 1 -- TestSystemModus
# =============================================================================

class TestSystemModus:
    def test_has_9_members(self):
        assert len(SystemModus) == 9

    def test_normal(self):
        assert SystemModus.NORMAL.value == "NORMAL"

    def test_konservativ(self):
        assert SystemModus.KONSERVATIV.value == "KONSERVATIV"

    def test_erhoehte_wachsamkeit(self):
        assert SystemModus.ERHOEHTE_WACHSAMKEIT.value == "ERHOEHTE_WACHSAMKEIT"

    def test_krise(self):
        assert SystemModus.KRISE.value == "KRISE"

    def test_minimal(self):
        assert SystemModus.MINIMAL.value == "MINIMAL"

    def test_notfall(self):
        assert SystemModus.NOTFALL.value == "NOTFALL"

    def test_rekalibrierung(self):
        assert SystemModus.REKALIBRIERUNG.value == "REKALIBRIERUNG"

    def test_kaltstart(self):
        assert SystemModus.KALTSTART.value == "KALTSTART"

    def test_konfidenz_kollaps(self):
        assert SystemModus.KONFIDENZ_KOLLAPS.value == "KONFIDENZ_KOLLAPS"

    def test_enum_membership(self):
        for m in SystemModus:
            assert isinstance(m, SystemModus)


# =============================================================================
# SECTION 2 -- TestSystemZustand
# =============================================================================

class TestSystemZustand:
    def test_frozen(self):
        z = _healthy_zustand()
        with pytest.raises(AttributeError):
            z.ece = 0.5

    def test_all_fields_present(self):
        z = _healthy_zustand()
        assert hasattr(z, "ece")
        assert hasattr(z, "ood_score")
        assert hasattr(z, "datenverlust_ratio")
        assert hasattr(z, "entscheidungs_count")
        assert hasattr(z, "aktive_rekalibrierung")
        assert hasattr(z, "meta_unsicherheit_u")

    def test_nan_ece_rejected(self):
        with pytest.raises(ValueError, match="finite"):
            SystemZustand(
                ece=float("nan"), ood_score=0.1, datenverlust_ratio=0.0,
                entscheidungs_count=100, aktive_rekalibrierung=False,
                meta_unsicherheit_u=0.1,
            )

    def test_inf_ood_score_rejected(self):
        with pytest.raises(ValueError, match="finite"):
            SystemZustand(
                ece=0.01, ood_score=float("inf"), datenverlust_ratio=0.0,
                entscheidungs_count=100, aktive_rekalibrierung=False,
                meta_unsicherheit_u=0.1,
            )

    def test_nan_datenverlust_rejected(self):
        with pytest.raises(ValueError, match="finite"):
            SystemZustand(
                ece=0.01, ood_score=0.1, datenverlust_ratio=float("nan"),
                entscheidungs_count=100, aktive_rekalibrierung=False,
                meta_unsicherheit_u=0.1,
            )

    def test_inf_meta_u_rejected(self):
        with pytest.raises(ValueError, match="finite"):
            SystemZustand(
                ece=0.01, ood_score=0.1, datenverlust_ratio=0.0,
                entscheidungs_count=100, aktive_rekalibrierung=False,
                meta_unsicherheit_u=float("-inf"),
            )

    def test_string_ece_rejected(self):
        with pytest.raises(TypeError, match="numeric"):
            SystemZustand(
                ece="bad", ood_score=0.1, datenverlust_ratio=0.0,
                entscheidungs_count=100, aktive_rekalibrierung=False,
                meta_unsicherheit_u=0.1,
            )

    def test_float_entscheidungs_count_rejected(self):
        with pytest.raises(TypeError, match="int"):
            SystemZustand(
                ece=0.01, ood_score=0.1, datenverlust_ratio=0.0,
                entscheidungs_count=100.5, aktive_rekalibrierung=False,
                meta_unsicherheit_u=0.1,
            )

    def test_string_aktive_rekalibrierung_rejected(self):
        with pytest.raises(TypeError, match="bool"):
            SystemZustand(
                ece=0.01, ood_score=0.1, datenverlust_ratio=0.0,
                entscheidungs_count=100, aktive_rekalibrierung="yes",
                meta_unsicherheit_u=0.1,
            )


# =============================================================================
# SECTION 3 -- TestModusKonfiguration
# =============================================================================

class TestModusKonfiguration:
    def test_frozen(self):
        mk = ModusKonfiguration(
            vorhersagen_aktiv=True, konfidenz_multiplikator=1.0,
            deep_path_erzwungen=False, warnungen_prominent=False,
            rekalibrierung_ausloesen=False,
        )
        with pytest.raises(AttributeError):
            mk.vorhersagen_aktiv = False

    def test_all_fields_present(self):
        mk = ModusKonfiguration(
            vorhersagen_aktiv=True, konfidenz_multiplikator=0.5,
            deep_path_erzwungen=True, warnungen_prominent=True,
            rekalibrierung_ausloesen=True,
        )
        assert mk.vorhersagen_aktiv is True
        assert mk.konfidenz_multiplikator == 0.5
        assert mk.deep_path_erzwungen is True
        assert mk.warnungen_prominent is True
        assert mk.rekalibrierung_ausloesen is True


# =============================================================================
# SECTION 4 -- TestDegradationResult
# =============================================================================

class TestDegradationResult:
    def test_frozen(self):
        z = _healthy_zustand()
        dr = DegradationResult(
            modus=SystemModus.NORMAL,
            konfiguration=MODUS_KONFIGURATIONEN[SystemModus.NORMAL],
            zustand=z,
            grund="test",
        )
        with pytest.raises(AttributeError):
            dr.modus = SystemModus.KRISE

    def test_all_fields_present(self):
        z = _healthy_zustand()
        dr = DegradationResult(
            modus=SystemModus.NORMAL,
            konfiguration=MODUS_KONFIGURATIONEN[SystemModus.NORMAL],
            zustand=z,
            grund="test reason",
        )
        assert dr.modus == SystemModus.NORMAL
        assert isinstance(dr.konfiguration, ModusKonfiguration)
        assert dr.zustand is z
        assert dr.grund == "test reason"


# =============================================================================
# SECTION 5 -- TestConstants
# =============================================================================

class TestConstants:
    def test_modus_konfigurationen_has_9_entries(self):
        assert len(MODUS_KONFIGURATIONEN) == 9

    def test_all_modes_have_configuration(self):
        for m in SystemModus:
            assert m in MODUS_KONFIGURATIONEN

    def test_ece_konservativ_threshold(self):
        assert ECE_KONSERVATIV_THRESHOLD == 0.03

    def test_ece_krise_threshold(self):
        assert ECE_KRISE_THRESHOLD == 0.05

    def test_ood_erhoehte_threshold(self):
        assert OOD_ERHOEHTE_THRESHOLD == 0.4

    def test_ood_krise_threshold(self):
        assert OOD_KRISE_THRESHOLD == 0.6

    def test_ood_notfall_threshold(self):
        assert OOD_NOTFALL_THRESHOLD == 0.8

    def test_meta_u_konservativ(self):
        assert META_U_KONSERVATIV == 0.3

    def test_meta_u_krise(self):
        assert META_U_KRISE == 0.5

    def test_meta_u_kollaps(self):
        assert META_U_KOLLAPS == 0.7

    def test_datenverlust_minimal_threshold(self):
        assert DATENVERLUST_MINIMAL_THRESHOLD == 0.3

    def test_datenverlust_notfall_threshold(self):
        assert DATENVERLUST_NOTFALL_THRESHOLD == 0.5

    def test_kaltstart_entscheidungs_minimum(self):
        assert KALTSTART_ENTSCHEIDUNGS_MINIMUM == 50


# =============================================================================
# SECTION 6 -- TestModeConfigurations
# =============================================================================

class TestModeConfigurations:
    def test_normal_predictions_active(self):
        cfg = MODUS_KONFIGURATIONEN[SystemModus.NORMAL]
        assert cfg.vorhersagen_aktiv is True

    def test_normal_multiplier_is_one(self):
        cfg = MODUS_KONFIGURATIONEN[SystemModus.NORMAL]
        assert cfg.konfidenz_multiplikator == 1.0

    def test_notfall_predictions_disabled(self):
        cfg = MODUS_KONFIGURATIONEN[SystemModus.NOTFALL]
        assert cfg.vorhersagen_aktiv is False

    def test_notfall_multiplier_zero(self):
        cfg = MODUS_KONFIGURATIONEN[SystemModus.NOTFALL]
        assert cfg.konfidenz_multiplikator == 0.0

    def test_konfidenz_kollaps_predictions_disabled(self):
        cfg = MODUS_KONFIGURATIONEN[SystemModus.KONFIDENZ_KOLLAPS]
        assert cfg.vorhersagen_aktiv is False

    def test_konfidenz_kollaps_multiplier_zero(self):
        cfg = MODUS_KONFIGURATIONEN[SystemModus.KONFIDENZ_KOLLAPS]
        assert cfg.konfidenz_multiplikator == 0.0

    def test_kaltstart_predictions_disabled(self):
        cfg = MODUS_KONFIGURATIONEN[SystemModus.KALTSTART]
        assert cfg.vorhersagen_aktiv is False

    def test_multiplier_decreasing_with_severity(self):
        """Multiplier decreases: NORMAL > KONSERVATIV > ERHOEHTE > KRISE > MINIMAL."""
        ordered = [
            SystemModus.NORMAL,
            SystemModus.KONSERVATIV,
            SystemModus.ERHOEHTE_WACHSAMKEIT,
            SystemModus.KRISE,
            SystemModus.MINIMAL,
        ]
        multipliers = [
            MODUS_KONFIGURATIONEN[m].konfidenz_multiplikator for m in ordered
        ]
        for i in range(len(multipliers) - 1):
            assert multipliers[i] > multipliers[i + 1], (
                f"{ordered[i].value} multiplier ({multipliers[i]}) should be "
                f"> {ordered[i+1].value} multiplier ({multipliers[i+1]})"
            )


# =============================================================================
# SECTION 7 -- TestDegradationsController (mode evaluation)
# =============================================================================

class TestDegradationsController:
    def setup_method(self):
        self.ctrl = DegradationsController()

    # -- NORMAL --
    def test_normal_all_healthy(self):
        z = _healthy_zustand()
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.NORMAL

    # -- KONSERVATIV --
    def test_konservativ_ece_elevated(self):
        z = _healthy_zustand(ece=0.04)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KONSERVATIV

    def test_konservativ_meta_u_elevated(self):
        z = _healthy_zustand(meta_unsicherheit_u=0.35)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KONSERVATIV

    # -- ERHOEHTE_WACHSAMKEIT --
    def test_erhoehte_wachsamkeit_ood_moderate(self):
        z = _healthy_zustand(ood_score=0.5)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.ERHOEHTE_WACHSAMKEIT

    # -- KRISE --
    def test_krise_ece_high(self):
        z = _healthy_zustand(ece=0.06)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KRISE

    def test_krise_ood_high(self):
        z = _healthy_zustand(ood_score=0.65)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KRISE

    def test_krise_meta_u_high(self):
        z = _healthy_zustand(meta_unsicherheit_u=0.55)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KRISE

    # -- MINIMAL --
    def test_minimal_data_loss(self):
        z = _healthy_zustand(datenverlust_ratio=0.35)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.MINIMAL

    # -- NOTFALL --
    def test_notfall_ood_extreme(self):
        z = _healthy_zustand(ood_score=0.85)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.NOTFALL

    def test_notfall_data_loss_extreme(self):
        z = _healthy_zustand(datenverlust_ratio=0.55)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.NOTFALL

    # -- REKALIBRIERUNG --
    def test_rekalibrierung_active(self):
        z = _healthy_zustand(aktive_rekalibrierung=True)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.REKALIBRIERUNG

    # -- KALTSTART --
    def test_kaltstart_low_decisions(self):
        z = _healthy_zustand(entscheidungs_count=10)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KALTSTART

    def test_kaltstart_zero_decisions(self):
        z = _healthy_zustand(entscheidungs_count=0)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KALTSTART

    # -- KONFIDENZ_KOLLAPS --
    def test_konfidenz_kollaps_meta_u_extreme(self):
        z = _healthy_zustand(meta_unsicherheit_u=0.75)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KONFIDENZ_KOLLAPS

    # -- Result contains reason --
    def test_result_has_reason_string(self):
        z = _healthy_zustand()
        result = self.ctrl.evaluate(z)
        assert isinstance(result.grund, str)
        assert len(result.grund) > 0

    # -- Result contains zustand --
    def test_result_contains_zustand(self):
        z = _healthy_zustand()
        result = self.ctrl.evaluate(z)
        assert result.zustand is z

    # -- TypeError on bad input --
    def test_evaluate_rejects_non_zustand(self):
        with pytest.raises(TypeError):
            self.ctrl.evaluate("not a zustand")


# =============================================================================
# SECTION 8 -- TestPriorityOrder
# =============================================================================

class TestPriorityOrder:
    def setup_method(self):
        self.ctrl = DegradationsController()

    def test_konfidenz_kollaps_overrides_notfall(self):
        """KONFIDENZ_KOLLAPS (prio 1) wins over NOTFALL conditions (prio 2)."""
        z = _healthy_zustand(
            meta_unsicherheit_u=0.75,  # triggers KONFIDENZ_KOLLAPS
            ood_score=0.85,            # would trigger NOTFALL
        )
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KONFIDENZ_KOLLAPS

    def test_notfall_overrides_krise(self):
        """NOTFALL (prio 2) wins over KRISE conditions (prio 5)."""
        z = _healthy_zustand(
            ood_score=0.85,            # triggers NOTFALL
            ece=0.06,                  # would trigger KRISE
        )
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.NOTFALL

    def test_kaltstart_overrides_rekalibrierung(self):
        """KALTSTART (prio 3) wins over REKALIBRIERUNG (prio 4)."""
        z = _healthy_zustand(
            entscheidungs_count=10,    # triggers KALTSTART
            aktive_rekalibrierung=True, # would trigger REKALIBRIERUNG
        )
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KALTSTART

    def test_rekalibrierung_overrides_krise(self):
        """REKALIBRIERUNG (prio 4) wins over KRISE conditions (prio 5)."""
        z = _healthy_zustand(
            aktive_rekalibrierung=True,  # triggers REKALIBRIERUNG
            ece=0.06,                    # would trigger KRISE
        )
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.REKALIBRIERUNG

    def test_krise_overrides_minimal(self):
        """KRISE (prio 5) wins over MINIMAL (prio 6)."""
        z = _healthy_zustand(
            ece=0.06,                  # triggers KRISE
            datenverlust_ratio=0.35,   # would trigger MINIMAL
        )
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KRISE

    def test_minimal_overrides_erhoehte(self):
        """MINIMAL (prio 6) wins over ERHOEHTE_WACHSAMKEIT (prio 7)."""
        z = _healthy_zustand(
            datenverlust_ratio=0.35,   # triggers MINIMAL
            ood_score=0.45,            # would trigger ERHOEHTE_WACHSAMKEIT
        )
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.MINIMAL

    def test_erhoehte_overrides_konservativ(self):
        """ERHOEHTE_WACHSAMKEIT (prio 7) wins over KONSERVATIV (prio 8)."""
        z = _healthy_zustand(
            ood_score=0.45,            # triggers ERHOEHTE_WACHSAMKEIT
            ece=0.04,                  # would trigger KONSERVATIV
        )
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.ERHOEHTE_WACHSAMKEIT

    def test_konfidenz_kollaps_overrides_all(self):
        """KONFIDENZ_KOLLAPS (prio 1) wins over everything."""
        z = SystemZustand(
            ece=0.06,
            ood_score=0.85,
            datenverlust_ratio=0.55,
            entscheidungs_count=10,
            aktive_rekalibrierung=True,
            meta_unsicherheit_u=0.75,
        )
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KONFIDENZ_KOLLAPS


# =============================================================================
# SECTION 9 -- TestIsPredictionsSafe
# =============================================================================

class TestIsPredictionsSafe:
    def setup_method(self):
        self.ctrl = DegradationsController()

    def test_normal_is_safe(self):
        z = _healthy_zustand()
        assert self.ctrl.is_predictions_safe(z) is True

    def test_konservativ_is_safe(self):
        z = _healthy_zustand(ece=0.04)
        assert self.ctrl.is_predictions_safe(z) is True

    def test_notfall_is_not_safe(self):
        z = _healthy_zustand(ood_score=0.85)
        assert self.ctrl.is_predictions_safe(z) is False

    def test_konfidenz_kollaps_is_not_safe(self):
        z = _healthy_zustand(meta_unsicherheit_u=0.75)
        assert self.ctrl.is_predictions_safe(z) is False

    def test_kaltstart_is_not_safe(self):
        z = _healthy_zustand(entscheidungs_count=10)
        assert self.ctrl.is_predictions_safe(z) is False


# =============================================================================
# SECTION 10 -- TestGetConfiguration
# =============================================================================

class TestGetConfiguration:
    def setup_method(self):
        self.ctrl = DegradationsController()

    def test_each_mode_returns_correct_config(self):
        for m in SystemModus:
            cfg = self.ctrl.get_configuration(m)
            assert cfg is MODUS_KONFIGURATIONEN[m]

    def test_rejects_non_enum(self):
        with pytest.raises(TypeError):
            self.ctrl.get_configuration("NORMAL")

    def test_normal_config(self):
        cfg = self.ctrl.get_configuration(SystemModus.NORMAL)
        assert cfg.vorhersagen_aktiv is True
        assert cfg.konfidenz_multiplikator == 1.0
        assert cfg.deep_path_erzwungen is False

    def test_notfall_config(self):
        cfg = self.ctrl.get_configuration(SystemModus.NOTFALL)
        assert cfg.vorhersagen_aktiv is False
        assert cfg.konfidenz_multiplikator == 0.0
        assert cfg.deep_path_erzwungen is True
        assert cfg.rekalibrierung_ausloesen is True


# =============================================================================
# SECTION 11 -- TestDeterminism
# =============================================================================

class TestDeterminism:
    def test_same_zustand_same_result(self):
        ctrl = DegradationsController()
        z = _healthy_zustand(ece=0.04)
        r1 = ctrl.evaluate(z)
        r2 = ctrl.evaluate(z)
        assert r1.modus == r2.modus
        assert r1.grund == r2.grund
        assert r1.konfiguration == r2.konfiguration

    def test_fresh_instances_same_result(self):
        ctrl1 = DegradationsController()
        ctrl2 = DegradationsController()
        z = _healthy_zustand(ood_score=0.85)
        r1 = ctrl1.evaluate(z)
        r2 = ctrl2.evaluate(z)
        assert r1.modus == r2.modus
        assert r1.grund == r2.grund

    def test_identical_zustand_objects_same_result(self):
        ctrl = DegradationsController()
        z1 = _healthy_zustand(meta_unsicherheit_u=0.55)
        z2 = _healthy_zustand(meta_unsicherheit_u=0.55)
        r1 = ctrl.evaluate(z1)
        r2 = ctrl.evaluate(z2)
        assert r1.modus == r2.modus


# =============================================================================
# SECTION 12 -- TestNumericalSafety
# =============================================================================

class TestNumericalSafety:
    def test_nan_ece_raises(self):
        with pytest.raises(ValueError):
            _healthy_zustand(ece=float("nan"))

    def test_inf_ood_raises(self):
        with pytest.raises(ValueError):
            _healthy_zustand(ood_score=float("inf"))

    def test_neg_inf_meta_u_raises(self):
        with pytest.raises(ValueError):
            _healthy_zustand(meta_unsicherheit_u=float("-inf"))

    def test_nan_datenverlust_raises(self):
        with pytest.raises(ValueError):
            _healthy_zustand(datenverlust_ratio=float("nan"))


# =============================================================================
# SECTION 13 -- TestImportContract
# =============================================================================

class TestImportContract:
    def test_all_symbols_importable(self):
        import jarvis.systems.degradation_ctrl as mod
        for name in mod.__all__:
            assert hasattr(mod, name), f"__all__ lists '{name}' but it is missing"

    def test_all_list_not_empty(self):
        import jarvis.systems.degradation_ctrl as mod
        assert len(mod.__all__) > 0

    def test_all_contains_systemmodus(self):
        import jarvis.systems.degradation_ctrl as mod
        assert "SystemModus" in mod.__all__

    def test_all_contains_degradationscontroller(self):
        import jarvis.systems.degradation_ctrl as mod
        assert "DegradationsController" in mod.__all__


# =============================================================================
# SECTION 14 -- TestEdgeCases
# =============================================================================

class TestEdgeCases:
    def setup_method(self):
        self.ctrl = DegradationsController()

    def test_all_zero_zustand(self):
        z = SystemZustand(
            ece=0.0, ood_score=0.0, datenverlust_ratio=0.0,
            entscheidungs_count=0, aktive_rekalibrierung=False,
            meta_unsicherheit_u=0.0,
        )
        result = self.ctrl.evaluate(z)
        # entscheidungs_count=0 < 50 => KALTSTART
        assert result.modus == SystemModus.KALTSTART

    def test_all_max_zustand(self):
        z = SystemZustand(
            ece=1.0, ood_score=1.0, datenverlust_ratio=1.0,
            entscheidungs_count=1000, aktive_rekalibrierung=True,
            meta_unsicherheit_u=1.0,
        )
        result = self.ctrl.evaluate(z)
        # meta_unsicherheit_u=1.0 > 0.7 => KONFIDENZ_KOLLAPS (prio 1)
        assert result.modus == SystemModus.KONFIDENZ_KOLLAPS

    def test_boundary_ece_at_konservativ_threshold(self):
        """At exactly the threshold (not >), should NOT trigger KONSERVATIV."""
        z = _healthy_zustand(ece=ECE_KONSERVATIV_THRESHOLD)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.NORMAL

    def test_boundary_ece_just_above_konservativ(self):
        z = _healthy_zustand(ece=ECE_KONSERVATIV_THRESHOLD + 1e-9)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KONSERVATIV

    def test_boundary_ood_at_erhoehte_threshold(self):
        """At exactly the threshold, should NOT trigger."""
        z = _healthy_zustand(ood_score=OOD_ERHOEHTE_THRESHOLD)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.NORMAL

    def test_boundary_ood_just_above_erhoehte(self):
        z = _healthy_zustand(ood_score=OOD_ERHOEHTE_THRESHOLD + 1e-9)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.ERHOEHTE_WACHSAMKEIT

    def test_boundary_meta_u_at_kollaps_threshold(self):
        """At exactly META_U_KOLLAPS, should NOT trigger KONFIDENZ_KOLLAPS."""
        z = _healthy_zustand(meta_unsicherheit_u=META_U_KOLLAPS)
        result = self.ctrl.evaluate(z)
        # meta_u=0.7 is > META_U_KRISE (0.5), so KRISE
        assert result.modus == SystemModus.KRISE

    def test_boundary_meta_u_just_above_kollaps(self):
        z = _healthy_zustand(meta_unsicherheit_u=META_U_KOLLAPS + 1e-9)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KONFIDENZ_KOLLAPS

    def test_boundary_kaltstart_at_minimum(self):
        """At exactly the minimum (50), NOT kaltstart."""
        z = _healthy_zustand(entscheidungs_count=KALTSTART_ENTSCHEIDUNGS_MINIMUM)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.NORMAL

    def test_boundary_kaltstart_just_below(self):
        z = _healthy_zustand(entscheidungs_count=KALTSTART_ENTSCHEIDUNGS_MINIMUM - 1)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KALTSTART

    def test_negative_ece_still_normal(self):
        """Negative ECE is unusual but shouldn't trigger any mode."""
        z = _healthy_zustand(ece=-0.01)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.NORMAL

    def test_negative_entscheidungs_count_is_kaltstart(self):
        z = _healthy_zustand(entscheidungs_count=-5)
        result = self.ctrl.evaluate(z)
        assert result.modus == SystemModus.KALTSTART
