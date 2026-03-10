# =============================================================================
# Tests for jarvis/risk/multi_timeframe.py (S18)
# =============================================================================

from dataclasses import dataclass
from typing import List

import pytest

from jarvis.risk.confidence_zone_engine import (
    ConfidenceZone,
    ConfidenceZoneEngine,
    ConfidenceZoneRequest,
)
from jarvis.risk.multi_timeframe import (
    MultiTimeframeCalibrator,
    RecalibrationResult,
    Timeframe,
    TimeframeConfig,
    TIMEFRAME_CONFIGS,
)


# ---------------------------------------------------------------------------
# Mock dependencies
# ---------------------------------------------------------------------------

@dataclass
class MockRegimeResult:
    regime: str
    confidence: float


class MockRegimeDetector:
    """Records calls and returns configurable regime."""

    def __init__(self, regime: str = "TRENDING", confidence: float = 0.85):
        self._regime = regime
        self._confidence = confidence
        self.calls: list = []

    def detect(self, data: List[float]) -> MockRegimeResult:
        self.calls.append({"data_len": len(data), "data": list(data)})
        return MockRegimeResult(regime=self._regime, confidence=self._confidence)


@dataclass
class MockRiskOutput:
    volatility_forecast: float = 0.2
    risk_regime: str = "NORMAL"
    exposure_weight: float = 0.5


class MockRiskEngine:
    """Records calls and returns configurable risk output."""

    def __init__(self, vol_forecast: float = 0.2):
        self._vol_forecast = vol_forecast
        self.calls: list = []

    def assess(
        self,
        returns_history: List[float],
        current_regime: str,
        meta_uncertainty: float,
    ) -> MockRiskOutput:
        self.calls.append({
            "returns_len": len(returns_history),
            "regime": current_regime,
            "meta_uncertainty": meta_uncertainty,
        })
        return MockRiskOutput(volatility_forecast=self._vol_forecast)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def regime_detector():
    return MockRegimeDetector()


@pytest.fixture
def risk_engine():
    return MockRiskEngine()


@pytest.fixture
def confidence_engine():
    return ConfidenceZoneEngine()


@pytest.fixture
def calibrator(regime_detector, risk_engine, confidence_engine):
    return MultiTimeframeCalibrator(regime_detector, risk_engine, confidence_engine)


@pytest.fixture
def returns_100():
    """100-element returns series."""
    return [0.01 * ((-1) ** i) for i in range(100)]


# ===========================================================================
# Timeframe enum
# ===========================================================================

class TestTimeframeEnum:

    def test_all_timeframes_exist(self):
        assert Timeframe.TF_5M.value == "5m"
        assert Timeframe.TF_15M.value == "15m"
        assert Timeframe.TF_1H.value == "1h"
        assert Timeframe.TF_4H.value == "4h"
        assert Timeframe.TF_1D.value == "1D"

    def test_timeframe_count(self):
        assert len(Timeframe) == 5


# ===========================================================================
# TimeframeConfig
# ===========================================================================

class TestTimeframeConfig:

    def test_all_timeframes_have_config(self):
        for tf in Timeframe:
            assert tf in TIMEFRAME_CONFIGS

    def test_config_immutable(self):
        cfg = TIMEFRAME_CONFIGS[Timeframe.TF_1D]
        with pytest.raises(AttributeError):
            cfg.risk_scale = 999.0

    @pytest.mark.parametrize("tf,label,bars,lookback,halflife,scale", [
        (Timeframe.TF_5M,  "5m",  288, 60, 20, 0.08),
        (Timeframe.TF_15M, "15m",  96, 40, 20, 0.15),
        (Timeframe.TF_1H,  "1h",   24, 30, 20, 0.30),
        (Timeframe.TF_4H,  "4h",    6, 20, 15, 0.60),
        (Timeframe.TF_1D,  "1D",    1, 20, 20, 1.00),
    ])
    def test_config_values(self, tf, label, bars, lookback, halflife, scale):
        cfg = TIMEFRAME_CONFIGS[tf]
        assert cfg.label == label
        assert cfg.bars_per_day == bars
        assert cfg.regime_lookback == lookback
        assert cfg.vol_halflife == halflife
        assert abs(cfg.risk_scale - scale) < 1e-9

    def test_risk_scale_monotonically_increasing(self):
        """Higher timeframes should have higher risk_scale."""
        ordered = [Timeframe.TF_5M, Timeframe.TF_15M, Timeframe.TF_1H,
                   Timeframe.TF_4H, Timeframe.TF_1D]
        scales = [TIMEFRAME_CONFIGS[tf].risk_scale for tf in ordered]
        for i in range(len(scales) - 1):
            assert scales[i] < scales[i + 1]

    def test_1d_risk_scale_is_one(self):
        """1D is the reference timeframe with scale = 1.0."""
        assert TIMEFRAME_CONFIGS[Timeframe.TF_1D].risk_scale == 1.0


# ===========================================================================
# switch_timeframe — basic behavior
# ===========================================================================

class TestSwitchTimeframeBasic:

    def test_returns_recalibration_result(self, calibrator, returns_100):
        result = calibrator.switch_timeframe(
            Timeframe.TF_1D, returns_100, 100.0, 0.3,
        )
        assert isinstance(result, RecalibrationResult)

    def test_recalibrated_always_true(self, calibrator, returns_100):
        result = calibrator.switch_timeframe(
            Timeframe.TF_1D, returns_100, 100.0, 0.3,
        )
        assert result.recalibrated is True

    def test_result_timeframe_label(self, calibrator, returns_100):
        result = calibrator.switch_timeframe(
            Timeframe.TF_1H, returns_100, 100.0, 0.3,
        )
        assert result.timeframe == "1h"

    def test_result_risk_scale(self, calibrator, returns_100):
        result = calibrator.switch_timeframe(
            Timeframe.TF_4H, returns_100, 100.0, 0.3,
        )
        assert abs(result.risk_scale - 0.60) < 1e-9

    def test_result_regime_from_detector(self, calibrator, returns_100):
        result = calibrator.switch_timeframe(
            Timeframe.TF_1D, returns_100, 100.0, 0.3,
        )
        assert result.regime == "TRENDING"

    def test_result_risk_from_engine(self, calibrator, returns_100):
        result = calibrator.switch_timeframe(
            Timeframe.TF_1D, returns_100, 100.0, 0.3,
        )
        assert isinstance(result.risk, MockRiskOutput)
        assert abs(result.risk.volatility_forecast - 0.2) < 1e-9

    def test_result_zone_is_confidence_zone(self, calibrator, returns_100):
        result = calibrator.switch_timeframe(
            Timeframe.TF_1D, returns_100, 100.0, 0.3,
        )
        assert isinstance(result.zone, ConfidenceZone)


# ===========================================================================
# R1: Full recalibration on every switch
# ===========================================================================

class TestFullRecalibration:

    def test_regime_detector_called(self, calibrator, regime_detector, returns_100):
        calibrator.switch_timeframe(Timeframe.TF_1D, returns_100, 100.0, 0.3)
        assert len(regime_detector.calls) == 1

    def test_risk_engine_called(self, calibrator, risk_engine, returns_100):
        calibrator.switch_timeframe(Timeframe.TF_1D, returns_100, 100.0, 0.3)
        assert len(risk_engine.calls) == 1

    def test_regime_uses_lookback_slice(self, calibrator, regime_detector, returns_100):
        """Regime detector receives only the lookback-sliced data."""
        calibrator.switch_timeframe(Timeframe.TF_1H, returns_100, 100.0, 0.3)
        cfg = TIMEFRAME_CONFIGS[Timeframe.TF_1H]
        assert regime_detector.calls[0]["data_len"] == cfg.regime_lookback

    def test_risk_receives_full_returns(self, calibrator, risk_engine, returns_100):
        """Risk engine receives the full returns history."""
        calibrator.switch_timeframe(Timeframe.TF_1D, returns_100, 100.0, 0.3)
        assert risk_engine.calls[0]["returns_len"] == 100

    def test_risk_receives_detected_regime(self, calibrator, risk_engine, returns_100):
        calibrator.switch_timeframe(Timeframe.TF_1D, returns_100, 100.0, 0.3)
        assert risk_engine.calls[0]["regime"] == "TRENDING"

    def test_risk_receives_meta_uncertainty(self, calibrator, risk_engine, returns_100):
        calibrator.switch_timeframe(Timeframe.TF_1D, returns_100, 50.0, 0.42)
        assert abs(risk_engine.calls[0]["meta_uncertainty"] - 0.42) < 1e-9

    def test_second_switch_recalibrates_again(
        self, calibrator, regime_detector, risk_engine, returns_100
    ):
        """R1: Every switch triggers full recalibration, even same timeframe."""
        calibrator.switch_timeframe(Timeframe.TF_1D, returns_100, 100.0, 0.3)
        calibrator.switch_timeframe(Timeframe.TF_1D, returns_100, 100.0, 0.3)
        assert len(regime_detector.calls) == 2
        assert len(risk_engine.calls) == 2


# ===========================================================================
# Confidence zone variance scaling
# ===========================================================================

class TestVarianceScaling:

    def test_zone_sigma_sq_scaled_by_risk_scale(self):
        """sigma_sq passed to confidence engine = vol_forecast² × risk_scale²."""
        zone_requests: list = []

        class CapturingEngine:
            def compute(self, req: ConfidenceZoneRequest) -> ConfidenceZone:
                zone_requests.append(req)
                return ConfidenceZoneEngine().compute(req)

        det = MockRegimeDetector()
        risk = MockRiskEngine(vol_forecast=0.25)
        cal = MultiTimeframeCalibrator(det, risk, CapturingEngine())

        returns = [0.01] * 100
        cal.switch_timeframe(Timeframe.TF_1H, returns, 100.0, 0.2)

        req = zone_requests[0]
        scale = TIMEFRAME_CONFIGS[Timeframe.TF_1H].risk_scale
        expected_sq = (0.25 ** 2) * (scale ** 2)
        assert abs(req.sigma_sq - expected_sq) < 1e-12

    def test_zone_mu_is_one_minus_meta_uncertainty(self):
        """mu passed to confidence engine = 1.0 - meta_uncertainty."""
        zone_requests: list = []

        class CapturingEngine:
            def compute(self, req: ConfidenceZoneRequest) -> ConfidenceZone:
                zone_requests.append(req)
                return ConfidenceZoneEngine().compute(req)

        det = MockRegimeDetector()
        risk = MockRiskEngine()
        cal = MultiTimeframeCalibrator(det, risk, CapturingEngine())

        returns = [0.01] * 100
        cal.switch_timeframe(Timeframe.TF_1D, returns, 100.0, 0.35)

        assert abs(zone_requests[0].mu - 0.65) < 1e-12

    def test_5m_produces_tighter_zones_than_1d(self):
        """Lower risk_scale -> smaller sigma_sq -> tighter zones."""
        det = MockRegimeDetector()
        risk = MockRiskEngine(vol_forecast=0.2)
        eng = ConfidenceZoneEngine()
        cal = MultiTimeframeCalibrator(det, risk, eng)

        returns = [0.01] * 100

        r_5m = cal.switch_timeframe(Timeframe.TF_5M, returns, 100.0, 0.3)
        r_1d = cal.switch_timeframe(Timeframe.TF_1D, returns, 100.0, 0.3)

        width_5m = r_5m.zone.entry_upper - r_5m.zone.entry_lower
        width_1d = r_1d.zone.entry_upper - r_1d.zone.entry_lower
        assert width_5m < width_1d


# ===========================================================================
# Current timeframe tracking
# ===========================================================================

class TestCurrentTimeframe:

    def test_initial_none(self, calibrator):
        assert calibrator.current_timeframe is None

    def test_set_after_switch(self, calibrator, returns_100):
        calibrator.switch_timeframe(Timeframe.TF_4H, returns_100, 100.0, 0.3)
        assert calibrator.current_timeframe == Timeframe.TF_4H

    def test_updated_on_second_switch(self, calibrator, returns_100):
        calibrator.switch_timeframe(Timeframe.TF_4H, returns_100, 100.0, 0.3)
        calibrator.switch_timeframe(Timeframe.TF_1H, returns_100, 100.0, 0.3)
        assert calibrator.current_timeframe == Timeframe.TF_1H


# ===========================================================================
# Input validation
# ===========================================================================

class TestInputValidation:

    def test_non_timeframe_enum_raises(self, calibrator, returns_100):
        with pytest.raises(TypeError, match="Timeframe"):
            calibrator.switch_timeframe("1h", returns_100, 100.0, 0.3)

    def test_insufficient_data_raises(self, calibrator):
        """5m needs 60 bars lookback, 10 bars should fail."""
        short_data = [0.01] * 10
        with pytest.raises(ValueError, match="Insufficient data"):
            calibrator.switch_timeframe(Timeframe.TF_5M, short_data, 100.0, 0.3)

    def test_exact_lookback_succeeds(self, calibrator):
        """Exactly regime_lookback bars should work."""
        cfg = TIMEFRAME_CONFIGS[Timeframe.TF_1D]
        data = [0.01] * cfg.regime_lookback
        result = calibrator.switch_timeframe(Timeframe.TF_1D, data, 100.0, 0.3)
        assert result.recalibrated is True

    def test_more_than_lookback_succeeds(self, calibrator, returns_100):
        """More data than lookback should work fine."""
        result = calibrator.switch_timeframe(Timeframe.TF_1D, returns_100, 100.0, 0.3)
        assert result.recalibrated is True


# ===========================================================================
# All timeframes
# ===========================================================================

class TestAllTimeframes:

    @pytest.mark.parametrize("tf", list(Timeframe))
    def test_switch_to_each_timeframe(self, tf):
        """Every timeframe must be switchable."""
        cfg = TIMEFRAME_CONFIGS[tf]
        data = [0.01] * max(cfg.regime_lookback, 20)
        det = MockRegimeDetector()
        risk = MockRiskEngine()
        eng = ConfidenceZoneEngine()
        cal = MultiTimeframeCalibrator(det, risk, eng)

        result = cal.switch_timeframe(tf, data, 100.0, 0.3)
        assert result.recalibrated is True
        assert result.timeframe == cfg.label
        assert abs(result.risk_scale - cfg.risk_scale) < 1e-9


# ===========================================================================
# Determinism (DET-07)
# ===========================================================================

class TestDeterminism:

    def test_identical_inputs_identical_outputs(self):
        """Same inputs must produce bit-identical zone outputs."""
        returns = [0.005 * ((-1) ** i) for i in range(100)]

        def make_calibrator():
            return MultiTimeframeCalibrator(
                MockRegimeDetector(regime="TRENDING", confidence=0.85),
                MockRiskEngine(vol_forecast=0.18),
                ConfidenceZoneEngine(),
            )

        r1 = make_calibrator().switch_timeframe(
            Timeframe.TF_1H, returns, 42000.0, 0.25,
        )
        r2 = make_calibrator().switch_timeframe(
            Timeframe.TF_1H, returns, 42000.0, 0.25,
        )

        assert r1.zone.entry_lower == r2.zone.entry_lower
        assert r1.zone.entry_upper == r2.zone.entry_upper
        assert r1.zone.entry_confidence == r2.zone.entry_confidence
        assert r1.zone.exit_soft == r2.zone.exit_soft
        assert r1.zone.exit_hard == r2.zone.exit_hard
        assert r1.zone.meta_uncertainty == r2.zone.meta_uncertainty
        assert r1.risk_scale == r2.risk_scale
        assert r1.timeframe == r2.timeframe


# ===========================================================================
# Edge cases
# ===========================================================================

class TestEdgeCases:

    def test_regime_detector_returns_shock(self):
        """SHOCK regime should produce wider confidence zones."""
        returns = [0.01] * 100
        det_trend = MockRegimeDetector(regime="TRENDING", confidence=0.5)
        det_shock = MockRegimeDetector(regime="SHOCK", confidence=0.5)
        risk = MockRiskEngine(vol_forecast=0.2)
        eng = ConfidenceZoneEngine()

        r_trend = MultiTimeframeCalibrator(det_trend, risk, eng).switch_timeframe(
            Timeframe.TF_1D, returns, 100.0, 0.3,
        )
        r_shock = MultiTimeframeCalibrator(det_shock, risk, eng).switch_timeframe(
            Timeframe.TF_1D, returns, 100.0, 0.3,
        )

        width_trend = r_trend.zone.entry_upper - r_trend.zone.entry_lower
        width_shock = r_shock.zone.entry_upper - r_shock.zone.entry_lower
        assert width_shock > width_trend

    def test_high_meta_uncertainty_widens_zone(self):
        """Higher meta_uncertainty -> lower mu -> wider entry box."""
        returns = [0.01] * 100
        det = MockRegimeDetector()
        risk = MockRiskEngine()
        eng = ConfidenceZoneEngine()
        cal = MultiTimeframeCalibrator(det, risk, eng)

        r_low = cal.switch_timeframe(Timeframe.TF_1D, returns, 100.0, 0.1)
        r_high = cal.switch_timeframe(Timeframe.TF_1D, returns, 100.0, 0.9)

        width_low = r_low.zone.entry_upper - r_low.zone.entry_lower
        width_high = r_high.zone.entry_upper - r_high.zone.entry_lower
        assert width_high > width_low

    def test_switch_same_timeframe_twice(self, calibrator, returns_100):
        """Switching to the same timeframe should still fully recalibrate."""
        r1 = calibrator.switch_timeframe(Timeframe.TF_1H, returns_100, 100.0, 0.3)
        r2 = calibrator.switch_timeframe(Timeframe.TF_1H, returns_100, 100.0, 0.3)
        assert r1.recalibrated is True
        assert r2.recalibrated is True
        assert calibrator.current_timeframe == Timeframe.TF_1H
