# jarvis/utils/exceptions.py
# Version: 6.1.0
# FAS-defined error codes and exception types for the JARVIS platform.
#
# CONSTRAINTS
# -----------
# stdlib only. No numpy. No file I/O. No logging.
#
# DETERMINISM GUARANTEES
# ----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.


class FehlerCode:
    """
    Structured error codes for all JARVIS subsystems.

    Each layer has a dedicated numeric range (1xxx..7xxx).
    Codes are integer constants — never strings.
    """

    # Daten-Layer (1xxx)
    DATENQUELLE_NICHT_VERFUEGBAR = 1001
    DATEN_VALIDIERUNG_FEHLER = 1002
    DATEN_VERALTET = 1003
    DATEN_UNVOLLSTAENDIG = 1004
    DATEN_NAN_INF = 1005

    # Feature-Layer (2xxx)
    FEATURE_BERECHNUNG_FEHLER = 2001
    FEATURE_DRIFT_ERKANNT = 2002
    FEATURE_FEHLEND = 2003
    FEATURE_NAN_INF = 2004

    # Modell-Layer (3xxx)
    MODELL_VORHERSAGE_FEHLER = 3001
    MODELL_DIVERGENZ_ERKANNT = 3002
    MODELL_UEBERANPASSUNG = 3003
    NUMERISCHE_INSTABILITAET = 3004
    SYSTEMVERTRAG_VERLETZUNG = 3005

    # Kalibrierungs-Layer (4xxx)
    KALIBRIERUNG_FEHLGESCHLAGEN = 4001
    ECE_SCHWELLENWERT_UEBERSCHRITTEN = 4002
    REKALIBRIERUNG_NOETIG = 4003
    KALIBRIERUNG_GATE_BLOCKIERT = 4004

    # OOD-Layer (5xxx)
    OOD_HOCH = 5001
    OOD_KRITISCH = 5002
    UNBEKANNT_UNBEKANNT = 5003
    OOD_KONSENS_NICHT_ERREICHT = 5004

    # System-Layer (6xxx)
    SYSTEM_DEGRADIERT = 6001
    SYSTEM_NOTFALL = 6002
    INTEGRITAET_VERLETZT = 6003
    SCHWELLENWERT_HASH_MISMATCH = 6004
    META_U_KOLLAPS = 6005

    # API-Layer (7xxx)
    RATE_LIMIT_UEBERSCHRITTEN = 7001
    UNGUELTIGE_ANFRAGE = 7002
    NICHT_AUTORISIERT = 7003


class NumericalInstabilityError(Exception):
    """Raised on NaN/Inf detection."""
    pass


class CalibrationGateViolation(Exception):
    """Raised when ECE >= 0.05. Blocks deployment."""
    pass


class ThresholdViolation(Exception):
    """Raised when thresholds changed. No warning — immediate error."""
    pass


class ContractViolation(Exception):
    """Raised when D(t) fields missing or inconsistent."""
    pass


class OODConsensusViolation(Exception):
    """Raised when OOD consensus not reachable (< 5 sensors active)."""
    pass
