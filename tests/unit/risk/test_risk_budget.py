# =============================================================================
# tests/unit/risk/test_risk_budget.py -- Risk Budget Allocation Tests
#
# Comprehensive tests for jarvis/risk/risk_budget.py (Phase MA-5).
# Covers: constants, 4-stage pipeline, regime adjustments, correlation
#         adjustments, constraints, determinism, immutability, edge cases.
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
from jarvis.risk.portfolio_risk import PortfolioRiskEngine, PortfolioRiskResult
from jarvis.risk.risk_budget import (
    # Constants
    MAX_SINGLE_ASSET,
    MAX_CORRELATION_BUCKET,
    RISK_BUDGET_DEFAULT_PCT,
    RISK_OFF_CRYPTO_FACTOR,
    RISK_OFF_INDICES_FACTOR,
    RISK_OFF_FOREX_FACTOR,
    CRISIS_CRYPTO_FACTOR,
    CRISIS_INDICES_FACTOR,
    BREAKDOWN_FACTOR,
    DIVERGENCE_FACTOR,
    COUPLED_FACTOR,
    # Dataclasses
    RiskBudget,
    RiskBudgetResult,
    # Allocator
    PortfolioRiskBudget,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

SAMPLE_RETURNS = [0.01 * ((-1) ** i) + 0.001 * i for i in range(30)]
SAMPLE_PRICES = [100.0 + i * 0.5 for i in range(30)]

DEFAULT_ASSET_REGIMES = {ac: AssetRegimeState.TRENDING_UP for ac in AssetClass}
DEFAULT_CONFIDENCES = {ac: 0.8 for ac in AssetClass}
DEFAULT_SUB_REGIME = {ac: "default" for ac in AssetClass}


def _make_regime(
    global_regime=GlobalRegimeState.RISK_ON,
    correlation_regime=CorrelationRegimeState.NORMAL,
) -> HierarchicalRegime:
    ar = DEFAULT_ASSET_REGIMES.copy()
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


def _make_portfolio_risk(regime=None) -> PortfolioRiskResult:
    if regime is None:
        regime = _make_regime()
    positions = {
        "BTC": (AssetClass.CRYPTO, 65000.0, 1.0),
        "EURUSD": (AssetClass.FOREX, 1.1, 100000.0),
        "SPY": (AssetClass.INDICES, 520.0, 100.0),
        "GOLD": (AssetClass.COMMODITIES, 2000.0, 5.0),
        "TLT": (AssetClass.RATES, 90.0, 100.0),
    }
    returns = {s: SAMPLE_RETURNS for s in positions}
    prices = {s: SAMPLE_PRICES for s in positions}
    return PortfolioRiskEngine().calculate_portfolio_risk(
        positions=positions,
        returns=returns,
        regime=regime,
        price_histories=prices,
    )


def _all_classes():
    return list(AssetClass)


def _allocate(
    total_capital=100000.0,
    asset_classes=None,
    regime=None,
    portfolio_risk=None,
):
    if asset_classes is None:
        asset_classes = _all_classes()
    if regime is None:
        regime = _make_regime()
    if portfolio_risk is None:
        portfolio_risk = _make_portfolio_risk(regime)
    return PortfolioRiskBudget().allocate(
        total_capital=total_capital,
        asset_classes=asset_classes,
        regime=regime,
        portfolio_risk=portfolio_risk,
    )


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    def test_max_single_asset(self):
        assert MAX_SINGLE_ASSET == 0.30

    def test_max_correlation_bucket(self):
        assert MAX_CORRELATION_BUCKET == 0.50

    def test_risk_budget_default(self):
        assert RISK_BUDGET_DEFAULT_PCT == 0.20

    def test_risk_off_crypto(self):
        assert RISK_OFF_CRYPTO_FACTOR == 0.5

    def test_risk_off_forex_safe_haven(self):
        assert RISK_OFF_FOREX_FACTOR == 1.2

    def test_crisis_crypto_severe(self):
        assert CRISIS_CRYPTO_FACTOR == 0.2

    def test_breakdown_factor(self):
        assert BREAKDOWN_FACTOR == 0.6

    def test_divergence_factor(self):
        assert DIVERGENCE_FACTOR == 1.1

    def test_coupled_factor(self):
        assert COUPLED_FACTOR == 0.85


# ---------------------------------------------------------------------------
# BASIC ALLOCATION
# ---------------------------------------------------------------------------

class TestBasicAllocation:
    def test_all_classes_allocated(self):
        r = _allocate()
        for ac in AssetClass:
            assert ac in r.budgets

    def test_num_asset_classes(self):
        r = _allocate()
        assert r.num_asset_classes == 5

    def test_total_capital_stored(self):
        r = _allocate(total_capital=200000.0)
        assert r.total_capital == 200000.0

    def test_utilization_positive(self):
        r = _allocate()
        assert r.utilization > 0.0

    def test_fractions_sum_to_one(self):
        r = _allocate()
        total_fraction = sum(b.risk_budget_fraction for b in r.budgets.values())
        assert abs(total_fraction - 1.0) < 1e-10

    def test_allocated_capital_matches_fraction(self):
        r = _allocate(total_capital=100000.0)
        for ac, budget in r.budgets.items():
            expected = 100000.0 * budget.risk_budget_fraction
            assert abs(budget.allocated_capital - expected) < 1e-6

    def test_total_allocated_sum(self):
        r = _allocate(total_capital=100000.0)
        total = sum(b.allocated_capital for b in r.budgets.values())
        assert abs(r.total_allocated - total) < 1e-6

    def test_result_hash(self):
        r = _allocate()
        assert len(r.result_hash) == 16
        assert all(c in "0123456789abcdef" for c in r.result_hash)

    def test_budget_hash(self):
        r = _allocate()
        for ac, b in r.budgets.items():
            assert len(b.result_hash) == 16


# ---------------------------------------------------------------------------
# REGIME ADJUSTMENTS (Stage 2)
# ---------------------------------------------------------------------------

class TestRegimeAdjustments:
    def test_risk_on_no_adjustment(self):
        r = _allocate(regime=_make_regime(global_regime=GlobalRegimeState.RISK_ON))
        for ac, b in r.budgets.items():
            assert abs(b.regime_adjustment_factor - 1.0) < 1e-10

    def test_risk_off_crypto_reduced(self):
        regime = _make_regime(global_regime=GlobalRegimeState.RISK_OFF)
        pr = _make_portfolio_risk(regime)
        r = _allocate(regime=regime, portfolio_risk=pr)
        crypto_budget = r.budgets[AssetClass.CRYPTO]
        assert crypto_budget.regime_adjustment_factor < 1.0

    def test_risk_off_forex_increased(self):
        regime = _make_regime(global_regime=GlobalRegimeState.RISK_OFF)
        pr = _make_portfolio_risk(regime)
        r = _allocate(regime=regime, portfolio_risk=pr)
        forex_budget = r.budgets[AssetClass.FOREX]
        assert forex_budget.regime_adjustment_factor > 1.0

    def test_crisis_crypto_severely_reduced(self):
        regime = _make_regime(global_regime=GlobalRegimeState.CRISIS)
        pr = _make_portfolio_risk(regime)
        r = _allocate(regime=regime, portfolio_risk=pr)
        crypto_budget = r.budgets[AssetClass.CRYPTO]
        assert crypto_budget.regime_adjustment_factor < 0.5

    def test_crisis_indices_reduced(self):
        regime = _make_regime(global_regime=GlobalRegimeState.CRISIS)
        pr = _make_portfolio_risk(regime)
        r = _allocate(regime=regime, portfolio_risk=pr)
        indices_budget = r.budgets[AssetClass.INDICES]
        assert indices_budget.regime_adjustment_factor < 1.0

    def test_regime_stored(self):
        regime = _make_regime(global_regime=GlobalRegimeState.RISK_OFF)
        pr = _make_portfolio_risk(regime)
        r = _allocate(regime=regime, portfolio_risk=pr)
        assert r.regime_applied == GlobalRegimeState.RISK_OFF


# ---------------------------------------------------------------------------
# CORRELATION ADJUSTMENTS (Stage 3)
# ---------------------------------------------------------------------------

class TestCorrelationAdjustments:
    def test_normal_no_adjustment(self):
        r = _allocate(
            regime=_make_regime(correlation_regime=CorrelationRegimeState.NORMAL),
        )
        for ac, b in r.budgets.items():
            assert abs(b.correlation_adjustment_factor - 1.0) < 1e-10

    def test_breakdown_reduces_all(self):
        regime = _make_regime(correlation_regime=CorrelationRegimeState.BREAKDOWN)
        pr = _make_portfolio_risk(regime)
        r = _allocate(regime=regime, portfolio_risk=pr)
        for ac, b in r.budgets.items():
            assert abs(b.correlation_adjustment_factor - BREAKDOWN_FACTOR) < 1e-10

    def test_divergence_increases(self):
        regime = _make_regime(correlation_regime=CorrelationRegimeState.DIVERGENCE)
        pr = _make_portfolio_risk(regime)
        r = _allocate(regime=regime, portfolio_risk=pr)
        for ac, b in r.budgets.items():
            assert abs(b.correlation_adjustment_factor - DIVERGENCE_FACTOR) < 1e-10

    def test_coupled_reduces_slightly(self):
        regime = _make_regime(correlation_regime=CorrelationRegimeState.COUPLED)
        pr = _make_portfolio_risk(regime)
        r = _allocate(regime=regime, portfolio_risk=pr)
        for ac, b in r.budgets.items():
            assert abs(b.correlation_adjustment_factor - COUPLED_FACTOR) < 1e-10

    def test_correlation_regime_stored(self):
        regime = _make_regime(correlation_regime=CorrelationRegimeState.DIVERGENCE)
        pr = _make_portfolio_risk(regime)
        r = _allocate(regime=regime, portfolio_risk=pr)
        assert r.correlation_regime_applied == CorrelationRegimeState.DIVERGENCE


# ---------------------------------------------------------------------------
# CONSTRAINTS (Stage 4)
# ---------------------------------------------------------------------------

class TestConstraints:
    def test_no_asset_exceeds_max(self):
        r = _allocate()
        for ac, b in r.budgets.items():
            assert b.risk_budget_fraction <= MAX_SINGLE_ASSET + 1e-10

    def test_single_class_gets_full_budget(self):
        r = _allocate(asset_classes=[AssetClass.CRYPTO])
        assert abs(r.budgets[AssetClass.CRYPTO].risk_budget_fraction - 1.0) < 1e-10

    def test_two_classes_sum_to_one(self):
        classes = [AssetClass.CRYPTO, AssetClass.FOREX]
        r = _allocate(asset_classes=classes)
        total = sum(b.risk_budget_fraction for b in r.budgets.values())
        assert abs(total - 1.0) < 1e-10


# ---------------------------------------------------------------------------
# EQUAL RISK CONTRIBUTION (Stage 1)
# ---------------------------------------------------------------------------

class TestEqualRiskContribution:
    def test_base_allocation_stored(self):
        r = _allocate()
        for ac, b in r.budgets.items():
            assert b.base_allocation > 0.0

    def test_base_allocations_sum_to_one(self):
        r = _allocate()
        total = sum(b.base_allocation for b in r.budgets.values())
        assert abs(total - 1.0) < 1e-10


# ---------------------------------------------------------------------------
# IMMUTABILITY
# ---------------------------------------------------------------------------

class TestImmutability:
    def test_result_frozen(self):
        r = _allocate()
        with pytest.raises(AttributeError):
            r.total_capital = 0.0

    def test_budget_frozen(self):
        r = _allocate()
        budget = list(r.budgets.values())[0]
        with pytest.raises(AttributeError):
            budget.allocated_capital = 0.0


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_hash(self):
        r1 = _allocate()
        r2 = _allocate()
        assert r1.result_hash == r2.result_hash

    def test_same_budgets(self):
        r1 = _allocate()
        r2 = _allocate()
        for ac in AssetClass:
            assert r1.budgets[ac].allocated_capital == r2.budgets[ac].allocated_capital

    def test_different_regime_different_hash(self):
        r1 = _allocate(regime=_make_regime(global_regime=GlobalRegimeState.RISK_ON))
        regime2 = _make_regime(global_regime=GlobalRegimeState.RISK_OFF)
        pr2 = _make_portfolio_risk(regime2)
        r2 = _allocate(regime=regime2, portfolio_risk=pr2)
        assert r1.result_hash != r2.result_hash

    def test_fresh_instance_same_result(self):
        regime = _make_regime()
        pr = _make_portfolio_risk(regime)
        r1 = PortfolioRiskBudget().allocate(
            total_capital=100000.0,
            asset_classes=_all_classes(),
            regime=regime,
            portfolio_risk=pr,
        )
        r2 = PortfolioRiskBudget().allocate(
            total_capital=100000.0,
            asset_classes=_all_classes(),
            regime=regime,
            portfolio_risk=pr,
        )
        assert r1.result_hash == r2.result_hash


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_asset_classes(self):
        r = _allocate(asset_classes=[])
        assert r.num_asset_classes == 0
        assert r.total_allocated == 0.0
        assert len(r.budgets) == 0

    def test_zero_capital(self):
        r = _allocate(total_capital=0.0)
        assert r.num_asset_classes == 0
        assert r.total_allocated == 0.0

    def test_single_asset_class(self):
        r = _allocate(asset_classes=[AssetClass.RATES])
        assert r.num_asset_classes == 1
        assert AssetClass.RATES in r.budgets
        assert abs(r.budgets[AssetClass.RATES].risk_budget_fraction - 1.0) < 1e-10

    def test_large_capital(self):
        r = _allocate(total_capital=1e9)
        assert r.total_capital == 1e9
        assert r.total_allocated > 0.0

    def test_all_five_classes(self):
        r = _allocate(asset_classes=_all_classes())
        assert r.num_asset_classes == 5
        assert len(r.budgets) == 5


# ---------------------------------------------------------------------------
# PRIVATE METHODS
# ---------------------------------------------------------------------------

class TestPrivateMethods:
    def test_risk_off_factor(self):
        allocator = PortfolioRiskBudget()
        assert allocator._risk_off_factor(AssetClass.CRYPTO) == 0.5
        assert allocator._risk_off_factor(AssetClass.FOREX) == 1.2

    def test_crisis_factor(self):
        allocator = PortfolioRiskBudget()
        assert allocator._crisis_factor(AssetClass.CRYPTO) == 0.2
        assert allocator._crisis_factor(AssetClass.INDICES) == 0.4

    def test_apply_constraints_caps_then_normalizes(self):
        allocator = PortfolioRiskBudget()
        allocation = {
            AssetClass.CRYPTO: 0.8,  # Over MAX_SINGLE_ASSET -> capped to 0.30
            AssetClass.FOREX: 0.2,
        }
        result = allocator._apply_constraints(allocation)
        # After cap: crypto=0.30, forex=0.20 -> normalized: 0.60, 0.40
        assert abs(result[AssetClass.CRYPTO] - 0.6) < 1e-10
        assert abs(result[AssetClass.FOREX] - 0.4) < 1e-10
        total = sum(result.values())
        assert abs(total - 1.0) < 1e-10

    def test_apply_constraints_empty(self):
        allocator = PortfolioRiskBudget()
        assert allocator._apply_constraints({}) == {}


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.risk.risk_budget import (
            PortfolioRiskBudget,
            RiskBudget,
            RiskBudgetResult,
        )
        assert PortfolioRiskBudget is not None
        assert RiskBudget is not None
        assert RiskBudgetResult is not None
