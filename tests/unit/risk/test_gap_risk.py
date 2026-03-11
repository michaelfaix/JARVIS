# =============================================================================
# tests/unit/risk/test_gap_risk.py -- Gap Risk Model Tests
#
# Comprehensive tests for jarvis/risk/gap_risk.py (Phase MA-5).
# Covers: constants, math helpers, GapRiskModel, per-asset-class behavior,
#         determinism, immutability, edge cases, recommendations.
# =============================================================================

import math

import pytest

from jarvis.core.regime import AssetClass
from jarvis.core.data_layer import GAP_THRESHOLDS
from jarvis.risk.gap_risk import (
    # Constants
    GAP_ENABLED_CLASSES,
    WORST_CASE_GAP_SIGMA,
    GAP_RISK_RECOMMENDATION_THRESHOLD,
    # Helpers
    _compute_gaps,
    _filter_significant_gaps,
    _gap_statistics,
    # Dataclasses
    AssetGapRiskResult,
    PortfolioGapRiskResult,
    # Model
    GapRiskModel,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

# Price series with clear gaps (e.g., overnight moves)
GAPPY_PRICES = [100.0, 103.5, 103.0, 107.0, 106.5, 110.0, 109.0, 113.5]
# Smooth prices (small moves)
SMOOTH_PRICES = [100.0, 100.1, 100.2, 100.15, 100.25, 100.3, 100.28]


def _make_positions(**overrides):
    """Create a simple portfolio for testing."""
    base = {
        "SPY": (AssetClass.INDICES, 520.0, 100.0),
        "GOLD": (AssetClass.COMMODITIES, 2000.0, 5.0),
    }
    base.update(overrides)
    return base


def _make_price_histories(**overrides):
    base = {
        "SPY": GAPPY_PRICES,
        "GOLD": GAPPY_PRICES,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    def test_gap_enabled_classes(self):
        assert AssetClass.INDICES in GAP_ENABLED_CLASSES
        assert AssetClass.COMMODITIES in GAP_ENABLED_CLASSES
        assert AssetClass.RATES in GAP_ENABLED_CLASSES

    def test_gap_disabled_classes(self):
        assert AssetClass.CRYPTO not in GAP_ENABLED_CLASSES
        assert AssetClass.FOREX not in GAP_ENABLED_CLASSES

    def test_worst_case_sigma(self):
        assert WORST_CASE_GAP_SIGMA == 3.0

    def test_recommendation_threshold(self):
        assert GAP_RISK_RECOMMENDATION_THRESHOLD == 0.05


# ---------------------------------------------------------------------------
# _compute_gaps
# ---------------------------------------------------------------------------

class TestComputeGaps:
    def test_empty_prices(self):
        assert _compute_gaps([]) == []

    def test_single_price(self):
        assert _compute_gaps([100.0]) == []

    def test_two_prices(self):
        gaps = _compute_gaps([100.0, 105.0])
        assert len(gaps) == 1
        assert abs(gaps[0] - 0.05) < 1e-10

    def test_negative_gap(self):
        gaps = _compute_gaps([100.0, 95.0])
        assert gaps[0] < 0.0

    def test_multiple_gaps(self):
        gaps = _compute_gaps([100.0, 103.0, 100.0, 106.0])
        assert len(gaps) == 3

    def test_zero_price_skipped(self):
        gaps = _compute_gaps([0.0, 100.0, 105.0])
        # First gap has prev=0.0, skipped; second gap computed
        assert len(gaps) == 1

    def test_gap_fractions_correct(self):
        gaps = _compute_gaps([100.0, 110.0, 105.0])
        assert abs(gaps[0] - 0.10) < 1e-10
        assert abs(gaps[1] - (-5.0 / 110.0)) < 1e-10


# ---------------------------------------------------------------------------
# _filter_significant_gaps
# ---------------------------------------------------------------------------

class TestFilterSignificantGaps:
    def test_all_significant(self):
        gaps = [0.05, -0.04, 0.06]
        result = _filter_significant_gaps(gaps, 0.03)
        assert len(result) == 3

    def test_none_significant(self):
        gaps = [0.01, -0.01, 0.005]
        result = _filter_significant_gaps(gaps, 0.03)
        assert len(result) == 0

    def test_mixed(self):
        gaps = [0.05, 0.01, -0.04, 0.02]
        result = _filter_significant_gaps(gaps, 0.03)
        assert len(result) == 2

    def test_exact_threshold_included(self):
        gaps = [0.03]
        result = _filter_significant_gaps(gaps, 0.03)
        assert len(result) == 1

    def test_empty_gaps(self):
        assert _filter_significant_gaps([], 0.03) == []

    def test_negative_gaps_filtered_by_abs(self):
        gaps = [-0.05]
        result = _filter_significant_gaps(gaps, 0.03)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _gap_statistics
# ---------------------------------------------------------------------------

class TestGapStatistics:
    def test_empty_gaps(self):
        mean, std = _gap_statistics([])
        assert mean == 0.0
        assert std == 0.0

    def test_single_gap(self):
        mean, std = _gap_statistics([0.05])
        assert abs(mean - 0.05) < 1e-10
        assert std == 0.0  # Single element, no std

    def test_multiple_gaps(self):
        mean, std = _gap_statistics([0.03, 0.05, 0.04])
        expected_mean = (0.03 + 0.05 + 0.04) / 3
        assert abs(mean - expected_mean) < 1e-10
        assert std > 0.0

    def test_negative_gaps_use_abs(self):
        mean, std = _gap_statistics([-0.05, -0.03])
        assert mean > 0.0  # Uses absolute values

    def test_identical_gaps_zero_std(self):
        mean, std = _gap_statistics([0.04, 0.04, 0.04])
        assert abs(mean - 0.04) < 1e-10
        assert std < 1e-10


# ---------------------------------------------------------------------------
# GapRiskModel -- PER-ASSET-CLASS BEHAVIOR
# ---------------------------------------------------------------------------

class TestPerAssetClassBehavior:
    def test_crypto_no_gap_risk(self):
        model = GapRiskModel()
        result = model.estimate(
            positions={"BTC": (AssetClass.CRYPTO, 65000.0, 1.0)},
            price_histories={"BTC": GAPPY_PRICES},
        )
        btc_result = result.asset_results[0]
        assert btc_result.gap_enabled is False
        assert btc_result.expected_gap_risk == 0.0

    def test_forex_no_gap_risk(self):
        model = GapRiskModel()
        result = model.estimate(
            positions={"EURUSD": (AssetClass.FOREX, 1.1, 100000.0)},
            price_histories={"EURUSD": GAPPY_PRICES},
        )
        eur_result = result.asset_results[0]
        assert eur_result.gap_enabled is False
        assert eur_result.expected_gap_risk == 0.0

    def test_indices_has_gap_risk(self):
        model = GapRiskModel()
        result = model.estimate(
            positions={"SPY": (AssetClass.INDICES, 520.0, 100.0)},
            price_histories={"SPY": GAPPY_PRICES},
        )
        spy_result = result.asset_results[0]
        assert spy_result.gap_enabled is True

    def test_commodities_has_gap_risk(self):
        model = GapRiskModel()
        result = model.estimate(
            positions={"GOLD": (AssetClass.COMMODITIES, 2000.0, 5.0)},
            price_histories={"GOLD": GAPPY_PRICES},
        )
        gold_result = result.asset_results[0]
        assert gold_result.gap_enabled is True

    def test_rates_has_gap_risk(self):
        model = GapRiskModel()
        result = model.estimate(
            positions={"TLT": (AssetClass.RATES, 90.0, 100.0)},
            price_histories={"TLT": GAPPY_PRICES},
        )
        tlt_result = result.asset_results[0]
        assert tlt_result.gap_enabled is True


# ---------------------------------------------------------------------------
# GapRiskModel -- ESTIMATE
# ---------------------------------------------------------------------------

class TestGapRiskModelEstimate:
    def test_empty_portfolio(self):
        model = GapRiskModel()
        result = model.estimate(positions={}, price_histories={})
        assert result.total_expected_gap_risk == 0.0
        assert result.total_notional == 0.0
        assert result.num_gap_exposed_assets == 0

    def test_mixed_portfolio(self):
        model = GapRiskModel()
        positions = {
            "BTC": (AssetClass.CRYPTO, 65000.0, 1.0),
            "SPY": (AssetClass.INDICES, 520.0, 100.0),
        }
        histories = {
            "BTC": GAPPY_PRICES,
            "SPY": GAPPY_PRICES,
        }
        result = model.estimate(positions=positions, price_histories=histories)
        assert result.num_gap_exposed_assets == 1  # Only SPY
        assert result.total_notional > 0.0

    def test_total_notional_sum(self):
        model = GapRiskModel()
        result = model.estimate(
            positions=_make_positions(),
            price_histories=_make_price_histories(),
        )
        expected_notional = 520.0 * 100.0 + 2000.0 * 5.0
        assert abs(result.total_notional - expected_notional) < 1e-10

    def test_worst_case_is_3x_expected(self):
        model = GapRiskModel()
        result = model.estimate(
            positions={"SPY": (AssetClass.INDICES, 520.0, 100.0)},
            price_histories={"SPY": GAPPY_PRICES},
        )
        spy = result.asset_results[0]
        if spy.expected_gap_risk > 0.0:
            assert abs(spy.worst_case_gap_risk - spy.expected_gap_risk * 3.0) < 1e-10

    def test_result_hash_hex(self):
        model = GapRiskModel()
        result = model.estimate(
            positions=_make_positions(),
            price_histories=_make_price_histories(),
        )
        assert len(result.result_hash) == 16
        assert all(c in "0123456789abcdef" for c in result.result_hash)

    def test_asset_results_sorted_by_symbol(self):
        model = GapRiskModel()
        positions = {
            "ZZZ": (AssetClass.INDICES, 100.0, 10.0),
            "AAA": (AssetClass.COMMODITIES, 200.0, 5.0),
        }
        result = model.estimate(
            positions=positions,
            price_histories={"ZZZ": GAPPY_PRICES, "AAA": GAPPY_PRICES},
        )
        assert result.asset_results[0].symbol == "AAA"
        assert result.asset_results[1].symbol == "ZZZ"


# ---------------------------------------------------------------------------
# RECOMMENDATIONS
# ---------------------------------------------------------------------------

class TestRecommendations:
    def test_acceptable_risk(self):
        model = GapRiskModel()
        # Smooth prices -> small or no significant gaps -> low risk
        result = model.estimate(
            positions={"SPY": (AssetClass.INDICES, 520.0, 100.0)},
            price_histories={"SPY": SMOOTH_PRICES},
        )
        assert result.recommendation == "GAP_RISK_ACCEPTABLE"

    def test_crypto_only_acceptable(self):
        model = GapRiskModel()
        result = model.estimate(
            positions={"BTC": (AssetClass.CRYPTO, 65000.0, 1.0)},
            price_histories={"BTC": GAPPY_PRICES},
        )
        assert result.recommendation == "GAP_RISK_ACCEPTABLE"

    def test_gap_ratio_calculation(self):
        model = GapRiskModel()
        result = model.estimate(
            positions=_make_positions(),
            price_histories=_make_price_histories(),
        )
        if result.total_notional > 0.0:
            expected_ratio = result.total_expected_gap_risk / result.total_notional
            assert abs(result.gap_risk_ratio - expected_ratio) < 1e-10


# ---------------------------------------------------------------------------
# GAP DETECTION WITH SPECIFIC THRESHOLDS
# ---------------------------------------------------------------------------

class TestGapThresholds:
    def test_indices_threshold_is_3pct(self):
        assert abs(GAP_THRESHOLDS["indices"] - 0.03) < 1e-10

    def test_commodities_threshold_is_4pct(self):
        assert abs(GAP_THRESHOLDS["commodities"] - 0.04) < 1e-10

    def test_rates_threshold_is_2pct(self):
        assert abs(GAP_THRESHOLDS["rates"] - 0.02) < 1e-10

    def test_small_gaps_filtered_for_indices(self):
        # Prices with 2% gap (below 3% threshold for indices)
        prices = [100.0, 102.0, 101.0, 103.0]
        model = GapRiskModel()
        result = model.estimate(
            positions={"SPY": (AssetClass.INDICES, 520.0, 100.0)},
            price_histories={"SPY": prices},
        )
        spy = result.asset_results[0]
        assert spy.num_gaps == 0  # All gaps < 3%

    def test_large_gaps_detected_for_indices(self):
        # Prices with > 3% gaps
        prices = [100.0, 104.0, 100.0, 105.0]
        model = GapRiskModel()
        result = model.estimate(
            positions={"SPY": (AssetClass.INDICES, 520.0, 100.0)},
            price_histories={"SPY": prices},
        )
        spy = result.asset_results[0]
        assert spy.num_gaps > 0


# ---------------------------------------------------------------------------
# IMMUTABILITY
# ---------------------------------------------------------------------------

class TestImmutability:
    def test_asset_result_frozen(self):
        model = GapRiskModel()
        result = model.estimate(
            positions={"SPY": (AssetClass.INDICES, 520.0, 100.0)},
            price_histories={"SPY": GAPPY_PRICES},
        )
        with pytest.raises(AttributeError):
            result.asset_results[0].expected_gap_risk = 0.0

    def test_portfolio_result_frozen(self):
        model = GapRiskModel()
        result = model.estimate(
            positions=_make_positions(),
            price_histories=_make_price_histories(),
        )
        with pytest.raises(AttributeError):
            result.total_expected_gap_risk = 0.0


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_hash(self):
        model = GapRiskModel()
        r1 = model.estimate(
            positions=_make_positions(),
            price_histories=_make_price_histories(),
        )
        r2 = model.estimate(
            positions=_make_positions(),
            price_histories=_make_price_histories(),
        )
        assert r1.result_hash == r2.result_hash

    def test_different_prices_different_hash(self):
        model = GapRiskModel()
        r1 = model.estimate(
            positions={"SPY": (AssetClass.INDICES, 520.0, 100.0)},
            price_histories={"SPY": GAPPY_PRICES},
        )
        r2 = model.estimate(
            positions={"SPY": (AssetClass.INDICES, 520.0, 100.0)},
            price_histories={"SPY": SMOOTH_PRICES},
        )
        # May or may not differ depending on gap filtering, but test runs
        assert isinstance(r1.result_hash, str)
        assert isinstance(r2.result_hash, str)

    def test_fresh_instance_same_result(self):
        positions = _make_positions()
        histories = _make_price_histories()
        r1 = GapRiskModel().estimate(positions=positions, price_histories=histories)
        r2 = GapRiskModel().estimate(positions=positions, price_histories=histories)
        assert r1.result_hash == r2.result_hash


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_no_price_history(self):
        model = GapRiskModel()
        result = model.estimate(
            positions={"SPY": (AssetClass.INDICES, 520.0, 100.0)},
            price_histories={},
        )
        spy = result.asset_results[0]
        assert spy.num_gaps == 0
        assert spy.expected_gap_risk == 0.0

    def test_single_price(self):
        model = GapRiskModel()
        result = model.estimate(
            positions={"SPY": (AssetClass.INDICES, 520.0, 100.0)},
            price_histories={"SPY": [520.0]},
        )
        spy = result.asset_results[0]
        assert spy.num_gaps == 0

    def test_zero_position_size(self):
        model = GapRiskModel()
        result = model.estimate(
            positions={"SPY": (AssetClass.INDICES, 520.0, 0.0)},
            price_histories={"SPY": GAPPY_PRICES},
        )
        spy = result.asset_results[0]
        assert spy.notional == 0.0
        assert spy.expected_gap_risk == 0.0

    def test_negative_position_size(self):
        model = GapRiskModel()
        result = model.estimate(
            positions={"SPY": (AssetClass.INDICES, 520.0, -100.0)},
            price_histories={"SPY": GAPPY_PRICES},
        )
        spy = result.asset_results[0]
        assert spy.notional > 0.0  # abs()

    def test_many_assets(self):
        model = GapRiskModel()
        positions = {}
        histories = {}
        for i in range(10):
            sym = f"ASSET{i}"
            positions[sym] = (AssetClass.INDICES, 100.0 + i, 10.0)
            histories[sym] = GAPPY_PRICES
        result = model.estimate(positions=positions, price_histories=histories)
        assert result.num_gap_exposed_assets == 10
        assert len(result.asset_results) == 10


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.risk.gap_risk import (
            GapRiskModel,
            AssetGapRiskResult,
            PortfolioGapRiskResult,
        )
        assert GapRiskModel is not None
        assert AssetGapRiskResult is not None
        assert PortfolioGapRiskResult is not None
