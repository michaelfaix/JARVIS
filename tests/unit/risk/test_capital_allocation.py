# =============================================================================
# Tests for jarvis/risk/capital_allocation.py (S29)
# =============================================================================

import numpy as np
import pytest

from jarvis.risk.capital_allocation import (
    AllocationResult,
    CapitalAllocationEngine,
    PortfolioAllocation,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    return CapitalAllocationEngine()


def _two_strategies():
    return {
        "s1": {
            "win_rate": 0.55,
            "avg_win": 1.2,
            "avg_loss": 1.0,
            "vol": 0.2,
            "confidence": 0.7,
        },
        "s2": {
            "win_rate": 0.50,
            "avg_win": 1.0,
            "avg_loss": 1.0,
            "vol": 0.3,
            "confidence": 0.5,
        },
    }


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

class TestConstants:
    def test_max_kelly_fraction(self):
        assert CapitalAllocationEngine.MAX_KELLY_FRACTION == 0.25

    def test_max_total_exposure(self):
        assert CapitalAllocationEngine.MAX_TOTAL_EXPOSURE == 0.80

    def test_volatility_target(self):
        assert CapitalAllocationEngine.VOLATILITY_TARGET == 0.15

    def test_rebalance_threshold(self):
        assert CapitalAllocationEngine.REBALANCE_THRESHOLD == 0.05


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------

class TestAllocationResult:
    def test_all_fields(self):
        r = AllocationResult(
            kelly_fraction=0.1,
            risk_budget_fraction=0.15,
            vol_target_fraction=0.2,
            final_allocation=0.1,
            exposure_cap_applied=False,
            reason="test",
        )
        assert r.kelly_fraction == 0.1
        assert r.final_allocation == 0.1
        assert r.exposure_cap_applied is False
        assert r.reason == "test"


class TestPortfolioAllocation:
    def test_all_fields(self):
        r = PortfolioAllocation(
            allocations={},
            total_gross_exposure=0.5,
            portfolio_vol_est=0.15,
            vol_target_met=True,
            rebalance_required=False,
        )
        assert r.total_gross_exposure == 0.5
        assert r.vol_target_met is True


# ---------------------------------------------------------------------------
# KELLY FRACTION
# ---------------------------------------------------------------------------

class TestKellyFraction:
    def test_basic_kelly(self, engine):
        k = engine.compute_kelly_fraction(
            win_rate=0.6, avg_win=1.5, avg_loss=1.0, confidence=1.0
        )
        assert 0.0 <= k <= engine.MAX_KELLY_FRACTION

    def test_kelly_capped_at_max(self, engine):
        k = engine.compute_kelly_fraction(
            win_rate=0.99, avg_win=10.0, avg_loss=0.1, confidence=1.0
        )
        assert k <= engine.MAX_KELLY_FRACTION

    def test_kelly_non_negative(self, engine):
        k = engine.compute_kelly_fraction(
            win_rate=0.3, avg_win=0.5, avg_loss=1.0, confidence=1.0
        )
        assert k >= 0.0

    def test_kelly_zero_win_rate(self, engine):
        k = engine.compute_kelly_fraction(
            win_rate=0.0, avg_win=1.0, avg_loss=1.0, confidence=1.0
        )
        assert k == 0.0

    def test_kelly_high_confidence_higher_fraction(self, engine):
        k_low = engine.compute_kelly_fraction(
            win_rate=0.6, avg_win=1.5, avg_loss=1.0, confidence=0.3
        )
        k_high = engine.compute_kelly_fraction(
            win_rate=0.6, avg_win=1.5, avg_loss=1.0, confidence=0.9
        )
        assert k_high >= k_low

    def test_kelly_returns_float(self, engine):
        k = engine.compute_kelly_fraction(
            win_rate=0.6, avg_win=1.5, avg_loss=1.0
        )
        assert isinstance(k, float)

    def test_invalid_win_rate_above_1(self, engine):
        with pytest.raises(ValueError, match="win_rate"):
            engine.compute_kelly_fraction(1.5, 1.0, 1.0)

    def test_invalid_win_rate_negative(self, engine):
        with pytest.raises(ValueError, match="win_rate"):
            engine.compute_kelly_fraction(-0.1, 1.0, 1.0)

    def test_invalid_avg_loss_zero(self, engine):
        with pytest.raises(ValueError, match="avg_loss"):
            engine.compute_kelly_fraction(0.5, 1.0, 0.0)

    def test_invalid_avg_loss_negative(self, engine):
        with pytest.raises(ValueError, match="avg_loss"):
            engine.compute_kelly_fraction(0.5, 1.0, -1.0)

    def test_invalid_confidence_zero(self, engine):
        with pytest.raises(ValueError, match="confidence"):
            engine.compute_kelly_fraction(0.5, 1.0, 1.0, confidence=0.0)

    def test_invalid_confidence_above_1(self, engine):
        with pytest.raises(ValueError, match="confidence"):
            engine.compute_kelly_fraction(0.5, 1.0, 1.0, confidence=1.5)

    def test_confidence_exactly_1(self, engine):
        k = engine.compute_kelly_fraction(0.6, 1.5, 1.0, confidence=1.0)
        assert 0.0 <= k <= engine.MAX_KELLY_FRACTION

    def test_win_rate_exactly_0(self, engine):
        k = engine.compute_kelly_fraction(0.0, 1.0, 1.0)
        assert k == 0.0

    def test_win_rate_exactly_1(self, engine):
        k = engine.compute_kelly_fraction(1.0, 1.0, 1.0)
        assert 0.0 < k <= engine.MAX_KELLY_FRACTION

    def test_kelly_formula_manual(self, engine):
        # f* = (p*b - q) / b = (0.6*1.5 - 0.4) / 1.5 = (0.9 - 0.4) / 1.5 = 0.333
        # adjusted = 0.333 * 1.0 * 0.25 = 0.0833
        k = engine.compute_kelly_fraction(0.6, 1.5, 1.0, confidence=1.0)
        expected = ((0.6 * 1.5 - 0.4) / 1.5) * 1.0 * 0.25
        assert k == pytest.approx(expected, abs=1e-6)


# ---------------------------------------------------------------------------
# RISK BUDGET FRACTION
# ---------------------------------------------------------------------------

class TestRiskBudgetFraction:
    def test_equal_vols(self, engine):
        f = engine.compute_risk_budget_fraction(
            strategy_vol=0.2, portfolio_vol=0.2
        )
        # vol_ratio = 1.0, fraction = 0.20 / 1.0 = 0.20
        assert f == pytest.approx(0.20)

    def test_high_strategy_vol_lower_fraction(self, engine):
        f_low = engine.compute_risk_budget_fraction(
            strategy_vol=0.1, portfolio_vol=0.2
        )
        f_high = engine.compute_risk_budget_fraction(
            strategy_vol=0.4, portfolio_vol=0.2
        )
        assert f_low > f_high

    def test_zero_strategy_vol(self, engine):
        f = engine.compute_risk_budget_fraction(
            strategy_vol=0.0, portfolio_vol=0.2
        )
        assert f == 0.0

    def test_zero_portfolio_vol_raises(self, engine):
        with pytest.raises(ValueError, match="portfolio_vol"):
            engine.compute_risk_budget_fraction(
                strategy_vol=0.2, portfolio_vol=0.0
            )

    def test_result_clipped_to_1(self, engine):
        f = engine.compute_risk_budget_fraction(
            strategy_vol=0.01, portfolio_vol=0.2, risk_budget_pct=0.5
        )
        assert f <= 1.0

    def test_result_non_negative(self, engine):
        f = engine.compute_risk_budget_fraction(
            strategy_vol=0.5, portfolio_vol=0.1
        )
        assert f >= 0.0

    def test_custom_risk_budget_pct(self, engine):
        f1 = engine.compute_risk_budget_fraction(0.2, 0.2, risk_budget_pct=0.10)
        f2 = engine.compute_risk_budget_fraction(0.2, 0.2, risk_budget_pct=0.30)
        assert f2 > f1

    def test_vol_ratio_clipped(self, engine):
        # Extreme vol ratio should be clipped to [0.1, 10.0]
        f = engine.compute_risk_budget_fraction(
            strategy_vol=100.0, portfolio_vol=0.2
        )
        # vol_ratio clipped to 10.0 → fraction = 0.20 / 10.0 = 0.02
        assert f == pytest.approx(0.02)


# ---------------------------------------------------------------------------
# VOL TARGETING FRACTION
# ---------------------------------------------------------------------------

class TestVolTargetingFraction:
    def test_double_vol_halves_position(self, engine):
        f = engine.compute_vol_targeting_fraction(
            current_vol=0.30, target_vol=0.15
        )
        assert f == pytest.approx(0.5)

    def test_half_vol_doubles_but_clipped(self, engine):
        f = engine.compute_vol_targeting_fraction(
            current_vol=0.075, target_vol=0.15
        )
        # 0.15/0.075 = 2.0 → clipped to 1.0
        assert f == pytest.approx(1.0)

    def test_zero_vol_returns_base_clipped(self, engine):
        f = engine.compute_vol_targeting_fraction(
            current_vol=0.0, base_fraction=0.8
        )
        assert f == pytest.approx(0.8)

    def test_default_target_vol(self, engine):
        f = engine.compute_vol_targeting_fraction(current_vol=0.15)
        # 0.15 / 0.15 = 1.0
        assert f == pytest.approx(1.0)

    def test_result_clipped_to_1(self, engine):
        f = engine.compute_vol_targeting_fraction(
            current_vol=0.01, target_vol=0.15
        )
        assert f <= 1.0

    def test_result_non_negative(self, engine):
        f = engine.compute_vol_targeting_fraction(current_vol=1.0)
        assert f >= 0.0

    def test_custom_base_fraction(self, engine):
        f = engine.compute_vol_targeting_fraction(
            current_vol=0.15, target_vol=0.15, base_fraction=0.5
        )
        assert f == pytest.approx(0.5)

    def test_returns_float(self, engine):
        f = engine.compute_vol_targeting_fraction(current_vol=0.2)
        assert isinstance(f, float)


# ---------------------------------------------------------------------------
# ALLOCATE SINGLE
# ---------------------------------------------------------------------------

class TestAllocateSingle:
    def test_basic_allocation(self, engine):
        r = engine.allocate_single(
            strategy_id="s1",
            win_rate=0.55,
            avg_win=1.2,
            avg_loss=1.0,
            strategy_vol=0.2,
            portfolio_vol=0.2,
            confidence=0.7,
            risk_compression=False,
        )
        assert isinstance(r, AllocationResult)
        assert 0.0 <= r.final_allocation <= engine.MAX_KELLY_FRACTION

    def test_allocation_is_min_of_three(self, engine):
        r = engine.allocate_single(
            strategy_id="s1",
            win_rate=0.55,
            avg_win=1.2,
            avg_loss=1.0,
            strategy_vol=0.2,
            portfolio_vol=0.2,
            confidence=0.7,
            risk_compression=False,
        )
        expected_min = min(
            r.kelly_fraction, r.risk_budget_fraction, r.vol_target_fraction
        )
        assert r.final_allocation <= expected_min + 1e-10

    def test_risk_compression_reduces(self, engine):
        r_normal = engine.allocate_single(
            "s1", 0.55, 1.0, 1.0, 0.2, 0.2, 0.7, False
        )
        r_compr = engine.allocate_single(
            "s1", 0.55, 1.0, 1.0, 0.2, 0.2, 0.7, True
        )
        assert r_compr.final_allocation < r_normal.final_allocation

    def test_risk_compression_reason(self, engine):
        r = engine.allocate_single(
            "s1", 0.55, 1.0, 1.0, 0.2, 0.2, 0.7, True
        )
        assert "Risk compression" in r.reason

    def test_normal_reason_format(self, engine):
        r = engine.allocate_single(
            "s1", 0.55, 1.0, 1.0, 0.2, 0.2, 0.7, False
        )
        assert "Kelly=" in r.reason
        assert "RiskBudget=" in r.reason
        assert "VolTarget=" in r.reason

    def test_exposure_cap_applied(self, engine):
        # Very high win rate → kelly could be high, but capped
        r = engine.allocate_single(
            "s1", 0.99, 10.0, 0.1, 0.01, 0.2, 1.0, False
        )
        assert r.final_allocation <= engine.MAX_KELLY_FRACTION

    def test_all_fields_populated(self, engine):
        r = engine.allocate_single(
            "s1", 0.55, 1.2, 1.0, 0.2, 0.2, 0.7, False
        )
        assert r.kelly_fraction >= 0.0
        assert r.risk_budget_fraction >= 0.0
        assert r.vol_target_fraction >= 0.0
        assert isinstance(r.exposure_cap_applied, bool)
        assert isinstance(r.reason, str)

    def test_risk_compression_factor_0_25(self, engine):
        r_normal = engine.allocate_single(
            "s1", 0.55, 1.2, 1.0, 0.2, 0.2, 0.7, False
        )
        r_compr = engine.allocate_single(
            "s1", 0.55, 1.2, 1.0, 0.2, 0.2, 0.7, True
        )
        # Compressed should be ~25% of normal (unless capped)
        if r_normal.final_allocation > 0:
            ratio = r_compr.final_allocation / r_normal.final_allocation
            assert ratio <= 0.25 + 1e-6


# ---------------------------------------------------------------------------
# ALLOCATE PORTFOLIO
# ---------------------------------------------------------------------------

class TestAllocatePortfolio:
    def test_basic_portfolio(self, engine):
        result = engine.allocate_portfolio(
            _two_strategies(), portfolio_vol=0.2, risk_compression=False
        )
        assert isinstance(result, PortfolioAllocation)
        assert 0.0 <= result.total_gross_exposure <= engine.MAX_TOTAL_EXPOSURE

    def test_allocations_per_strategy(self, engine):
        result = engine.allocate_portfolio(
            _two_strategies(), portfolio_vol=0.2, risk_compression=False
        )
        assert "s1" in result.allocations
        assert "s2" in result.allocations
        assert isinstance(result.allocations["s1"], AllocationResult)

    def test_total_exposure_capped(self, engine):
        # Many strategies should still be capped
        strategies = {
            f"s{i}": {
                "win_rate": 0.7,
                "avg_win": 2.0,
                "avg_loss": 1.0,
                "vol": 0.1,
                "confidence": 0.9,
            }
            for i in range(20)
        }
        result = engine.allocate_portfolio(
            strategies, portfolio_vol=0.2, risk_compression=False
        )
        assert result.total_gross_exposure <= engine.MAX_TOTAL_EXPOSURE

    def test_risk_compression_portfolio(self, engine):
        r_normal = engine.allocate_portfolio(
            _two_strategies(), portfolio_vol=0.2, risk_compression=False
        )
        r_compr = engine.allocate_portfolio(
            _two_strategies(), portfolio_vol=0.2, risk_compression=True
        )
        assert r_compr.total_gross_exposure <= r_normal.total_gross_exposure

    def test_empty_strategies(self, engine):
        result = engine.allocate_portfolio(
            {}, portfolio_vol=0.2, risk_compression=False
        )
        assert result.total_gross_exposure == 0.0
        assert result.portfolio_vol_est == 0.0
        assert len(result.allocations) == 0

    def test_vol_target_met_field(self, engine):
        result = engine.allocate_portfolio(
            _two_strategies(), portfolio_vol=0.2, risk_compression=False
        )
        assert isinstance(result.vol_target_met, bool)

    def test_rebalance_required_field(self, engine):
        result = engine.allocate_portfolio(
            _two_strategies(), portfolio_vol=0.2, risk_compression=False
        )
        assert isinstance(result.rebalance_required, bool)

    def test_portfolio_vol_est_non_negative(self, engine):
        result = engine.allocate_portfolio(
            _two_strategies(), portfolio_vol=0.2, risk_compression=False
        )
        assert result.portfolio_vol_est >= 0.0

    def test_default_params_used(self, engine):
        # Strategy with minimal params — defaults should be used
        strategies = {"s1": {}}
        result = engine.allocate_portfolio(
            strategies, portfolio_vol=0.2, risk_compression=False
        )
        assert "s1" in result.allocations


# ---------------------------------------------------------------------------
# DETERMINISM
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_kelly_deterministic(self, engine):
        k1 = engine.compute_kelly_fraction(0.6, 1.5, 1.0, 0.8)
        k2 = engine.compute_kelly_fraction(0.6, 1.5, 1.0, 0.8)
        assert k1 == k2

    def test_portfolio_deterministic(self, engine):
        r1 = engine.allocate_portfolio(
            _two_strategies(), portfolio_vol=0.2, risk_compression=False
        )
        r2 = engine.allocate_portfolio(
            _two_strategies(), portfolio_vol=0.2, risk_compression=False
        )
        assert r1.total_gross_exposure == r2.total_gross_exposure
        assert r1.portfolio_vol_est == r2.portfolio_vol_est

    def test_stateless(self, engine):
        """Engine should be stateless — no side effects between calls."""
        engine.allocate_portfolio(
            _two_strategies(), portfolio_vol=0.2, risk_compression=True
        )
        r = engine.allocate_portfolio(
            _two_strategies(), portfolio_vol=0.2, risk_compression=False
        )
        r2 = engine.allocate_portfolio(
            _two_strategies(), portfolio_vol=0.2, risk_compression=False
        )
        assert r.total_gross_exposure == r2.total_gross_exposure


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_very_low_win_rate(self, engine):
        k = engine.compute_kelly_fraction(0.01, 1.0, 1.0)
        assert k == 0.0

    def test_very_high_vol(self, engine):
        f = engine.compute_vol_targeting_fraction(current_vol=5.0)
        assert f >= 0.0
        assert f <= 1.0

    def test_single_strategy_portfolio(self, engine):
        strategies = {
            "only": {
                "win_rate": 0.6,
                "avg_win": 1.5,
                "avg_loss": 1.0,
                "vol": 0.2,
                "confidence": 0.8,
            }
        }
        result = engine.allocate_portfolio(
            strategies, portfolio_vol=0.2, risk_compression=False
        )
        assert len(result.allocations) == 1
        assert result.total_gross_exposure > 0

    def test_all_low_confidence(self, engine):
        strategies = {
            f"s{i}": {
                "win_rate": 0.5,
                "avg_win": 1.0,
                "avg_loss": 1.0,
                "vol": 0.2,
                "confidence": 0.01,
            }
            for i in range(5)
        }
        result = engine.allocate_portfolio(
            strategies, portfolio_vol=0.2, risk_compression=False
        )
        # Very low confidence → very small allocations
        for alloc in result.allocations.values():
            assert alloc.final_allocation < 0.1
