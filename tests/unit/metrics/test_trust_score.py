# =============================================================================
# tests/unit/metrics/test_trust_score.py
# Tests for jarvis/metrics/trust_score.py
# =============================================================================

import pytest

from jarvis.metrics.trust_score import (
    TRUST_HIGH,
    TRUST_MEDIUM,
    TRUST_LOW,
    TRUST_CRITICAL,
    TRUST_WEIGHT_CALIBRATION,
    TRUST_WEIGHT_OOD,
    TRUST_WEIGHT_STABILITY,
    TRUST_WEIGHT_RISK,
    TRUST_WEIGHT_OPERATIONAL,
    ECE_NORMALIZER,
    VARIANCE_NORMALIZER,
    DRAWDOWN_NORMALIZER,
    TrustScoreResult,
    TrustScoreEngine,
    _clip01,
    _classify_trust,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_trust_high(self):
        assert TRUST_HIGH == 0.8

    def test_trust_medium(self):
        assert TRUST_MEDIUM == 0.6

    def test_trust_low(self):
        assert TRUST_LOW == 0.4

    def test_trust_critical(self):
        assert TRUST_CRITICAL == 0.2

    def test_weight_calibration(self):
        assert TRUST_WEIGHT_CALIBRATION == 0.30

    def test_weight_ood(self):
        assert TRUST_WEIGHT_OOD == 0.25

    def test_weight_stability(self):
        assert TRUST_WEIGHT_STABILITY == 0.20

    def test_weight_risk(self):
        assert TRUST_WEIGHT_RISK == 0.15

    def test_weight_operational(self):
        assert TRUST_WEIGHT_OPERATIONAL == 0.10

    def test_weights_sum_to_one(self):
        total = (
            TRUST_WEIGHT_CALIBRATION
            + TRUST_WEIGHT_OOD
            + TRUST_WEIGHT_STABILITY
            + TRUST_WEIGHT_RISK
            + TRUST_WEIGHT_OPERATIONAL
        )
        assert total == pytest.approx(1.0)

    def test_ece_normalizer(self):
        assert ECE_NORMALIZER == 0.05

    def test_variance_normalizer(self):
        assert VARIANCE_NORMALIZER == 0.10

    def test_drawdown_normalizer(self):
        assert DRAWDOWN_NORMALIZER == 0.15


# =============================================================================
# SECTION 2 -- HELPERS
# =============================================================================

class TestClip01:
    def test_within_range(self):
        assert _clip01(0.5) == 0.5

    def test_below_zero(self):
        assert _clip01(-0.5) == 0.0

    def test_above_one(self):
        assert _clip01(1.5) == 1.0


class TestClassifyTrust:
    def test_high(self):
        assert _classify_trust(0.9) == "HIGH"

    def test_high_boundary(self):
        assert _classify_trust(0.8) == "HIGH"

    def test_medium(self):
        assert _classify_trust(0.7) == "MEDIUM"

    def test_medium_boundary(self):
        assert _classify_trust(0.6) == "MEDIUM"

    def test_low(self):
        assert _classify_trust(0.5) == "LOW"

    def test_low_boundary(self):
        assert _classify_trust(0.4) == "LOW"

    def test_critical(self):
        assert _classify_trust(0.3) == "CRITICAL"

    def test_critical_zero(self):
        assert _classify_trust(0.0) == "CRITICAL"


# =============================================================================
# SECTION 3 -- TRUST SCORE RESULT DATACLASS
# =============================================================================

class TestTrustScoreResult:
    def test_frozen(self):
        r = TrustScoreResult(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, "HIGH")
        with pytest.raises(AttributeError):
            r.trust_score = 0.0

    def test_fields(self):
        r = TrustScoreResult(
            calibration_score=0.8,
            ood_score=0.9,
            stability_score=0.7,
            risk_score=0.6,
            operational_score=1.0,
            trust_score=0.79,
            classification="MEDIUM",
        )
        assert r.calibration_score == 0.8
        assert r.ood_score == 0.9
        assert r.stability_score == 0.7
        assert r.risk_score == 0.6
        assert r.operational_score == 1.0
        assert r.trust_score == 0.79
        assert r.classification == "MEDIUM"

    def test_equality(self):
        r1 = TrustScoreResult(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, "HIGH")
        r2 = TrustScoreResult(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, "HIGH")
        assert r1 == r2


# =============================================================================
# SECTION 4 -- COMPUTE: PERFECT SCORES
# =============================================================================

class TestComputePerfect:
    def test_all_perfect(self):
        eng = TrustScoreEngine()
        r = eng.compute(
            ece=0.0,
            ood_recall=1.0,
            prediction_variance=0.0,
            drawdown=0.0,
            uptime=1.0,
        )
        assert r.calibration_score == pytest.approx(1.0)
        assert r.ood_score == pytest.approx(1.0)
        assert r.stability_score == pytest.approx(1.0)
        assert r.risk_score == pytest.approx(1.0)
        assert r.operational_score == pytest.approx(1.0)
        assert r.trust_score == pytest.approx(1.0)
        assert r.classification == "HIGH"

    def test_all_worst(self):
        eng = TrustScoreEngine()
        r = eng.compute(
            ece=0.05,
            ood_recall=0.0,
            prediction_variance=0.10,
            drawdown=0.15,
            uptime=0.0,
        )
        assert r.calibration_score == pytest.approx(0.0)
        assert r.ood_score == pytest.approx(0.0)
        assert r.stability_score == pytest.approx(0.0)
        assert r.risk_score == pytest.approx(0.0)
        assert r.operational_score == pytest.approx(0.0)
        assert r.trust_score == pytest.approx(0.0)
        assert r.classification == "CRITICAL"


# =============================================================================
# SECTION 5 -- COMPUTE: COMPONENT FORMULAS
# =============================================================================

class TestComputeComponents:
    def test_calibration_formula(self):
        eng = TrustScoreEngine()
        r = eng.compute(ece=0.025, ood_recall=0.0, prediction_variance=0.0,
                        drawdown=0.0, uptime=0.0)
        # cal = 1 - min(0.025/0.05, 1) = 1 - 0.5 = 0.5
        assert r.calibration_score == pytest.approx(0.5)

    def test_calibration_saturates(self):
        eng = TrustScoreEngine()
        r = eng.compute(ece=0.10, ood_recall=0.0, prediction_variance=0.0,
                        drawdown=0.0, uptime=0.0)
        # min(0.10/0.05, 1) = min(2, 1) = 1 → cal = 0
        assert r.calibration_score == pytest.approx(0.0)

    def test_stability_formula(self):
        eng = TrustScoreEngine()
        r = eng.compute(ece=0.0, ood_recall=0.0, prediction_variance=0.05,
                        drawdown=0.0, uptime=0.0)
        # stab = 1 - min(0.05/0.10, 1) = 1 - 0.5 = 0.5
        assert r.stability_score == pytest.approx(0.5)

    def test_risk_formula(self):
        eng = TrustScoreEngine()
        r = eng.compute(ece=0.0, ood_recall=0.0, prediction_variance=0.0,
                        drawdown=0.075, uptime=0.0)
        # risk = 1 - min(0.075/0.15, 1) = 1 - 0.5 = 0.5
        assert r.risk_score == pytest.approx(0.5)

    def test_ood_passthrough(self):
        eng = TrustScoreEngine()
        r = eng.compute(ece=0.0, ood_recall=0.75, prediction_variance=0.0,
                        drawdown=0.0, uptime=0.0)
        assert r.ood_score == pytest.approx(0.75)

    def test_uptime_passthrough(self):
        eng = TrustScoreEngine()
        r = eng.compute(ece=0.0, ood_recall=0.0, prediction_variance=0.0,
                        drawdown=0.0, uptime=0.85)
        assert r.operational_score == pytest.approx(0.85)

    def test_weighted_sum(self):
        eng = TrustScoreEngine()
        r = eng.compute(ece=0.0, ood_recall=1.0, prediction_variance=0.0,
                        drawdown=0.0, uptime=1.0)
        # cal=1.0, ood=1.0, stab=1.0, risk=1.0, ops=1.0
        assert r.trust_score == pytest.approx(1.0)

    def test_partial_scores(self):
        eng = TrustScoreEngine()
        r = eng.compute(
            ece=0.025,              # cal = 0.5
            ood_recall=0.8,         # ood = 0.8
            prediction_variance=0.05,  # stab = 0.5
            drawdown=0.075,         # risk = 0.5
            uptime=0.9,             # ops = 0.9
        )
        expected = (
            0.30 * 0.5
            + 0.25 * 0.8
            + 0.20 * 0.5
            + 0.15 * 0.5
            + 0.10 * 0.9
        )
        assert r.trust_score == pytest.approx(expected)


# =============================================================================
# SECTION 6 -- COMPUTE: CLASSIFICATION
# =============================================================================

class TestComputeClassification:
    def test_high_trust(self):
        eng = TrustScoreEngine()
        r = eng.compute(ece=0.0, ood_recall=1.0, prediction_variance=0.0,
                        drawdown=0.0, uptime=1.0)
        assert r.classification == "HIGH"

    def test_medium_trust(self):
        eng = TrustScoreEngine()
        # cal=0.5, ood=0.8, stab=0.5, risk=0.5, ops=0.8
        # trust = 0.3*0.5 + 0.25*0.8 + 0.2*0.5 + 0.15*0.5 + 0.1*0.8 = 0.6
        r = eng.compute(
            ece=0.025, ood_recall=0.8, prediction_variance=0.05,
            drawdown=0.075, uptime=0.8,
        )
        assert r.classification == "MEDIUM"

    def test_critical_trust(self):
        eng = TrustScoreEngine()
        r = eng.compute(ece=0.05, ood_recall=0.0, prediction_variance=0.10,
                        drawdown=0.15, uptime=0.0)
        assert r.classification == "CRITICAL"


# =============================================================================
# SECTION 7 -- COMPUTE: EDGE CASES
# =============================================================================

class TestComputeEdgeCases:
    def test_ece_zero(self):
        eng = TrustScoreEngine()
        r = eng.compute(ece=0.0, ood_recall=0.0, prediction_variance=0.0,
                        drawdown=0.0, uptime=0.0)
        assert r.calibration_score == 1.0

    def test_very_large_ece(self):
        eng = TrustScoreEngine()
        r = eng.compute(ece=1.0, ood_recall=0.0, prediction_variance=0.0,
                        drawdown=0.0, uptime=0.0)
        assert r.calibration_score == 0.0

    def test_negative_ece_clipped(self):
        """Negative ECE would produce cal > 1, clipped to 1."""
        eng = TrustScoreEngine()
        r = eng.compute(ece=-0.01, ood_recall=0.0, prediction_variance=0.0,
                        drawdown=0.0, uptime=0.0)
        assert r.calibration_score == 1.0

    def test_ood_above_one_clipped(self):
        eng = TrustScoreEngine()
        r = eng.compute(ece=0.0, ood_recall=1.5, prediction_variance=0.0,
                        drawdown=0.0, uptime=0.0)
        assert r.ood_score == 1.0

    def test_uptime_above_one_clipped(self):
        eng = TrustScoreEngine()
        r = eng.compute(ece=0.0, ood_recall=0.0, prediction_variance=0.0,
                        drawdown=0.0, uptime=1.5)
        assert r.operational_score == 1.0


# =============================================================================
# SECTION 8 -- COMPUTE: VALIDATION
# =============================================================================

class TestComputeValidation:
    def test_ece_type_error(self):
        eng = TrustScoreEngine()
        with pytest.raises(TypeError, match="ece must be numeric"):
            eng.compute("bad", 0.0, 0.0, 0.0, 0.0)

    def test_ood_type_error(self):
        eng = TrustScoreEngine()
        with pytest.raises(TypeError, match="ood_recall must be numeric"):
            eng.compute(0.0, "bad", 0.0, 0.0, 0.0)

    def test_variance_type_error(self):
        eng = TrustScoreEngine()
        with pytest.raises(TypeError, match="prediction_variance must be numeric"):
            eng.compute(0.0, 0.0, "bad", 0.0, 0.0)

    def test_drawdown_type_error(self):
        eng = TrustScoreEngine()
        with pytest.raises(TypeError, match="drawdown must be numeric"):
            eng.compute(0.0, 0.0, 0.0, "bad", 0.0)

    def test_uptime_type_error(self):
        eng = TrustScoreEngine()
        with pytest.raises(TypeError, match="uptime must be numeric"):
            eng.compute(0.0, 0.0, 0.0, 0.0, "bad")

    def test_int_accepted(self):
        eng = TrustScoreEngine()
        r = eng.compute(0, 1, 0, 0, 1)
        assert isinstance(r, TrustScoreResult)


# =============================================================================
# SECTION 9 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_compute_deterministic(self):
        eng = TrustScoreEngine()
        results = [
            eng.compute(0.02, 0.8, 0.05, 0.07, 0.95)
            for _ in range(10)
        ]
        assert all(r == results[0] for r in results)

    def test_independent_engines(self):
        r1 = TrustScoreEngine().compute(0.01, 0.9, 0.03, 0.05, 0.99)
        r2 = TrustScoreEngine().compute(0.01, 0.9, 0.03, 0.05, 0.99)
        assert r1 == r2
