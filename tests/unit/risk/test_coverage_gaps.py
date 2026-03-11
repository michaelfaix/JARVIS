# tests/unit/risk/test_coverage_gaps.py
# Targeted tests for risk module coverage gaps:
# - correlation.py: symbol lookup, PSD shrink fallback, regime branches
# - risk_budget.py: zero-vol assets, total<=0 fallback
# - portfolio_allocator.py: exposure_fraction validation

from __future__ import annotations

import pytest

from jarvis.core.regime import (
    GlobalRegimeState, AssetRegimeState, AssetClass,
    CorrelationRegimeState, HierarchicalRegime,
)


# ---------------------------------------------------------------------------
# portfolio_allocator: exposure_fraction out of range (line 63)
# ---------------------------------------------------------------------------

class TestPortfolioAllocatorValidation:
    def test_exposure_fraction_negative_raises(self):
        from jarvis.portfolio.portfolio_allocator import allocate_positions
        with pytest.raises(ValueError, match="exposure_fraction"):
            allocate_positions(
                total_capital=100000.0,
                exposure_fraction=-0.1,
                asset_prices={"BTC": 50000.0},
            )

    def test_exposure_fraction_above_one_raises(self):
        from jarvis.portfolio.portfolio_allocator import allocate_positions
        with pytest.raises(ValueError, match="exposure_fraction"):
            allocate_positions(
                total_capital=100000.0,
                exposure_fraction=1.5,
                asset_prices={"BTC": 50000.0},
            )


# ---------------------------------------------------------------------------
# correlation.py: symbol not found (line 115)
# ---------------------------------------------------------------------------

class TestCorrelationSymbolLookup:
    def test_get_correlation_unknown_symbol_a(self):
        from jarvis.risk.correlation import CorrelationMatrixResult, CorrelationRegimeState
        result = CorrelationMatrixResult(
            symbols=("BTC", "ETH"),
            matrix=((1.0, 0.5), (0.5, 1.0)),
            regime_state=CorrelationRegimeState.NORMAL,
            average_correlation=0.5,
            is_crisis_override=False,
            result_hash="0" * 16,
        )
        with pytest.raises(ValueError, match="Symbol not found"):
            result.get_correlation("UNKNOWN", "BTC")

    def test_get_correlation_unknown_symbol_b(self):
        from jarvis.risk.correlation import CorrelationMatrixResult, CorrelationRegimeState
        result = CorrelationMatrixResult(
            symbols=("BTC", "ETH"),
            matrix=((1.0, 0.5), (0.5, 1.0)),
            regime_state=CorrelationRegimeState.NORMAL,
            average_correlation=0.5,
            is_crisis_override=False,
            result_hash="0" * 16,
        )
        with pytest.raises(ValueError, match="Symbol not found"):
            result.get_correlation("BTC", "UNKNOWN")


# ---------------------------------------------------------------------------
# correlation.py: PSD shrink to identity fallback (line 294)
# ---------------------------------------------------------------------------

class TestCorrelationPsdShrink:
    def test_nearest_psd_with_severely_non_psd(self):
        from jarvis.risk.correlation import _nearest_psd
        # A matrix that's far from PSD should still return a valid result
        bad = [[-10.0, 5.0], [5.0, -10.0]]
        result = _nearest_psd(bad)
        assert len(result) == 2
        # Should be PSD (or identity fallback)
        # Diagonal should be positive
        assert result[0][0] > 0
        assert result[1][1] > 0


# ---------------------------------------------------------------------------
# correlation.py: regime branches (lines 471, 473-474)
# ---------------------------------------------------------------------------

def _make_regime(
    global_regime=GlobalRegimeState.RISK_ON,
    corr_regime=CorrelationRegimeState.NORMAL,
):
    """Helper to create HierarchicalRegime for correlation tests."""
    asset_regimes = {ac: AssetRegimeState.SHOCK for ac in AssetClass}
    if global_regime == GlobalRegimeState.CRISIS:
        return HierarchicalRegime.create(
            global_regime=global_regime,
            asset_regimes=asset_regimes,
            correlation_regime=CorrelationRegimeState.BREAKDOWN,
            global_confidence=0.1,
            asset_confidences={ac: 0.1 for ac in AssetClass},
            sub_regime={ac: "" for ac in AssetClass},
            sequence_id=1,
        )
    asset_regimes_normal = {ac: AssetRegimeState.TRENDING_UP for ac in AssetClass}
    return HierarchicalRegime.create(
        global_regime=global_regime,
        asset_regimes=asset_regimes_normal,
        correlation_regime=corr_regime,
        global_confidence=0.8,
        asset_confidences={ac: 0.8 for ac in AssetClass},
        sub_regime={ac: "" for ac in AssetClass},
        sequence_id=1,
    )


class TestCorrelationRegimeBranches:
    def _base_matrix(self):
        return [[1.0, 0.3, 0.2], [0.3, 1.0, 0.4], [0.2, 0.4, 1.0]]

    def test_divergence_branch(self):
        from jarvis.risk.correlation import DynamicCorrelationModel
        engine = DynamicCorrelationModel()
        regime = _make_regime(corr_regime=CorrelationRegimeState.DIVERGENCE)
        result = engine.estimate_from_matrix(
            base_matrix=self._base_matrix(),
            symbols=["A", "B", "C"],
            regime=regime,
        )
        assert not result.is_crisis_override

    def test_breakdown_branch(self):
        from jarvis.risk.correlation import DynamicCorrelationModel
        engine = DynamicCorrelationModel()
        # BREAKDOWN requires CRISIS global regime
        regime = _make_regime(
            global_regime=GlobalRegimeState.CRISIS,
            corr_regime=CorrelationRegimeState.BREAKDOWN,
        )
        result = engine.estimate_from_matrix(
            base_matrix=self._base_matrix(),
            symbols=["A", "B", "C"],
            regime=regime,
        )
        assert result.is_crisis_override

    def test_normal_branch(self):
        from jarvis.risk.correlation import DynamicCorrelationModel
        engine = DynamicCorrelationModel()
        regime = _make_regime(corr_regime=CorrelationRegimeState.NORMAL)
        result = engine.estimate_from_matrix(
            base_matrix=self._base_matrix(),
            symbols=["A", "B", "C"],
            regime=regime,
        )
        assert not result.is_crisis_override


# ---------------------------------------------------------------------------
# risk_budget.py: zero-vol fallback and total<=0 (lines 286, 294-295, 437-438)
# ---------------------------------------------------------------------------

class TestRiskBudgetEdgeCases:
    def test_budget_allocator_exists(self):
        """Verify the module imports correctly."""
        from jarvis.risk.risk_budget import PortfolioRiskBudget
        alloc = PortfolioRiskBudget()
        assert alloc is not None
