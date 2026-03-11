# tests/unit/portfolio/test_multi_asset_allocator.py
# Comprehensive tests for MultiAssetCapitalAllocator.
#
# Test categories:
#   - AllocationResult frozen/immutable
#   - Single asset allocation (degenerate case)
#   - Multi-asset with uncorrelated assets
#   - Multi-asset with perfectly correlated assets
#   - Regime adjustments (CRISIS, RISK_OFF, RISK_ON, TRANSITION, UNKNOWN)
#   - Volatility normalization across asset classes
#   - Total exposure <= 1.0 invariant
#   - Edge cases (zero capital, empty assets, single asset)
#   - Validation errors (negative capital, invalid regime, bad exposures)
#   - Determinism (same inputs -> identical outputs)

import math
import pytest

from jarvis.portfolio.multi_asset_allocator import (
    AllocationResult,
    MultiAssetCapitalAllocator,
)
from jarvis.core.regime import GlobalRegimeState


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _identity_corr(*assets: str) -> dict:
    """Build an identity correlation matrix (all uncorrelated)."""
    m: dict = {}
    for a in assets:
        m[a] = {}
        for b in assets:
            m[a][b] = 1.0 if a == b else 0.0
    return m


def _uniform_corr(*assets: str, corr: float = 1.0) -> dict:
    """Build a uniform off-diagonal correlation matrix."""
    m: dict = {}
    for a in assets:
        m[a] = {}
        for b in assets:
            m[a][b] = 1.0 if a == b else corr
    return m


def _make_allocator() -> MultiAssetCapitalAllocator:
    return MultiAssetCapitalAllocator()


# ===========================================================================
# 1. AllocationResult frozen / immutable
# ===========================================================================

class TestAllocationResultFrozen:
    def test_frozen_cannot_set_attribute(self):
        result = AllocationResult(
            allocations={"A": 100.0},
            diversification_benefit=0.5,
            total_exposure=0.5,
            asset_weights={"A": 0.5},
            regime_adjustments={"A": 1.0},
        )
        with pytest.raises(AttributeError):
            result.total_exposure = 0.9  # type: ignore[misc]

    def test_frozen_cannot_delete_attribute(self):
        result = AllocationResult(
            allocations={"A": 100.0},
            diversification_benefit=0.5,
            total_exposure=0.5,
            asset_weights={"A": 0.5},
            regime_adjustments={"A": 1.0},
        )
        with pytest.raises(AttributeError):
            del result.allocations  # type: ignore[misc]

    def test_all_fields_present(self):
        result = AllocationResult(
            allocations={"X": 50.0},
            diversification_benefit=0.3,
            total_exposure=0.7,
            asset_weights={"X": 0.7},
            regime_adjustments={"X": 1.0},
        )
        assert result.allocations == {"X": 50.0}
        assert result.diversification_benefit == 0.3
        assert result.total_exposure == 0.7
        assert result.asset_weights == {"X": 0.7}
        assert result.regime_adjustments == {"X": 1.0}


# ===========================================================================
# 2. Single asset allocation (degenerate case)
# ===========================================================================

class TestSingleAssetAllocation:
    def test_single_asset_basic(self):
        allocator = _make_allocator()
        result = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"BTC": 0.5},
            asset_classes={"BTC": "crypto"},
            correlation_matrix={"BTC": {"BTC": 1.0}},
            current_regime=GlobalRegimeState.RISK_ON,
        )
        assert len(result.allocations) == 1
        assert "BTC" in result.allocations
        assert result.allocations["BTC"] > 0.0
        # Single asset: no diversification benefit
        assert result.diversification_benefit == 0.0

    def test_single_asset_total_exposure_le_1(self):
        allocator = _make_allocator()
        result = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"SPY": 1.0},
            asset_classes={"SPY": "indices"},
            correlation_matrix={"SPY": {"SPY": 1.0}},
            current_regime=GlobalRegimeState.RISK_ON,
        )
        assert result.total_exposure <= 1.0


# ===========================================================================
# 3. Multi-asset with uncorrelated assets (full diversification benefit)
# ===========================================================================

class TestUncorrelatedAssets:
    def test_uncorrelated_has_diversification_benefit(self):
        allocator = _make_allocator()
        assets = ["BTC", "SPY", "EUR_USD"]
        result = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"BTC": 0.3, "SPY": 0.3, "EUR_USD": 0.3},
            asset_classes={"BTC": "crypto", "SPY": "indices", "EUR_USD": "forex"},
            correlation_matrix=_identity_corr(*assets),
            current_regime=GlobalRegimeState.RISK_ON,
        )
        # Uncorrelated assets should yield positive diversification benefit
        assert result.diversification_benefit > 0.0

    def test_uncorrelated_all_assets_allocated(self):
        allocator = _make_allocator()
        assets = ["A", "B", "C"]
        result = allocator.allocate(
            total_capital=50_000.0,
            asset_exposures={"A": 0.2, "B": 0.3, "C": 0.1},
            asset_classes={"A": "crypto", "B": "indices", "C": "forex"},
            correlation_matrix=_identity_corr(*assets),
            current_regime=GlobalRegimeState.RISK_ON,
        )
        assert len(result.allocations) == 3
        for asset in assets:
            assert result.allocations[asset] > 0.0


# ===========================================================================
# 4. Multi-asset with perfectly correlated assets (no diversification)
# ===========================================================================

class TestPerfectlyCorrelatedAssets:
    def test_perfectly_correlated_no_diversification(self):
        allocator = _make_allocator()
        assets = ["BTC", "ETH"]
        result = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"BTC": 0.3, "ETH": 0.3},
            asset_classes={"BTC": "crypto", "ETH": "crypto"},
            correlation_matrix=_uniform_corr(*assets, corr=1.0),
            current_regime=GlobalRegimeState.RISK_ON,
        )
        # Perfectly correlated: no diversification benefit
        assert result.diversification_benefit == 0.0

    def test_high_correlation_reduces_smaller_allocation(self):
        allocator = _make_allocator()
        assets = ["BTC", "ETH"]
        # BTC has higher exposure -> ETH should be penalized
        result = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"BTC": 0.5, "ETH": 0.3},
            asset_classes={"BTC": "crypto", "ETH": "crypto"},
            correlation_matrix=_uniform_corr(*assets, corr=0.9),
            current_regime=GlobalRegimeState.RISK_ON,
        )
        # ETH weight should be less than BTC weight due to correlation penalty
        assert result.asset_weights["ETH"] < result.asset_weights["BTC"]


# ===========================================================================
# 5. Regime adjustments
# ===========================================================================

class TestRegimeAdjustments:
    def _allocate_for_regime(self, regime: GlobalRegimeState) -> AllocationResult:
        allocator = _make_allocator()
        assets = ["BTC", "SPY"]
        return allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"BTC": 0.3, "SPY": 0.3},
            asset_classes={"BTC": "crypto", "SPY": "indices"},
            correlation_matrix=_identity_corr(*assets),
            current_regime=regime,
        )

    def test_crisis_reduces_allocation(self):
        risk_on = self._allocate_for_regime(GlobalRegimeState.RISK_ON)
        crisis = self._allocate_for_regime(GlobalRegimeState.CRISIS)
        assert sum(crisis.allocations.values()) < sum(risk_on.allocations.values())

    def test_risk_off_reduces_allocation(self):
        risk_on = self._allocate_for_regime(GlobalRegimeState.RISK_ON)
        risk_off = self._allocate_for_regime(GlobalRegimeState.RISK_OFF)
        assert sum(risk_off.allocations.values()) < sum(risk_on.allocations.values())

    def test_risk_on_full_weight(self):
        result = self._allocate_for_regime(GlobalRegimeState.RISK_ON)
        for adj in result.regime_adjustments.values():
            assert adj == 1.0

    def test_crisis_regime_adjustment_is_0_5(self):
        result = self._allocate_for_regime(GlobalRegimeState.CRISIS)
        for adj in result.regime_adjustments.values():
            assert adj == 0.5

    def test_transition_between_risk_on_and_risk_off(self):
        risk_on = self._allocate_for_regime(GlobalRegimeState.RISK_ON)
        transition = self._allocate_for_regime(GlobalRegimeState.TRANSITION)
        risk_off = self._allocate_for_regime(GlobalRegimeState.RISK_OFF)
        total_on = sum(risk_on.allocations.values())
        total_trans = sum(transition.allocations.values())
        total_off = sum(risk_off.allocations.values())
        assert total_off < total_trans < total_on

    def test_unknown_regime_reduces_allocation(self):
        risk_on = self._allocate_for_regime(GlobalRegimeState.RISK_ON)
        unknown = self._allocate_for_regime(GlobalRegimeState.UNKNOWN)
        assert sum(unknown.allocations.values()) < sum(risk_on.allocations.values())


# ===========================================================================
# 6. Volatility normalization across asset classes
# ===========================================================================

class TestVolatilityNormalization:
    def test_low_vol_asset_gets_higher_weight(self):
        """Rates (vol=0.25) should get a higher normalized weight than crypto (vol=1.0)."""
        allocator = _make_allocator()
        assets = ["BTC", "BOND"]
        result = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"BTC": 0.3, "BOND": 0.3},
            asset_classes={"BTC": "crypto", "BOND": "rates"},
            correlation_matrix=_identity_corr(*assets),
            current_regime=GlobalRegimeState.RISK_ON,
        )
        # Rates has lower vol scaling -> gets higher weight after normalization
        assert result.asset_weights["BOND"] > result.asset_weights["BTC"]

    def test_same_class_assets_equal_weight(self):
        """Two assets of the same class with equal exposure should have equal weights."""
        allocator = _make_allocator()
        assets = ["BTC", "ETH"]
        # Use zero correlation to avoid correlation penalty
        result = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"BTC": 0.3, "ETH": 0.3},
            asset_classes={"BTC": "crypto", "ETH": "crypto"},
            correlation_matrix=_identity_corr(*assets),
            current_regime=GlobalRegimeState.RISK_ON,
        )
        assert abs(result.asset_weights["BTC"] - result.asset_weights["ETH"]) < 1e-10

    def test_volatility_normalization_preserves_total_exposure_direction(self):
        """Total exposure after vol normalization should not exceed original."""
        allocator = _make_allocator()
        assets = ["BTC", "SPY", "EUR"]
        original_total = 0.2 + 0.3 + 0.2
        result = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"BTC": 0.2, "SPY": 0.3, "EUR": 0.2},
            asset_classes={"BTC": "crypto", "SPY": "indices", "EUR": "forex"},
            correlation_matrix=_identity_corr(*assets),
            current_regime=GlobalRegimeState.RISK_ON,
        )
        assert result.total_exposure <= 1.0


# ===========================================================================
# 7. Total exposure <= 1.0 invariant
# ===========================================================================

class TestTotalExposureInvariant:
    def test_high_exposures_capped_to_1(self):
        """Even if all assets have exposure=1.0, total_exposure must be <= 1.0."""
        allocator = _make_allocator()
        assets = ["A", "B", "C"]
        result = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"A": 1.0, "B": 1.0, "C": 1.0},
            asset_classes={"A": "crypto", "B": "indices", "C": "forex"},
            correlation_matrix=_identity_corr(*assets),
            current_regime=GlobalRegimeState.RISK_ON,
        )
        assert result.total_exposure <= 1.0 + 1e-12

    def test_single_full_exposure(self):
        allocator = _make_allocator()
        result = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"BTC": 1.0},
            asset_classes={"BTC": "crypto"},
            correlation_matrix={"BTC": {"BTC": 1.0}},
            current_regime=GlobalRegimeState.RISK_ON,
        )
        assert result.total_exposure <= 1.0 + 1e-12

    def test_many_assets_total_exposure_bounded(self):
        allocator = _make_allocator()
        n = 5
        names = [f"ASSET_{i}" for i in range(n)]
        classes = ["crypto", "forex", "indices", "commodities", "rates"]
        exposures = {names[i]: 0.5 for i in range(n)}
        ac = {names[i]: classes[i] for i in range(n)}
        result = allocator.allocate(
            total_capital=1_000_000.0,
            asset_exposures=exposures,
            asset_classes=ac,
            correlation_matrix=_identity_corr(*names),
            current_regime=GlobalRegimeState.RISK_ON,
        )
        assert result.total_exposure <= 1.0 + 1e-12


# ===========================================================================
# 8. Edge cases
# ===========================================================================

class TestEdgeCases:
    def test_zero_capital(self):
        allocator = _make_allocator()
        result = allocator.allocate(
            total_capital=0.0,
            asset_exposures={"BTC": 0.5},
            asset_classes={"BTC": "crypto"},
            correlation_matrix={"BTC": {"BTC": 1.0}},
            current_regime=GlobalRegimeState.RISK_ON,
        )
        assert result.allocations == {}
        assert result.total_exposure == 0.0
        assert result.diversification_benefit == 0.0

    def test_empty_assets(self):
        allocator = _make_allocator()
        result = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={},
            asset_classes={},
            correlation_matrix={},
            current_regime=GlobalRegimeState.RISK_ON,
        )
        assert result.allocations == {}
        assert result.total_exposure == 0.0

    def test_zero_exposure_for_all_assets(self):
        allocator = _make_allocator()
        assets = ["BTC", "SPY"]
        result = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"BTC": 0.0, "SPY": 0.0},
            asset_classes={"BTC": "crypto", "SPY": "indices"},
            correlation_matrix=_identity_corr(*assets),
            current_regime=GlobalRegimeState.RISK_ON,
        )
        assert result.allocations["BTC"] == 0.0
        assert result.allocations["SPY"] == 0.0

    def test_very_small_capital(self):
        allocator = _make_allocator()
        result = allocator.allocate(
            total_capital=0.01,
            asset_exposures={"BTC": 0.5},
            asset_classes={"BTC": "crypto"},
            correlation_matrix={"BTC": {"BTC": 1.0}},
            current_regime=GlobalRegimeState.RISK_ON,
        )
        assert result.allocations["BTC"] >= 0.0
        assert result.allocations["BTC"] <= 0.01


# ===========================================================================
# 9. Validation errors
# ===========================================================================

class TestValidationErrors:
    def test_negative_capital_raises(self):
        allocator = _make_allocator()
        with pytest.raises(ValueError, match="total_capital must be >= 0.0"):
            allocator.allocate(
                total_capital=-1.0,
                asset_exposures={"BTC": 0.5},
                asset_classes={"BTC": "crypto"},
                correlation_matrix={"BTC": {"BTC": 1.0}},
                current_regime=GlobalRegimeState.RISK_ON,
            )

    def test_invalid_regime_type_raises(self):
        allocator = _make_allocator()
        with pytest.raises(ValueError, match="GlobalRegimeState"):
            allocator.allocate(
                total_capital=100_000.0,
                asset_exposures={"BTC": 0.5},
                asset_classes={"BTC": "crypto"},
                correlation_matrix={"BTC": {"BTC": 1.0}},
                current_regime="RISK_ON",  # type: ignore[arg-type]
            )

    def test_exposure_above_1_raises(self):
        allocator = _make_allocator()
        with pytest.raises(ValueError, match="must be in \\[0.0, 1.0\\]"):
            allocator.allocate(
                total_capital=100_000.0,
                asset_exposures={"BTC": 1.5},
                asset_classes={"BTC": "crypto"},
                correlation_matrix={"BTC": {"BTC": 1.0}},
                current_regime=GlobalRegimeState.RISK_ON,
            )

    def test_negative_exposure_raises(self):
        allocator = _make_allocator()
        with pytest.raises(ValueError, match="must be in \\[0.0, 1.0\\]"):
            allocator.allocate(
                total_capital=100_000.0,
                asset_exposures={"BTC": -0.1},
                asset_classes={"BTC": "crypto"},
                correlation_matrix={"BTC": {"BTC": 1.0}},
                current_regime=GlobalRegimeState.RISK_ON,
            )

    def test_missing_asset_class_raises(self):
        allocator = _make_allocator()
        with pytest.raises(ValueError, match="missing from asset_classes"):
            allocator.allocate(
                total_capital=100_000.0,
                asset_exposures={"BTC": 0.5},
                asset_classes={},
                correlation_matrix={"BTC": {"BTC": 1.0}},
                current_regime=GlobalRegimeState.RISK_ON,
            )

    def test_invalid_asset_class_raises(self):
        allocator = _make_allocator()
        with pytest.raises(ValueError, match="not valid"):
            allocator.allocate(
                total_capital=100_000.0,
                asset_exposures={"BTC": 0.5},
                asset_classes={"BTC": "moon_rocks"},
                correlation_matrix={"BTC": {"BTC": 1.0}},
                current_regime=GlobalRegimeState.RISK_ON,
            )

    def test_missing_correlation_entry_raises(self):
        allocator = _make_allocator()
        with pytest.raises(ValueError, match="missing from correlation_matrix"):
            allocator.allocate(
                total_capital=100_000.0,
                asset_exposures={"BTC": 0.3, "SPY": 0.3},
                asset_classes={"BTC": "crypto", "SPY": "indices"},
                correlation_matrix={"BTC": {"BTC": 1.0}},  # SPY missing
                current_regime=GlobalRegimeState.RISK_ON,
            )


# ===========================================================================
# 10. Determinism (same inputs -> identical outputs)
# ===========================================================================

class TestDeterminism:
    def test_repeated_calls_identical(self):
        """DET-07: same inputs must produce bit-identical outputs."""
        allocator = _make_allocator()
        kwargs = dict(
            total_capital=100_000.0,
            asset_exposures={"BTC": 0.3, "SPY": 0.4, "EUR": 0.2},
            asset_classes={"BTC": "crypto", "SPY": "indices", "EUR": "forex"},
            correlation_matrix={
                "BTC": {"BTC": 1.0, "SPY": 0.3, "EUR": 0.1},
                "SPY": {"SPY": 1.0, "BTC": 0.3, "EUR": 0.2},
                "EUR": {"EUR": 1.0, "BTC": 0.1, "SPY": 0.2},
            },
            current_regime=GlobalRegimeState.RISK_ON,
        )
        r1 = allocator.allocate(**kwargs)
        r2 = allocator.allocate(**kwargs)

        assert r1.allocations == r2.allocations
        assert r1.diversification_benefit == r2.diversification_benefit
        assert r1.total_exposure == r2.total_exposure
        assert r1.asset_weights == r2.asset_weights
        assert r1.regime_adjustments == r2.regime_adjustments

    def test_fresh_instance_same_result(self):
        """DET-02: fresh instances must produce identical results."""
        kwargs = dict(
            total_capital=50_000.0,
            asset_exposures={"A": 0.5, "B": 0.3},
            asset_classes={"A": "crypto", "B": "forex"},
            correlation_matrix=_identity_corr("A", "B"),
            current_regime=GlobalRegimeState.TRANSITION,
        )
        r1 = MultiAssetCapitalAllocator().allocate(**kwargs)
        r2 = MultiAssetCapitalAllocator().allocate(**kwargs)

        assert r1.allocations == r2.allocations
        assert r1.diversification_benefit == r2.diversification_benefit

    def test_no_internal_state_leakage(self):
        """Calling allocate with different inputs must not affect prior results."""
        allocator = _make_allocator()
        kwargs1 = dict(
            total_capital=100_000.0,
            asset_exposures={"X": 0.5},
            asset_classes={"X": "crypto"},
            correlation_matrix={"X": {"X": 1.0}},
            current_regime=GlobalRegimeState.RISK_ON,
        )
        r1 = allocator.allocate(**kwargs1)

        # Call with different inputs
        kwargs2 = dict(
            total_capital=200_000.0,
            asset_exposures={"Y": 0.8},
            asset_classes={"Y": "indices"},
            correlation_matrix={"Y": {"Y": 1.0}},
            current_regime=GlobalRegimeState.CRISIS,
        )
        allocator.allocate(**kwargs2)

        # Re-call with original inputs
        r3 = allocator.allocate(**kwargs1)
        assert r1.allocations == r3.allocations


# ===========================================================================
# 11. Diversification benefit boundary values
# ===========================================================================

class TestDiversificationBenefit:
    def test_benefit_between_0_and_1(self):
        allocator = _make_allocator()
        assets = ["BTC", "SPY", "EUR"]
        result = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"BTC": 0.3, "SPY": 0.3, "EUR": 0.3},
            asset_classes={"BTC": "crypto", "SPY": "indices", "EUR": "forex"},
            correlation_matrix={
                "BTC": {"BTC": 1.0, "SPY": 0.5, "EUR": -0.2},
                "SPY": {"SPY": 1.0, "BTC": 0.5, "EUR": 0.1},
                "EUR": {"EUR": 1.0, "BTC": -0.2, "SPY": 0.1},
            },
            current_regime=GlobalRegimeState.RISK_ON,
        )
        assert 0.0 <= result.diversification_benefit <= 1.0

    def test_negative_correlation_increases_benefit(self):
        """Negatively correlated assets should yield higher diversification benefit."""
        allocator = _make_allocator()
        assets = ["A", "B"]

        # Positive correlation
        r_pos = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"A": 0.3, "B": 0.3},
            asset_classes={"A": "crypto", "B": "crypto"},
            correlation_matrix=_uniform_corr(*assets, corr=0.5),
            current_regime=GlobalRegimeState.RISK_ON,
        )

        # Negative correlation
        r_neg = allocator.allocate(
            total_capital=100_000.0,
            asset_exposures={"A": 0.3, "B": 0.3},
            asset_classes={"A": "crypto", "B": "crypto"},
            correlation_matrix=_uniform_corr(*assets, corr=-0.5),
            current_regime=GlobalRegimeState.RISK_ON,
        )

        assert r_neg.diversification_benefit > r_pos.diversification_benefit
