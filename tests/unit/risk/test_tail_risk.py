# =============================================================================
# tests/unit/risk/test_tail_risk.py -- Multivariate Tail Risk Model Tests
#
# Comprehensive tests for jarvis/risk/tail_risk.py (Phase MA-5).
# Covers: constants, math helpers, MultivariateTailModel, determinism,
#         immutability, edge cases, single/multi-asset portfolios.
# =============================================================================

import math

import pytest

from jarvis.core.regime import AssetClass, AssetRegimeState
from jarvis.risk.asset_risk import AssetRiskCalculator, AssetRiskResult, TAIL_PARAMS
from jarvis.risk.tail_risk import (
    # Constants
    VAR_95_Z,
    VAR_99_Z,
    TAIL_DEPENDENCE_BASE,
    TAIL_DEPENDENCE_CORR_FACTOR,
    WORST_CASE_MULTIPLIER,
    # Helpers
    _portfolio_var_parametric,
    _estimate_tail_dependence,
    _cvar_from_var,
    # Dataclass
    MultivariateTailRiskResult,
    # Model
    MultivariateTailModel,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

SAMPLE_RETURNS = [0.01 * ((-1) ** i) + 0.001 * i for i in range(30)]

def _make_asset_risk(symbol: str, asset_class: AssetClass) -> AssetRiskResult:
    return AssetRiskCalculator().calculate_risk(
        symbol=symbol,
        asset_class=asset_class,
        returns=SAMPLE_RETURNS,
        current_price=100.0,
        position_size=10.0,
        regime_state=AssetRegimeState.TRENDING_UP,
        liquidity_score=0.8,
    )


def _identity_matrix(n: int) -> tuple:
    return tuple(
        tuple(1.0 if i == j else 0.0 for j in range(n))
        for i in range(n)
    )


def _uniform_corr_matrix(n: int, off_diag: float) -> tuple:
    return tuple(
        tuple(1.0 if i == j else off_diag for j in range(n))
        for i in range(n)
    )


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    def test_var_95_z(self):
        assert VAR_95_Z == 1.645

    def test_var_99_z(self):
        assert VAR_99_Z == 2.326

    def test_tail_dependence_base(self):
        assert TAIL_DEPENDENCE_BASE == 0.1

    def test_tail_dependence_corr_factor(self):
        assert TAIL_DEPENDENCE_CORR_FACTOR == 0.3

    def test_worst_case_multiplier(self):
        assert WORST_CASE_MULTIPLIER == 3.0


# ---------------------------------------------------------------------------
# _portfolio_var_parametric
# ---------------------------------------------------------------------------

class TestPortfolioVarParametric:
    def test_empty_list(self):
        assert _portfolio_var_parametric([], ()) == 0.0

    def test_single_asset(self):
        assert _portfolio_var_parametric([0.05], ((1.0,),)) == 0.05

    def test_two_uncorrelated_assets(self):
        # With identity correlation: var = sqrt(v1^2 + v2^2)
        var = _portfolio_var_parametric([0.03, 0.04], _identity_matrix(2))
        expected = math.sqrt(0.03**2 + 0.04**2)
        assert abs(var - expected) < 1e-10

    def test_two_perfectly_correlated(self):
        # corr=1.0: var = v1 + v2
        corr = ((1.0, 1.0), (1.0, 1.0))
        var = _portfolio_var_parametric([0.03, 0.04], corr)
        assert abs(var - 0.07) < 1e-10

    def test_diversification_benefit(self):
        # Uncorrelated should be less than perfectly correlated
        uncorr = _portfolio_var_parametric([0.03, 0.04], _identity_matrix(2))
        perfect = _portfolio_var_parametric([0.03, 0.04], _uniform_corr_matrix(2, 1.0))
        assert uncorr < perfect

    def test_negative_correlation_reduces_risk(self):
        neg_corr = ((1.0, -0.5), (-0.5, 1.0))
        no_corr = _identity_matrix(2)
        neg = _portfolio_var_parametric([0.03, 0.04], neg_corr)
        zero = _portfolio_var_parametric([0.03, 0.04], no_corr)
        assert neg < zero

    def test_three_assets(self):
        vars_ = [0.02, 0.03, 0.04]
        corr = _identity_matrix(3)
        var = _portfolio_var_parametric(vars_, corr)
        expected = math.sqrt(0.02**2 + 0.03**2 + 0.04**2)
        assert abs(var - expected) < 1e-10

    def test_handles_missing_correlation_entries(self):
        # Short matrix: should fall back to identity for missing entries
        corr = ((1.0, 0.5), (0.5, 1.0))
        var = _portfolio_var_parametric([0.03, 0.04, 0.05], corr)
        assert var > 0.0

    def test_zero_vars(self):
        var = _portfolio_var_parametric([0.0, 0.0], _identity_matrix(2))
        assert var == 0.0


# ---------------------------------------------------------------------------
# _estimate_tail_dependence
# ---------------------------------------------------------------------------

class TestEstimateTailDependence:
    def test_zero_correlation_low_dependence(self):
        td = _estimate_tail_dependence(0.0, 5.0)
        # Only tail component: 0.1 * (5.0/5.0) = 0.1
        assert abs(td - 0.1) < 1e-10

    def test_high_correlation_increases_dependence(self):
        low = _estimate_tail_dependence(0.2, 5.0)
        high = _estimate_tail_dependence(0.8, 5.0)
        assert high > low

    def test_fat_tails_increase_dependence(self):
        thin = _estimate_tail_dependence(0.5, 10.0)
        fat = _estimate_tail_dependence(0.5, 3.0)
        assert fat > thin

    def test_very_fat_tails_capped(self):
        td = _estimate_tail_dependence(0.0, 1.5)
        # tail_decay <= 2.0: tail_component = 0.1 * 2.5 = 0.25
        assert abs(td - 0.25) < 1e-10

    def test_result_clamped_0_1(self):
        # Very high correlation + very fat tails
        td = _estimate_tail_dependence(1.0, 1.0)
        assert 0.0 <= td <= 1.0

    def test_negative_correlation_clamped(self):
        td = _estimate_tail_dependence(-0.5, 5.0)
        # Negative correlation clamped to 0 for corr_component
        assert td >= 0.0

    def test_exact_boundary_tail_decay_2(self):
        # tail_decay == 2.0 is NOT > 2.0, so uses the else branch
        td = _estimate_tail_dependence(0.0, 2.0)
        assert abs(td - 0.25) < 1e-10

    def test_thin_tails_low_dependence(self):
        td = _estimate_tail_dependence(0.0, 20.0)
        # tail_component = 0.1 * (5.0/20.0) = 0.025
        assert td < 0.1


# ---------------------------------------------------------------------------
# _cvar_from_var
# ---------------------------------------------------------------------------

class TestCVarFromVar:
    def test_zero_tail_dependence(self):
        # ratio = 1.0 + 0.5 * 0 = 1.0
        assert _cvar_from_var(0.05, 0.0) == 0.05

    def test_max_tail_dependence(self):
        # ratio = 1.0 + 0.5 * 1.0 = 1.5
        assert abs(_cvar_from_var(0.05, 1.0) - 0.075) < 1e-10

    def test_cvar_gte_var(self):
        for td in [0.0, 0.2, 0.5, 0.8, 1.0]:
            assert _cvar_from_var(0.05, td) >= 0.05

    def test_higher_dependence_higher_cvar(self):
        low = _cvar_from_var(0.05, 0.2)
        high = _cvar_from_var(0.05, 0.8)
        assert high > low

    def test_zero_var(self):
        assert _cvar_from_var(0.0, 0.5) == 0.0


# ---------------------------------------------------------------------------
# MultivariateTailModel -- ESTIMATE
# ---------------------------------------------------------------------------

class TestMultivariateTailModelEstimate:
    def test_empty_portfolio(self):
        model = MultivariateTailModel()
        result = model.estimate(
            asset_risks={},
            correlation_matrix=(),
            symbols=(),
        )
        assert result.num_assets == 0
        assert result.var_95 == 0.0
        assert result.diversification_adjusted is False

    def test_single_asset(self):
        model = MultivariateTailModel()
        risk = _make_asset_risk("BTC", AssetClass.CRYPTO)
        result = model.estimate(
            asset_risks={"BTC": risk},
            correlation_matrix=((1.0,),),
            symbols=("BTC",),
        )
        assert result.num_assets == 1
        assert result.var_95 > 0.0
        assert result.diversification_adjusted is False

    def test_two_assets_uncorrelated(self):
        model = MultivariateTailModel()
        btc = _make_asset_risk("BTC", AssetClass.CRYPTO)
        eth = _make_asset_risk("ETH", AssetClass.CRYPTO)
        result = model.estimate(
            asset_risks={"BTC": btc, "ETH": eth},
            correlation_matrix=_identity_matrix(2),
            symbols=("BTC", "ETH"),
        )
        assert result.num_assets == 2
        assert result.diversification_adjusted is True
        assert result.var_95 > 0.0
        assert result.var_99 > result.var_95

    def test_correlated_higher_risk(self):
        model = MultivariateTailModel()
        btc = _make_asset_risk("BTC", AssetClass.CRYPTO)
        eth = _make_asset_risk("ETH", AssetClass.CRYPTO)
        uncorr = model.estimate(
            asset_risks={"BTC": btc, "ETH": eth},
            correlation_matrix=_identity_matrix(2),
            symbols=("BTC", "ETH"),
        )
        corr = model.estimate(
            asset_risks={"BTC": btc, "ETH": eth},
            correlation_matrix=_uniform_corr_matrix(2, 0.8),
            symbols=("BTC", "ETH"),
        )
        assert corr.var_95 > uncorr.var_95

    def test_cvar_gte_var(self):
        model = MultivariateTailModel()
        btc = _make_asset_risk("BTC", AssetClass.CRYPTO)
        result = model.estimate(
            asset_risks={"BTC": btc},
            correlation_matrix=((1.0,),),
            symbols=("BTC",),
        )
        assert result.cvar_95 >= result.var_95
        assert result.cvar_99 >= result.var_99

    def test_worst_case_is_3x_var99(self):
        model = MultivariateTailModel()
        btc = _make_asset_risk("BTC", AssetClass.CRYPTO)
        result = model.estimate(
            asset_risks={"BTC": btc},
            correlation_matrix=((1.0,),),
            symbols=("BTC",),
        )
        assert abs(result.worst_case - result.var_99 * 3.0) < 1e-10

    def test_result_hash_hex(self):
        model = MultivariateTailModel()
        btc = _make_asset_risk("BTC", AssetClass.CRYPTO)
        result = model.estimate(
            asset_risks={"BTC": btc},
            correlation_matrix=((1.0,),),
            symbols=("BTC",),
        )
        assert len(result.result_hash) == 16
        assert all(c in "0123456789abcdef" for c in result.result_hash)

    def test_multi_asset_class_portfolio(self):
        model = MultivariateTailModel()
        btc = _make_asset_risk("BTC", AssetClass.CRYPTO)
        spy = _make_asset_risk("SPY", AssetClass.INDICES)
        tlt = _make_asset_risk("TLT", AssetClass.RATES)
        corr = _uniform_corr_matrix(3, 0.3)
        result = model.estimate(
            asset_risks={"BTC": btc, "SPY": spy, "TLT": tlt},
            correlation_matrix=corr,
            symbols=("BTC", "SPY", "TLT"),
        )
        assert result.num_assets == 3
        assert result.var_95 > 0.0
        assert result.tail_dependence > 0.0

    def test_tail_dependence_stored(self):
        model = MultivariateTailModel()
        btc = _make_asset_risk("BTC", AssetClass.CRYPTO)
        spy = _make_asset_risk("SPY", AssetClass.INDICES)
        result = model.estimate(
            asset_risks={"BTC": btc, "SPY": spy},
            correlation_matrix=_uniform_corr_matrix(2, 0.6),
            symbols=("BTC", "SPY"),
        )
        assert 0.0 <= result.tail_dependence <= 1.0


# ---------------------------------------------------------------------------
# AVERAGE OFF-DIAGONAL
# ---------------------------------------------------------------------------

class TestAverageOffDiagonal:
    def test_single_asset(self):
        model = MultivariateTailModel()
        assert model._average_off_diagonal(((1.0,),), 1) == 0.0

    def test_two_assets(self):
        model = MultivariateTailModel()
        matrix = ((1.0, 0.6), (0.6, 1.0))
        assert abs(model._average_off_diagonal(matrix, 2) - 0.6) < 1e-10

    def test_three_assets(self):
        model = MultivariateTailModel()
        matrix = ((1.0, 0.3, 0.5), (0.3, 1.0, 0.4), (0.5, 0.4, 1.0))
        expected = (0.3 + 0.5 + 0.4) / 3
        assert abs(model._average_off_diagonal(matrix, 3) - expected) < 1e-10


# ---------------------------------------------------------------------------
# IMMUTABILITY
# ---------------------------------------------------------------------------

class TestImmutability:
    def test_result_frozen(self):
        model = MultivariateTailModel()
        btc = _make_asset_risk("BTC", AssetClass.CRYPTO)
        result = model.estimate(
            asset_risks={"BTC": btc},
            correlation_matrix=((1.0,),),
            symbols=("BTC",),
        )
        with pytest.raises(AttributeError):
            result.var_95 = 0.0

    def test_empty_result_frozen(self):
        model = MultivariateTailModel()
        result = model.estimate(
            asset_risks={},
            correlation_matrix=(),
            symbols=(),
        )
        with pytest.raises(AttributeError):
            result.num_assets = 5


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_hash(self):
        model = MultivariateTailModel()
        btc = _make_asset_risk("BTC", AssetClass.CRYPTO)
        r1 = model.estimate(
            asset_risks={"BTC": btc},
            correlation_matrix=((1.0,),),
            symbols=("BTC",),
        )
        r2 = model.estimate(
            asset_risks={"BTC": btc},
            correlation_matrix=((1.0,),),
            symbols=("BTC",),
        )
        assert r1.result_hash == r2.result_hash
        assert r1.var_95 == r2.var_95

    def test_different_correlation_different_hash(self):
        model = MultivariateTailModel()
        btc = _make_asset_risk("BTC", AssetClass.CRYPTO)
        spy = _make_asset_risk("SPY", AssetClass.INDICES)
        r1 = model.estimate(
            asset_risks={"BTC": btc, "SPY": spy},
            correlation_matrix=_identity_matrix(2),
            symbols=("BTC", "SPY"),
        )
        r2 = model.estimate(
            asset_risks={"BTC": btc, "SPY": spy},
            correlation_matrix=_uniform_corr_matrix(2, 0.8),
            symbols=("BTC", "SPY"),
        )
        assert r1.result_hash != r2.result_hash

    def test_fresh_instance_same_result(self):
        btc = _make_asset_risk("BTC", AssetClass.CRYPTO)
        r1 = MultivariateTailModel().estimate(
            asset_risks={"BTC": btc},
            correlation_matrix=((1.0,),),
            symbols=("BTC",),
        )
        r2 = MultivariateTailModel().estimate(
            asset_risks={"BTC": btc},
            correlation_matrix=((1.0,),),
            symbols=("BTC",),
        )
        assert r1.result_hash == r2.result_hash


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_five_assets(self):
        model = MultivariateTailModel()
        assets = {}
        classes = [AssetClass.CRYPTO, AssetClass.FOREX, AssetClass.INDICES,
                   AssetClass.COMMODITIES, AssetClass.RATES]
        symbols = ("BTC", "EURUSD", "SPY", "GOLD", "TLT")
        for sym, ac in zip(symbols, classes):
            assets[sym] = _make_asset_risk(sym, ac)
        corr = _uniform_corr_matrix(5, 0.3)
        result = model.estimate(
            asset_risks=assets,
            correlation_matrix=corr,
            symbols=symbols,
        )
        assert result.num_assets == 5
        assert result.var_95 > 0.0

    def test_high_correlation_stress(self):
        model = MultivariateTailModel()
        btc = _make_asset_risk("BTC", AssetClass.CRYPTO)
        eth = _make_asset_risk("ETH", AssetClass.CRYPTO)
        corr = _uniform_corr_matrix(2, 0.99)
        result = model.estimate(
            asset_risks={"BTC": btc, "ETH": eth},
            correlation_matrix=corr,
            symbols=("BTC", "ETH"),
        )
        assert result.var_95 > 0.0
        assert result.tail_dependence > 0.0


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.risk.tail_risk import (
            MultivariateTailModel,
            MultivariateTailRiskResult,
        )
        assert MultivariateTailModel is not None
        assert MultivariateTailRiskResult is not None
