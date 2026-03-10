# =============================================================================
# Tests for jarvis/execution/execution_optimizer.py (S30)
# =============================================================================

import numpy as np
import pytest

from jarvis.execution.execution_optimizer import (
    ExecutionPlan,
    SimulatedExecutionOptimizer,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

@pytest.fixture
def opt():
    return SimulatedExecutionOptimizer()


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

class TestConstants:
    def test_latency_budget_urgent(self):
        assert SimulatedExecutionOptimizer.LATENCY_BUDGET_URGENT == 50.0

    def test_latency_budget_normal(self):
        assert SimulatedExecutionOptimizer.LATENCY_BUDGET_NORMAL == 500.0

    def test_latency_budget_passive(self):
        assert SimulatedExecutionOptimizer.LATENCY_BUDGET_PASSIVE == 5000.0

    def test_max_spread_abort_pct(self):
        assert SimulatedExecutionOptimizer.MAX_SPREAD_ABORT_PCT == 0.005

    def test_max_impact_pct(self):
        assert SimulatedExecutionOptimizer.MAX_IMPACT_PCT == 0.002


# ---------------------------------------------------------------------------
# EXECUTION PLAN DATACLASS
# ---------------------------------------------------------------------------

class TestExecutionPlan:
    def test_all_fields(self):
        p = ExecutionPlan(
            base_size=0.1,
            adjusted_size=0.08,
            estimated_slippage=0.001,
            max_market_impact=0.0005,
            recommended_algo="VWAP",
            urgency_score=0.5,
            latency_budget_ms=500.0,
            abort_if_spread_pct=0.005,
            risk_cleared=True,
        )
        assert p.base_size == 0.1
        assert p.adjusted_size == 0.08
        assert p.recommended_algo == "VWAP"
        assert p.risk_cleared is True


# ---------------------------------------------------------------------------
# ESTIMATE SLIPPAGE
# ---------------------------------------------------------------------------

class TestEstimateSlippage:
    def test_basic_slippage(self, opt):
        s = opt.estimate_slippage(0.01, 0.8, 0.2, 0.001)
        assert 0.0 <= s <= 0.05

    def test_slippage_increases_with_vol(self, opt):
        low = opt.estimate_slippage(0.01, 0.8, 0.10, 0.001)
        high = opt.estimate_slippage(0.01, 0.8, 0.50, 0.001)
        assert high > low

    def test_slippage_increases_with_low_liquidity(self, opt):
        liq_high = opt.estimate_slippage(0.01, 0.9, 0.2, 0.001)
        liq_low = opt.estimate_slippage(0.01, 0.1, 0.2, 0.001)
        assert liq_low > liq_high

    def test_slippage_increases_with_order_size(self, opt):
        small = opt.estimate_slippage(0.01, 0.8, 0.2, 0.001)
        large = opt.estimate_slippage(0.10, 0.8, 0.2, 0.001)
        assert large > small

    def test_slippage_increases_with_spread(self, opt):
        narrow = opt.estimate_slippage(0.01, 0.8, 0.2, 0.0005)
        wide = opt.estimate_slippage(0.01, 0.8, 0.2, 0.005)
        assert wide > narrow

    def test_slippage_capped_at_5_pct(self, opt):
        s = opt.estimate_slippage(1.0, 0.0, 1.0, 0.1)
        assert s <= 0.05

    def test_slippage_non_negative(self, opt):
        s = opt.estimate_slippage(0.0, 1.0, 0.0, 0.0)
        assert s >= 0.0

    def test_zero_inputs(self, opt):
        s = opt.estimate_slippage(0.0, 0.0, 0.0, 0.0)
        assert s >= 0.0

    def test_nan_raises(self, opt):
        with pytest.raises(ValueError, match="order_size_pct"):
            opt.estimate_slippage(float("nan"), 0.8, 0.2, 0.001)

    def test_inf_raises(self, opt):
        with pytest.raises(ValueError, match="current_vol"):
            opt.estimate_slippage(0.01, 0.8, float("inf"), 0.001)

    def test_negative_raises(self, opt):
        with pytest.raises(ValueError, match="liquidity_score"):
            opt.estimate_slippage(0.01, -0.1, 0.2, 0.001)

    def test_negative_spread_raises(self, opt):
        with pytest.raises(ValueError, match="bid_ask_spread_pct"):
            opt.estimate_slippage(0.01, 0.8, 0.2, -0.001)

    def test_returns_float(self, opt):
        s = opt.estimate_slippage(0.01, 0.8, 0.2, 0.001)
        assert isinstance(s, float)

    def test_formula_manual(self, opt):
        # base = 0.001 / 2 = 0.0005
        # vol_comp = 0.2 * 0.1 * 0.01 = 0.0002
        # liq_factor = 1.0 + (1.0 - 0.8) * 2.0 = 1.4
        # total = (0.0005 + 0.0002) * 1.4 = 0.00098
        s = opt.estimate_slippage(0.01, 0.8, 0.2, 0.001)
        assert s == pytest.approx(0.00098)

    def test_perfect_liquidity_factor_1(self, opt):
        # liq_score = 1.0 → liq_factor = 1.0 + 0 = 1.0
        s1 = opt.estimate_slippage(0.01, 1.0, 0.2, 0.001)
        # base = 0.0005, vol = 0.0002, total = 0.0007 * 1.0
        assert s1 == pytest.approx(0.0007)


# ---------------------------------------------------------------------------
# COMPUTE MARKET IMPACT
# ---------------------------------------------------------------------------

class TestComputeMarketImpact:
    def test_basic_impact(self, opt):
        i = opt.compute_market_impact(0.01, 0.02)
        assert 0.0 <= i <= opt.MAX_IMPACT_PCT

    def test_zero_daily_vol_returns_max(self, opt):
        i = opt.compute_market_impact(0.01, 0.0)
        assert i == opt.MAX_IMPACT_PCT

    def test_impact_increases_with_order_size(self, opt):
        small = opt.compute_market_impact(0.001, 0.02)
        large = opt.compute_market_impact(0.01, 0.02)
        assert large >= small

    def test_impact_capped(self, opt):
        i = opt.compute_market_impact(1.0, 0.001)
        assert i <= opt.MAX_IMPACT_PCT

    def test_zero_order_size(self, opt):
        i = opt.compute_market_impact(0.0, 0.02)
        assert i == pytest.approx(0.0)

    def test_returns_float(self, opt):
        i = opt.compute_market_impact(0.01, 0.02)
        assert isinstance(i, float)

    def test_formula_manual(self, opt):
        # ratio = clip(0.01 / 0.04, 0, 1) = 0.25
        # impact = 0.1 * sqrt(0.25) = 0.1 * 0.5 = 0.05
        # clipped to MAX_IMPACT_PCT = 0.002
        i = opt.compute_market_impact(0.01, 0.04)
        assert i == opt.MAX_IMPACT_PCT

    def test_very_small_ratio(self, opt):
        # ratio = 0.0001 / 0.1 = 0.001
        # impact = 0.1 * sqrt(0.001) = 0.1 * 0.0316 = 0.00316 → clipped to 0.002
        i = opt.compute_market_impact(0.0001, 0.1)
        assert i <= opt.MAX_IMPACT_PCT


# ---------------------------------------------------------------------------
# SELECT ALGORITHM
# ---------------------------------------------------------------------------

class TestSelectAlgorithm:
    def test_aggressive_on_high_urgency(self, opt):
        assert opt.select_algorithm(0.9, 0.8, 60) == "AGGRESSIVE"

    def test_aggressive_boundary(self, opt):
        assert opt.select_algorithm(0.81, 0.8, 60) == "AGGRESSIVE"

    def test_not_aggressive_at_0_8(self, opt):
        assert opt.select_algorithm(0.8, 0.8, 60) != "AGGRESSIVE"

    def test_twap_on_long_horizon(self, opt):
        assert opt.select_algorithm(0.1, 0.5, 7200) == "TWAP"

    def test_twap_boundary(self, opt):
        assert opt.select_algorithm(0.1, 0.5, 3601) == "TWAP"

    def test_not_twap_at_3600(self, opt):
        assert opt.select_algorithm(0.1, 0.5, 3600) != "TWAP"

    def test_vwap_on_high_liquidity(self, opt):
        assert opt.select_algorithm(0.5, 0.8, 1800) == "VWAP"

    def test_vwap_boundary(self, opt):
        assert opt.select_algorithm(0.5, 0.71, 1800) == "VWAP"

    def test_not_vwap_at_0_7(self, opt):
        assert opt.select_algorithm(0.5, 0.7, 1800) != "VWAP"

    def test_limit_default(self, opt):
        assert opt.select_algorithm(0.3, 0.5, 1800) == "LIMIT"

    def test_urgency_highest_priority(self, opt):
        # Even with long horizon and high liquidity, urgency wins
        assert opt.select_algorithm(0.9, 0.9, 7200) == "AGGRESSIVE"

    def test_twap_over_vwap(self, opt):
        # Long horizon but not urgent → TWAP even if high liquidity
        assert opt.select_algorithm(0.5, 0.9, 7200) == "TWAP"


# ---------------------------------------------------------------------------
# OPTIMIZE — RISK CLEARANCE
# ---------------------------------------------------------------------------

class TestOptimizeRiskClearance:
    def test_no_execution_without_risk_clearance(self, opt):
        plan = opt.optimize(0.1, 0.8, 0.001, 0.2, 0.02, 0.5, 3600, risk_cleared=False)
        assert plan.adjusted_size == 0.0
        assert plan.recommended_algo == "HOLD"
        assert plan.risk_cleared is False

    def test_no_clearance_slippage_zero(self, opt):
        plan = opt.optimize(0.1, 0.8, 0.001, 0.2, 0.02, 0.5, 3600, risk_cleared=False)
        assert plan.estimated_slippage == 0.0
        assert plan.max_market_impact == 0.0

    def test_no_clearance_preserves_base_size(self, opt):
        plan = opt.optimize(0.15, 0.8, 0.001, 0.2, 0.02, 0.5, 3600, risk_cleared=False)
        assert plan.base_size == 0.15

    def test_no_clearance_latency_normal(self, opt):
        plan = opt.optimize(0.1, 0.8, 0.001, 0.2, 0.02, 0.5, 3600, risk_cleared=False)
        assert plan.latency_budget_ms == opt.LATENCY_BUDGET_NORMAL

    def test_no_clearance_abort_spread_default(self, opt):
        plan = opt.optimize(0.1, 0.8, 0.001, 0.2, 0.02, 0.5, 3600, risk_cleared=False)
        assert plan.abort_if_spread_pct == opt.MAX_SPREAD_ABORT_PCT


# ---------------------------------------------------------------------------
# OPTIMIZE — FULL PIPELINE
# ---------------------------------------------------------------------------

class TestOptimizeFullPipeline:
    def test_basic_optimize(self, opt):
        plan = opt.optimize(0.05, 0.7, 0.001, 0.2, 0.02, 0.5, 3600, risk_cleared=True)
        assert isinstance(plan, ExecutionPlan)
        assert plan.risk_cleared is True
        assert plan.adjusted_size > 0.0

    def test_adjusted_size_leq_base(self, opt):
        plan = opt.optimize(0.1, 0.5, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        assert plan.adjusted_size <= plan.base_size

    def test_adjusted_size_clipped_to_1(self, opt):
        plan = opt.optimize(2.0, 1.0, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        assert plan.adjusted_size <= 1.0

    def test_urgency_clipped_to_1(self, opt):
        plan = opt.optimize(0.1, 0.8, 0.001, 0.2, 0.02, 1.5, 1800, risk_cleared=True)
        assert plan.urgency_score <= 1.0

    def test_slippage_populated(self, opt):
        plan = opt.optimize(0.05, 0.7, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        assert plan.estimated_slippage >= 0.0

    def test_impact_populated(self, opt):
        plan = opt.optimize(0.05, 0.7, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        assert plan.max_market_impact >= 0.0

    def test_algo_aggressive_high_urgency(self, opt):
        plan = opt.optimize(0.05, 0.7, 0.001, 0.2, 0.02, 0.9, 60, risk_cleared=True)
        assert plan.recommended_algo == "AGGRESSIVE"

    def test_algo_twap_long_horizon(self, opt):
        plan = opt.optimize(0.05, 0.7, 0.001, 0.2, 0.02, 0.1, 7200, risk_cleared=True)
        assert plan.recommended_algo == "TWAP"

    def test_algo_vwap_high_liquidity(self, opt):
        plan = opt.optimize(0.05, 0.8, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        assert plan.recommended_algo == "VWAP"

    def test_algo_limit_default(self, opt):
        plan = opt.optimize(0.05, 0.5, 0.001, 0.2, 0.02, 0.3, 1800, risk_cleared=True)
        assert plan.recommended_algo == "LIMIT"


# ---------------------------------------------------------------------------
# OPTIMIZE — LATENCY BUDGET
# ---------------------------------------------------------------------------

class TestOptimizeLatency:
    def test_urgent_latency(self, opt):
        plan = opt.optimize(0.05, 0.8, 0.001, 0.2, 0.02, 0.8, 60, risk_cleared=True)
        assert plan.latency_budget_ms == opt.LATENCY_BUDGET_URGENT

    def test_normal_latency(self, opt):
        plan = opt.optimize(0.05, 0.8, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        assert plan.latency_budget_ms == opt.LATENCY_BUDGET_NORMAL

    def test_passive_latency(self, opt):
        plan = opt.optimize(0.05, 0.8, 0.001, 0.2, 0.02, 0.1, 1800, risk_cleared=True)
        assert plan.latency_budget_ms == opt.LATENCY_BUDGET_PASSIVE

    def test_urgency_boundary_0_7(self, opt):
        # urgency = 0.7 → NOT > 0.7 → normal
        plan = opt.optimize(0.05, 0.8, 0.001, 0.2, 0.02, 0.7, 1800, risk_cleared=True)
        assert plan.latency_budget_ms == opt.LATENCY_BUDGET_NORMAL

    def test_urgency_boundary_0_3(self, opt):
        # urgency = 0.3 → NOT > 0.3 → passive
        plan = opt.optimize(0.05, 0.5, 0.001, 0.2, 0.02, 0.3, 1800, risk_cleared=True)
        assert plan.latency_budget_ms == opt.LATENCY_BUDGET_PASSIVE


# ---------------------------------------------------------------------------
# OPTIMIZE — SPREAD ABORT
# ---------------------------------------------------------------------------

class TestOptimizeSpreadAbort:
    def test_abort_spread_at_least_max(self, opt):
        plan = opt.optimize(0.05, 0.8, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        assert plan.abort_if_spread_pct >= opt.MAX_SPREAD_ABORT_PCT

    def test_abort_spread_doubles_current(self, opt):
        plan = opt.optimize(0.05, 0.8, 0.01, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        # max(0.005, 0.01 * 2) = max(0.005, 0.02) = 0.02
        assert plan.abort_if_spread_pct == pytest.approx(0.02)

    def test_abort_spread_small_spread(self, opt):
        plan = opt.optimize(0.05, 0.8, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        # max(0.005, 0.001 * 2) = max(0.005, 0.002) = 0.005
        assert plan.abort_if_spread_pct == pytest.approx(0.005)


# ---------------------------------------------------------------------------
# OPTIMIZE — LIQUIDITY ADJUSTMENT
# ---------------------------------------------------------------------------

class TestOptimizeLiquidityAdjustment:
    def test_high_liquidity_less_reduction(self, opt):
        plan_high = opt.optimize(0.1, 0.9, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        plan_low = opt.optimize(0.1, 0.3, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        assert plan_high.adjusted_size > plan_low.adjusted_size

    def test_liq_factor_clipped_to_0_1(self, opt):
        # liquidity_score = 0.0 → liq_factor = clip(0.0, 0.1, 1.0) = 0.1
        plan = opt.optimize(0.5, 0.0, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        assert plan.adjusted_size == pytest.approx(0.05)

    def test_liq_factor_max_1(self, opt):
        # liquidity_score = 1.0 → liq_factor = 1.0
        plan = opt.optimize(0.5, 1.0, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        assert plan.adjusted_size == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# DETERMINISM
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_output(self, opt):
        p1 = opt.optimize(0.05, 0.7, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        p2 = opt.optimize(0.05, 0.7, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        assert p1.adjusted_size == p2.adjusted_size
        assert p1.estimated_slippage == p2.estimated_slippage
        assert p1.max_market_impact == p2.max_market_impact
        assert p1.recommended_algo == p2.recommended_algo

    def test_stateless(self, opt):
        opt.optimize(0.1, 0.3, 0.01, 0.5, 0.01, 0.9, 60, risk_cleared=True)
        p = opt.optimize(0.05, 0.8, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        p2 = opt.optimize(0.05, 0.8, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        assert p.adjusted_size == p2.adjusted_size


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_base_size(self, opt):
        plan = opt.optimize(0.0, 0.8, 0.001, 0.2, 0.02, 0.5, 1800, risk_cleared=True)
        assert plan.adjusted_size == 0.0

    def test_very_high_vol(self, opt):
        plan = opt.optimize(0.05, 0.8, 0.001, 2.0, 0.02, 0.5, 1800, risk_cleared=True)
        assert plan.estimated_slippage <= 0.05

    def test_very_small_daily_vol(self, opt):
        plan = opt.optimize(0.05, 0.8, 0.001, 0.2, 0.0, 0.5, 1800, risk_cleared=True)
        assert plan.max_market_impact == opt.MAX_IMPACT_PCT
