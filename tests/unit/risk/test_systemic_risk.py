# =============================================================================
# tests/unit/risk/test_systemic_risk.py -- Systemic Risk Monitor Tests
#
# Comprehensive tests for jarvis/risk/systemic_risk.py (Phase MA-5).
# Covers: constants, classify_correlation_regime, compute_portfolio_fragility,
#         simulate_tail_stress, compute_concentration_risk, determinism,
#         immutability, edge cases.
# =============================================================================

import math

import pytest

from jarvis.core.regime import AssetClass, CorrelationRegimeState
from jarvis.risk.systemic_risk import (
    # Constants
    CORR_LOW_THRESHOLD,
    CORR_MEDIUM_THRESHOLD,
    CORR_FM04_THRESHOLD,
    TAIL_STRESS_MULTIPLIERS,
    RECOVERY_FAST_THRESHOLD,
    RECOVERY_SLOW_THRESHOLD,
    FRAGILITY_LOW_THRESHOLD,
    FRAGILITY_HIGH_THRESHOLD,
    FRAGILITY_CONFIDENCE_PENALTY_FACTOR,
    CONCENTRATION_LOW_THRESHOLD,
    CONCENTRATION_HIGH_THRESHOLD,
    CONCENTRATION_WEIGHT_PENALTY_FACTOR,
    # Helpers
    _upper_triangle_values,
    _mean_corr_per_asset,
    # Functions
    classify_correlation_regime,
    compute_portfolio_fragility,
    simulate_tail_stress,
    compute_concentration_risk,
    # Dataclasses
    CorrelationRegimeResult,
    PortfolioFragilityIndex,
    TailDependencyStressResult,
    ConcentrationRiskScore,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

def _identity_matrix(n):
    return tuple(
        tuple(1.0 if i == j else 0.0 for j in range(n))
        for i in range(n)
    )

def _uniform_corr_matrix(n, off_diag):
    return tuple(
        tuple(1.0 if i == j else off_diag for j in range(n))
        for i in range(n)
    )


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    def test_corr_low_threshold(self):
        assert CORR_LOW_THRESHOLD == 0.40

    def test_corr_medium_threshold(self):
        assert CORR_MEDIUM_THRESHOLD == 0.65

    def test_fm04_threshold(self):
        assert CORR_FM04_THRESHOLD == 0.85

    def test_stress_multipliers(self):
        assert TAIL_STRESS_MULTIPLIERS["MILD"] == 1.30
        assert TAIL_STRESS_MULTIPLIERS["MODERATE"] == 1.60
        assert TAIL_STRESS_MULTIPLIERS["SEVERE"] == 2.00
        assert TAIL_STRESS_MULTIPLIERS["EXTREME"] == 2.50

    def test_recovery_thresholds(self):
        assert RECOVERY_FAST_THRESHOLD == 0.70
        assert RECOVERY_SLOW_THRESHOLD == 0.85

    def test_fragility_thresholds(self):
        assert FRAGILITY_LOW_THRESHOLD == 0.30
        assert FRAGILITY_HIGH_THRESHOLD == 0.60

    def test_concentration_thresholds(self):
        assert CONCENTRATION_LOW_THRESHOLD == 0.25
        assert CONCENTRATION_HIGH_THRESHOLD == 0.50

    def test_penalty_factors(self):
        assert FRAGILITY_CONFIDENCE_PENALTY_FACTOR == 0.20
        assert CONCENTRATION_WEIGHT_PENALTY_FACTOR == 0.30


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

class TestUpperTriangleValues:
    def test_identity_2x2(self):
        vals = _upper_triangle_values(_identity_matrix(2), 2)
        assert len(vals) == 1
        assert vals[0] == 0.0

    def test_uniform_3x3(self):
        vals = _upper_triangle_values(_uniform_corr_matrix(3, 0.5), 3)
        assert len(vals) == 3
        assert all(abs(v - 0.5) < 1e-10 for v in vals)

    def test_single_asset(self):
        vals = _upper_triangle_values(((1.0,),), 1)
        assert vals == []

    def test_negative_corr_uses_abs(self):
        matrix = ((1.0, -0.6), (-0.6, 1.0))
        vals = _upper_triangle_values(matrix, 2)
        assert abs(vals[0] - 0.6) < 1e-10


class TestMeanCorrPerAsset:
    def test_uniform_corr(self):
        means = _mean_corr_per_asset(_uniform_corr_matrix(3, 0.4), 3)
        assert len(means) == 3
        for m in means:
            assert abs(m - 0.4) < 1e-10

    def test_single_asset(self):
        means = _mean_corr_per_asset(((1.0,),), 1)
        assert len(means) == 1
        assert means[0] == 0.0


# ---------------------------------------------------------------------------
# CLASSIFY CORRELATION REGIME
# ---------------------------------------------------------------------------

class TestClassifyCorrelationRegime:
    def test_single_asset_normal(self):
        r = classify_correlation_regime(corr_matrix=((1.0,),), n_assets=1)
        assert r.state == CorrelationRegimeState.NORMAL
        assert r.n_pairs == 0

    def test_low_corr_normal(self):
        matrix = _uniform_corr_matrix(3, 0.2)
        r = classify_correlation_regime(corr_matrix=matrix, n_assets=3)
        assert r.state == CorrelationRegimeState.NORMAL
        assert r.mean_pairwise_corr < CORR_LOW_THRESHOLD

    def test_medium_corr_coupled(self):
        matrix = _uniform_corr_matrix(3, 0.5)
        r = classify_correlation_regime(corr_matrix=matrix, n_assets=3)
        assert r.state == CorrelationRegimeState.COUPLED

    def test_high_corr_breakdown(self):
        matrix = _uniform_corr_matrix(3, 0.8)
        r = classify_correlation_regime(corr_matrix=matrix, n_assets=3)
        assert r.state == CorrelationRegimeState.BREAKDOWN

    def test_fm04_not_triggered_low(self):
        matrix = _uniform_corr_matrix(3, 0.5)
        r = classify_correlation_regime(corr_matrix=matrix, n_assets=3)
        assert r.fm04_triggered is False

    def test_fm04_triggered_high(self):
        matrix = _uniform_corr_matrix(3, 0.9)
        r = classify_correlation_regime(corr_matrix=matrix, n_assets=3)
        assert r.fm04_triggered is True

    def test_n_pairs_correct(self):
        r = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(4, 0.3), n_assets=4,
        )
        assert r.n_pairs == 6  # C(4,2) = 6

    def test_max_pairwise(self):
        matrix = ((1.0, 0.3, 0.7), (0.3, 1.0, 0.5), (0.7, 0.5, 1.0))
        r = classify_correlation_regime(corr_matrix=matrix, n_assets=3)
        assert abs(r.max_pairwise_corr - 0.7) < 1e-10

    def test_result_hash(self):
        r = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.5), n_assets=3,
        )
        assert len(r.result_hash) == 16
        assert all(c in "0123456789abcdef" for c in r.result_hash)

    def test_boundary_at_040(self):
        # Exactly at 0.40 -> should be COUPLED (>= 0.40)
        matrix = _uniform_corr_matrix(2, 0.40)
        r = classify_correlation_regime(corr_matrix=matrix, n_assets=2)
        assert r.state == CorrelationRegimeState.COUPLED

    def test_boundary_at_065(self):
        matrix = _uniform_corr_matrix(2, 0.65)
        r = classify_correlation_regime(corr_matrix=matrix, n_assets=2)
        assert r.state == CorrelationRegimeState.BREAKDOWN


# ---------------------------------------------------------------------------
# COMPUTE PORTFOLIO FRAGILITY
# ---------------------------------------------------------------------------

class TestComputePortfolioFragility:
    def test_single_asset(self):
        r = compute_portfolio_fragility(
            corr_matrix=((1.0,),), asset_ids=["BTC"],
        )
        assert r.hhi_correlation == 0.0
        assert r.fragility_band == "LOW"

    def test_uncorrelated_low_fragility(self):
        r = compute_portfolio_fragility(
            corr_matrix=_identity_matrix(4),
            asset_ids=["A", "B", "C", "D"],
        )
        assert r.hhi_correlation == 0.0
        assert r.fragility_band == "LOW"
        assert r.confidence_penalty == 0.0

    def test_high_corr_high_fragility(self):
        r = compute_portfolio_fragility(
            corr_matrix=_uniform_corr_matrix(3, 0.9),
            asset_ids=["A", "B", "C"],
        )
        assert r.hhi_correlation > 0.0
        assert r.fragility_band in ("MEDIUM", "HIGH")

    def test_dominant_asset_identified(self):
        matrix = ((1.0, 0.9, 0.8), (0.9, 1.0, 0.3), (0.8, 0.3, 1.0))
        r = compute_portfolio_fragility(
            corr_matrix=matrix, asset_ids=["A", "B", "C"],
        )
        assert r.dominant_asset_id == "A"  # Highest mean corr with others
        assert r.dominant_corr > 0.0

    def test_confidence_penalty_range(self):
        r = compute_portfolio_fragility(
            corr_matrix=_uniform_corr_matrix(3, 0.9),
            asset_ids=["A", "B", "C"],
        )
        assert 0.0 <= r.confidence_penalty <= 0.20

    def test_result_hash(self):
        r = compute_portfolio_fragility(
            corr_matrix=_uniform_corr_matrix(3, 0.5),
            asset_ids=["A", "B", "C"],
        )
        assert len(r.result_hash) == 16

    def test_empty_assets(self):
        r = compute_portfolio_fragility(corr_matrix=(), asset_ids=[])
        assert r.hhi_correlation == 0.0
        assert r.dominant_asset_id == ""


# ---------------------------------------------------------------------------
# SIMULATE TAIL STRESS
# ---------------------------------------------------------------------------

class TestSimulateTailStress:
    def test_moderate_stress(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.4), n_assets=3,
        )
        r = simulate_tail_stress(
            current_corr_regime=regime, stress_scenario="MODERATE",
        )
        assert r.stressed_mean_corr > r.base_mean_corr
        assert r.stress_multiplier == 1.60

    def test_stressed_clipped_to_one(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.8), n_assets=3,
        )
        r = simulate_tail_stress(
            current_corr_regime=regime, stress_scenario="EXTREME",
        )
        assert r.stressed_mean_corr <= 1.0

    def test_mild_stress(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.3), n_assets=3,
        )
        r = simulate_tail_stress(
            current_corr_regime=regime, stress_scenario="MILD",
        )
        assert r.stress_multiplier == 1.30

    def test_severe_stress(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.3), n_assets=3,
        )
        r = simulate_tail_stress(
            current_corr_regime=regime, stress_scenario="SEVERE",
        )
        assert r.stress_multiplier == 2.00

    def test_fm04_base_not_triggered(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.3), n_assets=3,
        )
        r = simulate_tail_stress(current_corr_regime=regime)
        assert r.fm04_triggered_base is False

    def test_fm04_stress_can_trigger(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.6), n_assets=3,
        )
        r = simulate_tail_stress(
            current_corr_regime=regime, stress_scenario="EXTREME",
        )
        # 0.6 * 2.5 = 1.5 -> clipped to 1.0 > 0.85
        assert r.fm04_triggered_stress is True

    def test_recovery_fast(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.3), n_assets=3,
        )
        r = simulate_tail_stress(
            current_corr_regime=regime, stress_scenario="MILD",
        )
        # 0.3 * 1.3 = 0.39 < 0.70
        assert r.recovery_scenario == "FAST"

    def test_recovery_slow(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.5), n_assets=3,
        )
        r = simulate_tail_stress(
            current_corr_regime=regime, stress_scenario="MODERATE",
        )
        # 0.5 * 1.6 = 0.80, 0.70 <= 0.80 < 0.85
        assert r.recovery_scenario == "SLOW"

    def test_recovery_persistent(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.7), n_assets=3,
        )
        r = simulate_tail_stress(
            current_corr_regime=regime, stress_scenario="SEVERE",
        )
        # 0.7 * 2.0 = 1.4 -> clipped to 1.0 >= 0.85
        assert r.recovery_scenario == "PERSISTENT"

    def test_confidence_impact_fm04(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.6), n_assets=3,
        )
        r = simulate_tail_stress(
            current_corr_regime=regime, stress_scenario="EXTREME",
        )
        # fm04_stress = True: impact = stressed * 0.30
        assert abs(r.confidence_impact - r.stressed_mean_corr * 0.30) < 1e-10

    def test_confidence_impact_no_fm04(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.3), n_assets=3,
        )
        r = simulate_tail_stress(
            current_corr_regime=regime, stress_scenario="MILD",
        )
        # fm04_stress = False: impact = stressed * 0.10
        assert abs(r.confidence_impact - r.stressed_mean_corr * 0.10) < 1e-10

    def test_result_hash(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.5), n_assets=3,
        )
        r = simulate_tail_stress(current_corr_regime=regime)
        assert len(r.result_hash) == 16

    def test_unknown_scenario_defaults_moderate(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.4), n_assets=3,
        )
        r = simulate_tail_stress(
            current_corr_regime=regime, stress_scenario="UNKNOWN",
        )
        assert r.stress_multiplier == 1.60  # Default fallback


# ---------------------------------------------------------------------------
# COMPUTE CONCENTRATION RISK
# ---------------------------------------------------------------------------

class TestComputeConcentrationRisk:
    def test_equal_weights_low(self):
        weights = {"crypto": 0.2, "forex": 0.2, "indices": 0.2,
                   "commodities": 0.2, "rates": 0.2}
        r = compute_concentration_risk(weights_by_class=weights)
        assert abs(r.hhi_weight - 0.2) < 1e-10  # 5 * (0.2^2) = 0.2
        assert r.concentration_band == "LOW"

    def test_single_asset_high(self):
        weights = {"crypto": 1.0}
        r = compute_concentration_risk(weights_by_class=weights)
        assert abs(r.hhi_weight - 1.0) < 1e-10
        assert r.concentration_band == "HIGH"

    def test_dominant_identified(self):
        weights = {"crypto": 0.6, "forex": 0.2, "indices": 0.2}
        r = compute_concentration_risk(weights_by_class=weights)
        assert r.dominant_class == "crypto"
        assert abs(r.dominant_weight - 0.6) < 1e-10

    def test_weight_penalty_range(self):
        weights = {"crypto": 1.0}
        r = compute_concentration_risk(weights_by_class=weights)
        assert 0.0 <= r.weight_penalty <= 0.30

    def test_weight_penalty_formula(self):
        weights = {"crypto": 0.5, "forex": 0.5}
        r = compute_concentration_risk(weights_by_class=weights)
        # HHI = 2 * 0.5^2 = 0.5
        expected_penalty = min(0.5 * 0.30, 0.30)
        assert abs(r.weight_penalty - expected_penalty) < 1e-10

    def test_empty_weights(self):
        r = compute_concentration_risk(weights_by_class={})
        assert r.hhi_weight == 0.0
        assert r.concentration_band == "LOW"
        assert r.dominant_class == ""

    def test_unnormalized_weights(self):
        weights = {"crypto": 100.0, "forex": 100.0}
        r = compute_concentration_risk(weights_by_class=weights)
        # Should normalize: 0.5 each -> HHI = 0.5
        assert abs(r.hhi_weight - 0.5) < 1e-10

    def test_result_hash(self):
        weights = {"crypto": 0.3, "forex": 0.7}
        r = compute_concentration_risk(weights_by_class=weights)
        assert len(r.result_hash) == 16

    def test_band_boundary_025(self):
        # Two assets: 70/30 split -> HHI = 0.49+0.09 = 0.58 -> MEDIUM
        weights = {"a": 0.7, "b": 0.3}
        r = compute_concentration_risk(weights_by_class=weights)
        assert r.concentration_band in ("MEDIUM", "HIGH")

    def test_three_equal_medium(self):
        # 3 assets: 1/3 each -> HHI = 3*(1/3)^2 = 0.333 -> MEDIUM
        weights = {"a": 1.0, "b": 1.0, "c": 1.0}
        r = compute_concentration_risk(weights_by_class=weights)
        assert abs(r.hhi_weight - 1.0/3.0) < 1e-10
        assert r.concentration_band == "MEDIUM"


# ---------------------------------------------------------------------------
# IMMUTABILITY
# ---------------------------------------------------------------------------

class TestImmutability:
    def test_corr_regime_frozen(self):
        r = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.5), n_assets=3,
        )
        with pytest.raises(AttributeError):
            r.state = CorrelationRegimeState.NORMAL

    def test_fragility_frozen(self):
        r = compute_portfolio_fragility(
            corr_matrix=_uniform_corr_matrix(3, 0.5),
            asset_ids=["A", "B", "C"],
        )
        with pytest.raises(AttributeError):
            r.hhi_correlation = 0.0

    def test_stress_frozen(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.5), n_assets=3,
        )
        r = simulate_tail_stress(current_corr_regime=regime)
        with pytest.raises(AttributeError):
            r.stressed_mean_corr = 0.0

    def test_concentration_frozen(self):
        r = compute_concentration_risk(weights_by_class={"a": 1.0})
        with pytest.raises(AttributeError):
            r.hhi_weight = 0.0


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_classify_same_hash(self):
        matrix = _uniform_corr_matrix(3, 0.5)
        r1 = classify_correlation_regime(corr_matrix=matrix, n_assets=3)
        r2 = classify_correlation_regime(corr_matrix=matrix, n_assets=3)
        assert r1.result_hash == r2.result_hash

    def test_fragility_same_hash(self):
        matrix = _uniform_corr_matrix(3, 0.5)
        ids = ["A", "B", "C"]
        r1 = compute_portfolio_fragility(corr_matrix=matrix, asset_ids=ids)
        r2 = compute_portfolio_fragility(corr_matrix=matrix, asset_ids=ids)
        assert r1.result_hash == r2.result_hash

    def test_stress_same_hash(self):
        regime = classify_correlation_regime(
            corr_matrix=_uniform_corr_matrix(3, 0.5), n_assets=3,
        )
        r1 = simulate_tail_stress(current_corr_regime=regime)
        r2 = simulate_tail_stress(current_corr_regime=regime)
        assert r1.result_hash == r2.result_hash

    def test_concentration_same_hash(self):
        w = {"a": 0.3, "b": 0.7}
        r1 = compute_concentration_risk(weights_by_class=w)
        r2 = compute_concentration_risk(weights_by_class=w)
        assert r1.result_hash == r2.result_hash


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.risk.systemic_risk import (
            classify_correlation_regime,
            compute_portfolio_fragility,
            simulate_tail_stress,
            compute_concentration_risk,
            CorrelationRegimeResult,
            PortfolioFragilityIndex,
            TailDependencyStressResult,
            ConcentrationRiskScore,
        )
        assert classify_correlation_regime is not None
