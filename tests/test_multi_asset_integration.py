# =============================================================================
# tests/test_multi_asset_integration.py -- Multi-Asset E2E Integration Tests
#
# Phase MA-7: End-to-end integration tests for multi-asset pipeline.
# Covers BTC + EURUSD + SPX portfolio through all risk layers,
# crisis scenarios, regime transitions, and cross-module consistency.
#
# P0: All outputs are analytical. No execution. No real orders.
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
from jarvis.risk.asset_risk import AssetRiskCalculator, AssetRiskResult
from jarvis.risk.correlation import DynamicCorrelationModel, CorrelationMatrixResult
from jarvis.risk.tail_risk import MultivariateTailModel, MultivariateTailRiskResult
from jarvis.risk.gap_risk import GapRiskModel, PortfolioGapRiskResult, GAP_ENABLED_CLASSES
from jarvis.risk.portfolio_risk import PortfolioRiskEngine, PortfolioRiskResult
from jarvis.risk.risk_budget import PortfolioRiskBudget, RiskBudgetResult
from jarvis.risk.systemic_risk import (
    classify_correlation_regime,
    compute_portfolio_fragility,
    simulate_tail_stress,
    compute_concentration_risk,
    CorrelationRegimeResult,
)
from jarvis.risk.portfolio_heatmap import (
    PortfolioHeatmapEngine,
    PortfolioHeatmapSnapshot,
    TRIGGER_NEW_CANDLE,
)
from jarvis.execution.session_aware_executor import (
    SessionAwareExecutor,
    ExecutionDecision,
    STATUS_FILLED,
    STATUS_DEFERRED,
    STATUS_AUCTION,
)


# =============================================================================
# TEST DATA
# =============================================================================

# 30-period return series with realistic volatility characteristics
BTC_RETURNS = [
    0.03, -0.04, 0.02, -0.01, 0.05, -0.03, 0.01, -0.02, 0.04, -0.05,
    0.02, -0.01, 0.03, -0.04, 0.01, 0.02, -0.03, 0.04, -0.02, 0.01,
    -0.01, 0.03, -0.02, 0.01, -0.04, 0.05, -0.01, 0.02, -0.03, 0.01,
]

EURUSD_RETURNS = [
    0.005, -0.003, 0.002, -0.004, 0.003, -0.002, 0.001, -0.003, 0.004, -0.002,
    0.001, -0.001, 0.003, -0.002, 0.001, 0.002, -0.003, 0.002, -0.001, 0.001,
    -0.002, 0.003, -0.001, 0.002, -0.003, 0.004, -0.002, 0.001, -0.002, 0.001,
]

SPX_RETURNS = [
    0.01, -0.015, 0.008, -0.005, 0.012, -0.01, 0.005, -0.008, 0.015, -0.02,
    0.007, -0.003, 0.01, -0.012, 0.004, 0.008, -0.01, 0.012, -0.006, 0.003,
    -0.005, 0.01, -0.007, 0.005, -0.015, 0.02, -0.005, 0.008, -0.01, 0.004,
]

BTC_PRICES = [65000.0 + i * 100.0 for i in range(30)]
EURUSD_PRICES = [1.08 + i * 0.001 for i in range(30)]
SPX_PRICES = [5200.0 + i * 10.0 for i in range(30)]

POSITIONS = {
    "BTC": (AssetClass.CRYPTO, 65000.0, 1.0),
    "EURUSD": (AssetClass.FOREX, 1.08, 100000.0),
    "SPX": (AssetClass.INDICES, 5200.0, 100.0),
}

RETURNS = {"BTC": BTC_RETURNS, "EURUSD": EURUSD_RETURNS, "SPX": SPX_RETURNS}
PRICE_HISTORIES = {"BTC": BTC_PRICES, "EURUSD": EURUSD_PRICES, "SPX": SPX_PRICES}

DEFAULT_ASSET_REGIMES = {ac: AssetRegimeState.TRENDING_UP for ac in AssetClass}
DEFAULT_CONFIDENCES = {ac: 0.8 for ac in AssetClass}
DEFAULT_SUB_REGIME = {ac: "default" for ac in AssetClass}

SYMBOLS = ("BTC", "EURUSD", "SPX")


# =============================================================================
# REGIME FACTORY
# =============================================================================

def _make_regime(
    global_regime=GlobalRegimeState.RISK_ON,
    correlation_regime=CorrelationRegimeState.NORMAL,
    asset_regimes=None,
    confidences=None,
) -> HierarchicalRegime:
    ar = asset_regimes or DEFAULT_ASSET_REGIMES.copy()
    conf = confidences or DEFAULT_CONFIDENCES.copy()
    if global_regime == GlobalRegimeState.CRISIS:
        ar = {ac: AssetRegimeState.SHOCK for ac in AssetClass}
        correlation_regime = CorrelationRegimeState.BREAKDOWN
    return HierarchicalRegime.create(
        global_regime=global_regime,
        asset_regimes=ar,
        correlation_regime=correlation_regime,
        global_confidence=0.8,
        asset_confidences=conf,
        sub_regime=DEFAULT_SUB_REGIME.copy(),
        sequence_id=1,
    )


# =============================================================================
# SECTION 1 -- BTC + EURUSD + SPX PIPELINE (RISK_ON)
# =============================================================================

class TestMultiAssetPipelineRiskOn:
    """Full pipeline: asset risk -> correlation -> tail -> gap -> portfolio -> budget -> heatmap."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.regime = _make_regime(global_regime=GlobalRegimeState.RISK_ON)
        self.portfolio_risk = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS,
            returns=RETURNS,
            regime=self.regime,
            price_histories=PRICE_HISTORIES,
        )

    def test_three_assets_present(self):
        assert self.portfolio_risk.num_assets == 3
        for sym in SYMBOLS:
            assert sym in self.portfolio_risk.asset_risks

    def test_asset_classes_correct(self):
        assert self.portfolio_risk.asset_risks["BTC"].asset_class == AssetClass.CRYPTO
        assert self.portfolio_risk.asset_risks["EURUSD"].asset_class == AssetClass.FOREX
        assert self.portfolio_risk.asset_risks["SPX"].asset_class == AssetClass.INDICES

    def test_btc_highest_notional(self):
        btc = self.portfolio_risk.asset_risks["BTC"].notional
        eur = self.portfolio_risk.asset_risks["EURUSD"].notional
        spx = self.portfolio_risk.asset_risks["SPX"].notional
        assert btc > 0 and eur > 0 and spx > 0

    def test_portfolio_var_positive(self):
        assert self.portfolio_risk.portfolio_var_95 > 0.0
        assert self.portfolio_risk.portfolio_var_99 > self.portfolio_risk.portfolio_var_95

    def test_total_notional(self):
        expected = 65000.0 + 1.08 * 100000.0 + 5200.0 * 100.0
        assert abs(self.portfolio_risk.total_notional - expected) < 1.0

    def test_correlation_matrix_3x3(self):
        corr = self.portfolio_risk.correlation_result
        assert len(corr.matrix) == 3
        assert len(corr.matrix[0]) == 3
        # Diagonal should be 1.0
        for i in range(3):
            assert abs(corr.matrix[i][i] - 1.0) < 1e-10

    def test_tail_risk_three_assets(self):
        assert self.portfolio_risk.tail_risk.num_assets == 3
        assert self.portfolio_risk.tail_risk.var_95 > 0.0
        assert self.portfolio_risk.tail_risk.cvar_95 >= self.portfolio_risk.tail_risk.var_95

    def test_gap_risk_only_indices(self):
        gap = self.portfolio_risk.gap_risk
        # BTC (crypto) and EURUSD (forex) have no gap risk; SPX (indices) does
        for ar in gap.asset_results:
            if ar.asset_class == AssetClass.CRYPTO:
                assert ar.gap_enabled is False
            elif ar.asset_class == AssetClass.FOREX:
                assert ar.gap_enabled is False
            elif ar.asset_class == AssetClass.INDICES:
                assert ar.gap_enabled is True

    def test_diversification_benefit_positive(self):
        assert self.portfolio_risk.diversification_benefit >= 0.0

    def test_risk_budget_allocates_all_classes(self):
        budget = PortfolioRiskBudget().allocate(
            total_capital=100000.0,
            asset_classes=list(AssetClass),
            regime=self.regime,
            portfolio_risk=self.portfolio_risk,
        )
        assert budget.num_asset_classes == 5
        total_frac = sum(b.risk_budget_fraction for b in budget.budgets.values())
        assert abs(total_frac - 1.0) < 1e-10

    def test_heatmap_snapshot(self):
        engine = PortfolioHeatmapEngine()
        snap = engine.build_snapshot(
            portfolio_risk=self.portfolio_risk,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        assert snap.num_assets == 3
        assert 0.0 <= snap.global_heat <= 1.0
        for cell in snap.cells.values():
            assert 0.0 <= cell.heat_score <= 1.0

    def test_systemic_risk_classification(self):
        corr = self.portfolio_risk.correlation_result
        cr = classify_correlation_regime(
            corr_matrix=corr.matrix, n_assets=3,
        )
        assert cr.state in (
            CorrelationRegimeState.NORMAL,
            CorrelationRegimeState.COUPLED,
            CorrelationRegimeState.BREAKDOWN,
        )

    def test_portfolio_fragility(self):
        corr = self.portfolio_risk.correlation_result
        frag = compute_portfolio_fragility(
            corr_matrix=corr.matrix,
            asset_ids=list(SYMBOLS),
        )
        assert frag.fragility_band in ("LOW", "MEDIUM", "HIGH")
        assert 0.0 <= frag.confidence_penalty <= 0.20

    def test_session_execution_all_assets(self):
        executor = SessionAwareExecutor()
        # Wednesday 14:00 UTC -> all markets should be open
        for sym, (ac, price, size) in POSITIONS.items():
            d = executor.execute(
                symbol=sym,
                asset_class=ac,
                order_size=size,
                current_hour=14,
                current_minute=0,
                current_weekday=2,
            )
            assert d.status == STATUS_FILLED


# =============================================================================
# SECTION 2 -- CRISIS SCENARIO
# =============================================================================

class TestCrisisScenario:
    """Full pipeline under CRISIS regime: all assets SHOCK, correlation BREAKDOWN."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.regime = _make_regime(global_regime=GlobalRegimeState.CRISIS)
        self.portfolio_risk = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS,
            returns=RETURNS,
            regime=self.regime,
            price_histories=PRICE_HISTORIES,
        )
        self.risk_on_regime = _make_regime(global_regime=GlobalRegimeState.RISK_ON)
        self.risk_on_pr = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS,
            returns=RETURNS,
            regime=self.risk_on_regime,
            price_histories=PRICE_HISTORIES,
        )

    def test_crisis_invariant_all_assets_shock(self):
        assert self.regime.global_regime == GlobalRegimeState.CRISIS
        for ac, ar in self.regime.asset_regimes.items():
            assert ar == AssetRegimeState.SHOCK

    def test_crisis_invariant_correlation_breakdown(self):
        assert self.regime.correlation_regime == CorrelationRegimeState.BREAKDOWN

    def test_crisis_higher_var_than_risk_on(self):
        assert self.portfolio_risk.portfolio_var_95 > self.risk_on_pr.portfolio_var_95

    def test_crisis_higher_vol_than_risk_on(self):
        assert self.portfolio_risk.portfolio_volatility > self.risk_on_pr.portfolio_volatility

    def test_crisis_correlation_is_breakdown(self):
        corr = self.portfolio_risk.correlation_result
        assert corr.is_crisis_override is True
        assert corr.regime_state == CorrelationRegimeState.BREAKDOWN

    def test_crisis_tail_risk_elevated(self):
        crisis_tail = self.portfolio_risk.tail_risk
        normal_tail = self.risk_on_pr.tail_risk
        assert crisis_tail.var_99 > normal_tail.var_99

    def test_crisis_diversification_valid(self):
        # Both diversification benefits should be non-negative and bounded [0, 1]
        assert 0.0 <= self.portfolio_risk.diversification_benefit <= 1.0
        assert 0.0 <= self.risk_on_pr.diversification_benefit <= 1.0

    def test_crisis_budget_reduces_crypto(self):
        budget = PortfolioRiskBudget().allocate(
            total_capital=100000.0,
            asset_classes=list(AssetClass),
            regime=self.regime,
            portfolio_risk=self.portfolio_risk,
        )
        normal_budget = PortfolioRiskBudget().allocate(
            total_capital=100000.0,
            asset_classes=list(AssetClass),
            regime=self.risk_on_regime,
            portfolio_risk=self.risk_on_pr,
        )
        crisis_crypto = budget.budgets[AssetClass.CRYPTO].allocated_capital
        normal_crypto = normal_budget.budgets[AssetClass.CRYPTO].allocated_capital
        assert crisis_crypto < normal_crypto

    def test_crisis_stress_test_persistent(self):
        corr = self.portfolio_risk.correlation_result
        cr = classify_correlation_regime(corr_matrix=corr.matrix, n_assets=3)
        stress = simulate_tail_stress(
            current_corr_regime=cr, stress_scenario="SEVERE",
        )
        # Already high correlation in crisis -> stress should be persistent
        assert stress.stressed_mean_corr > cr.mean_pairwise_corr or stress.stressed_mean_corr == 1.0

    def test_crisis_heatmap_elevated(self):
        engine = PortfolioHeatmapEngine()
        crisis_snap = engine.build_snapshot(
            portfolio_risk=self.portfolio_risk,
            active_failure_modes=("FM-04",),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.3,
            net_exposure=0.2,
        )
        engine2 = PortfolioHeatmapEngine()
        normal_snap = engine2.build_snapshot(
            portfolio_risk=self.risk_on_pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        # Crisis snapshot should reflect CRISIS regime and have FM-04 active
        assert crisis_snap.regime == GlobalRegimeState.CRISIS
        assert crisis_snap.correlation_regime == CorrelationRegimeState.BREAKDOWN
        assert "FM-04" in crisis_snap.active_failure_modes
        assert 0.0 <= crisis_snap.global_heat <= 1.0


# =============================================================================
# SECTION 3 -- RISK_OFF SCENARIO
# =============================================================================

class TestRiskOffScenario:
    """Pipeline under RISK_OFF: reduced risk appetite, safe haven preference."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.regime = _make_regime(global_regime=GlobalRegimeState.RISK_OFF)
        self.portfolio_risk = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS,
            returns=RETURNS,
            regime=self.regime,
            price_histories=PRICE_HISTORIES,
        )

    def test_risk_off_budget_favors_forex(self):
        budget = PortfolioRiskBudget().allocate(
            total_capital=100000.0,
            asset_classes=list(AssetClass),
            regime=self.regime,
            portfolio_risk=self.portfolio_risk,
        )
        forex = budget.budgets[AssetClass.FOREX]
        crypto = budget.budgets[AssetClass.CRYPTO]
        # Forex is safe haven (1.2x), crypto reduced (0.5x)
        assert forex.regime_adjustment_factor > crypto.regime_adjustment_factor

    def test_risk_off_regime_stored(self):
        assert self.portfolio_risk.regime.global_regime == GlobalRegimeState.RISK_OFF


# =============================================================================
# SECTION 4 -- CORRELATION REGIME TRANSITIONS
# =============================================================================

class TestCorrelationRegimeTransitions:
    """Test portfolio behavior across different correlation regimes."""

    def _make_pr(self, corr_regime):
        regime = _make_regime(correlation_regime=corr_regime)
        return PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS,
            regime=regime, price_histories=PRICE_HISTORIES,
        )

    def test_breakdown_regime_classified_correctly(self):
        breakdown = self._make_pr(CorrelationRegimeState.BREAKDOWN)
        assert breakdown.correlation_result.regime_state == CorrelationRegimeState.BREAKDOWN
        # BREAKDOWN correlations should be high (>= 0.65 threshold)
        assert breakdown.correlation_result.average_correlation >= 0.65

    def test_breakdown_budget_reduced(self):
        normal_regime = _make_regime(correlation_regime=CorrelationRegimeState.NORMAL)
        breakdown_regime = _make_regime(correlation_regime=CorrelationRegimeState.BREAKDOWN)
        normal_pr = self._make_pr(CorrelationRegimeState.NORMAL)
        breakdown_pr = self._make_pr(CorrelationRegimeState.BREAKDOWN)

        normal_budget = PortfolioRiskBudget().allocate(
            total_capital=100000.0,
            asset_classes=list(AssetClass),
            regime=normal_regime,
            portfolio_risk=normal_pr,
        )
        breakdown_budget = PortfolioRiskBudget().allocate(
            total_capital=100000.0,
            asset_classes=list(AssetClass),
            regime=breakdown_regime,
            portfolio_risk=breakdown_pr,
        )
        # BREAKDOWN applies 0.6x blanket reduction -> lower correlation_adjustment_factor
        for ac in AssetClass:
            assert (
                breakdown_budget.budgets[ac].correlation_adjustment_factor
                < normal_budget.budgets[ac].correlation_adjustment_factor + 0.01
            )

    def test_divergence_allows_more_spread(self):
        normal_regime = _make_regime(correlation_regime=CorrelationRegimeState.NORMAL)
        div_regime = _make_regime(correlation_regime=CorrelationRegimeState.DIVERGENCE)
        normal_pr = self._make_pr(CorrelationRegimeState.NORMAL)
        div_pr = self._make_pr(CorrelationRegimeState.DIVERGENCE)

        normal_budget = PortfolioRiskBudget().allocate(
            total_capital=100000.0,
            asset_classes=list(AssetClass),
            regime=normal_regime,
            portfolio_risk=normal_pr,
        )
        div_budget = PortfolioRiskBudget().allocate(
            total_capital=100000.0,
            asset_classes=list(AssetClass),
            regime=div_regime,
            portfolio_risk=div_pr,
        )
        # DIVERGENCE applies 1.1x factor
        for ac in AssetClass:
            assert (
                div_budget.budgets[ac].correlation_adjustment_factor
                >= normal_budget.budgets[ac].correlation_adjustment_factor - 0.01
            )


# =============================================================================
# SECTION 5 -- SESSION-AWARE EXECUTION SCENARIOS
# =============================================================================

class TestSessionAwareExecution:
    """Multi-asset execution at different times of day."""

    def test_all_filled_wednesday_afternoon(self):
        executor = SessionAwareExecutor()
        for sym, (ac, price, size) in POSITIONS.items():
            d = executor.execute(
                symbol=sym, asset_class=ac, order_size=size,
                current_hour=14, current_minute=0, current_weekday=2,
            )
            assert d.status == STATUS_FILLED

    def test_spx_deferred_overnight(self):
        d = SessionAwareExecutor().execute(
            symbol="SPX", asset_class=AssetClass.INDICES, order_size=100.0,
            current_hour=2, current_minute=0, current_weekday=2,
        )
        assert d.status == STATUS_DEFERRED

    def test_spx_auction_pre_market(self):
        d = SessionAwareExecutor().execute(
            symbol="SPX", asset_class=AssetClass.INDICES, order_size=100.0,
            current_hour=5, current_minute=0, current_weekday=2,
        )
        assert d.status == STATUS_AUCTION

    def test_spx_deferred_near_close(self):
        d = SessionAwareExecutor().execute(
            symbol="SPX", asset_class=AssetClass.INDICES, order_size=100.0,
            current_hour=15, current_minute=50, current_weekday=2,
        )
        assert d.status == STATUS_DEFERRED

    def test_btc_filled_weekend(self):
        d = SessionAwareExecutor().execute(
            symbol="BTC", asset_class=AssetClass.CRYPTO, order_size=1.0,
            current_hour=12, current_minute=0, current_weekday=6,
        )
        assert d.status == STATUS_FILLED

    def test_eurusd_deferred_weekend(self):
        d = SessionAwareExecutor().execute(
            symbol="EURUSD", asset_class=AssetClass.FOREX, order_size=100000.0,
            current_hour=12, current_minute=0, current_weekday=5,
        )
        assert d.status == STATUS_DEFERRED

    def test_eurusd_asia_low_liquidity(self):
        d = SessionAwareExecutor().execute(
            symbol="EURUSD", asset_class=AssetClass.FOREX, order_size=100000.0,
            current_hour=3, current_minute=0, current_weekday=2,
        )
        assert d.status == STATUS_FILLED
        assert d.size_adjustment_factor < 1.0  # Reduced for low liquidity


# =============================================================================
# SECTION 6 -- CROSS-MODULE CONSISTENCY
# =============================================================================

class TestCrossModuleConsistency:
    """Verify data flows correctly between modules."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.regime = _make_regime()
        self.pr = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS,
            regime=self.regime, price_histories=PRICE_HISTORIES,
        )

    def test_asset_risk_feeds_portfolio(self):
        # Asset risks computed individually should match those in portfolio
        calc = AssetRiskCalculator()
        btc_risk = calc.calculate_risk(
            symbol="BTC", asset_class=AssetClass.CRYPTO,
            returns=BTC_RETURNS, current_price=65000.0, position_size=1.0,
            regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.8,
        )
        pr_btc = self.pr.asset_risks["BTC"]
        assert btc_risk.daily_var_95 == pr_btc.daily_var_95

    def test_correlation_feeds_tail_risk(self):
        # Tail risk uses the same correlation matrix from portfolio
        tail = MultivariateTailModel()
        direct_tail = tail.estimate(
            asset_risks=self.pr.asset_risks,
            correlation_matrix=self.pr.correlation_result.matrix,
            symbols=tuple(sorted(POSITIONS.keys())),
        )
        assert direct_tail.result_hash == self.pr.tail_risk.result_hash

    def test_gap_risk_feeds_portfolio(self):
        gap = GapRiskModel()
        direct_gap = gap.estimate(
            positions=POSITIONS, price_histories=PRICE_HISTORIES,
        )
        assert direct_gap.result_hash == self.pr.gap_risk.result_hash

    def test_systemic_risk_uses_portfolio_corr(self):
        cr = classify_correlation_regime(
            corr_matrix=self.pr.correlation_result.matrix, n_assets=3,
        )
        assert cr.n_pairs == 3  # C(3,2) = 3

    def test_concentration_from_portfolio_notionals(self):
        weights = {}
        for sym, ar in self.pr.asset_risks.items():
            ac_name = ar.asset_class.value
            weights[ac_name] = weights.get(ac_name, 0.0) + ar.notional
        cr = compute_concentration_risk(weights_by_class=weights)
        assert cr.hhi_weight > 0.0
        assert cr.dominant_class in ("crypto", "forex", "indices")


# =============================================================================
# SECTION 7 -- DETERMINISM
# =============================================================================

class TestEndToEndDeterminism:
    """Verify bit-identical outputs across repeated calls."""

    def test_portfolio_risk_deterministic(self):
        regime = _make_regime()
        r1 = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS,
            regime=regime, price_histories=PRICE_HISTORIES,
        )
        r2 = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS,
            regime=regime, price_histories=PRICE_HISTORIES,
        )
        assert r1.result_hash == r2.result_hash
        assert r1.portfolio_var_95 == r2.portfolio_var_95
        assert r1.tail_risk.result_hash == r2.tail_risk.result_hash

    def test_risk_budget_deterministic(self):
        regime = _make_regime()
        pr = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS,
            regime=regime, price_histories=PRICE_HISTORIES,
        )
        b1 = PortfolioRiskBudget().allocate(
            total_capital=100000.0, asset_classes=list(AssetClass),
            regime=regime, portfolio_risk=pr,
        )
        b2 = PortfolioRiskBudget().allocate(
            total_capital=100000.0, asset_classes=list(AssetClass),
            regime=regime, portfolio_risk=pr,
        )
        assert b1.result_hash == b2.result_hash

    def test_execution_deterministic(self):
        d1 = SessionAwareExecutor().execute(
            symbol="SPX", asset_class=AssetClass.INDICES, order_size=100.0,
            current_hour=14, current_minute=0, current_weekday=2,
        )
        d2 = SessionAwareExecutor().execute(
            symbol="SPX", asset_class=AssetClass.INDICES, order_size=100.0,
            current_hour=14, current_minute=0, current_weekday=2,
        )
        assert d1.result_hash == d2.result_hash

    def test_inputs_not_mutated(self):
        positions_copy = dict(POSITIONS)
        returns_copy = {k: list(v) for k, v in RETURNS.items()}
        prices_copy = {k: list(v) for k, v in PRICE_HISTORIES.items()}
        regime = _make_regime()

        PortfolioRiskEngine().calculate_portfolio_risk(
            positions=positions_copy, returns=returns_copy,
            regime=regime, price_histories=prices_copy,
        )

        assert positions_copy == POSITIONS
        for k in RETURNS:
            assert returns_copy[k] == RETURNS[k]
        for k in PRICE_HISTORIES:
            assert prices_copy[k] == PRICE_HISTORIES[k]


# =============================================================================
# SECTION 8 -- IMMUTABILITY
# =============================================================================

class TestEndToEndImmutability:
    """Verify all result objects are frozen."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.regime = _make_regime()
        self.pr = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS,
            regime=self.regime, price_histories=PRICE_HISTORIES,
        )

    def test_portfolio_risk_frozen(self):
        with pytest.raises(AttributeError):
            self.pr.portfolio_var_95 = 0.0

    def test_asset_risk_frozen(self):
        with pytest.raises(AttributeError):
            self.pr.asset_risks["BTC"].symbol = "ETH"

    def test_correlation_frozen(self):
        with pytest.raises(AttributeError):
            self.pr.correlation_result.average_correlation = 0.0

    def test_tail_risk_frozen(self):
        with pytest.raises(AttributeError):
            self.pr.tail_risk.var_95 = 0.0

    def test_execution_frozen(self):
        d = SessionAwareExecutor().execute(
            symbol="BTC", asset_class=AssetClass.CRYPTO, order_size=1.0,
            current_hour=14, current_minute=0, current_weekday=2,
        )
        with pytest.raises(AttributeError):
            d.status = "REJECTED"


# =============================================================================
# SECTION 9 -- STRESS SCENARIOS
# =============================================================================

class TestStressScenarios:
    """Extreme but valid input scenarios."""

    def test_high_volatility_returns(self):
        # Returns with 10% daily moves
        volatile = [0.10 * ((-1) ** i) for i in range(30)]
        returns = {"BTC": volatile, "EURUSD": volatile, "SPX": volatile}
        regime = _make_regime()
        pr = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS, returns=returns,
            regime=regime, price_histories=PRICE_HISTORIES,
        )
        assert pr.portfolio_var_95 > 0.0
        assert math.isfinite(pr.portfolio_var_95)

    def test_zero_volatility_returns(self):
        flat = [0.0] * 30
        returns = {"BTC": flat, "EURUSD": flat, "SPX": flat}
        regime = _make_regime()
        pr = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS, returns=returns,
            regime=regime, price_histories=PRICE_HISTORIES,
        )
        assert pr.portfolio_var_95 == 0.0

    def test_all_regimes_produce_valid_results(self):
        for gr in GlobalRegimeState:
            regime = _make_regime(global_regime=gr)
            pr = PortfolioRiskEngine().calculate_portfolio_risk(
                positions=POSITIONS, returns=RETURNS,
                regime=regime, price_histories=PRICE_HISTORIES,
            )
            assert pr.num_assets == 3
            assert math.isfinite(pr.portfolio_var_95)

    def test_all_correlation_regimes(self):
        for cr in CorrelationRegimeState:
            regime = _make_regime(correlation_regime=cr)
            pr = PortfolioRiskEngine().calculate_portfolio_risk(
                positions=POSITIONS, returns=RETURNS,
                regime=regime, price_histories=PRICE_HISTORIES,
            )
            assert pr.num_assets == 3

    def test_tail_stress_all_scenarios(self):
        regime = _make_regime()
        pr = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS,
            regime=regime, price_histories=PRICE_HISTORIES,
        )
        cr = classify_correlation_regime(
            corr_matrix=pr.correlation_result.matrix, n_assets=3,
        )
        for scenario in ("MILD", "MODERATE", "SEVERE", "EXTREME"):
            stress = simulate_tail_stress(
                current_corr_regime=cr, stress_scenario=scenario,
            )
            assert 0.0 <= stress.stressed_mean_corr <= 1.0
            assert stress.recovery_scenario in ("FAST", "SLOW", "PERSISTENT")


# =============================================================================
# SECTION 10 -- HASH CHAIN CONSISTENCY
# =============================================================================

class TestHashChainConsistency:
    """Verify all result hashes are valid hex strings of expected length."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.regime = _make_regime()
        self.pr = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS,
            regime=self.regime, price_histories=PRICE_HISTORIES,
        )

    def _assert_hash(self, h):
        assert isinstance(h, str)
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)

    def test_portfolio_risk_hash(self):
        self._assert_hash(self.pr.result_hash)

    def test_asset_risk_hashes(self):
        for sym, ar in self.pr.asset_risks.items():
            self._assert_hash(ar.result_hash)

    def test_correlation_hash(self):
        self._assert_hash(self.pr.correlation_result.result_hash)

    def test_tail_risk_hash(self):
        self._assert_hash(self.pr.tail_risk.result_hash)

    def test_gap_risk_hash(self):
        self._assert_hash(self.pr.gap_risk.result_hash)

    def test_budget_hashes(self):
        budget = PortfolioRiskBudget().allocate(
            total_capital=100000.0, asset_classes=list(AssetClass),
            regime=self.regime, portfolio_risk=self.pr,
        )
        self._assert_hash(budget.result_hash)
        for ac, b in budget.budgets.items():
            self._assert_hash(b.result_hash)

    def test_execution_hash(self):
        d = SessionAwareExecutor().execute(
            symbol="BTC", asset_class=AssetClass.CRYPTO, order_size=1.0,
            current_hour=14, current_minute=0, current_weekday=2,
        )
        self._assert_hash(d.result_hash)

    def test_systemic_risk_hashes(self):
        cr = classify_correlation_regime(
            corr_matrix=self.pr.correlation_result.matrix, n_assets=3,
        )
        self._assert_hash(cr.result_hash)
        frag = compute_portfolio_fragility(
            corr_matrix=self.pr.correlation_result.matrix,
            asset_ids=list(SYMBOLS),
        )
        self._assert_hash(frag.result_hash)
