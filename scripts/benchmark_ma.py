"""Phase MA-8: Performance Benchmarks for Multi-Asset Risk Pipeline."""
import time

from jarvis.core.regime import (
    AssetClass, AssetRegimeState, CorrelationRegimeState,
    GlobalRegimeState, HierarchicalRegime,
)
from jarvis.execution.session_aware_executor import SessionAwareExecutor
from jarvis.orchestrator.pipeline import run_full_pipeline
from jarvis.risk.asset_risk import AssetRiskCalculator
from jarvis.risk.correlation import DynamicCorrelationModel
from jarvis.risk.gap_risk import GapRiskModel
from jarvis.risk.portfolio_heatmap import PortfolioHeatmapEngine, TRIGGER_NEW_CANDLE
from jarvis.risk.portfolio_risk import PortfolioRiskEngine
from jarvis.risk.risk_budget import PortfolioRiskBudget
from jarvis.risk.risk_engine import RiskEngine
from jarvis.risk.systemic_risk import (
    classify_correlation_regime, compute_concentration_risk,
    compute_portfolio_fragility, simulate_tail_stress,
)
from jarvis.risk.tail_risk import MultivariateTailModel


def _make_regime(gr=GlobalRegimeState.RISK_ON, cr=CorrelationRegimeState.NORMAL):
    ar = ({ac: AssetRegimeState.SHOCK for ac in AssetClass}
          if gr == GlobalRegimeState.CRISIS
          else {ac: AssetRegimeState.TRENDING_UP for ac in AssetClass})
    return HierarchicalRegime.create(
        global_regime=gr,
        asset_regimes=ar,
        correlation_regime=cr,
        global_confidence=0.8,
        asset_confidences={ac: 0.8 for ac in AssetClass},
        sub_regime={ac: "default" for ac in AssetClass},
        sequence_id=1,
    )


def bench(name, func, n=1000):
    # warmup
    func()
    t0 = time.perf_counter_ns()
    for _ in range(n):
        func()
    t1 = time.perf_counter_ns()
    us = (t1 - t0) / n / 1000
    ms = us / 1000
    print(f"  {name:55s} {us:10.1f} us  ({ms:.3f} ms)")
    return us


def main():
    # -- Test data --
    btc_ret = [0.03, -0.04, 0.02, -0.01, 0.05, -0.03, 0.01, -0.02, 0.04, -0.05,
               0.02, -0.01, 0.03, -0.04, 0.01, 0.02, -0.03, 0.04, -0.02, 0.01,
               -0.01, 0.03, -0.02, 0.01, -0.04, 0.05, -0.01, 0.02, -0.03, 0.01]
    eur_ret = [r * 0.15 for r in btc_ret]
    spx_ret = [r * 0.4 for r in btc_ret]

    returns = {"BTC": btc_ret, "EURUSD": eur_ret, "SPX": spx_ret}
    symbols = ["BTC", "EURUSD", "SPX"]
    positions = {
        "BTC": (AssetClass.CRYPTO, 65000.0, 1.0),
        "EURUSD": (AssetClass.FOREX, 1.08, 100000.0),
        "SPX": (AssetClass.INDICES, 5200.0, 100.0),
    }
    btc_prices = [65000.0 + i * 100.0 for i in range(30)]
    eur_prices = [1.08 + i * 0.001 for i in range(30)]
    spx_prices = [5200.0 + i * 10.0 for i in range(30)]
    price_histories = {"BTC": btc_prices, "EURUSD": eur_prices, "SPX": spx_prices}
    regime = _make_regime()

    calc = AssetRiskCalculator()
    corr_model = DynamicCorrelationModel()
    tail_model = MultivariateTailModel()
    gap_model = GapRiskModel()
    pr_engine = PortfolioRiskEngine()
    budget_engine = PortfolioRiskBudget()
    executor = SessionAwareExecutor()

    print("=" * 80)
    print("JARVIS Multi-Asset Risk Pipeline - Performance Benchmarks")
    print("=" * 80)
    print()
    print("--- Individual Module Benchmarks (1000 iterations) ---")
    print()

    bench("AssetRiskCalculator.calculate_risk (CRYPTO)", lambda: calc.calculate_risk(
        symbol="BTC", asset_class=AssetClass.CRYPTO, returns=btc_ret,
        current_price=65000.0, position_size=1.0,
        regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.8,
    ))
    bench("AssetRiskCalculator.calculate_risk (FOREX)", lambda: calc.calculate_risk(
        symbol="EURUSD", asset_class=AssetClass.FOREX, returns=eur_ret,
        current_price=1.08, position_size=100000.0,
        regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.9,
    ))
    bench("AssetRiskCalculator.calculate_risk (INDICES)", lambda: calc.calculate_risk(
        symbol="SPX", asset_class=AssetClass.INDICES, returns=spx_ret,
        current_price=5200.0, position_size=100.0,
        regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.95,
    ))

    bench("DynamicCorrelationModel.estimate (3 assets)", lambda: corr_model.estimate(
        returns=returns, symbols=symbols, regime=regime,
    ))

    # Pre-compute for downstream
    ar_btc = calc.calculate_risk(symbol="BTC", asset_class=AssetClass.CRYPTO, returns=btc_ret, current_price=65000.0, position_size=1.0, regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.8)
    ar_eur = calc.calculate_risk(symbol="EURUSD", asset_class=AssetClass.FOREX, returns=eur_ret, current_price=1.08, position_size=100000.0, regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.9)
    ar_spx = calc.calculate_risk(symbol="SPX", asset_class=AssetClass.INDICES, returns=spx_ret, current_price=5200.0, position_size=100.0, regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.95)
    corr_result = corr_model.estimate(returns=returns, symbols=symbols, regime=regime)
    asset_risks = {"BTC": ar_btc, "EURUSD": ar_eur, "SPX": ar_spx}

    bench("MultivariateTailModel.estimate (3 assets)", lambda: tail_model.estimate(
        asset_risks=asset_risks, correlation_matrix=corr_result.matrix,
        symbols=corr_result.symbols,
    ))

    bench("GapRiskModel.estimate (3 assets)", lambda: gap_model.estimate(
        positions=positions, price_histories=price_histories,
    ))

    bench("PortfolioRiskEngine.calculate_portfolio_risk", lambda: pr_engine.calculate_portfolio_risk(
        positions=positions, returns=returns, regime=regime, price_histories=price_histories,
    ), n=100)

    pr = pr_engine.calculate_portfolio_risk(positions=positions, returns=returns, regime=regime, price_histories=price_histories)

    bench("PortfolioRiskBudget.allocate (5 classes)", lambda: budget_engine.allocate(
        total_capital=100000.0, asset_classes=list(AssetClass), regime=regime, portfolio_risk=pr,
    ))

    bench("classify_correlation_regime", lambda: classify_correlation_regime(
        corr_matrix=pr.correlation_result.matrix, n_assets=3,
    ))

    cr = classify_correlation_regime(corr_matrix=pr.correlation_result.matrix, n_assets=3)

    bench("compute_portfolio_fragility", lambda: compute_portfolio_fragility(
        corr_matrix=pr.correlation_result.matrix, asset_ids=symbols,
    ))

    bench("simulate_tail_stress (SEVERE)", lambda: simulate_tail_stress(
        current_corr_regime=cr, stress_scenario="SEVERE",
    ))

    weights = {"CRYPTO": 0.3, "FOREX": 0.2, "INDICES": 0.5}
    bench("compute_concentration_risk", lambda: compute_concentration_risk(
        weights_by_class=weights,
    ))

    bench("PortfolioHeatmapEngine.build_snapshot", lambda: PortfolioHeatmapEngine().build_snapshot(
        portfolio_risk=pr, active_failure_modes=(), trigger_reason=TRIGGER_NEW_CANDLE,
        gross_exposure=0.5, net_exposure=0.3,
    ), n=100)

    bench("SessionAwareExecutor.execute (CRYPTO)", lambda: executor.execute(
        symbol="BTC", asset_class=AssetClass.CRYPTO, order_size=1.0,
        current_hour=15, current_minute=30, current_weekday=2,
    ))
    bench("SessionAwareExecutor.execute (FOREX)", lambda: executor.execute(
        symbol="EURUSD", asset_class=AssetClass.FOREX, order_size=100000.0,
        current_hour=15, current_minute=30, current_weekday=2,
    ))
    bench("SessionAwareExecutor.execute (INDICES)", lambda: executor.execute(
        symbol="SPX", asset_class=AssetClass.INDICES, order_size=100.0,
        current_hour=15, current_minute=30, current_weekday=2,
    ))

    print()
    print("--- Core Pipeline Benchmarks (100 iterations) ---")
    print()

    bench("RiskEngine.assess (core)", lambda: RiskEngine().assess(
        returns_history=btc_ret, current_regime=GlobalRegimeState.RISK_ON,
        meta_uncertainty=0.2,
    ), n=100)

    bench("run_full_pipeline (core, 3 assets)", lambda: run_full_pipeline(
        returns_history=btc_ret, current_regime=GlobalRegimeState.RISK_ON,
        meta_uncertainty=0.2, total_capital=100000.0,
        asset_prices={"BTC": 65000.0, "ETH": 3200.0, "SPY": 520.0},
    ), n=100)

    print()
    print("--- Full Multi-Asset E2E Pipeline (100 iterations) ---")
    print()

    def full_pipeline():
        ab = calc.calculate_risk(symbol="BTC", asset_class=AssetClass.CRYPTO, returns=btc_ret, current_price=65000.0, position_size=1.0, regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.8)
        ae = calc.calculate_risk(symbol="EURUSD", asset_class=AssetClass.FOREX, returns=eur_ret, current_price=1.08, position_size=100000.0, regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.9)
        a_s = calc.calculate_risk(symbol="SPX", asset_class=AssetClass.INDICES, returns=spx_ret, current_price=5200.0, position_size=100.0, regime_state=AssetRegimeState.TRENDING_UP, liquidity_score=0.95)
        c = corr_model.estimate(returns=returns, symbols=symbols, regime=regime)
        tail_model.estimate(asset_risks={"BTC": ab, "EURUSD": ae, "SPX": a_s}, correlation_matrix=c.matrix, symbols=c.symbols)
        gap_model.estimate(positions=positions, price_histories=price_histories)
        p = pr_engine.calculate_portfolio_risk(positions=positions, returns=returns, regime=regime, price_histories=price_histories)
        budget_engine.allocate(total_capital=100000.0, asset_classes=list(AssetClass), regime=regime, portfolio_risk=p)
        cr_ = classify_correlation_regime(corr_matrix=c.matrix, n_assets=3)
        compute_portfolio_fragility(corr_matrix=c.matrix, asset_ids=symbols)
        simulate_tail_stress(current_corr_regime=cr_, stress_scenario="SEVERE")
        compute_concentration_risk(weights_by_class=weights)
        PortfolioHeatmapEngine().build_snapshot(portfolio_risk=p, active_failure_modes=(), trigger_reason=TRIGGER_NEW_CANDLE, gross_exposure=0.5, net_exposure=0.3)
        executor.execute(symbol="BTC", asset_class=AssetClass.CRYPTO, order_size=1.0, current_hour=15, current_minute=30, current_weekday=2)
        executor.execute(symbol="EURUSD", asset_class=AssetClass.FOREX, order_size=100000.0, current_hour=15, current_minute=30, current_weekday=2)
        executor.execute(symbol="SPX", asset_class=AssetClass.INDICES, order_size=100.0, current_hour=15, current_minute=30, current_weekday=2)

    total_us = bench("FULL MA Pipeline (3 assets, all 16 steps)", full_pipeline, n=100)

    print()
    print("=" * 80)
    target_ms = 500.0
    actual_ms = total_us / 1000
    status = "PASS" if actual_ms < target_ms else "FAIL"
    print(f"  FAS Target: < {target_ms:.0f} ms (P95)")
    print(f"  Measured:     {actual_ms:.3f} ms")
    print(f"  Status:       {status}")
    print(f"  Headroom:     {((target_ms - actual_ms) / target_ms * 100):.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()
