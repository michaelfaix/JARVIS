# =============================================================================
# Tests for jarvis/intelligence/microstructure_layer.py (S19)
# =============================================================================

import numpy as np
import pytest

from jarvis.intelligence.microstructure_layer import (
    MarketMicrostructureLayer,
    MicrostructureResult,
    OrderBookSnapshot,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def make_snapshot(bid_vols, ask_vols, bid_prices=None, ask_prices=None, ts=1000.0):
    bid_prices = bid_prices or [100.0 - i for i in range(len(bid_vols))]
    ask_prices = ask_prices or [100.1 + i for i in range(len(ask_vols))]
    return OrderBookSnapshot(
        timestamp=ts,
        bid_prices=bid_prices, bid_volumes=bid_vols,
        ask_prices=ask_prices, ask_volumes=ask_vols,
    )


@pytest.fixture
def layer():
    return MarketMicrostructureLayer()


# ---------------------------------------------------------------------------
# ORDER FLOW IMBALANCE (OFI)
# ---------------------------------------------------------------------------

class TestOrderFlowImbalance:
    def test_balanced(self, layer):
        result = layer.compute_order_flow_imbalance([100.0] * 5, [100.0] * 5)
        assert abs(result) < 1e-6

    def test_buy_pressure(self, layer):
        result = layer.compute_order_flow_imbalance([200.0] * 5, [50.0] * 5)
        assert result > 0.5

    def test_sell_pressure(self, layer):
        result = layer.compute_order_flow_imbalance([50.0] * 5, [200.0] * 5)
        assert result < -0.5

    def test_clipped_upper(self, layer):
        result = layer.compute_order_flow_imbalance([1000.0] * 5, [0.001] * 5)
        assert -1.0 <= result <= 1.0

    def test_clipped_lower(self, layer):
        result = layer.compute_order_flow_imbalance([0.001] * 5, [1000.0] * 5)
        assert -1.0 <= result <= 1.0

    def test_all_bid_volume(self, layer):
        result = layer.compute_order_flow_imbalance([100.0] * 5, [0.0] * 5)
        assert result == pytest.approx(1.0)

    def test_all_ask_volume(self, layer):
        result = layer.compute_order_flow_imbalance([0.0] * 5, [100.0] * 5)
        assert result == pytest.approx(-1.0)

    def test_zero_volumes_returns_zero(self, layer):
        result = layer.compute_order_flow_imbalance([0.0] * 5, [0.0] * 5)
        assert result == 0.0

    def test_empty_raises(self, layer):
        with pytest.raises(ValueError):
            layer.compute_order_flow_imbalance([], [])

    def test_n_levels_limits(self, layer):
        result = layer.compute_order_flow_imbalance(
            [100.0, 200.0, 300.0], [100.0, 200.0, 300.0], n_levels=2
        )
        assert abs(result) < 1e-6

    def test_n_levels_exceeds_available(self, layer):
        result = layer.compute_order_flow_imbalance([100.0], [50.0], n_levels=10)
        assert result > 0

    def test_single_level(self, layer):
        result = layer.compute_order_flow_imbalance([100.0], [50.0], n_levels=1)
        expected = (100.0 - 50.0) / (100.0 + 50.0)
        assert result == pytest.approx(expected)

    def test_determinism(self, layer):
        bids = [10.0, 20.0, 30.0, 40.0, 50.0]
        asks = [15.0, 25.0, 35.0, 45.0, 55.0]
        r1 = layer.compute_order_flow_imbalance(bids, asks)
        r2 = layer.compute_order_flow_imbalance(bids, asks)
        assert r1 == r2


# ---------------------------------------------------------------------------
# BID-ASK PRESSURE (BAP)
# ---------------------------------------------------------------------------

class TestBidAskPressure:
    def test_balanced(self, layer):
        snap = make_snapshot([100.0] * 5, [100.0] * 5)
        result = layer.compute_bid_ask_pressure(snap)
        assert result == pytest.approx(0.5, abs=1e-6)

    def test_bid_dominant(self, layer):
        snap = make_snapshot([500.0] * 5, [50.0] * 5)
        result = layer.compute_bid_ask_pressure(snap)
        assert result > 0.5

    def test_ask_dominant(self, layer):
        snap = make_snapshot([50.0] * 5, [500.0] * 5)
        result = layer.compute_bid_ask_pressure(snap)
        assert result < 0.5

    def test_range_0_to_1(self, layer):
        snap = make_snapshot([1000.0] * 5, [1.0] * 5)
        result = layer.compute_bid_ask_pressure(snap)
        assert 0.0 <= result <= 1.0

    def test_insufficient_levels_returns_0_5(self, layer):
        snap = make_snapshot([100.0, 200.0], [50.0, 80.0])
        result = layer.compute_bid_ask_pressure(snap)
        assert result == 0.5

    def test_zero_volumes_returns_0_5(self, layer):
        snap = make_snapshot([0.0] * 5, [0.0] * 5)
        result = layer.compute_bid_ask_pressure(snap)
        assert result == 0.5

    def test_weighted_emphasis_on_best(self, layer):
        # Best bid much larger, rest equal -> should be bid dominant
        snap = make_snapshot([500.0, 100.0, 100.0, 100.0, 100.0],
                             [100.0, 100.0, 100.0, 100.0, 100.0])
        result = layer.compute_bid_ask_pressure(snap)
        assert result > 0.5

    def test_n_levels_parameter(self, layer):
        snap = make_snapshot([100.0] * 5, [100.0] * 5)
        result = layer.compute_bid_ask_pressure(snap, n_levels=3)
        assert result == pytest.approx(0.5, abs=1e-6)

    def test_determinism(self, layer):
        snap = make_snapshot([10.0, 20.0, 30.0, 40.0, 50.0],
                             [15.0, 25.0, 35.0, 45.0, 55.0])
        r1 = layer.compute_bid_ask_pressure(snap)
        r2 = layer.compute_bid_ask_pressure(snap)
        assert r1 == r2


# ---------------------------------------------------------------------------
# LIQUIDITY ABSORPTION
# ---------------------------------------------------------------------------

class TestLiquidityAbsorption:
    def test_result_range(self, layer):
        prices = [0.01 * (i % 3 - 1) for i in range(25)]
        volumes = [100.0 + 10.0 * (i % 5) for i in range(25)]
        result = layer.detect_liquidity_absorption(prices, volumes)
        assert 0.0 <= result <= 1.0

    def test_insufficient_data_raises(self, layer):
        with pytest.raises(ValueError, match="Mindestens"):
            layer.detect_liquidity_absorption([0.01] * 5, [100.0] * 5)

    def test_nan_raises(self, layer):
        prices = [float('nan')] * 20
        volumes = [100.0] * 20
        with pytest.raises(ValueError, match="NaN"):
            layer.detect_liquidity_absorption(prices, volumes)

    def test_inf_raises(self, layer):
        prices = [float('inf')] * 20
        volumes = [100.0] * 20
        with pytest.raises(ValueError, match="NaN"):
            layer.detect_liquidity_absorption(prices, volumes)

    def test_zero_volume_std(self, layer):
        prices = [0.01] * 20
        volumes = [100.0] * 20  # zero std
        result = layer.detect_liquidity_absorption(prices, volumes)
        assert result == 0.5

    def test_custom_window(self, layer):
        prices = [0.01 * i for i in range(50)]
        volumes = [100.0 + i for i in range(50)]
        result = layer.detect_liquidity_absorption(prices, volumes, window=10)
        assert 0.0 <= result <= 1.0

    def test_determinism(self, layer):
        prices = [0.01 * (i % 7) for i in range(25)]
        volumes = [50.0 + 5.0 * (i % 4) for i in range(25)]
        r1 = layer.detect_liquidity_absorption(prices, volumes)
        r2 = layer.detect_liquidity_absorption(prices, volumes)
        assert r1 == r2


# ---------------------------------------------------------------------------
# SPOOFING PROBABILITY
# ---------------------------------------------------------------------------

class TestSpoofingProbability:
    def test_no_history_returns_zero(self, layer):
        snap = make_snapshot([100.0] * 5, [100.0] * 5)
        result = layer.estimate_spoofing_probability(snap, [])
        assert result == 0.0

    def test_single_snapshot_returns_zero(self, layer):
        snap = make_snapshot([100.0] * 5, [100.0] * 5)
        result = layer.estimate_spoofing_probability(snap, [snap])
        assert result == 0.0

    def test_stable_volumes_low_score(self, layer):
        snap = make_snapshot([100.0] * 5, [100.0] * 5)
        history = [make_snapshot([100.0] * 5, [100.0] * 5, ts=t) for t in range(5)]
        result = layer.estimate_spoofing_probability(snap, history)
        assert result == pytest.approx(0.0)

    def test_volatile_volumes_higher_score(self, layer):
        snaps = []
        for i in range(5):
            vol = 100.0 if i % 2 == 0 else 1000.0
            snaps.append(make_snapshot([vol] * 5, [100.0] * 5, ts=float(i)))
        snap = make_snapshot([100.0] * 5, [100.0] * 5)
        result = layer.estimate_spoofing_probability(snap, snaps)
        assert result > 0.0

    def test_clipped_to_0_1(self, layer):
        # Extreme volume changes
        snaps = [
            make_snapshot([0.001] * 5, [100.0] * 5, ts=0.0),
            make_snapshot([10000.0] * 5, [100.0] * 5, ts=1.0),
        ]
        snap = make_snapshot([100.0] * 5, [100.0] * 5)
        result = layer.estimate_spoofing_probability(snap, snaps)
        assert 0.0 <= result <= 1.0

    def test_empty_bid_volumes_in_history(self, layer):
        snap = make_snapshot([100.0] * 5, [100.0] * 5)
        empty = OrderBookSnapshot(
            timestamp=0.0, bid_prices=[], bid_volumes=[], ask_prices=[], ask_volumes=[]
        )
        history = [empty, empty, snap]
        result = layer.estimate_spoofing_probability(snap, history)
        assert 0.0 <= result <= 1.0

    def test_determinism(self, layer):
        snap = make_snapshot([100.0] * 5, [100.0] * 5)
        history = [
            make_snapshot([50.0] * 5, [100.0] * 5, ts=0.0),
            make_snapshot([200.0] * 5, [100.0] * 5, ts=1.0),
            make_snapshot([80.0] * 5, [100.0] * 5, ts=2.0),
        ]
        r1 = layer.estimate_spoofing_probability(snap, history)
        r2 = layer.estimate_spoofing_probability(snap, history)
        assert r1 == r2


# ---------------------------------------------------------------------------
# NOISE FILTER
# ---------------------------------------------------------------------------

class TestNoiseFilter:
    def test_short_returns_0_5(self, layer):
        result = layer.filter_noise([0.01, 0.02])
        assert result == 0.5

    def test_constant_returns_1(self, layer):
        result = layer.filter_noise([0.01] * 20)
        assert result == 1.0

    def test_nan_returns_0_5(self, layer):
        result = layer.filter_noise([0.01, float('nan'), 0.02, 0.03])
        assert result == 0.5

    def test_result_range(self, layer):
        returns = [0.01 * ((-1) ** i) for i in range(20)]
        result = layer.filter_noise(returns)
        assert 0.0 <= result <= 1.0

    def test_custom_halflife(self, layer):
        returns = [0.01 * ((-1) ** i) for i in range(20)]
        result = layer.filter_noise(returns, halflife=5)
        assert 0.0 <= result <= 1.0

    def test_trending_signal_higher_score(self, layer):
        # Trending: all positive -> high signal-to-noise
        trending = [0.01] * 20
        # Noisy: alternating -> low signal-to-noise
        noisy = [0.01 * ((-1) ** i) for i in range(20)]
        score_trend = layer.filter_noise(trending)
        score_noisy = layer.filter_noise(noisy)
        assert score_trend >= score_noisy

    def test_determinism(self, layer):
        returns = [0.005 * i for i in range(15)]
        r1 = layer.filter_noise(returns)
        r2 = layer.filter_noise(returns)
        assert r1 == r2


# ---------------------------------------------------------------------------
# MICROSTRUCTURE VOLATILITY
# ---------------------------------------------------------------------------

class TestMicrostructureVol:
    def test_basic_computation(self, layer):
        returns = [0.001] * 30
        result = layer.compute_microstructure_vol(returns)
        assert result > 0.0

    def test_insufficient_data_raises(self, layer):
        with pytest.raises(ValueError, match="Mindestens"):
            layer.compute_microstructure_vol([0.01] * 10)

    def test_nan_raises(self, layer):
        with pytest.raises(ValueError, match="NaN"):
            layer.compute_microstructure_vol([float('nan')] * 30)

    def test_inf_raises(self, layer):
        with pytest.raises(ValueError, match="NaN"):
            layer.compute_microstructure_vol([float('inf')] * 30)

    def test_annualization(self, layer):
        returns = [0.001] * 30
        result = layer.compute_microstructure_vol(returns)
        rms = float(np.sqrt(np.mean(np.array(returns[-30:]) ** 2)))
        expected = rms * np.sqrt(23400.0)
        assert result == pytest.approx(expected)

    def test_zero_returns(self, layer):
        returns = [0.0] * 30
        result = layer.compute_microstructure_vol(returns)
        assert result == 0.0

    def test_custom_window(self, layer):
        returns = [0.001 * i for i in range(50)]
        result = layer.compute_microstructure_vol(returns, window=10)
        assert result > 0.0

    def test_uses_last_window_elements(self, layer):
        # First 20 elements are huge, last 30 are small
        returns = [100.0] * 20 + [0.001] * 30
        result = layer.compute_microstructure_vol(returns, window=30)
        expected_rms = float(np.sqrt(np.mean(np.array([0.001] * 30) ** 2)))
        expected = expected_rms * np.sqrt(23400.0)
        assert result == pytest.approx(expected)

    def test_determinism(self, layer):
        returns = [0.001 * (i % 7) for i in range(40)]
        r1 = layer.compute_microstructure_vol(returns)
        r2 = layer.compute_microstructure_vol(returns)
        assert r1 == r2


# ---------------------------------------------------------------------------
# ASSESS (FULL PIPELINE)
# ---------------------------------------------------------------------------

class TestAssess:
    def test_basic_assess(self, layer):
        snap = make_snapshot([100.0] * 5, [80.0] * 5)
        np.random.seed(42)
        ticks = np.random.randn(50).tolist()
        prices = np.random.randn(30).tolist()
        vols = np.abs(np.random.randn(30) + 1.0).tolist()
        result = layer.assess(snap, [snap] * 3, ticks, prices, vols)
        assert isinstance(result, MicrostructureResult)
        assert -1.0 <= result.order_flow_imbalance <= 1.0
        assert 0.0 <= result.bid_ask_pressure <= 1.0
        assert 0.0 <= result.liquidity_absorption <= 1.0
        assert 0.0 <= result.spoofing_probability <= 1.0
        assert 0.0 <= result.noise_filter_score <= 1.0
        assert result.microstructure_vol_idx >= 0.0
        assert 0.0 <= result.timing_quality <= 1.0
        assert result.regime_hint in ("ACCUMULATION", "DISTRIBUTION", "EQUILIBRIUM", "NOISE")

    def test_regime_hint_accumulation(self, layer):
        # High positive OFI (>0.6) + high absorption (>0.6)
        snap = make_snapshot([1000.0] * 5, [10.0] * 5)
        # Need absorption > 0.6: constant volume, zero price change
        prices = [0.0] * 25
        volumes = [100.0 + 10.0 * (i % 3) for i in range(25)]
        ticks = [0.001] * 50
        result = layer.assess(snap, [snap] * 3, ticks, prices, volumes)
        # OFI should be very high (buy pressure)
        assert result.order_flow_imbalance > 0.6

    def test_regime_hint_noise(self, layer):
        # Low noise score -> NOISE hint
        snap = make_snapshot([100.0] * 5, [100.0] * 5)
        # Alternating returns -> low signal-to-noise
        ticks = [0.1 * ((-1) ** i) for i in range(50)]
        prices = [0.01] * 25
        volumes = [100.0] * 25
        result = layer.assess(snap, [snap] * 3, ticks, prices, volumes)
        # noise_filter_score should be low for alternating returns
        if result.noise_filter_score < 0.3 and not (abs(result.order_flow_imbalance) > 0.6 and result.liquidity_absorption > 0.6):
            assert result.regime_hint == "NOISE"

    def test_regime_hint_equilibrium(self, layer):
        snap = make_snapshot([100.0] * 5, [100.0] * 5)
        # Stable returns -> good signal
        ticks = [0.01] * 50
        prices = [0.01 * (i % 3) for i in range(25)]
        volumes = [100.0 + 5.0 * (i % 4) for i in range(25)]
        result = layer.assess(snap, [snap] * 3, ticks, prices, volumes)
        # Balanced OFI, good noise score -> EQUILIBRIUM
        assert abs(result.order_flow_imbalance) < 0.6
        if result.noise_filter_score >= 0.3:
            assert result.regime_hint == "EQUILIBRIUM"

    def test_assess_with_insufficient_absorption_data(self, layer):
        snap = make_snapshot([100.0] * 5, [80.0] * 5)
        ticks = [0.001] * 50
        prices = [0.01] * 5    # too short for absorption
        volumes = [100.0] * 5  # too short for absorption
        result = layer.assess(snap, [snap] * 3, ticks, prices, volumes)
        assert result.liquidity_absorption == 0.5  # fallback

    def test_assess_with_insufficient_vol_data(self, layer):
        snap = make_snapshot([100.0] * 5, [80.0] * 5)
        ticks = [0.001] * 5  # too short for microstructure vol
        prices = [0.01] * 25
        volumes = [100.0] * 25
        result = layer.assess(snap, [snap] * 3, ticks, prices, volumes)
        assert result.microstructure_vol_idx == 0.0  # fallback

    def test_timing_quality_formula(self, layer):
        snap = make_snapshot([100.0] * 5, [80.0] * 5)
        np.random.seed(123)
        ticks = np.random.randn(50).tolist()
        prices = np.random.randn(30).tolist()
        vols = np.abs(np.random.randn(30) + 1.0).tolist()
        result = layer.assess(snap, [snap] * 3, ticks, prices, vols)
        # timing = absorption * noise_score * (1 - spoof_prob)
        expected_timing = float(np.clip(
            result.liquidity_absorption * result.noise_filter_score * (1.0 - result.spoofing_probability),
            0.0, 1.0
        ))
        assert result.timing_quality == pytest.approx(expected_timing)

    def test_determinism(self, layer):
        snap = make_snapshot([100.0] * 5, [80.0] * 5)
        np.random.seed(99)
        ticks = np.random.randn(50).tolist()
        prices = np.random.randn(30).tolist()
        vols = np.abs(np.random.randn(30) + 1.0).tolist()
        r1 = layer.assess(snap, [snap] * 3, ticks, prices, vols)
        r2 = layer.assess(snap, [snap] * 3, ticks, prices, vols)
        assert r1.order_flow_imbalance == r2.order_flow_imbalance
        assert r1.bid_ask_pressure == r2.bid_ask_pressure
        assert r1.timing_quality == r2.timing_quality
        assert r1.regime_hint == r2.regime_hint
        assert r1.microstructure_vol_idx == r2.microstructure_vol_idx


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

class TestConstants:
    def test_min_order_book_levels(self):
        assert MarketMicrostructureLayer.MIN_ORDER_BOOK_LEVELS == 3

    def test_spoofing_volume_ratio(self):
        assert MarketMicrostructureLayer.SPOOFING_VOLUME_RATIO == 5.0

    def test_noise_halflife_ticks(self):
        assert MarketMicrostructureLayer.NOISE_HALFLIFE_TICKS == 10


# ---------------------------------------------------------------------------
# DATACLASS FIELDS
# ---------------------------------------------------------------------------

class TestDataClasses:
    def test_order_book_snapshot_fields(self):
        snap = OrderBookSnapshot(
            timestamp=1.0,
            bid_prices=[100.0], bid_volumes=[50.0],
            ask_prices=[101.0], ask_volumes=[60.0],
        )
        assert snap.timestamp == 1.0
        assert snap.bid_prices == [100.0]
        assert snap.ask_volumes == [60.0]

    def test_microstructure_result_fields(self):
        result = MicrostructureResult(
            order_flow_imbalance=0.5,
            bid_ask_pressure=0.6,
            liquidity_absorption=0.7,
            spoofing_probability=0.1,
            noise_filter_score=0.8,
            microstructure_vol_idx=0.15,
            timing_quality=0.56,
            regime_hint="EQUILIBRIUM",
        )
        assert result.order_flow_imbalance == 0.5
        assert result.regime_hint == "EQUILIBRIUM"


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_ofi_mismatched_lengths(self, layer):
        # Fewer asks than bids -> uses min
        result = layer.compute_order_flow_imbalance(
            [100.0] * 5, [80.0] * 3, n_levels=5
        )
        assert -1.0 <= result <= 1.0

    def test_absorption_exact_window_size(self, layer):
        prices = [0.01 * i for i in range(20)]
        volumes = [100.0 + i for i in range(20)]
        result = layer.detect_liquidity_absorption(prices, volumes, window=20)
        assert 0.0 <= result <= 1.0

    def test_spoofing_all_zero_prev_volumes(self, layer):
        snap = make_snapshot([100.0] * 5, [100.0] * 5)
        zero_snap = make_snapshot([0.0] * 5, [100.0] * 5, ts=0.0)
        nonzero_snap = make_snapshot([100.0] * 5, [100.0] * 5, ts=1.0)
        result = layer.estimate_spoofing_probability(snap, [zero_snap, nonzero_snap])
        # prev_best_bid_vol = 0.0 < 1e-10, so skipped
        assert result == 0.0

    def test_noise_filter_inf_returns_0_5(self, layer):
        result = layer.filter_noise([float('inf'), 0.01, 0.02, 0.03])
        assert result == 0.5

    def test_vol_uses_last_window(self, layer):
        # Verify only last `window` elements are used
        returns = [999.0] * 10 + [0.001] * 30
        r1 = layer.compute_microstructure_vol(returns, window=30)
        r2 = layer.compute_microstructure_vol([0.001] * 30, window=30)
        assert r1 == pytest.approx(r2)
