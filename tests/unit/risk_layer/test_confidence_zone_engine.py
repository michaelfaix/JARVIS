# =============================================================================
# Tests for jarvis/risk/confidence_zone_engine.py (S16)
# =============================================================================

import math

import numpy as np
import pytest

from jarvis.risk.confidence_zone_engine import (
    ConfidenceZone,
    ConfidenceZoneEngine,
    ConfidenceZoneRequest,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    return ConfidenceZoneEngine()


@pytest.fixture
def base_request():
    """Standard request: TRENDING regime, reasonable values."""
    return ConfidenceZoneRequest(
        current_price=100.0,
        regime="TRENDING",
        sigma_sq=0.04,   # sigma = 0.2
        mu=0.7,
        regime_confidence=0.8,
    )


# ===========================================================================
# Basic output structure
# ===========================================================================

class TestBasicOutput:

    def test_returns_confidence_zone(self, engine, base_request):
        result = engine.compute(base_request)
        assert isinstance(result, ConfidenceZone)

    def test_all_fields_are_float(self, engine, base_request):
        result = engine.compute(base_request)
        for field_name in [
            "entry_lower", "entry_upper", "entry_confidence",
            "exit_soft", "exit_hard", "exit_confidence",
            "expected_move_pct", "vol_adjusted_stop", "meta_uncertainty",
        ]:
            val = getattr(result, field_name)
            assert isinstance(val, float), f"{field_name} is not float: {type(val)}"

    def test_all_fields_finite(self, engine, base_request):
        result = engine.compute(base_request)
        for field_name in [
            "entry_lower", "entry_upper", "entry_confidence",
            "exit_soft", "exit_hard", "exit_confidence",
            "expected_move_pct", "vol_adjusted_stop", "meta_uncertainty",
        ]:
            val = getattr(result, field_name)
            assert np.isfinite(val), f"{field_name} is not finite: {val}"


# ===========================================================================
# Entry Box computation
# ===========================================================================

class TestEntryBox:

    def test_entry_lower_less_than_upper(self, engine, base_request):
        result = engine.compute(base_request)
        assert result.entry_lower < result.entry_upper

    def test_entry_box_symmetric_around_price(self, engine, base_request):
        result = engine.compute(base_request)
        mid = (result.entry_lower + result.entry_upper) / 2.0
        assert abs(mid - base_request.current_price) < 1e-9

    def test_entry_box_formula(self, engine):
        """Verify exact formula: box_width = adjusted_sigma * (1 + (1 - mu))."""
        req = ConfidenceZoneRequest(
            current_price=100.0,
            regime="TRENDING",  # vol_mult = 1.0
            sigma_sq=0.01,      # sigma = 0.1
            mu=0.5,
            regime_confidence=0.9,
        )
        result = engine.compute(req)

        sigma = math.sqrt(0.01)          # 0.1
        adjusted_sigma = sigma * 1.0     # 0.1 (TRENDING)
        box_width = adjusted_sigma * (1.0 + (1.0 - 0.5))  # 0.1 * 1.5 = 0.15
        expected_lower = 100.0 * (1.0 - box_width)  # 85.0
        expected_upper = 100.0 * (1.0 + box_width)  # 115.0

        assert abs(result.entry_lower - expected_lower) < 1e-9
        assert abs(result.entry_upper - expected_upper) < 1e-9

    def test_high_mu_narrows_box(self, engine):
        """Higher mu (information quality) should narrow the entry box."""
        req_low = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=0.2, regime_confidence=0.8,
        )
        req_high = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=0.9, regime_confidence=0.8,
        )
        low_result = engine.compute(req_low)
        high_result = engine.compute(req_high)

        low_width = low_result.entry_upper - low_result.entry_lower
        high_width = high_result.entry_upper - high_result.entry_lower
        assert high_width < low_width


# ===========================================================================
# Entry Confidence
# ===========================================================================

class TestEntryConfidence:

    def test_entry_confidence_formula(self, engine):
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=0.7, regime_confidence=0.8,
        )
        result = engine.compute(req)
        expected = 0.7 * 0.8  # 0.56
        assert abs(result.entry_confidence - expected) < 1e-9

    def test_entry_confidence_clipped_low(self, engine):
        """mu=0 and regime_confidence=0 -> raw=0 -> clipped to 1e-6."""
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=0.0, regime_confidence=0.0,
        )
        result = engine.compute(req)
        assert abs(result.entry_confidence - 1e-6) < 1e-12

    def test_entry_confidence_clipped_high(self, engine):
        """mu=1 and regime_confidence=1 -> raw=1 -> clipped to 1-1e-6."""
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=1.0, regime_confidence=1.0,
        )
        result = engine.compute(req)
        assert abs(result.entry_confidence - (1.0 - 1e-6)) < 1e-12

    def test_entry_confidence_in_bounds(self, engine, base_request):
        result = engine.compute(base_request)
        assert 1e-6 <= result.entry_confidence <= 1.0 - 1e-6


# ===========================================================================
# Exit Risk Corridor
# ===========================================================================

class TestExitCorridor:

    def test_exit_soft_above_hard(self, engine, base_request):
        """Soft exit is closer to price than hard exit."""
        result = engine.compute(base_request)
        assert result.exit_soft > result.exit_hard

    def test_exit_soft_below_price(self, engine, base_request):
        result = engine.compute(base_request)
        assert result.exit_soft < base_request.current_price

    def test_exit_hard_below_soft(self, engine, base_request):
        result = engine.compute(base_request)
        assert result.exit_hard < result.exit_soft

    def test_exit_formula(self, engine):
        req = ConfidenceZoneRequest(
            current_price=200.0, regime="TRENDING",  # vol_mult=1.0
            sigma_sq=0.01, mu=0.6, regime_confidence=0.9,
        )
        result = engine.compute(req)

        sigma = math.sqrt(0.01)           # 0.1
        adjusted_sigma = sigma * 1.0      # 0.1
        expected_soft = 200.0 * (1.0 - adjusted_sigma * 1.5)  # 200 * 0.85 = 170
        expected_hard = 200.0 * (1.0 - adjusted_sigma * 2.5)  # 200 * 0.75 = 150

        assert abs(result.exit_soft - expected_soft) < 1e-9
        assert abs(result.exit_hard - expected_hard) < 1e-9


# ===========================================================================
# Exit Confidence
# ===========================================================================

class TestExitConfidence:

    def test_exit_confidence_formula(self, engine):
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=0.7, regime_confidence=0.8,
        )
        result = engine.compute(req)
        expected = 1.0 - 0.7  # 0.3
        assert abs(result.exit_confidence - expected) < 1e-9

    def test_exit_confidence_clipped_low(self, engine):
        """mu=1 -> raw=0 -> clipped to 1e-6."""
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=1.0, regime_confidence=0.5,
        )
        result = engine.compute(req)
        assert abs(result.exit_confidence - 1e-6) < 1e-12

    def test_exit_confidence_clipped_high(self, engine):
        """mu=0 -> raw=1 -> clipped to 1-1e-6."""
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=0.0, regime_confidence=0.5,
        )
        result = engine.compute(req)
        assert abs(result.exit_confidence - (1.0 - 1e-6)) < 1e-12

    def test_exit_confidence_in_bounds(self, engine, base_request):
        result = engine.compute(base_request)
        assert 1e-6 <= result.exit_confidence <= 1.0 - 1e-6


# ===========================================================================
# Expected Move %
# ===========================================================================

class TestExpectedMove:

    def test_expected_move_formula(self, engine):
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",  # vol_mult=1.0
            sigma_sq=0.0025,  # sigma = 0.05
            mu=0.5, regime_confidence=0.5,
        )
        result = engine.compute(req)
        expected = math.sqrt(0.0025) * 1.0 * 100.0  # 0.05 * 100 = 5.0
        assert abs(result.expected_move_pct - expected) < 1e-9

    def test_expected_move_positive(self, engine, base_request):
        result = engine.compute(base_request)
        assert result.expected_move_pct > 0

    def test_shock_regime_higher_move(self, engine):
        req_trend = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=0.5, regime_confidence=0.5,
        )
        req_shock = ConfidenceZoneRequest(
            current_price=100.0, regime="SHOCK",
            sigma_sq=0.04, mu=0.5, regime_confidence=0.5,
        )
        trend_result = engine.compute(req_trend)
        shock_result = engine.compute(req_shock)
        assert shock_result.expected_move_pct > trend_result.expected_move_pct


# ===========================================================================
# Volatility Adjusted Stop
# ===========================================================================

class TestVolAdjustedStop:

    def test_vol_adjusted_stop_formula(self, engine):
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",  # vol_mult=1.0
            sigma_sq=0.01,  # sigma = 0.1
            mu=0.5, regime_confidence=0.5,
        )
        result = engine.compute(req)
        expected = 100.0 * (1.0 - 0.1 * 1.0 * 2.0)  # 100 * 0.8 = 80.0
        assert abs(result.vol_adjusted_stop - expected) < 1e-9

    def test_vol_adjusted_stop_below_price(self, engine, base_request):
        result = engine.compute(base_request)
        assert result.vol_adjusted_stop < base_request.current_price

    def test_vol_adjusted_stop_above_exit_hard(self, engine, base_request):
        """Vol stop at 2.0 sigma should be above hard exit at 2.5 sigma."""
        result = engine.compute(base_request)
        assert result.vol_adjusted_stop > result.exit_hard


# ===========================================================================
# Meta-Uncertainty
# ===========================================================================

class TestMetaUncertainty:

    def test_meta_uncertainty_formula(self, engine):
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=0.7, regime_confidence=0.8,
        )
        result = engine.compute(req)
        expected = 1.0 - (0.7 * 0.8)  # 0.44
        assert abs(result.meta_uncertainty - expected) < 1e-9

    def test_meta_uncertainty_clipped_low(self, engine):
        """mu=1, regime_confidence=1 -> raw=0 -> clipped to 1e-6."""
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=1.0, regime_confidence=1.0,
        )
        result = engine.compute(req)
        assert abs(result.meta_uncertainty - 1e-6) < 1e-12

    def test_meta_uncertainty_clipped_high(self, engine):
        """mu=0 -> raw=1 -> clipped to 1-1e-6."""
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=0.0, regime_confidence=0.0,
        )
        result = engine.compute(req)
        assert abs(result.meta_uncertainty - (1.0 - 1e-6)) < 1e-12

    def test_meta_uncertainty_in_bounds(self, engine, base_request):
        result = engine.compute(base_request)
        assert 1e-6 <= result.meta_uncertainty <= 1.0 - 1e-6

    def test_meta_uncertainty_always_present(self, engine, base_request):
        """R4: meta_uncertainty must always be visible."""
        result = engine.compute(base_request)
        assert hasattr(result, "meta_uncertainty")


# ===========================================================================
# Regime Volatility Multiplier
# ===========================================================================

class TestRegimeMultiplier:

    @pytest.mark.parametrize("regime,expected_mult", [
        ("TRENDING", 1.0),
        ("RANGING", 0.8),
        ("HIGH_VOL", 1.8),
        ("SHOCK", 3.0),
        ("UNKNOWN", 2.5),
    ])
    def test_known_regime_multipliers(self, engine, regime, expected_mult):
        req = ConfidenceZoneRequest(
            current_price=100.0, regime=regime,
            sigma_sq=0.01, mu=0.5, regime_confidence=0.5,
        )
        result = engine.compute(req)
        sigma = math.sqrt(0.01)
        expected_move = sigma * expected_mult * 100.0
        assert abs(result.expected_move_pct - expected_move) < 1e-9

    def test_unknown_regime_defaults_to_2_5(self, engine):
        """Unrecognized regime string defaults to 2.5 multiplier."""
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="SOME_NEW_REGIME",
            sigma_sq=0.01, mu=0.5, regime_confidence=0.5,
        )
        result = engine.compute(req)
        sigma = math.sqrt(0.01)
        expected_move = sigma * 2.5 * 100.0
        assert abs(result.expected_move_pct - expected_move) < 1e-9

    def test_ranging_smaller_zones_than_shock(self, engine):
        """RANGING (0.8) should produce tighter zones than SHOCK (3.0)."""
        req_ranging = ConfidenceZoneRequest(
            current_price=100.0, regime="RANGING",
            sigma_sq=0.04, mu=0.5, regime_confidence=0.5,
        )
        req_shock = ConfidenceZoneRequest(
            current_price=100.0, regime="SHOCK",
            sigma_sq=0.04, mu=0.5, regime_confidence=0.5,
        )
        ranging = engine.compute(req_ranging)
        shock = engine.compute(req_shock)
        ranging_width = ranging.entry_upper - ranging.entry_lower
        shock_width = shock.entry_upper - shock.entry_lower
        assert shock_width > ranging_width


# ===========================================================================
# Input Validation
# ===========================================================================

class TestInputValidation:

    def test_nan_price_raises(self, engine):
        req = ConfidenceZoneRequest(
            current_price=float("nan"), regime="TRENDING",
            sigma_sq=0.04, mu=0.5, regime_confidence=0.5,
        )
        with pytest.raises(ValueError, match="current_price"):
            engine.compute(req)

    def test_inf_price_raises(self, engine):
        req = ConfidenceZoneRequest(
            current_price=float("inf"), regime="TRENDING",
            sigma_sq=0.04, mu=0.5, regime_confidence=0.5,
        )
        with pytest.raises(ValueError, match="current_price"):
            engine.compute(req)

    def test_negative_price_raises(self, engine):
        req = ConfidenceZoneRequest(
            current_price=-1.0, regime="TRENDING",
            sigma_sq=0.04, mu=0.5, regime_confidence=0.5,
        )
        with pytest.raises(ValueError, match="current_price"):
            engine.compute(req)

    def test_nan_sigma_sq_raises(self, engine):
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=float("nan"), mu=0.5, regime_confidence=0.5,
        )
        with pytest.raises(ValueError, match="sigma_sq"):
            engine.compute(req)

    def test_negative_sigma_sq_raises(self, engine):
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=-0.01, mu=0.5, regime_confidence=0.5,
        )
        with pytest.raises(ValueError, match="sigma_sq"):
            engine.compute(req)

    def test_nan_mu_raises(self, engine):
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=float("nan"), regime_confidence=0.5,
        )
        with pytest.raises(ValueError, match="mu"):
            engine.compute(req)

    def test_negative_mu_raises(self, engine):
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=-0.1, regime_confidence=0.5,
        )
        with pytest.raises(ValueError, match="mu"):
            engine.compute(req)

    def test_zero_price_accepted(self, engine):
        """Price=0 is technically valid (no NaN/Inf, >= 0)."""
        req = ConfidenceZoneRequest(
            current_price=0.0, regime="TRENDING",
            sigma_sq=0.04, mu=0.5, regime_confidence=0.5,
        )
        result = engine.compute(req)
        assert result.entry_lower == 0.0
        assert result.entry_upper == 0.0

    def test_zero_sigma_sq_uses_floor(self, engine):
        """sigma_sq=0 -> floored to 1e-10."""
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.0, mu=0.5, regime_confidence=0.5,
        )
        result = engine.compute(req)
        # Should produce tiny but non-zero zones
        assert result.expected_move_pct > 0


# ===========================================================================
# Determinism (DET-07)
# ===========================================================================

class TestDeterminism:

    def test_identical_inputs_identical_outputs(self, engine):
        """Same inputs must produce bit-identical outputs."""
        req = ConfidenceZoneRequest(
            current_price=42000.0, regime="HIGH_VOL",
            sigma_sq=0.09, mu=0.65, regime_confidence=0.72,
        )
        r1 = engine.compute(req)
        r2 = engine.compute(req)

        assert r1.entry_lower == r2.entry_lower
        assert r1.entry_upper == r2.entry_upper
        assert r1.entry_confidence == r2.entry_confidence
        assert r1.exit_soft == r2.exit_soft
        assert r1.exit_hard == r2.exit_hard
        assert r1.exit_confidence == r2.exit_confidence
        assert r1.expected_move_pct == r2.expected_move_pct
        assert r1.vol_adjusted_stop == r2.vol_adjusted_stop
        assert r1.meta_uncertainty == r2.meta_uncertainty

    def test_fresh_engine_same_result(self):
        """Different engine instances produce identical results."""
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="TRENDING",
            sigma_sq=0.04, mu=0.7, regime_confidence=0.8,
        )
        r1 = ConfidenceZoneEngine().compute(req)
        r2 = ConfidenceZoneEngine().compute(req)
        assert r1.entry_lower == r2.entry_lower
        assert r1.meta_uncertainty == r2.meta_uncertainty


# ===========================================================================
# R1: No signal output
# ===========================================================================

class TestNoSignals:

    def test_no_buy_sell_attributes(self, engine, base_request):
        """R1: output must not contain signal-like attributes."""
        result = engine.compute(base_request)
        for attr in ["signal", "buy", "sell", "action", "direction", "side"]:
            assert not hasattr(result, attr)


# ===========================================================================
# Edge cases / realistic scenarios
# ===========================================================================

class TestEdgeCases:

    def test_btc_price(self, engine):
        """Realistic BTC price scenario from FAS smoke test."""
        req = ConfidenceZoneRequest(
            current_price=65000.0, regime="TRENDING",
            sigma_sq=0.04, mu=0.7, regime_confidence=0.8,
        )
        result = engine.compute(req)
        assert result.entry_lower < 65000.0 < result.entry_upper
        assert result.exit_soft < 65000.0
        assert result.exit_hard < result.exit_soft

    def test_very_low_volatility(self, engine):
        """Near-zero sigma_sq should produce tight zones."""
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="RANGING",
            sigma_sq=1e-12, mu=0.9, regime_confidence=0.95,
        )
        result = engine.compute(req)
        width = result.entry_upper - result.entry_lower
        assert width < 0.01  # Very tight

    def test_very_high_volatility(self, engine):
        """Large sigma_sq in SHOCK should produce wide zones."""
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="SHOCK",
            sigma_sq=1.0, mu=0.3, regime_confidence=0.2,
        )
        result = engine.compute(req)
        width = result.entry_upper - result.entry_lower
        assert width > 100.0  # Very wide

    def test_mu_zero_maximum_uncertainty(self, engine):
        """mu=0 means zero information -> maximum meta_uncertainty."""
        req = ConfidenceZoneRequest(
            current_price=100.0, regime="UNKNOWN",
            sigma_sq=0.04, mu=0.0, regime_confidence=0.0,
        )
        result = engine.compute(req)
        assert result.meta_uncertainty == pytest.approx(1.0 - 1e-6, abs=1e-12)
        assert result.entry_confidence == pytest.approx(1e-6, abs=1e-12)
        assert result.exit_confidence == pytest.approx(1.0 - 1e-6, abs=1e-12)
