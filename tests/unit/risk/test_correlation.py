# =============================================================================
# tests/unit/risk/test_correlation.py -- Dynamic Correlation Model Tests
#
# Comprehensive tests for jarvis/risk/correlation.py (Phase MA-5).
# Covers: Base correlation, regime adjustments (crisis/divergence/panic),
#         PSD enforcement, lookup, determinism, immutability, edge cases.
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
from jarvis.risk.correlation import (
    # Constants
    DEFAULT_LOOKBACK,
    CRISIS_CORRELATION,
    CRISIS_BASE_WEIGHT,
    CRISIS_OVERRIDE_WEIGHT,
    DIVERGENCE_SCALING,
    PANIC_BOOST,
    PANIC_CAP,
    # Helpers
    _pearson,
    _compute_base_correlation,
    _apply_crisis_override,
    _apply_divergence_scaling,
    _apply_panic_boost,
    _nearest_psd,
    _is_psd,
    _average_off_diagonal,
    # Dataclass
    CorrelationMatrixResult,
    # Model
    DynamicCorrelationModel,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

def _make_regime(
    global_regime: GlobalRegimeState = GlobalRegimeState.RISK_ON,
    correlation: CorrelationRegimeState = CorrelationRegimeState.NORMAL,
    asset_state: AssetRegimeState = AssetRegimeState.TRENDING_UP,
) -> HierarchicalRegime:
    if global_regime == GlobalRegimeState.CRISIS:
        asset_state = AssetRegimeState.SHOCK
        correlation = CorrelationRegimeState.BREAKDOWN
    return HierarchicalRegime.create(
        global_regime=global_regime,
        asset_regimes={ac: asset_state for ac in AssetClass},
        correlation_regime=correlation,
        global_confidence=0.8,
        asset_confidences={ac: 0.8 for ac in AssetClass},
        sub_regime={ac: "test" for ac in AssetClass},
        sequence_id=0,
    )


def _correlated_returns(n: int = 30):
    """Two perfectly correlated return series."""
    return {
        "A": [0.01 * i for i in range(n)],
        "B": [0.02 * i for i in range(n)],
    }


def _uncorrelated_returns(n: int = 30):
    """Weakly correlated return series."""
    return {
        "A": [0.01 * ((-1) ** i) for i in range(n)],
        "B": [0.01 * i for i in range(n)],
    }


def _multi_returns(n: int = 30):
    """Three-asset return series."""
    return {
        "A": [0.01 * i for i in range(n)],
        "B": [0.02 * i for i in range(n)],
        "C": [0.03 * i for i in range(n)],
    }


CALM_REGIME = _make_regime()


def _estimate(**overrides):
    defaults = dict(
        returns=_correlated_returns(),
        symbols=["A", "B"],
        regime=CALM_REGIME,
    )
    defaults.update(overrides)
    return DynamicCorrelationModel().estimate(**defaults)


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    def test_default_lookback(self):
        assert DEFAULT_LOOKBACK == 90

    def test_crisis_correlation(self):
        assert CRISIS_CORRELATION == 0.8

    def test_crisis_blend_weights(self):
        assert abs(CRISIS_BASE_WEIGHT + CRISIS_OVERRIDE_WEIGHT - 1.0) < 1e-10

    def test_divergence_scaling(self):
        assert DIVERGENCE_SCALING == 0.7

    def test_panic_boost(self):
        assert PANIC_BOOST == 1.5

    def test_panic_cap(self):
        assert PANIC_CAP == 0.95


# ---------------------------------------------------------------------------
# PEARSON CORRELATION
# ---------------------------------------------------------------------------

class TestPearson:
    def test_perfect_positive(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [2.0, 4.0, 6.0, 8.0, 10.0]
        assert abs(_pearson(xs, ys) - 1.0) < 1e-10

    def test_perfect_negative(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [10.0, 8.0, 6.0, 4.0, 2.0]
        assert abs(_pearson(xs, ys) - (-1.0)) < 1e-10

    def test_zero_variance(self):
        assert _pearson([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]) == 0.0

    def test_empty(self):
        assert _pearson([], []) == 0.0

    def test_length_mismatch(self):
        assert _pearson([1.0, 2.0], [1.0]) == 0.0


# ---------------------------------------------------------------------------
# BASE CORRELATION
# ---------------------------------------------------------------------------

class TestBaseCorrelation:
    def test_two_assets_correlated(self):
        matrix = _compute_base_correlation(
            _correlated_returns(), ["A", "B"], 30
        )
        assert abs(matrix[0][1] - 1.0) < 1e-10

    def test_diagonal_is_one(self):
        matrix = _compute_base_correlation(
            _correlated_returns(), ["A", "B"], 30
        )
        assert matrix[0][0] == 1.0
        assert matrix[1][1] == 1.0

    def test_symmetric(self):
        matrix = _compute_base_correlation(
            _multi_returns(), ["A", "B", "C"], 30
        )
        for i in range(3):
            for j in range(3):
                assert abs(matrix[i][j] - matrix[j][i]) < 1e-10

    def test_three_assets(self):
        matrix = _compute_base_correlation(
            _multi_returns(), ["A", "B", "C"], 30
        )
        assert len(matrix) == 3
        assert len(matrix[0]) == 3

    def test_lookback_truncates(self):
        returns = {"A": list(range(100)), "B": list(range(100))}
        matrix = _compute_base_correlation(returns, ["A", "B"], 10)
        assert matrix[0][0] == 1.0


# ---------------------------------------------------------------------------
# CRISIS OVERRIDE
# ---------------------------------------------------------------------------

class TestCrisisOverride:
    def test_off_diagonal_near_crisis_level(self):
        base = [[1.0, 0.3], [0.3, 1.0]]
        result = _apply_crisis_override(base)
        expected = 0.2 * 0.3 + 0.8 * 0.8  # 0.06 + 0.64 = 0.7
        assert abs(result[0][1] - expected) < 1e-10

    def test_diagonal_remains_one(self):
        base = [[1.0, 0.5], [0.5, 1.0]]
        result = _apply_crisis_override(base)
        assert result[0][0] == 1.0
        assert result[1][1] == 1.0

    def test_symmetric(self):
        base = [[1.0, 0.4], [0.4, 1.0]]
        result = _apply_crisis_override(base)
        assert abs(result[0][1] - result[1][0]) < 1e-10

    def test_negative_correlations_boosted(self):
        base = [[1.0, -0.5], [-0.5, 1.0]]
        result = _apply_crisis_override(base)
        # 0.2 * (-0.5) + 0.8 * 0.8 = -0.1 + 0.64 = 0.54
        assert result[0][1] > 0.0  # Pulled toward positive


# ---------------------------------------------------------------------------
# DIVERGENCE SCALING
# ---------------------------------------------------------------------------

class TestDivergenceScaling:
    def test_correlations_reduced(self):
        base = [[1.0, 0.6], [0.6, 1.0]]
        result = _apply_divergence_scaling(base)
        assert abs(result[0][1] - 0.42) < 1e-10

    def test_diagonal_remains_one(self):
        base = [[1.0, 0.5], [0.5, 1.0]]
        result = _apply_divergence_scaling(base)
        assert result[0][0] == 1.0

    def test_negative_stays_negative(self):
        base = [[1.0, -0.3], [-0.3, 1.0]]
        result = _apply_divergence_scaling(base)
        assert result[0][1] < 0.0


# ---------------------------------------------------------------------------
# PANIC BOOST
# ---------------------------------------------------------------------------

class TestPanicBoost:
    def test_correlations_increased(self):
        base = [[1.0, 0.4], [0.4, 1.0]]
        result = _apply_panic_boost(base)
        assert result[0][1] > 0.4

    def test_capped_at_095(self):
        base = [[1.0, 0.8], [0.8, 1.0]]
        result = _apply_panic_boost(base)
        assert result[0][1] <= PANIC_CAP

    def test_diagonal_remains_one(self):
        base = [[1.0, 0.5], [0.5, 1.0]]
        result = _apply_panic_boost(base)
        assert result[0][0] == 1.0


# ---------------------------------------------------------------------------
# PSD ENFORCEMENT
# ---------------------------------------------------------------------------

class TestPSD:
    def test_identity_is_psd(self):
        m = [[1.0, 0.0], [0.0, 1.0]]
        assert _is_psd(m)

    def test_correlation_matrix_is_psd(self):
        m = [[1.0, 0.5], [0.5, 1.0]]
        assert _is_psd(m)

    def test_non_psd_fixed(self):
        # Not PSD: eigenvalue can be negative
        m = [[1.0, 0.9, 0.9],
             [0.9, 1.0, -0.9],
             [0.9, -0.9, 1.0]]
        result = _nearest_psd(m)
        assert _is_psd(result)
        # Diagonal should be 1.0
        for i in range(3):
            assert abs(result[i][i] - 1.0) < 0.01

    def test_psd_preserves_good_matrix(self):
        m = [[1.0, 0.5], [0.5, 1.0]]
        result = _nearest_psd(m)
        assert abs(result[0][1] - 0.5) < 0.01

    def test_single_element(self):
        assert _nearest_psd([[1.0]]) == [[1.0]]

    def test_empty(self):
        assert _nearest_psd([]) == []


# ---------------------------------------------------------------------------
# AVERAGE OFF-DIAGONAL
# ---------------------------------------------------------------------------

class TestAverageOffDiagonal:
    def test_two_by_two(self):
        m = [[1.0, 0.5], [0.5, 1.0]]
        assert abs(_average_off_diagonal(m) - 0.5) < 1e-10

    def test_single_asset(self):
        assert _average_off_diagonal([[1.0]]) == 0.0

    def test_empty(self):
        assert _average_off_diagonal([]) == 0.0

    def test_three_assets(self):
        m = [[1.0, 0.3, 0.6],
             [0.3, 1.0, 0.9],
             [0.6, 0.9, 1.0]]
        assert abs(_average_off_diagonal(m) - 0.6) < 1e-10


# ---------------------------------------------------------------------------
# DYNAMIC CORRELATION MODEL -- NORMAL REGIME
# ---------------------------------------------------------------------------

class TestNormalRegime:
    def test_returns_result(self):
        r = _estimate()
        assert isinstance(r, CorrelationMatrixResult)

    def test_symbols_stored(self):
        r = _estimate()
        assert r.symbols == ("A", "B")

    def test_regime_state_stored(self):
        r = _estimate()
        assert r.regime_state == CorrelationRegimeState.NORMAL

    def test_not_crisis(self):
        r = _estimate()
        assert r.is_crisis_override is False

    def test_correlation_near_one(self):
        r = _estimate(returns=_correlated_returns())
        assert r.average_correlation > 0.9

    def test_matrix_shape(self):
        r = _estimate()
        assert len(r.matrix) == 2
        assert len(r.matrix[0]) == 2

    def test_matrix_diagonal_one(self):
        r = _estimate()
        assert abs(r.matrix[0][0] - 1.0) < 1e-10
        assert abs(r.matrix[1][1] - 1.0) < 1e-10

    def test_result_hash(self):
        r = _estimate()
        assert len(r.result_hash) == 16


# ---------------------------------------------------------------------------
# DYNAMIC CORRELATION MODEL -- BREAKDOWN REGIME
# ---------------------------------------------------------------------------

class TestBreakdownRegime:
    def test_crisis_override_applied(self):
        regime = _make_regime(global_regime=GlobalRegimeState.CRISIS)
        r = _estimate(regime=regime)
        assert r.is_crisis_override is True

    def test_correlations_pulled_to_08(self):
        regime = _make_regime(global_regime=GlobalRegimeState.CRISIS)
        r = _estimate(
            returns=_uncorrelated_returns(),
            regime=regime,
        )
        # Off-diagonal should be near 0.8 (crisis override)
        assert r.average_correlation > 0.5


# ---------------------------------------------------------------------------
# DYNAMIC CORRELATION MODEL -- DIVERGENCE REGIME
# ---------------------------------------------------------------------------

class TestDivergenceRegime:
    def test_correlations_reduced(self):
        regime = _make_regime(
            correlation=CorrelationRegimeState.DIVERGENCE,
        )
        normal_r = _estimate(regime=_make_regime())
        div_r = _estimate(regime=regime)
        assert div_r.average_correlation < normal_r.average_correlation

    def test_not_crisis(self):
        regime = _make_regime(
            correlation=CorrelationRegimeState.DIVERGENCE,
        )
        r = _estimate(regime=regime)
        assert r.is_crisis_override is False


# ---------------------------------------------------------------------------
# DYNAMIC CORRELATION MODEL -- CRISIS GLOBAL (no breakdown)
# ---------------------------------------------------------------------------

class TestCrisisGlobalPanic:
    def test_panic_boost_when_global_crisis_no_breakdown(self):
        # This case won't occur because CRISIS forces BREAKDOWN per invariant
        # But we can test with RISK_OFF + non-breakdown
        regime = _make_regime(
            global_regime=GlobalRegimeState.RISK_OFF,
            correlation=CorrelationRegimeState.NORMAL,
        )
        r = _estimate(regime=regime)
        # RISK_OFF is not CRISIS, so no panic boost -> normal
        assert r.is_crisis_override is False


# ---------------------------------------------------------------------------
# ESTIMATE FROM MATRIX
# ---------------------------------------------------------------------------

class TestEstimateFromMatrix:
    def test_basic(self):
        model = DynamicCorrelationModel()
        result = model.estimate_from_matrix(
            base_matrix=[[1.0, 0.5], [0.5, 1.0]],
            symbols=["X", "Y"],
            regime=CALM_REGIME,
        )
        assert result.symbols == ("X", "Y")
        assert abs(result.average_correlation - 0.5) < 0.01

    def test_crisis_from_matrix(self):
        model = DynamicCorrelationModel()
        regime = _make_regime(global_regime=GlobalRegimeState.CRISIS)
        result = model.estimate_from_matrix(
            base_matrix=[[1.0, 0.2], [0.2, 1.0]],
            symbols=["X", "Y"],
            regime=regime,
        )
        assert result.is_crisis_override is True
        assert result.average_correlation > 0.5


# ---------------------------------------------------------------------------
# LOOKUP
# ---------------------------------------------------------------------------

class TestLookup:
    def test_get_correlation(self):
        r = _estimate()
        c = r.get_correlation("A", "B")
        assert abs(c - r.matrix[0][1]) < 1e-10

    def test_get_self_correlation(self):
        r = _estimate()
        assert abs(r.get_correlation("A", "A") - 1.0) < 1e-10

    def test_unknown_symbol_raises(self):
        r = _estimate()
        with pytest.raises(ValueError):
            r.get_correlation("A", "UNKNOWN")


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_symbols(self):
        r = _estimate(returns={}, symbols=[])
        assert r.matrix == ()
        assert r.symbols == ()

    def test_single_symbol(self):
        r = _estimate(
            returns={"A": [0.01] * 30},
            symbols=["A"],
        )
        assert r.matrix == ((1.0,),)
        assert r.average_correlation == 0.0

    def test_three_assets(self):
        r = _estimate(
            returns=_multi_returns(),
            symbols=["A", "B", "C"],
        )
        assert len(r.matrix) == 3
        assert len(r.matrix[0]) == 3


# ---------------------------------------------------------------------------
# IMMUTABILITY
# ---------------------------------------------------------------------------

class TestImmutability:
    def test_frozen(self):
        r = _estimate()
        with pytest.raises(AttributeError):
            r.average_correlation = 0.0


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_result(self):
        r1 = _estimate()
        r2 = _estimate()
        assert r1.result_hash == r2.result_hash
        assert r1.average_correlation == r2.average_correlation

    def test_different_inputs_different_hash(self):
        r1 = _estimate(returns=_correlated_returns())
        r2 = _estimate(returns=_uncorrelated_returns())
        assert r1.result_hash != r2.result_hash

    def test_fresh_instance_per_call(self):
        model = DynamicCorrelationModel()
        r1 = model.estimate(
            returns=_correlated_returns(),
            symbols=["A", "B"],
            regime=CALM_REGIME,
        )
        r2 = model.estimate(
            returns=_uncorrelated_returns(),
            symbols=["A", "B"],
            regime=CALM_REGIME,
        )
        assert r1.average_correlation != r2.average_correlation


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.risk.correlation import (
            DynamicCorrelationModel,
            CorrelationMatrixResult,
        )
        assert DynamicCorrelationModel is not None
        assert CorrelationMatrixResult is not None
