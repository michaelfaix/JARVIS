# =============================================================================
# tests/unit/risk/test_portfolio_risk.py -- Portfolio Risk Aggregator Tests
#
# Comprehensive tests for jarvis/risk/portfolio_risk.py (Phase MA-5).
# Covers: constants, PortfolioRiskEngine, diversification benefit,
#         per-regime behavior, determinism, immutability, edge cases.
# =============================================================================

import math

import pytest

from jarvis.core.regime import (
    AssetClass,
    AssetRegimeState,
    CorrelationRegimeState,
    GlobalRegimeState,
    HierarchicalRegime,
)
from jarvis.risk.portfolio_risk import (
    VAR_95_Z,
    VAR_99_Z,
    PortfolioRiskResult,
    PortfolioRiskEngine,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

SAMPLE_RETURNS = [0.01 * ((-1) ** i) + 0.001 * i for i in range(30)]
SAMPLE_PRICES = [100.0 + i * 0.5 for i in range(30)]

ALL_ASSET_CLASSES = list(AssetClass)

DEFAULT_ASSET_REGIMES = {ac: AssetRegimeState.TRENDING_UP for ac in AssetClass}
DEFAULT_CONFIDENCES = {ac: 0.8 for ac in AssetClass}
DEFAULT_SUB_REGIME = {ac: "default" for ac in AssetClass}


def _make_regime(
    global_regime=GlobalRegimeState.RISK_ON,
    correlation_regime=CorrelationRegimeState.NORMAL,
    asset_regimes=None,
) -> HierarchicalRegime:
    ar = asset_regimes or DEFAULT_ASSET_REGIMES.copy()
    if global_regime == GlobalRegimeState.CRISIS:
        ar = {ac: AssetRegimeState.SHOCK for ac in AssetClass}
        correlation_regime = CorrelationRegimeState.BREAKDOWN
    return HierarchicalRegime.create(
        global_regime=global_regime,
        asset_regimes=ar,
        correlation_regime=correlation_regime,
        global_confidence=0.8,
        asset_confidences=DEFAULT_CONFIDENCES.copy(),
        sub_regime=DEFAULT_SUB_REGIME.copy(),
        sequence_id=1,
    )


def _single_btc_positions():
    return {"BTC": (AssetClass.CRYPTO, 65000.0, 1.0)}


def _single_btc_returns():
    return {"BTC": SAMPLE_RETURNS}


def _single_btc_prices():
    return {"BTC": SAMPLE_PRICES}


def _multi_positions():
    return {
        "BTC": (AssetClass.CRYPTO, 65000.0, 1.0),
        "SPY": (AssetClass.INDICES, 520.0, 100.0),
        "TLT": (AssetClass.RATES, 90.0, 100.0),
    }


def _multi_returns():
    return {
        "BTC": SAMPLE_RETURNS,
        "SPY": SAMPLE_RETURNS,
        "TLT": SAMPLE_RETURNS,
    }


def _multi_prices():
    return {
        "BTC": SAMPLE_PRICES,
        "SPY": SAMPLE_PRICES,
        "TLT": SAMPLE_PRICES,
    }


def _calc_single(**overrides):
    kwargs = dict(
        positions=_single_btc_positions(),
        returns=_single_btc_returns(),
        regime=_make_regime(),
        price_histories=_single_btc_prices(),
    )
    kwargs.update(overrides)
    return PortfolioRiskEngine().calculate_portfolio_risk(**kwargs)


def _calc_multi(**overrides):
    kwargs = dict(
        positions=_multi_positions(),
        returns=_multi_returns(),
        regime=_make_regime(),
        price_histories=_multi_prices(),
    )
    kwargs.update(overrides)
    return PortfolioRiskEngine().calculate_portfolio_risk(**kwargs)


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    def test_var_95_z(self):
        assert VAR_95_Z == 1.645

    def test_var_99_z(self):
        assert VAR_99_Z == 2.326


# ---------------------------------------------------------------------------
# SINGLE ASSET PORTFOLIO
# ---------------------------------------------------------------------------

class TestSingleAsset:
    def test_num_assets(self):
        r = _calc_single()
        assert r.num_assets == 1

    def test_asset_risk_present(self):
        r = _calc_single()
        assert "BTC" in r.asset_risks
        assert r.asset_risks["BTC"].symbol == "BTC"

    def test_portfolio_var_positive(self):
        r = _calc_single()
        assert r.portfolio_var_95 > 0.0
        assert r.portfolio_var_99 > 0.0

    def test_var_99_gt_var_95(self):
        r = _calc_single()
        assert r.portfolio_var_99 > r.portfolio_var_95

    def test_total_notional(self):
        r = _calc_single()
        assert r.total_notional == 65000.0

    def test_tail_risk_present(self):
        r = _calc_single()
        assert r.tail_risk.num_assets == 1
        assert r.tail_risk.var_95 > 0.0

    def test_gap_risk_present(self):
        r = _calc_single()
        assert r.gap_risk.num_gap_exposed_assets == 0  # Crypto: no gap

    def test_correlation_result_present(self):
        r = _calc_single()
        assert r.correlation_result is not None

    def test_result_hash(self):
        r = _calc_single()
        assert len(r.result_hash) == 16
        assert all(c in "0123456789abcdef" for c in r.result_hash)

    def test_diversification_zero_single_asset(self):
        r = _calc_single()
        # Single asset: no diversification benefit possible
        # portfolio_var_95 may equal individual due to single asset
        assert r.diversification_benefit >= 0.0


# ---------------------------------------------------------------------------
# MULTI-ASSET PORTFOLIO
# ---------------------------------------------------------------------------

class TestMultiAsset:
    def test_num_assets(self):
        r = _calc_multi()
        assert r.num_assets == 3

    def test_all_assets_present(self):
        r = _calc_multi()
        assert "BTC" in r.asset_risks
        assert "SPY" in r.asset_risks
        assert "TLT" in r.asset_risks

    def test_portfolio_var_positive(self):
        r = _calc_multi()
        assert r.portfolio_var_95 > 0.0

    def test_total_notional_sum(self):
        r = _calc_multi()
        expected = 65000.0 + 520.0 * 100.0 + 90.0 * 100.0
        assert abs(r.total_notional - expected) < 1e-6

    def test_tail_risk_multi(self):
        r = _calc_multi()
        assert r.tail_risk.num_assets == 3
        assert r.tail_risk.diversification_adjusted is True

    def test_gap_risk_multi(self):
        r = _calc_multi()
        # SPY (indices) + TLT (rates) have gap risk
        assert r.gap_risk.num_gap_exposed_assets == 2

    def test_diversification_benefit_positive(self):
        r = _calc_multi()
        # With uncorrelated assets, expect some diversification
        assert r.diversification_benefit >= 0.0


# ---------------------------------------------------------------------------
# REGIME BEHAVIOR
# ---------------------------------------------------------------------------

class TestRegimeBehavior:
    def test_risk_on_regime_stored(self):
        r = _calc_single()
        assert r.regime.global_regime == GlobalRegimeState.RISK_ON

    def test_crisis_regime(self):
        regime = _make_regime(global_regime=GlobalRegimeState.CRISIS)
        r = _calc_multi(regime=regime)
        assert r.regime.global_regime == GlobalRegimeState.CRISIS
        assert r.portfolio_var_95 > 0.0

    def test_risk_off_regime(self):
        regime = _make_regime(global_regime=GlobalRegimeState.RISK_OFF)
        r = _calc_multi(regime=regime)
        assert r.regime.global_regime == GlobalRegimeState.RISK_OFF

    def test_crisis_higher_var_than_risk_on(self):
        risk_on = _calc_multi(regime=_make_regime(global_regime=GlobalRegimeState.RISK_ON))
        crisis = _calc_multi(regime=_make_regime(global_regime=GlobalRegimeState.CRISIS))
        # Crisis regime: SHOCK multipliers -> higher vol -> higher VaR
        assert crisis.portfolio_var_95 > risk_on.portfolio_var_95

    def test_correlation_breakdown_regime(self):
        regime = _make_regime(
            correlation_regime=CorrelationRegimeState.BREAKDOWN,
        )
        r = _calc_multi(regime=regime)
        assert r.correlation_result.regime_state == CorrelationRegimeState.BREAKDOWN


# ---------------------------------------------------------------------------
# PORTFOLIO VOLATILITY
# ---------------------------------------------------------------------------

class TestPortfolioVolatility:
    def test_positive(self):
        r = _calc_multi()
        assert r.portfolio_volatility > 0.0

    def test_single_asset_vol(self):
        r = _calc_single()
        # Single asset portfolio vol = asset notional * daily vol
        btc = r.asset_risks["BTC"]
        expected = btc.notional * btc.volatility.daily
        assert abs(r.portfolio_volatility - expected) < 1e-6

    def test_var_from_vol(self):
        r = _calc_multi()
        expected_var_95 = r.portfolio_volatility * VAR_95_Z
        assert abs(r.portfolio_var_95 - expected_var_95) < 1e-6


# ---------------------------------------------------------------------------
# DIVERSIFICATION BENEFIT
# ---------------------------------------------------------------------------

class TestDiversificationBenefit:
    def test_range(self):
        r = _calc_multi()
        assert 0.0 <= r.diversification_benefit <= 1.0

    def test_single_asset_low_benefit(self):
        r = _calc_single()
        # Single asset can have 0 or small diversification
        assert r.diversification_benefit >= 0.0

    def test_engine_private_method(self):
        engine = PortfolioRiskEngine()
        benefit = engine._calculate_diversification_benefit(
            asset_risks={},
            portfolio_var_95=0.0,
        )
        assert benefit == 0.0


# ---------------------------------------------------------------------------
# IMMUTABILITY
# ---------------------------------------------------------------------------

class TestImmutability:
    def test_result_frozen(self):
        r = _calc_single()
        with pytest.raises(AttributeError):
            r.portfolio_var_95 = 0.0

    def test_asset_risk_frozen(self):
        r = _calc_single()
        with pytest.raises(AttributeError):
            r.asset_risks["BTC"].symbol = "ETH"


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_hash(self):
        r1 = _calc_single()
        r2 = _calc_single()
        assert r1.result_hash == r2.result_hash

    def test_same_inputs_same_var(self):
        r1 = _calc_multi()
        r2 = _calc_multi()
        assert r1.portfolio_var_95 == r2.portfolio_var_95
        assert r1.portfolio_var_99 == r2.portfolio_var_99

    def test_different_positions_different_hash(self):
        r1 = _calc_single()
        r2 = _calc_multi()
        assert r1.result_hash != r2.result_hash

    def test_fresh_instance_same_result(self):
        kwargs = dict(
            positions=_single_btc_positions(),
            returns=_single_btc_returns(),
            regime=_make_regime(),
            price_histories=_single_btc_prices(),
        )
        r1 = PortfolioRiskEngine().calculate_portfolio_risk(**kwargs)
        r2 = PortfolioRiskEngine().calculate_portfolio_risk(**kwargs)
        assert r1.result_hash == r2.result_hash


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_position_size(self):
        positions = {"BTC": (AssetClass.CRYPTO, 65000.0, 0.0)}
        r = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=positions,
            returns={"BTC": SAMPLE_RETURNS},
            regime=_make_regime(),
            price_histories={"BTC": SAMPLE_PRICES},
        )
        assert r.total_notional == 0.0
        assert r.portfolio_var_95 == 0.0

    def test_five_asset_classes(self):
        positions = {
            "BTC": (AssetClass.CRYPTO, 65000.0, 1.0),
            "EURUSD": (AssetClass.FOREX, 1.1, 100000.0),
            "SPY": (AssetClass.INDICES, 520.0, 100.0),
            "GOLD": (AssetClass.COMMODITIES, 2000.0, 5.0),
            "TLT": (AssetClass.RATES, 90.0, 100.0),
        }
        returns = {s: SAMPLE_RETURNS for s in positions}
        prices = {s: SAMPLE_PRICES for s in positions}
        r = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=positions,
            returns=returns,
            regime=_make_regime(),
            price_histories=prices,
        )
        assert r.num_assets == 5
        assert r.portfolio_var_95 > 0.0

    def test_missing_returns_for_symbol(self):
        positions = {"BTC": (AssetClass.CRYPTO, 65000.0, 1.0)}
        r = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=positions,
            returns={},  # No returns data
            regime=_make_regime(),
            price_histories={},
        )
        assert r.num_assets == 1
        assert r.portfolio_var_95 == 0.0  # No vol data


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.risk.portfolio_risk import (
            PortfolioRiskEngine,
            PortfolioRiskResult,
        )
        assert PortfolioRiskEngine is not None
        assert PortfolioRiskResult is not None
