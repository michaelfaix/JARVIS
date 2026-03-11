# tests/unit/utils/test_exceptions.py
# Unit tests for jarvis/utils/exceptions.py

import pytest

from jarvis.utils.exceptions import (
    FehlerCode,
    NumericalInstabilityError,
    CalibrationGateViolation,
    ThresholdViolation,
    ContractViolation,
    OODConsensusViolation,
)


# ---------------------------------------------------------------------------
# FehlerCode: completeness
# ---------------------------------------------------------------------------

class TestFehlerCodeCompleteness:
    """Verify all 27 error codes are present and in the correct ranges."""

    def test_total_error_code_count(self):
        """FehlerCode must have exactly 30 error codes (7 layers)."""
        codes = [
            attr for attr in dir(FehlerCode)
            if not attr.startswith("_") and isinstance(getattr(FehlerCode, attr), int)
        ]
        assert len(codes) == 30

    # --- Daten-Layer (1xxx) ---

    def test_daten_layer_codes_exist(self):
        assert FehlerCode.DATENQUELLE_NICHT_VERFUEGBAR == 1001
        assert FehlerCode.DATEN_VALIDIERUNG_FEHLER == 1002
        assert FehlerCode.DATEN_VERALTET == 1003
        assert FehlerCode.DATEN_UNVOLLSTAENDIG == 1004
        assert FehlerCode.DATEN_NAN_INF == 1005

    def test_daten_layer_range(self):
        daten_codes = [1001, 1002, 1003, 1004, 1005]
        for code in daten_codes:
            assert 1000 <= code < 2000

    # --- Feature-Layer (2xxx) ---

    def test_feature_layer_codes_exist(self):
        assert FehlerCode.FEATURE_BERECHNUNG_FEHLER == 2001
        assert FehlerCode.FEATURE_DRIFT_ERKANNT == 2002
        assert FehlerCode.FEATURE_FEHLEND == 2003
        assert FehlerCode.FEATURE_NAN_INF == 2004

    def test_feature_layer_range(self):
        feature_codes = [2001, 2002, 2003, 2004]
        for code in feature_codes:
            assert 2000 <= code < 3000

    # --- Modell-Layer (3xxx) ---

    def test_modell_layer_codes_exist(self):
        assert FehlerCode.MODELL_VORHERSAGE_FEHLER == 3001
        assert FehlerCode.MODELL_DIVERGENZ_ERKANNT == 3002
        assert FehlerCode.MODELL_UEBERANPASSUNG == 3003
        assert FehlerCode.NUMERISCHE_INSTABILITAET == 3004
        assert FehlerCode.SYSTEMVERTRAG_VERLETZUNG == 3005

    def test_modell_layer_range(self):
        modell_codes = [3001, 3002, 3003, 3004, 3005]
        for code in modell_codes:
            assert 3000 <= code < 4000

    # --- Kalibrierungs-Layer (4xxx) ---

    def test_kalibrierung_layer_codes_exist(self):
        assert FehlerCode.KALIBRIERUNG_FEHLGESCHLAGEN == 4001
        assert FehlerCode.ECE_SCHWELLENWERT_UEBERSCHRITTEN == 4002
        assert FehlerCode.REKALIBRIERUNG_NOETIG == 4003
        assert FehlerCode.KALIBRIERUNG_GATE_BLOCKIERT == 4004

    def test_kalibrierung_layer_range(self):
        kal_codes = [4001, 4002, 4003, 4004]
        for code in kal_codes:
            assert 4000 <= code < 5000

    # --- OOD-Layer (5xxx) ---

    def test_ood_layer_codes_exist(self):
        assert FehlerCode.OOD_HOCH == 5001
        assert FehlerCode.OOD_KRITISCH == 5002
        assert FehlerCode.UNBEKANNT_UNBEKANNT == 5003
        assert FehlerCode.OOD_KONSENS_NICHT_ERREICHT == 5004

    def test_ood_layer_range(self):
        ood_codes = [5001, 5002, 5003, 5004]
        for code in ood_codes:
            assert 5000 <= code < 6000

    # --- System-Layer (6xxx) ---

    def test_system_layer_codes_exist(self):
        assert FehlerCode.SYSTEM_DEGRADIERT == 6001
        assert FehlerCode.SYSTEM_NOTFALL == 6002
        assert FehlerCode.INTEGRITAET_VERLETZT == 6003
        assert FehlerCode.SCHWELLENWERT_HASH_MISMATCH == 6004
        assert FehlerCode.META_U_KOLLAPS == 6005

    def test_system_layer_range(self):
        sys_codes = [6001, 6002, 6003, 6004, 6005]
        for code in sys_codes:
            assert 6000 <= code < 7000

    # --- API-Layer (7xxx) ---

    def test_api_layer_codes_exist(self):
        assert FehlerCode.RATE_LIMIT_UEBERSCHRITTEN == 7001
        assert FehlerCode.UNGUELTIGE_ANFRAGE == 7002
        assert FehlerCode.NICHT_AUTORISIERT == 7003

    def test_api_layer_range(self):
        api_codes = [7001, 7002, 7003]
        for code in api_codes:
            assert 7000 <= code < 8000


# ---------------------------------------------------------------------------
# Exception classes
# ---------------------------------------------------------------------------

class TestExceptionClasses:
    """Verify all 5 exception classes exist, inherit from Exception, and work."""

    def test_numerical_instability_error_inherits_exception(self):
        assert issubclass(NumericalInstabilityError, Exception)

    def test_calibration_gate_violation_inherits_exception(self):
        assert issubclass(CalibrationGateViolation, Exception)

    def test_threshold_violation_inherits_exception(self):
        assert issubclass(ThresholdViolation, Exception)

    def test_contract_violation_inherits_exception(self):
        assert issubclass(ContractViolation, Exception)

    def test_ood_consensus_violation_inherits_exception(self):
        assert issubclass(OODConsensusViolation, Exception)

    def test_numerical_instability_error_raise_catch(self):
        with pytest.raises(NumericalInstabilityError, match="test NaN"):
            raise NumericalInstabilityError("test NaN")

    def test_calibration_gate_violation_raise_catch(self):
        with pytest.raises(CalibrationGateViolation, match="ECE too high"):
            raise CalibrationGateViolation("ECE too high")

    def test_threshold_violation_raise_catch(self):
        with pytest.raises(ThresholdViolation, match="hash mismatch"):
            raise ThresholdViolation("hash mismatch")

    def test_contract_violation_raise_catch(self):
        with pytest.raises(ContractViolation, match="missing field"):
            raise ContractViolation("missing field")

    def test_ood_consensus_violation_raise_catch(self):
        with pytest.raises(OODConsensusViolation, match="< 5 sensors"):
            raise OODConsensusViolation("< 5 sensors")


# ---------------------------------------------------------------------------
# Import contract
# ---------------------------------------------------------------------------

class TestImportContract:
    """Verify that all public names are importable from jarvis.utils.exceptions."""

    def test_all_public_names_importable(self):
        from jarvis.utils import exceptions
        required = [
            "FehlerCode",
            "NumericalInstabilityError",
            "CalibrationGateViolation",
            "ThresholdViolation",
            "ContractViolation",
            "OODConsensusViolation",
        ]
        for name in required:
            assert hasattr(exceptions, name), f"{name} not found in exceptions module"
