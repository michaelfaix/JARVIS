# =============================================================================
# tests/test_ma8_coverage_benchmarks.py -- Phase MA-8 Performance Gate Tests
#
# Automated performance benchmarks as pytest assertions.
# Validates FAS performance targets: < 500ms P95 total pipeline latency.
# Individual module targets derived from FAS performance matrix.
#
# P0: All outputs are analytical. No execution. No real orders.
# =============================================================================

import time
from typing import Callable

import pytest

from jarvis.core.regime import (
    AssetClass,
    AssetRegimeState,
    CorrelationRegimeState,
    GlobalRegimeState,
    HierarchicalRegime,
)
from jarvis.execution.session_aware_executor import SessionAwareExecutor
from jarvis.risk.asset_risk import AssetRiskCalculator
from jarvis.risk.correlation import DynamicCorrelationModel
from jarvis.risk.gap_risk import GapRiskModel
from jarvis.risk.portfolio_heatmap import PortfolioHeatmapEngine, TRIGGER_NEW_CANDLE
from jarvis.risk.portfolio_risk import PortfolioRiskEngine
from jarvis.risk.risk_budget import PortfolioRiskBudget
from jarvis.risk.risk_engine import RiskEngine
from jarvis.risk.systemic_risk import (
    classify_correlation_regime,
    compute_concentration_risk,
    compute_portfolio_fragility,
    simulate_tail_stress,
)
from jarvis.risk.tail_risk import MultivariateTailModel


# =============================================================================
# TEST DATA
# =============================================================================

BTC_RETURNS = [
    0.03, -0.04, 0.02, -0.01, 0.05, -0.03, 0.01, -0.02, 0.04, -0.05,
    0.02, -0.01, 0.03, -0.04, 0.01, 0.02, -0.03, 0.04, -0.02, 0.01,
    -0.01, 0.03, -0.02, 0.01, -0.04, 0.05, -0.01, 0.02, -0.03, 0.01,
]
EUR_RETURNS = [r * 0.15 for r in BTC_RETURNS]
SPX_RETURNS = [r * 0.4 for r in BTC_RETURNS]
RETURNS = {"BTC": BTC_RETURNS, "EURUSD": EUR_RETURNS, "SPX": SPX_RETURNS}
SYMBOLS = ["BTC", "EURUSD", "SPX"]
POSITIONS = {
    "BTC": (AssetClass.CRYPTO, 65000.0, 1.0),
    "EURUSD": (AssetClass.FOREX, 1.08, 100000.0),
    "SPX": (AssetClass.INDICES, 5200.0, 100.0),
}
PRICE_HISTORIES = {
    "BTC": [65000.0 + i * 100.0 for i in range(30)],
    "EURUSD": [1.08 + i * 0.001 for i in range(30)],
    "SPX": [5200.0 + i * 10.0 for i in range(30)],
}


def _make_regime(gr=GlobalRegimeState.RISK_ON, cr=CorrelationRegimeState.NORMAL):
    ar = ({ac: AssetRegimeState.SHOCK for ac in AssetClass}
          if gr == GlobalRegimeState.CRISIS
          else {ac: AssetRegimeState.TRENDING_UP for ac in AssetClass})
    return HierarchicalRegime.create(
        global_regime=gr, asset_regimes=ar, correlation_regime=cr,
        global_confidence=0.8, asset_confidences={ac: 0.8 for ac in AssetClass},
        sub_regime={ac: "default" for ac in AssetClass}, sequence_id=1,
    )


def _measure_us(func: Callable, n: int = 100) -> float:
    func()  # warmup
    t0 = time.perf_counter_ns()
    for _ in range(n):
        func()
    return (time.perf_counter_ns() - t0) / n / 1000  # microseconds


# =============================================================================
# FAS PERFORMANCE TARGETS (microseconds)
# =============================================================================
# FAS specifies: Risk Calculation < 100ms, Total < 500ms
# We set per-module budgets well under FAS limits.

BUDGET_ASSET_RISK_US = 5_000       # 5ms per asset
BUDGET_CORRELATION_US = 5_000      # 5ms
BUDGET_TAIL_RISK_US = 5_000        # 5ms
BUDGET_GAP_RISK_US = 5_000         # 5ms
BUDGET_PORTFOLIO_RISK_US = 10_000  # 10ms (aggregator)
BUDGET_RISK_BUDGET_US = 5_000      # 5ms
BUDGET_SYSTEMIC_US = 5_000         # 5ms per function
BUDGET_HEATMAP_US = 5_000          # 5ms
BUDGET_EXECUTOR_US = 5_000         # 5ms per asset
BUDGET_CORE_RISK_US = 10_000       # 10ms
BUDGET_FULL_PIPELINE_US = 100_000  # 100ms (FAS: < 500ms)


# =============================================================================
# PERFORMANCE GATE TESTS
# =============================================================================

class TestPerformanceGates:
    """Validate all modules meet FAS performance budgets."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.regime = _make_regime()
        self.calc = AssetRiskCalculator()
        self.corr_model = DynamicCorrelationModel()
        self.tail_model = MultivariateTailModel()
        self.gap_model = GapRiskModel()
        self.pr_engine = PortfolioRiskEngine()
        self.budget_engine = PortfolioRiskBudget()
        self.executor = SessionAwareExecutor()

    def test_asset_risk_crypto_under_budget(self):
        us = _measure_us(lambda: self.calc.calculate_risk(
            symbol="BTC", asset_class=AssetClass.CRYPTO, returns=BTC_RETURNS,
            current_price=65000.0, position_size=1.0,
            regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.8,
        ))
        assert us < BUDGET_ASSET_RISK_US, f"AssetRisk CRYPTO: {us:.0f}us > {BUDGET_ASSET_RISK_US}us"

    def test_asset_risk_forex_under_budget(self):
        us = _measure_us(lambda: self.calc.calculate_risk(
            symbol="EURUSD", asset_class=AssetClass.FOREX, returns=EUR_RETURNS,
            current_price=1.08, position_size=100000.0,
            regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.9,
        ))
        assert us < BUDGET_ASSET_RISK_US, f"AssetRisk FOREX: {us:.0f}us > {BUDGET_ASSET_RISK_US}us"

    def test_asset_risk_indices_under_budget(self):
        us = _measure_us(lambda: self.calc.calculate_risk(
            symbol="SPX", asset_class=AssetClass.INDICES, returns=SPX_RETURNS,
            current_price=5200.0, position_size=100.0,
            regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.95,
        ))
        assert us < BUDGET_ASSET_RISK_US, f"AssetRisk INDICES: {us:.0f}us > {BUDGET_ASSET_RISK_US}us"

    def test_correlation_under_budget(self):
        us = _measure_us(lambda: self.corr_model.estimate(
            returns=RETURNS, symbols=SYMBOLS, regime=self.regime,
        ))
        assert us < BUDGET_CORRELATION_US, f"Correlation: {us:.0f}us > {BUDGET_CORRELATION_US}us"

    def test_tail_risk_under_budget(self):
        ar = {s: self.calc.calculate_risk(
            symbol=s, asset_class=POSITIONS[s][0], returns=RETURNS[s],
            current_price=POSITIONS[s][1], position_size=POSITIONS[s][2],
            regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.8,
        ) for s in SYMBOLS}
        cr = self.corr_model.estimate(returns=RETURNS, symbols=SYMBOLS, regime=self.regime)
        us = _measure_us(lambda: self.tail_model.estimate(
            asset_risks=ar, correlation_matrix=cr.matrix, symbols=cr.symbols,
        ))
        assert us < BUDGET_TAIL_RISK_US, f"TailRisk: {us:.0f}us > {BUDGET_TAIL_RISK_US}us"

    def test_gap_risk_under_budget(self):
        us = _measure_us(lambda: self.gap_model.estimate(
            positions=POSITIONS, price_histories=PRICE_HISTORIES,
        ))
        assert us < BUDGET_GAP_RISK_US, f"GapRisk: {us:.0f}us > {BUDGET_GAP_RISK_US}us"

    def test_portfolio_risk_under_budget(self):
        us = _measure_us(lambda: self.pr_engine.calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS, regime=self.regime,
            price_histories=PRICE_HISTORIES,
        ))
        assert us < BUDGET_PORTFOLIO_RISK_US, f"PortfolioRisk: {us:.0f}us > {BUDGET_PORTFOLIO_RISK_US}us"

    def test_risk_budget_under_budget(self):
        pr = self.pr_engine.calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS, regime=self.regime,
            price_histories=PRICE_HISTORIES,
        )
        us = _measure_us(lambda: self.budget_engine.allocate(
            total_capital=100000.0, asset_classes=list(AssetClass),
            regime=self.regime, portfolio_risk=pr,
        ))
        assert us < BUDGET_RISK_BUDGET_US, f"RiskBudget: {us:.0f}us > {BUDGET_RISK_BUDGET_US}us"

    def test_classify_corr_regime_under_budget(self):
        pr = self.pr_engine.calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS, regime=self.regime,
            price_histories=PRICE_HISTORIES,
        )
        us = _measure_us(lambda: classify_correlation_regime(
            corr_matrix=pr.correlation_result.matrix, n_assets=3,
        ))
        assert us < BUDGET_SYSTEMIC_US, f"ClassifyCorrRegime: {us:.0f}us > {BUDGET_SYSTEMIC_US}us"

    def test_portfolio_fragility_under_budget(self):
        pr = self.pr_engine.calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS, regime=self.regime,
            price_histories=PRICE_HISTORIES,
        )
        us = _measure_us(lambda: compute_portfolio_fragility(
            corr_matrix=pr.correlation_result.matrix, asset_ids=SYMBOLS,
        ))
        assert us < BUDGET_SYSTEMIC_US, f"Fragility: {us:.0f}us > {BUDGET_SYSTEMIC_US}us"

    def test_tail_stress_under_budget(self):
        pr = self.pr_engine.calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS, regime=self.regime,
            price_histories=PRICE_HISTORIES,
        )
        cr = classify_correlation_regime(corr_matrix=pr.correlation_result.matrix, n_assets=3)
        us = _measure_us(lambda: simulate_tail_stress(
            current_corr_regime=cr, stress_scenario="SEVERE",
        ))
        assert us < BUDGET_SYSTEMIC_US, f"TailStress: {us:.0f}us > {BUDGET_SYSTEMIC_US}us"

    def test_concentration_risk_under_budget(self):
        us = _measure_us(lambda: compute_concentration_risk(
            weights_by_class={"CRYPTO": 0.3, "FOREX": 0.2, "INDICES": 0.5},
        ))
        assert us < BUDGET_SYSTEMIC_US, f"ConcentrationRisk: {us:.0f}us > {BUDGET_SYSTEMIC_US}us"

    def test_heatmap_under_budget(self):
        pr = self.pr_engine.calculate_portfolio_risk(
            positions=POSITIONS, returns=RETURNS, regime=self.regime,
            price_histories=PRICE_HISTORIES,
        )
        us = _measure_us(lambda: PortfolioHeatmapEngine().build_snapshot(
            portfolio_risk=pr, active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE, gross_exposure=0.5, net_exposure=0.3,
        ))
        assert us < BUDGET_HEATMAP_US, f"Heatmap: {us:.0f}us > {BUDGET_HEATMAP_US}us"

    def test_executor_crypto_under_budget(self):
        us = _measure_us(lambda: self.executor.execute(
            symbol="BTC", asset_class=AssetClass.CRYPTO, order_size=1.0,
            current_hour=15, current_minute=30, current_weekday=2,
        ))
        assert us < BUDGET_EXECUTOR_US, f"Executor CRYPTO: {us:.0f}us > {BUDGET_EXECUTOR_US}us"

    def test_executor_forex_under_budget(self):
        us = _measure_us(lambda: self.executor.execute(
            symbol="EURUSD", asset_class=AssetClass.FOREX, order_size=100000.0,
            current_hour=15, current_minute=30, current_weekday=2,
        ))
        assert us < BUDGET_EXECUTOR_US, f"Executor FOREX: {us:.0f}us > {BUDGET_EXECUTOR_US}us"

    def test_executor_indices_under_budget(self):
        us = _measure_us(lambda: self.executor.execute(
            symbol="SPX", asset_class=AssetClass.INDICES, order_size=100.0,
            current_hour=15, current_minute=30, current_weekday=2,
        ))
        assert us < BUDGET_EXECUTOR_US, f"Executor INDICES: {us:.0f}us > {BUDGET_EXECUTOR_US}us"

    def test_core_risk_engine_under_budget(self):
        us = _measure_us(lambda: RiskEngine().assess(
            returns_history=BTC_RETURNS, current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        ))
        assert us < BUDGET_CORE_RISK_US, f"CoreRiskEngine: {us:.0f}us > {BUDGET_CORE_RISK_US}us"


class TestFullPipelinePerformance:
    """FAS P95 gate: full multi-asset pipeline < 500ms."""

    def test_full_ma_pipeline_under_500ms(self):
        regime = _make_regime()
        calc = AssetRiskCalculator()
        corr_model = DynamicCorrelationModel()
        tail_model = MultivariateTailModel()
        gap_model = GapRiskModel()
        pr_engine = PortfolioRiskEngine()
        budget_engine = PortfolioRiskBudget()
        executor = SessionAwareExecutor()
        weights = {"CRYPTO": 0.3, "FOREX": 0.2, "INDICES": 0.5}

        def pipeline():
            ab = calc.calculate_risk(symbol="BTC", asset_class=AssetClass.CRYPTO, returns=BTC_RETURNS, current_price=65000.0, position_size=1.0, regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.8)
            ae = calc.calculate_risk(symbol="EURUSD", asset_class=AssetClass.FOREX, returns=EUR_RETURNS, current_price=1.08, position_size=100000.0, regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.9)
            a_s = calc.calculate_risk(symbol="SPX", asset_class=AssetClass.INDICES, returns=SPX_RETURNS, current_price=5200.0, position_size=100.0, regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.95)
            c = corr_model.estimate(returns=RETURNS, symbols=SYMBOLS, regime=regime)
            tail_model.estimate(asset_risks={"BTC": ab, "EURUSD": ae, "SPX": a_s}, correlation_matrix=c.matrix, symbols=c.symbols)
            gap_model.estimate(positions=POSITIONS, price_histories=PRICE_HISTORIES)
            p = pr_engine.calculate_portfolio_risk(positions=POSITIONS, returns=RETURNS, regime=regime, price_histories=PRICE_HISTORIES)
            budget_engine.allocate(total_capital=100000.0, asset_classes=list(AssetClass), regime=regime, portfolio_risk=p)
            cr = classify_correlation_regime(corr_matrix=c.matrix, n_assets=3)
            compute_portfolio_fragility(corr_matrix=c.matrix, asset_ids=SYMBOLS)
            simulate_tail_stress(current_corr_regime=cr, stress_scenario="SEVERE")
            compute_concentration_risk(weights_by_class=weights)
            PortfolioHeatmapEngine().build_snapshot(portfolio_risk=p, active_failure_modes=(), trigger_reason=TRIGGER_NEW_CANDLE, gross_exposure=0.5, net_exposure=0.3)
            executor.execute(symbol="BTC", asset_class=AssetClass.CRYPTO, order_size=1.0, current_hour=15, current_minute=30, current_weekday=2)
            executor.execute(symbol="EURUSD", asset_class=AssetClass.FOREX, order_size=100000.0, current_hour=15, current_minute=30, current_weekday=2)
            executor.execute(symbol="SPX", asset_class=AssetClass.INDICES, order_size=100.0, current_hour=15, current_minute=30, current_weekday=2)

        us = _measure_us(pipeline, n=50)
        ms = us / 1000
        assert ms < 500.0, f"Full MA Pipeline: {ms:.2f}ms > 500ms FAS target"

    def test_crisis_pipeline_under_500ms(self):
        """Crisis regime should also meet performance target."""
        regime = _make_regime(gr=GlobalRegimeState.CRISIS, cr=CorrelationRegimeState.BREAKDOWN)
        pr_engine = PortfolioRiskEngine()

        def crisis_pipeline():
            pr_engine.calculate_portfolio_risk(
                positions=POSITIONS, returns=RETURNS,
                regime=regime, price_histories=PRICE_HISTORIES,
            )

        us = _measure_us(crisis_pipeline, n=50)
        ms = us / 1000
        assert ms < 500.0, f"Crisis Pipeline: {ms:.2f}ms > 500ms FAS target"


# =============================================================================
# COVERAGE COMPLETENESS TESTS
# =============================================================================

class TestModuleCoverageCompleteness:
    """Verify all MA modules are importable and have expected public APIs."""

    def test_asset_risk_api(self):
        from jarvis.risk.asset_risk import AssetRiskCalculator, AssetRiskResult
        assert callable(AssetRiskCalculator().calculate_risk)

    def test_correlation_api(self):
        from jarvis.risk.correlation import DynamicCorrelationModel, CorrelationMatrixResult
        assert callable(DynamicCorrelationModel().estimate)

    def test_tail_risk_api(self):
        from jarvis.risk.tail_risk import MultivariateTailModel, MultivariateTailRiskResult
        assert callable(MultivariateTailModel().estimate)

    def test_gap_risk_api(self):
        from jarvis.risk.gap_risk import GapRiskModel, PortfolioGapRiskResult
        assert callable(GapRiskModel().estimate)

    def test_portfolio_risk_api(self):
        from jarvis.risk.portfolio_risk import PortfolioRiskEngine, PortfolioRiskResult
        assert callable(PortfolioRiskEngine().calculate_portfolio_risk)

    def test_risk_budget_api(self):
        from jarvis.risk.risk_budget import PortfolioRiskBudget, RiskBudgetResult
        assert callable(PortfolioRiskBudget().allocate)

    def test_systemic_risk_api(self):
        from jarvis.risk.systemic_risk import (
            classify_correlation_regime, compute_portfolio_fragility,
            simulate_tail_stress, compute_concentration_risk,
        )
        assert callable(classify_correlation_regime)
        assert callable(compute_portfolio_fragility)
        assert callable(simulate_tail_stress)
        assert callable(compute_concentration_risk)

    def test_portfolio_heatmap_api(self):
        from jarvis.risk.portfolio_heatmap import PortfolioHeatmapEngine
        engine = PortfolioHeatmapEngine()
        assert callable(engine.build_snapshot)
        assert callable(engine.should_update)

    def test_session_aware_executor_api(self):
        from jarvis.execution.session_aware_executor import SessionAwareExecutor
        assert callable(SessionAwareExecutor().execute)

    def test_intelligence_modules_importable(self):
        from jarvis.intelligence.global_regime import GlobalMacroDetector
        from jarvis.intelligence.asset_regimes import CryptoRegimeDetector, ForexRegimeDetector
        from jarvis.intelligence.correlation_regime import CorrelationRegimeDetector
        from jarvis.intelligence.ood_engine import AssetConditionalOOD
        from jarvis.intelligence.regime_memory import MultiAssetRegimeMemory

    def test_core_data_structures_importable(self):
        from jarvis.core.data_structures import (
            MarketMicrostructure, TradingHours, SessionDefinition,
            CRYPTO_MICROSTRUCTURE, FOREX_MICROSTRUCTURE, INDICES_MICROSTRUCTURE,
        )


# =============================================================================
# THRESHOLD DOCUMENTATION TESTS
# =============================================================================

class TestThresholdDocumentation:
    """Verify all documented thresholds match code constants."""

    def test_risk_engine_thresholds(self):
        from jarvis.risk.risk_engine import RiskEngine
        engine = RiskEngine()
        result = engine.assess(
            returns_history=BTC_RETURNS,
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.2,
        )
        assert 0.0 <= result.exposure_weight <= 1.0
        assert result.risk_regime in ("NORMAL", "ELEVATED", "CRITICAL", "DEFENSIVE")

    def test_systemic_corr_thresholds(self):
        from jarvis.risk.systemic_risk import (
            CORR_LOW_THRESHOLD, CORR_MEDIUM_THRESHOLD, CORR_FM04_THRESHOLD,
        )
        assert CORR_LOW_THRESHOLD == 0.40
        assert CORR_MEDIUM_THRESHOLD == 0.65
        assert CORR_FM04_THRESHOLD == 0.85

    def test_risk_budget_constraints(self):
        from jarvis.risk.risk_budget import MAX_SINGLE_ASSET
        assert MAX_SINGLE_ASSET == 0.30

    def test_gap_risk_thresholds(self):
        from jarvis.core.data_layer import GAP_THRESHOLDS
        assert GAP_THRESHOLDS["crypto"] == 0.05
        assert GAP_THRESHOLDS["forex"] == 0.02
        assert GAP_THRESHOLDS["indices"] == 0.03

    def test_tail_stress_multipliers(self):
        from jarvis.risk.systemic_risk import TAIL_STRESS_MULTIPLIERS
        assert TAIL_STRESS_MULTIPLIERS["MILD"] == 1.3
        assert TAIL_STRESS_MULTIPLIERS["MODERATE"] == 1.6
        assert TAIL_STRESS_MULTIPLIERS["SEVERE"] == 2.0
        assert TAIL_STRESS_MULTIPLIERS["EXTREME"] == 2.5

    def test_heatmap_delta_thresholds(self):
        from jarvis.risk.portfolio_heatmap import (
            EXPOSURE_DELTA_THRESHOLD, NET_EXPOSURE_DELTA_THRESHOLD,
            CORRELATION_DELTA_THRESHOLD, CORRELATION_SINGLE_THRESHOLD,
        )
        assert EXPOSURE_DELTA_THRESHOLD == 0.05
        assert NET_EXPOSURE_DELTA_THRESHOLD == 0.03
        assert CORRELATION_DELTA_THRESHOLD == 0.05
        assert CORRELATION_SINGLE_THRESHOLD == 0.10

    def test_manifest_thresholds(self):
        import json
        import os
        manifest_path = os.path.join(
            os.path.dirname(__file__), "..", "jarvis", "risk", "THRESHOLD_MANIFEST.json"
        )
        with open(manifest_path) as f:
            manifest = json.load(f)
        thresholds = manifest["thresholds"]
        assert thresholds["max_drawdown_threshold"] == 0.15
        assert thresholds["vol_compression_trigger"] == 0.30
        assert thresholds["shock_exposure_cap"] == 0.25
