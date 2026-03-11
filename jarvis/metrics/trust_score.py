# =============================================================================
# jarvis/metrics/trust_score.py
# Authority: FAS v6.0.1 -- System Health Composite Trust Score
# =============================================================================
#
# SCOPE
# -----
# Composite trust score for system health assessment.  Aggregates five
# independent component metrics into a single [0, 1] trust score.
# 1.0 = fully trustworthy, 0.0 = not trustworthy.
#
# Public symbols:
#   TRUST_HIGH                    Classification boundary (0.8)
#   TRUST_MEDIUM                  Classification boundary (0.6)
#   TRUST_LOW                     Classification boundary (0.4)
#   TRUST_CRITICAL                Classification boundary (0.2)
#   TRUST_WEIGHT_CALIBRATION      Component weight (0.30)
#   TRUST_WEIGHT_OOD              Component weight (0.25)
#   TRUST_WEIGHT_STABILITY        Component weight (0.20)
#   TRUST_WEIGHT_RISK             Component weight (0.15)
#   TRUST_WEIGHT_OPERATIONAL      Component weight (0.10)
#   ECE_NORMALIZER                Calibration normalizer (0.05)
#   VARIANCE_NORMALIZER           Prediction variance normalizer (0.10)
#   DRAWDOWN_NORMALIZER           Drawdown normalizer (0.15)
#   TrustScoreResult              Frozen dataclass for trust output
#   TrustScoreEngine              Engine class
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses
#   external:  NONE
#   internal:  NONE
#   PROHIBITED: logging, random, file IO, network IO, datetime.now(), numpy
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-06  Fixed literals not parametrisable.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "TRUST_HIGH",
    "TRUST_MEDIUM",
    "TRUST_LOW",
    "TRUST_CRITICAL",
    "TRUST_WEIGHT_CALIBRATION",
    "TRUST_WEIGHT_OOD",
    "TRUST_WEIGHT_STABILITY",
    "TRUST_WEIGHT_RISK",
    "TRUST_WEIGHT_OPERATIONAL",
    "ECE_NORMALIZER",
    "VARIANCE_NORMALIZER",
    "DRAWDOWN_NORMALIZER",
    "TrustScoreResult",
    "TrustScoreEngine",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

TRUST_HIGH: float = 0.8
"""System highly trustworthy above this."""

TRUST_MEDIUM: float = 0.6
"""System conditionally trustworthy above this."""

TRUST_LOW: float = 0.4
"""System limited trustworthiness above this."""

TRUST_CRITICAL: float = 0.2
"""System not trustworthy below this."""

# Component weights (must sum to 1.0)
TRUST_WEIGHT_CALIBRATION: float = 0.30
"""Calibration quality weight."""

TRUST_WEIGHT_OOD: float = 0.25
"""OOD detection accuracy weight."""

TRUST_WEIGHT_STABILITY: float = 0.20
"""Prediction stability weight."""

TRUST_WEIGHT_RISK: float = 0.15
"""Risk control effectiveness weight."""

TRUST_WEIGHT_OPERATIONAL: float = 0.10
"""Operational reliability weight."""

# Component normalizers
ECE_NORMALIZER: float = 0.05
"""ECE normalizer — ECE at this level maps to calibration_score = 0."""

VARIANCE_NORMALIZER: float = 0.10
"""Prediction variance normalizer — variance at this maps to stability_score = 0."""

DRAWDOWN_NORMALIZER: float = 0.15
"""Drawdown normalizer — drawdown at this maps to risk_score = 0."""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class TrustScoreResult:
    """
    Trust score computation result.

    Fields:
        calibration_score:   Calibration quality [0, 1].
        ood_score:           OOD detection accuracy [0, 1].
        stability_score:     Prediction stability [0, 1].
        risk_score:          Risk control effectiveness [0, 1].
        operational_score:   Operational reliability [0, 1].
        trust_score:         Composite trust [0, 1].
        classification:      "HIGH", "MEDIUM", "LOW", or "CRITICAL".
    """
    calibration_score: float
    ood_score: float
    stability_score: float
    risk_score: float
    operational_score: float
    trust_score: float
    classification: str


# =============================================================================
# SECTION 3 -- HELPERS
# =============================================================================

def _clip01(value: float) -> float:
    """Clip value to [0.0, 1.0]."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _classify_trust(score: float) -> str:
    """Classify trust score into HIGH/MEDIUM/LOW/CRITICAL."""
    if score >= TRUST_HIGH:
        return "HIGH"
    if score >= TRUST_MEDIUM:
        return "MEDIUM"
    if score >= TRUST_LOW:
        return "LOW"
    return "CRITICAL"


# =============================================================================
# SECTION 4 -- ENGINE
# =============================================================================

class TrustScoreEngine:
    """
    Composite trust score engine.

    Aggregates five component metrics into a single trust score.
    1.0 = fully trustworthy, 0.0 = not trustworthy.

    Component formulas:
        calibration_score  = 1.0 - min(ece / ECE_NORMALIZER, 1.0)
        ood_score          = ood_recall  (direct passthrough)
        stability_score    = 1.0 - min(prediction_variance / VARIANCE_NORMALIZER, 1.0)
        risk_score         = 1.0 - min(drawdown / DRAWDOWN_NORMALIZER, 1.0)
        operational_score  = uptime  (direct passthrough)

    Stateless: all inputs passed explicitly.
    """

    def compute(
        self,
        ece: float,
        ood_recall: float,
        prediction_variance: float,
        drawdown: float,
        uptime: float,
    ) -> TrustScoreResult:
        """
        Compute composite trust score.

        Args:
            ece:                   Expected Calibration Error [0, inf).
            ood_recall:            OOD detection recall [0, 1].
            prediction_variance:   Prediction variance [0, inf).
            drawdown:              Max drawdown [0, 1].
            uptime:                System uptime fraction [0, 1].

        Returns:
            TrustScoreResult.

        Raises:
            TypeError: If any input is not numeric.
        """
        for name, val in [
            ("ece", ece),
            ("ood_recall", ood_recall),
            ("prediction_variance", prediction_variance),
            ("drawdown", drawdown),
            ("uptime", uptime),
        ]:
            if not isinstance(val, (int, float)):
                raise TypeError(
                    f"{name} must be numeric, "
                    f"got {type(val).__name__}"
                )

        cal_score = _clip01(
            1.0 - min(ece / ECE_NORMALIZER, 1.0)
        )
        ood_score = _clip01(ood_recall)
        stab_score = _clip01(
            1.0 - min(prediction_variance / VARIANCE_NORMALIZER, 1.0)
        )
        risk_score = _clip01(
            1.0 - min(drawdown / DRAWDOWN_NORMALIZER, 1.0)
        )
        ops_score = _clip01(uptime)

        trust = _clip01(
            TRUST_WEIGHT_CALIBRATION * cal_score
            + TRUST_WEIGHT_OOD * ood_score
            + TRUST_WEIGHT_STABILITY * stab_score
            + TRUST_WEIGHT_RISK * risk_score
            + TRUST_WEIGHT_OPERATIONAL * ops_score
        )

        return TrustScoreResult(
            calibration_score=cal_score,
            ood_score=ood_score,
            stability_score=stab_score,
            risk_score=risk_score,
            operational_score=ops_score,
            trust_score=trust,
            classification=_classify_trust(trust),
        )
