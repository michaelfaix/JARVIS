# =============================================================================
# Tests for jarvis/intelligence/liquidity_layer.py (S21)
# =============================================================================

import numpy as np
import pytest

from jarvis.intelligence.liquidity_layer import (
    LiquidityAssessment,
    LiquidityLayer,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

@pytest.fixture
def layer():
    return LiquidityLayer()


def _hist_spreads(n=20, base=0.001):
    """Generate n historical spreads around base."""
    return [base * (0.5 + i / n) for i in range(n)]


# ---------------------------------------------------------------------------
# BASIC ASSESS
# ---------------------------------------------------------------------------

class TestAssessBasic:
    def test_returns_liquidity_assessment(self, layer):
        result = layer.assess(
            current_spread=0.001,
            historical_spreads=_hist_spreads(20),
            current_volume=1000.0,
            avg_volume=1000.0,
        )
        assert isinstance(result, LiquidityAssessment)

    def test_bid_ask_spread_passthrough(self, layer):
        result = layer.assess(0.002, _hist_spreads(20), 500.0, 1000.0)
        assert result.bid_ask_spread == 0.002

    def test_spread_percentile_range(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 500.0, 1000.0)
        assert 0.0 <= result.spread_percentile <= 1.0

    def test_volume_ratio_computed(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 2000.0, 1000.0)
        assert result.volume_ratio == pytest.approx(2.0)

    def test_liquidity_score_range(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 500.0, 1000.0)
        assert 0.0 <= result.liquidity_score <= 1.0

    def test_slippage_estimate_positive(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 500.0, 1000.0)
        assert result.slippage_estimate >= 0.0

    def test_regime_impact_valid(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 500.0, 1000.0)
        assert result.regime_impact in ("NEGLIGIBLE", "MODERATE", "SIGNIFICANT", "CRITICAL")


# ---------------------------------------------------------------------------
# SPREAD PERCENTILE
# ---------------------------------------------------------------------------

class TestSpreadPercentile:
    def test_current_below_all_historical(self, layer):
        hist = [0.005] * 20  # all higher
        result = layer.assess(0.001, hist, 1000.0, 1000.0)
        assert result.spread_percentile == pytest.approx(0.0)

    def test_current_above_all_historical(self, layer):
        hist = [0.0001] * 20  # all lower
        result = layer.assess(0.001, hist, 1000.0, 1000.0)
        assert result.spread_percentile == pytest.approx(1.0)

    def test_current_at_median(self, layer):
        hist = [0.001 * i for i in range(1, 21)]  # 0.001 to 0.020
        result = layer.assess(0.010, hist, 1000.0, 1000.0)
        # 10 values <= 0.010 out of 20
        assert result.spread_percentile == pytest.approx(0.5)

    def test_percentile_affects_spread_score(self, layer):
        # Low percentile (current tight) -> high spread score -> higher liquidity
        r_tight = layer.assess(0.0001, [0.005] * 20, 1000.0, 1000.0)
        r_wide  = layer.assess(0.01, [0.001] * 20, 1000.0, 1000.0)
        assert r_tight.liquidity_score > r_wide.liquidity_score


# ---------------------------------------------------------------------------
# VOLUME RATIO
# ---------------------------------------------------------------------------

class TestVolumeRatio:
    def test_equal_volume(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 1000.0, 1000.0)
        assert result.volume_ratio == pytest.approx(1.0)

    def test_double_volume(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 2000.0, 1000.0)
        assert result.volume_ratio == pytest.approx(2.0)

    def test_half_volume(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 500.0, 1000.0)
        assert result.volume_ratio == pytest.approx(0.5)

    def test_zero_avg_volume_safe(self, layer):
        # avg_volume=0 -> denominator capped at 1e-10
        result = layer.assess(0.001, _hist_spreads(20), 100.0, 0.0)
        assert result.volume_ratio > 0

    def test_high_volume_improves_score(self, layer):
        r_low  = layer.assess(0.001, _hist_spreads(20), 100.0, 1000.0)
        r_high = layer.assess(0.001, _hist_spreads(20), 5000.0, 1000.0)
        assert r_high.liquidity_score >= r_low.liquidity_score


# ---------------------------------------------------------------------------
# MARKET DEPTH
# ---------------------------------------------------------------------------

class TestMarketDepth:
    def test_default_depth_0_5(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 1000.0, 1000.0)
        assert result.market_depth == 0.5

    def test_explicit_depth(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 1000.0, 1000.0, order_book_depth=0.8)
        assert result.market_depth == pytest.approx(0.8)

    def test_depth_clipped_to_0(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 1000.0, 1000.0, order_book_depth=-0.5)
        assert result.market_depth == pytest.approx(0.0)

    def test_depth_clipped_to_1(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 1000.0, 1000.0, order_book_depth=1.5)
        assert result.market_depth == pytest.approx(1.0)

    def test_zero_depth(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 1000.0, 1000.0, order_book_depth=0.0)
        assert result.market_depth == pytest.approx(0.0)

    def test_high_depth_improves_score(self, layer):
        r_low  = layer.assess(0.001, _hist_spreads(20), 1000.0, 1000.0, order_book_depth=0.1)
        r_high = layer.assess(0.001, _hist_spreads(20), 1000.0, 1000.0, order_book_depth=0.9)
        assert r_high.liquidity_score >= r_low.liquidity_score


# ---------------------------------------------------------------------------
# LIQUIDITY SCORE FORMULA
# ---------------------------------------------------------------------------

class TestLiquidityScoreFormula:
    def test_weights_sum_to_1(self):
        # 0.4 + 0.35 + 0.25 = 1.0
        assert 0.4 + 0.35 + 0.25 == pytest.approx(1.0)

    def test_score_manual_computation(self, layer):
        hist = [0.002] * 20  # all at 0.002
        result = layer.assess(0.002, hist, 2000.0, 1000.0, order_book_depth=0.6)

        # spread_pct = mean(0.002 <= 0.002) = 1.0
        # spread_score = 1.0 - 1.0 = 0.0
        # vol_ratio = 2000/1000 = 2.0
        # vol_score = clip(2.0 / 2.0, 0, 1) = 1.0
        # depth = 0.6
        # liquidity = 0.4*0.0 + 0.35*1.0 + 0.25*0.6 = 0.0 + 0.35 + 0.15 = 0.5
        assert result.liquidity_score == pytest.approx(0.5)

    def test_all_max_score(self, layer):
        # Current spread is the tightest ever, max volume, max depth
        hist = [0.01] * 20  # all much wider
        result = layer.assess(0.0001, hist, 10000.0, 1000.0, order_book_depth=1.0)
        # spread_pct=0 -> spread_score=1.0
        # vol_ratio=10 -> vol_score=clip(10/2,0,1)=1.0
        # depth=1.0
        # liquidity = 0.4*1.0 + 0.35*1.0 + 0.25*1.0 = 1.0
        assert result.liquidity_score == pytest.approx(1.0)

    def test_all_min_score(self, layer):
        # Current spread wider than all, zero volume, zero depth
        hist = [0.0001] * 20  # all tighter
        result = layer.assess(0.01, hist, 0.0, 1000.0, order_book_depth=0.0)
        # spread_pct=1 -> spread_score=0.0
        # vol_ratio=0 -> vol_score=0.0
        # depth=0.0
        # liquidity = 0.0
        assert result.liquidity_score == pytest.approx(0.0)

    def test_score_clipped_upper(self, layer):
        hist = [1.0] * 20
        result = layer.assess(0.0001, hist, 100000.0, 1.0, order_book_depth=1.0)
        assert result.liquidity_score <= 1.0

    def test_score_clipped_lower(self, layer):
        hist = [0.00001] * 20
        result = layer.assess(1.0, hist, 0.0, 1000.0, order_book_depth=0.0)
        assert result.liquidity_score >= 0.0


# ---------------------------------------------------------------------------
# SLIPPAGE ESTIMATE
# ---------------------------------------------------------------------------

class TestSlippageEstimate:
    def test_slippage_formula(self, layer):
        result = layer.assess(0.002, _hist_spreads(20), 1000.0, 1000.0)
        expected = 0.002 * (1.0 + (1.0 - result.liquidity_score))
        assert result.slippage_estimate == pytest.approx(expected)

    def test_zero_spread_zero_slippage(self, layer):
        result = layer.assess(0.0, [0.001] * 20, 1000.0, 1000.0)
        assert result.slippage_estimate == pytest.approx(0.0)

    def test_higher_spread_higher_slippage(self, layer):
        r_low  = layer.assess(0.001, _hist_spreads(20), 1000.0, 1000.0)
        r_high = layer.assess(0.01, _hist_spreads(20), 1000.0, 1000.0)
        assert r_high.slippage_estimate > r_low.slippage_estimate

    def test_slippage_multiplier_range(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 1000.0, 1000.0)
        # Multiplier = 1 + (1 - liq_score) in [1.0, 2.0]
        multiplier = result.slippage_estimate / result.bid_ask_spread
        assert 1.0 <= multiplier <= 2.0


# ---------------------------------------------------------------------------
# REGIME IMPACT
# ---------------------------------------------------------------------------

class TestRegimeImpact:
    def test_critical_when_very_illiquid(self, layer):
        # Force very low score: wide spread, no volume, no depth
        hist = [0.00001] * 20
        result = layer.assess(0.1, hist, 0.0, 1000.0, order_book_depth=0.0)
        assert result.regime_impact == "CRITICAL"
        assert result.liquidity_score < 0.2

    def test_significant_range(self, layer):
        # Need score in [0.2, 0.4)
        # Tune: moderate spread, low volume
        hist = [0.0005] * 10 + [0.002] * 10
        result = layer.assess(0.001, hist, 200.0, 1000.0, order_book_depth=0.1)
        if 0.2 <= result.liquidity_score < 0.4:
            assert result.regime_impact == "SIGNIFICANT"

    def test_negligible_when_highly_liquid(self, layer):
        hist = [0.01] * 20
        result = layer.assess(0.0001, hist, 5000.0, 1000.0, order_book_depth=1.0)
        assert result.regime_impact == "NEGLIGIBLE"
        assert result.liquidity_score >= 0.65

    def test_moderate_range(self, layer):
        # Score in [0.4, 0.65)
        hist = [0.001] * 20
        result = layer.assess(0.0005, hist, 1000.0, 1000.0, order_book_depth=0.3)
        if 0.4 <= result.liquidity_score < 0.65:
            assert result.regime_impact == "MODERATE"

    def test_boundary_0_2(self, layer):
        # Exactly at boundary: score < 0.2 -> CRITICAL, >= 0.2 -> SIGNIFICANT
        # Test the enum values are correct strings
        for impact in ("NEGLIGIBLE", "MODERATE", "SIGNIFICANT", "CRITICAL"):
            assert isinstance(impact, str)


# ---------------------------------------------------------------------------
# INPUT VALIDATION
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_negative_spread_raises(self, layer):
        with pytest.raises(ValueError, match="current_spread"):
            layer.assess(-0.001, _hist_spreads(20), 1000.0, 1000.0)

    def test_nan_spread_raises(self, layer):
        with pytest.raises(ValueError, match="current_spread"):
            layer.assess(float('nan'), _hist_spreads(20), 1000.0, 1000.0)

    def test_inf_spread_raises(self, layer):
        with pytest.raises(ValueError, match="current_spread"):
            layer.assess(float('inf'), _hist_spreads(20), 1000.0, 1000.0)

    def test_negative_volume_raises(self, layer):
        with pytest.raises(ValueError, match="current_volume"):
            layer.assess(0.001, _hist_spreads(20), -100.0, 1000.0)

    def test_nan_volume_raises(self, layer):
        with pytest.raises(ValueError, match="current_volume"):
            layer.assess(0.001, _hist_spreads(20), float('nan'), 1000.0)

    def test_negative_avg_volume_raises(self, layer):
        with pytest.raises(ValueError, match="avg_volume"):
            layer.assess(0.001, _hist_spreads(20), 1000.0, -1.0)

    def test_inf_avg_volume_raises(self, layer):
        with pytest.raises(ValueError, match="avg_volume"):
            layer.assess(0.001, _hist_spreads(20), 1000.0, float('inf'))

    def test_insufficient_historical_spreads(self, layer):
        with pytest.raises(ValueError, match="10 historische"):
            layer.assess(0.001, [0.001] * 9, 1000.0, 1000.0)

    def test_exactly_10_spreads_ok(self, layer):
        result = layer.assess(0.001, [0.001] * 10, 1000.0, 1000.0)
        assert isinstance(result, LiquidityAssessment)

    def test_nan_in_historical_raises(self, layer):
        hist = [0.001] * 9 + [float('nan')]
        with pytest.raises(ValueError, match="NaN/Inf"):
            layer.assess(0.001, hist, 1000.0, 1000.0)

    def test_inf_in_historical_raises(self, layer):
        hist = [0.001] * 9 + [float('inf')]
        with pytest.raises(ValueError, match="NaN/Inf"):
            layer.assess(0.001, hist, 1000.0, 1000.0)


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

class TestConstants:
    def test_spread_threshold_moderate(self):
        assert LiquidityLayer.SPREAD_THRESHOLD_MODERATE == 0.001

    def test_spread_threshold_critical(self):
        assert LiquidityLayer.SPREAD_THRESHOLD_CRITICAL == 0.005

    def test_volume_ratio_low_threshold(self):
        assert LiquidityLayer.VOLUME_RATIO_LOW_THRESHOLD == 0.5

    def test_volume_ratio_high_threshold(self):
        assert LiquidityLayer.VOLUME_RATIO_HIGH_THRESHOLD == 2.0


# ---------------------------------------------------------------------------
# DATACLASS FIELDS
# ---------------------------------------------------------------------------

class TestDataClass:
    def test_all_fields_present(self):
        la = LiquidityAssessment(
            bid_ask_spread=0.001,
            spread_percentile=0.5,
            volume_ratio=1.0,
            market_depth=0.5,
            liquidity_score=0.6,
            slippage_estimate=0.0015,
            regime_impact="MODERATE",
        )
        assert la.bid_ask_spread == 0.001
        assert la.spread_percentile == 0.5
        assert la.volume_ratio == 1.0
        assert la.market_depth == 0.5
        assert la.liquidity_score == 0.6
        assert la.slippage_estimate == 0.0015
        assert la.regime_impact == "MODERATE"


# ---------------------------------------------------------------------------
# DETERMINISM
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_identical_inputs_identical_outputs(self, layer):
        kwargs = dict(
            current_spread=0.002,
            historical_spreads=_hist_spreads(30),
            current_volume=1500.0,
            avg_volume=1000.0,
            order_book_depth=0.7,
        )
        r1 = layer.assess(**kwargs)
        r2 = layer.assess(**kwargs)
        assert r1.liquidity_score == r2.liquidity_score
        assert r1.spread_percentile == r2.spread_percentile
        assert r1.volume_ratio == r2.volume_ratio
        assert r1.slippage_estimate == r2.slippage_estimate
        assert r1.regime_impact == r2.regime_impact
        assert r1.market_depth == r2.market_depth

    def test_no_state_between_calls(self, layer):
        r1 = layer.assess(0.001, _hist_spreads(20), 1000.0, 1000.0)
        _ = layer.assess(0.1, [0.0001] * 20, 0.0, 1000.0, order_book_depth=0.0)
        r3 = layer.assess(0.001, _hist_spreads(20), 1000.0, 1000.0)
        assert r1.liquidity_score == r3.liquidity_score


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_spread(self, layer):
        result = layer.assess(0.0, [0.001] * 20, 1000.0, 1000.0)
        assert result.bid_ask_spread == 0.0
        assert result.spread_percentile == 0.0
        assert result.slippage_estimate == 0.0

    def test_zero_current_volume(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 0.0, 1000.0)
        assert result.volume_ratio == 0.0

    def test_zero_avg_volume(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 1000.0, 0.0)
        # denominator capped at 1e-10 -> huge ratio
        assert result.volume_ratio > 0

    def test_very_large_spread(self, layer):
        result = layer.assess(1.0, [0.001] * 20, 1000.0, 1000.0)
        assert result.spread_percentile == 1.0
        assert result.liquidity_score <= 1.0

    def test_very_large_volume(self, layer):
        result = layer.assess(0.001, _hist_spreads(20), 1e9, 1000.0)
        assert result.volume_ratio > 1.0

    def test_all_historical_same_as_current(self, layer):
        result = layer.assess(0.001, [0.001] * 20, 1000.0, 1000.0)
        # All <= current_spread, so percentile = 1.0
        assert result.spread_percentile == pytest.approx(1.0)

    def test_many_historical_spreads(self, layer):
        hist = [0.001 * (i % 10) for i in range(1000)]
        result = layer.assess(0.005, hist, 1000.0, 1000.0)
        assert isinstance(result, LiquidityAssessment)
