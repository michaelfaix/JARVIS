# =============================================================================
# tests/unit/risk/test_asset_risk.py -- Asset Risk Calculator Tests
#
# Comprehensive tests for jarvis/risk/asset_risk.py (Phase MA-5).
# Covers: EWMA volatility, tail risk, VaR/CVaR, regime multipliers,
#         per-asset-class behavior, determinism, immutability, edge cases.
# =============================================================================

import math

import pytest

from jarvis.core.regime import AssetClass, AssetRegimeState
from jarvis.risk.asset_risk import (
    # Constants
    ANNUALIZATION_FACTORS,
    EWMA_DECAY,
    VAR_95_Z,
    VAR_99_Z,
    VOL_MULTIPLIERS,
    TAIL_PARAMS,
    EXECUTION_COST_BPS,
    # Helpers
    _ewma_volatility,
    _compute_tail_var,
    _compute_cvar,
    # Dataclasses
    VolatilityEstimate,
    TailRiskEstimate,
    AssetRiskResult,
    # Calculator
    AssetRiskCalculator,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

SAMPLE_RETURNS = [0.01 * ((-1) ** i) + 0.001 * i for i in range(30)]

CALM_KWARGS = dict(
    symbol="BTC",
    asset_class=AssetClass.CRYPTO,
    returns=SAMPLE_RETURNS,
    current_price=65000.0,
    position_size=1.0,
    regime_state=AssetRegimeState.TRENDING_UP,
    liquidity_score=0.9,
)


def _calc(**overrides):
    kwargs = {**CALM_KWARGS, **overrides}
    return AssetRiskCalculator().calculate_risk(**kwargs)


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    def test_annualization_crypto(self):
        assert ANNUALIZATION_FACTORS[AssetClass.CRYPTO] == 365.0

    def test_annualization_forex(self):
        assert ANNUALIZATION_FACTORS[AssetClass.FOREX] == 252.0

    def test_annualization_all_present(self):
        for ac in AssetClass:
            assert ac in ANNUALIZATION_FACTORS

    def test_ewma_decay(self):
        assert EWMA_DECAY == 0.94

    def test_var_z_scores(self):
        assert VAR_95_Z == 1.645
        assert VAR_99_Z == 2.326

    def test_vol_multipliers_all_present(self):
        for ac in AssetClass:
            assert ac in VOL_MULTIPLIERS
            for state in AssetRegimeState:
                assert state in VOL_MULTIPLIERS[ac]

    def test_tail_params_all_present(self):
        for ac in AssetClass:
            assert ac in TAIL_PARAMS

    def test_execution_cost_all_present(self):
        for ac in AssetClass:
            assert ac in EXECUTION_COST_BPS

    def test_crypto_fattest_tails(self):
        assert TAIL_PARAMS[AssetClass.CRYPTO] < TAIL_PARAMS[AssetClass.RATES]

    def test_shock_highest_vol_multiplier(self):
        for ac in AssetClass:
            mults = VOL_MULTIPLIERS[ac]
            assert mults[AssetRegimeState.SHOCK] >= mults[AssetRegimeState.TRENDING_UP]


# ---------------------------------------------------------------------------
# EWMA VOLATILITY
# ---------------------------------------------------------------------------

class TestEWMAVolatility:
    def test_positive_output(self):
        vol = _ewma_volatility(SAMPLE_RETURNS)
        assert vol > 0.0

    def test_empty_returns(self):
        assert _ewma_volatility([]) == 0.0

    def test_single_return(self):
        assert _ewma_volatility([0.01]) == 0.0

    def test_constant_returns_low_vol(self):
        vol = _ewma_volatility([0.01] * 20)
        assert vol < 1e-10

    def test_volatile_returns_high_vol(self):
        volatile = [0.05 * ((-1) ** i) for i in range(20)]
        calm = [0.001 * ((-1) ** i) for i in range(20)]
        assert _ewma_volatility(volatile) > _ewma_volatility(calm)

    def test_more_data_still_works(self):
        vol = _ewma_volatility([0.01 * ((-1) ** i) for i in range(100)])
        assert vol > 0.0


# ---------------------------------------------------------------------------
# TAIL VAR
# ---------------------------------------------------------------------------

class TestTailVar:
    def test_positive_output(self):
        var = _compute_tail_var(SAMPLE_RETURNS, VAR_95_Z, 5.0)
        assert var > 0.0

    def test_fatter_tails_higher_var(self):
        fat = _compute_tail_var(SAMPLE_RETURNS, VAR_99_Z, 3.0)
        thin = _compute_tail_var(SAMPLE_RETURNS, VAR_99_Z, 10.0)
        assert fat > thin

    def test_higher_confidence_higher_var(self):
        var_95 = _compute_tail_var(SAMPLE_RETURNS, VAR_95_Z, 5.0)
        var_99 = _compute_tail_var(SAMPLE_RETURNS, VAR_99_Z, 5.0)
        assert var_99 > var_95

    def test_empty_returns(self):
        assert _compute_tail_var([], VAR_95_Z, 5.0) == 0.0

    def test_very_fat_tails(self):
        var = _compute_tail_var(SAMPLE_RETURNS, VAR_95_Z, 1.5)
        assert var > 0.0  # tail_decay <= 2 uses fixed factor


# ---------------------------------------------------------------------------
# CVAR
# ---------------------------------------------------------------------------

class TestCVaR:
    def test_cvar_gte_var(self):
        returns = [-0.05, -0.03, -0.01, 0.01, 0.02, 0.03]
        var = 0.02
        cvar = _compute_cvar(returns, var)
        assert cvar >= var

    def test_no_tail_returns(self):
        returns = [0.01, 0.02, 0.03]
        cvar = _compute_cvar(returns, 0.10)
        assert cvar == 0.10  # returns var_threshold if no tail

    def test_all_negative(self):
        returns = [-0.05, -0.03, -0.04]
        cvar = _compute_cvar(returns, 0.02)
        assert cvar > 0.02


# ---------------------------------------------------------------------------
# VOLATILITY ESTIMATE
# ---------------------------------------------------------------------------

class TestVolatilityEstimate:
    def test_frozen(self):
        r = _calc()
        with pytest.raises(AttributeError):
            r.volatility.daily = 0.0

    def test_daily_less_than_annualized(self):
        r = _calc()
        assert r.volatility.daily < r.volatility.annualized

    def test_regime_multiplier_stored(self):
        r = _calc(regime_state=AssetRegimeState.SHOCK)
        assert r.volatility.regime_multiplier == 2.0

    def test_shock_higher_vol(self):
        calm = _calc(regime_state=AssetRegimeState.TRENDING_UP)
        shock = _calc(regime_state=AssetRegimeState.SHOCK)
        assert shock.volatility.annualized > calm.volatility.annualized

    def test_ranging_tight_lower_vol(self):
        normal = _calc(regime_state=AssetRegimeState.TRENDING_UP)
        tight = _calc(regime_state=AssetRegimeState.RANGING_TIGHT)
        assert tight.volatility.annualized < normal.volatility.annualized


# ---------------------------------------------------------------------------
# ASSET RISK RESULT
# ---------------------------------------------------------------------------

class TestAssetRiskResult:
    def test_frozen(self):
        r = _calc()
        with pytest.raises(AttributeError):
            r.symbol = "ETH"

    def test_all_fields_present(self):
        r = _calc()
        assert r.symbol == "BTC"
        assert r.asset_class == AssetClass.CRYPTO
        assert r.notional > 0
        assert isinstance(r.volatility, VolatilityEstimate)
        assert r.daily_var_95 > 0
        assert r.daily_var_99 > 0
        assert r.tail_cvar_99 > 0
        assert isinstance(r.tail_risk, TailRiskEstimate)
        assert r.execution_cost_bps > 0
        assert 0.0 <= r.liquidity_score <= 1.0
        assert len(r.result_hash) == 16

    def test_result_hash_hex(self):
        r = _calc()
        assert all(c in "0123456789abcdef" for c in r.result_hash)

    def test_notional_calculation(self):
        r = _calc(current_price=100.0, position_size=10.0)
        assert r.notional == 1000.0

    def test_var_99_gt_var_95(self):
        r = _calc()
        assert r.daily_var_99 > r.daily_var_95


# ---------------------------------------------------------------------------
# PER-ASSET-CLASS BEHAVIOR
# ---------------------------------------------------------------------------

class TestPerAssetClass:
    def test_crypto(self):
        r = _calc(asset_class=AssetClass.CRYPTO, symbol="BTC")
        assert r.asset_class == AssetClass.CRYPTO
        assert r.tail_risk.tail_decay == 3.0
        assert r.execution_cost_bps == 10.0

    def test_forex(self):
        r = _calc(asset_class=AssetClass.FOREX, symbol="EURUSD",
                  current_price=1.1, position_size=100000.0)
        assert r.asset_class == AssetClass.FOREX
        assert r.tail_risk.tail_decay == 8.0
        assert r.execution_cost_bps == 2.0

    def test_indices(self):
        r = _calc(asset_class=AssetClass.INDICES, symbol="SPY",
                  current_price=520.0, position_size=100.0)
        assert r.tail_risk.tail_decay == 5.0
        assert r.execution_cost_bps == 3.0

    def test_commodities(self):
        r = _calc(asset_class=AssetClass.COMMODITIES, symbol="GOLD",
                  current_price=2000.0, position_size=5.0)
        assert r.tail_risk.tail_decay == 4.0
        assert r.execution_cost_bps == 5.0

    def test_rates(self):
        r = _calc(asset_class=AssetClass.RATES, symbol="TLT",
                  current_price=90.0, position_size=100.0)
        assert r.tail_risk.tail_decay == 10.0
        assert r.execution_cost_bps == 1.5


# ---------------------------------------------------------------------------
# REGIME MULTIPLIERS
# ---------------------------------------------------------------------------

class TestRegimeMultipliers:
    def test_all_regimes_produce_valid_result(self):
        for ac in AssetClass:
            for state in AssetRegimeState:
                r = _calc(asset_class=ac, regime_state=state)
                assert r.volatility.annualized >= 0.0
                assert r.daily_var_95 >= 0.0

    def test_shock_crypto_doubles_vol(self):
        r = _calc(asset_class=AssetClass.CRYPTO,
                  regime_state=AssetRegimeState.SHOCK)
        assert r.volatility.regime_multiplier == 2.0

    def test_shock_forex_less_extreme(self):
        r = _calc(asset_class=AssetClass.FOREX,
                  regime_state=AssetRegimeState.SHOCK)
        assert r.volatility.regime_multiplier == 1.8


# ---------------------------------------------------------------------------
# LIQUIDITY SCORE
# ---------------------------------------------------------------------------

class TestLiquidityScore:
    def test_clipped_high(self):
        r = _calc(liquidity_score=1.5)
        assert r.liquidity_score == 1.0

    def test_clipped_low(self):
        r = _calc(liquidity_score=-0.5)
        assert r.liquidity_score == 0.0

    def test_within_range(self):
        r = _calc(liquidity_score=0.7)
        assert r.liquidity_score == 0.7


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_result(self):
        r1 = _calc()
        r2 = _calc()
        assert r1.result_hash == r2.result_hash
        assert r1.daily_var_95 == r2.daily_var_95
        assert r1.volatility.daily == r2.volatility.daily

    def test_different_inputs_different_hash(self):
        r1 = _calc(current_price=65000.0)
        r2 = _calc(current_price=3200.0)
        assert r1.result_hash != r2.result_hash

    def test_fresh_instance_per_call(self):
        calc = AssetRiskCalculator()
        r1 = calc.calculate_risk(**CALM_KWARGS)
        r2 = calc.calculate_risk(**{**CALM_KWARGS, "current_price": 100.0})
        assert r1.notional != r2.notional


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_very_small_price(self):
        r = _calc(current_price=0.0001, position_size=1000000.0)
        assert r.notional > 0

    def test_zero_position(self):
        r = _calc(position_size=0.0)
        assert r.notional == 0.0
        assert r.daily_var_95 == 0.0

    def test_negative_position(self):
        r = _calc(position_size=-10.0)
        assert r.notional > 0  # abs()

    def test_minimal_returns(self):
        r = _calc(returns=[0.01, -0.01])
        assert r.volatility.daily >= 0.0


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.risk.asset_risk import (
            AssetRiskCalculator,
            AssetRiskResult,
            VolatilityEstimate,
            TailRiskEstimate,
        )
        assert AssetRiskCalculator is not None
