# =============================================================================
# tests/unit/intelligence/test_correlation_regime.py -- Correlation Regime Tests
#
# Comprehensive tests for jarvis/intelligence/correlation_regime.py (Phase MA-3).
# Covers: Pearson correlation, pairwise computation, average correlation,
#         regime classification, thresholds, detect/detect_from_matrix,
#         determinism, immutability, edge cases.
# =============================================================================

import math

import pytest

from jarvis.core.regime import CorrelationRegimeState
from jarvis.intelligence.correlation_regime import (
    # Constants
    BREAKDOWN_THRESHOLD,
    CONVERGENCE_DELTA,
    DIVERGENCE_DELTA,
    CORRELATION_WINDOW,
    ALERT_CRITICAL,
    ALERT_HIGH,
    ALERT_NORMAL,
    ALERT_LOW,
    CORRELATION_STATES,
    # Functions
    _mean,
    _pearson_correlation,
    compute_pairwise_correlations,
    compute_average_correlation,
    # Results
    CorrelationRegimeResult,
    # Detector
    CorrelationRegimeDetector,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

def _make_returns(n: int = 30, base: float = 0.01, step: float = 0.001):
    """Generate a simple deterministic return series."""
    return [base + i * step for i in range(n)]


def _make_correlated_returns(n: int = 30):
    """Two perfectly correlated series."""
    a = [0.01 * i for i in range(n)]
    b = [0.02 * i for i in range(n)]
    return {"A": a, "B": b}


def _make_uncorrelated_returns(n: int = 30):
    """Two uncorrelated series (one ascending, one alternating)."""
    a = [0.01 * i for i in range(n)]
    b = [0.01 * ((-1) ** i) for i in range(n)]
    return {"A": a, "B": b}


def _detect(**kwargs):
    defaults = dict(
        returns=_make_correlated_returns(),
        historical_average=0.5,
    )
    defaults.update(kwargs)
    return CorrelationRegimeDetector().detect(**defaults)


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    def test_breakdown_threshold(self):
        assert BREAKDOWN_THRESHOLD == 0.8

    def test_convergence_delta(self):
        assert CONVERGENCE_DELTA == 0.2

    def test_divergence_delta(self):
        assert DIVERGENCE_DELTA == 0.2

    def test_correlation_window(self):
        assert CORRELATION_WINDOW == 30

    def test_alert_levels(self):
        assert ALERT_CRITICAL == "CRITICAL"
        assert ALERT_HIGH == "HIGH"
        assert ALERT_NORMAL == "NORMAL"
        assert ALERT_LOW == "LOW"

    def test_correlation_states(self):
        assert CORRELATION_STATES == ("normal", "divergence", "convergence", "breakdown")


# ---------------------------------------------------------------------------
# PURE MATH HELPERS
# ---------------------------------------------------------------------------

class TestMean:
    def test_empty_list(self):
        assert _mean([]) == 0.0

    def test_single_value(self):
        assert _mean([5.0]) == 5.0

    def test_multiple_values(self):
        assert _mean([1.0, 2.0, 3.0]) == 2.0

    def test_negative_values(self):
        assert _mean([-1.0, 1.0]) == 0.0


class TestPearsonCorrelation:
    def test_perfect_positive(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [2.0, 4.0, 6.0, 8.0, 10.0]
        assert abs(_pearson_correlation(xs, ys) - 1.0) < 1e-10

    def test_perfect_negative(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [10.0, 8.0, 6.0, 4.0, 2.0]
        assert abs(_pearson_correlation(xs, ys) - (-1.0)) < 1e-10

    def test_zero_variance_x(self):
        xs = [5.0, 5.0, 5.0, 5.0]
        ys = [1.0, 2.0, 3.0, 4.0]
        assert _pearson_correlation(xs, ys) == 0.0

    def test_zero_variance_y(self):
        xs = [1.0, 2.0, 3.0, 4.0]
        ys = [5.0, 5.0, 5.0, 5.0]
        assert _pearson_correlation(xs, ys) == 0.0

    def test_length_mismatch(self):
        assert _pearson_correlation([1.0, 2.0], [1.0]) == 0.0

    def test_too_short(self):
        assert _pearson_correlation([1.0], [2.0]) == 0.0

    def test_empty(self):
        assert _pearson_correlation([], []) == 0.0

    def test_clipped_to_range(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [2.0, 4.0, 6.0, 8.0, 10.0]
        r = _pearson_correlation(xs, ys)
        assert -1.0 <= r <= 1.0

    def test_uncorrelated_near_zero(self):
        xs = [1.0, -1.0, 1.0, -1.0, 1.0, -1.0]
        ys = [1.0, 1.0, -1.0, -1.0, 1.0, 1.0]
        r = _pearson_correlation(xs, ys)
        assert abs(r) < 0.5  # not strongly correlated


# ---------------------------------------------------------------------------
# PAIRWISE CORRELATIONS
# ---------------------------------------------------------------------------

class TestPairwiseCorrelations:
    def test_two_assets_correlated(self):
        returns = _make_correlated_returns()
        pairs = compute_pairwise_correlations(returns)
        assert ("A", "B") in pairs
        assert abs(pairs[("A", "B")] - 1.0) < 1e-10

    def test_upper_triangle_only(self):
        returns = {"A": [1.0, 2.0, 3.0], "B": [2.0, 3.0, 4.0], "C": [3.0, 4.0, 5.0]}
        pairs = compute_pairwise_correlations(returns)
        assert ("A", "B") in pairs
        assert ("A", "C") in pairs
        assert ("B", "C") in pairs
        assert ("B", "A") not in pairs
        assert ("C", "A") not in pairs

    def test_sorted_order(self):
        returns = {"Z": [1.0, 2.0, 3.0], "A": [2.0, 3.0, 4.0]}
        pairs = compute_pairwise_correlations(returns)
        assert ("A", "Z") in pairs
        assert ("Z", "A") not in pairs

    def test_single_asset_no_pairs(self):
        pairs = compute_pairwise_correlations({"A": [1.0, 2.0, 3.0]})
        assert len(pairs) == 0

    def test_empty_returns(self):
        pairs = compute_pairwise_correlations({})
        assert len(pairs) == 0

    def test_three_assets_count(self):
        returns = {
            "A": [1.0, 2.0, 3.0],
            "B": [2.0, 3.0, 4.0],
            "C": [3.0, 4.0, 5.0],
        }
        pairs = compute_pairwise_correlations(returns)
        assert len(pairs) == 3  # C(3,2) = 3


# ---------------------------------------------------------------------------
# AVERAGE CORRELATION
# ---------------------------------------------------------------------------

class TestAverageCorrelation:
    def test_empty_pairs(self):
        assert compute_average_correlation({}) == 0.0

    def test_single_pair(self):
        assert compute_average_correlation({("A", "B"): 0.8}) == 0.8

    def test_multiple_pairs(self):
        pairs = {("A", "B"): 0.6, ("A", "C"): 0.4, ("B", "C"): 0.5}
        assert abs(compute_average_correlation(pairs) - 0.5) < 1e-10


# ---------------------------------------------------------------------------
# CLASSIFICATION
# ---------------------------------------------------------------------------

class TestClassification:
    def test_breakdown(self):
        """avg_corr > 0.8 -> breakdown."""
        r = CorrelationRegimeDetector().detect(
            returns=_make_correlated_returns(),
            historical_average=0.5,
        )
        # Perfectly correlated -> avg_corr ~ 1.0 > 0.8
        assert r.state == "breakdown"

    def test_convergence(self):
        """avg_corr > hist_avg + 0.2 -> convergence (but <= 0.8)."""
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.75},
            historical_average=0.4,
            num_assets=2,
        )
        # 0.75 > 0.4 + 0.2 = 0.6 -> convergence
        # 0.75 <= 0.8 -> not breakdown
        assert result.state == "convergence"

    def test_divergence(self):
        """avg_corr < hist_avg - 0.2 -> divergence."""
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.1},
            historical_average=0.5,
            num_assets=2,
        )
        # 0.1 < 0.5 - 0.2 = 0.3 -> divergence
        assert result.state == "divergence"

    def test_normal(self):
        """avg_corr within normal band."""
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.5},
            historical_average=0.5,
            num_assets=2,
        )
        assert result.state == "normal"

    def test_breakdown_priority_over_convergence(self):
        """Breakdown takes priority even if convergence also matches."""
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.85},
            historical_average=0.3,
            num_assets=2,
        )
        # 0.85 > 0.8 -> breakdown (even though 0.85 > 0.3+0.2=0.5 -> convergence)
        assert result.state == "breakdown"

    def test_breakdown_boundary_above(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.801},
            historical_average=0.5,
            num_assets=2,
        )
        assert result.state == "breakdown"

    def test_breakdown_boundary_at(self):
        """At exactly 0.8 -> NOT breakdown (> not >=)."""
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.8},
            historical_average=0.5,
            num_assets=2,
        )
        assert result.state != "breakdown"

    def test_convergence_boundary(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.71},
            historical_average=0.5,
            num_assets=2,
        )
        # 0.71 > 0.5 + 0.2 = 0.7 -> convergence
        assert result.state == "convergence"

    def test_divergence_boundary(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.29},
            historical_average=0.5,
            num_assets=2,
        )
        # 0.29 < 0.5 - 0.2 = 0.3 -> divergence
        assert result.state == "divergence"

    def test_normal_at_upper_edge(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.7},
            historical_average=0.5,
            num_assets=2,
        )
        # 0.7 > 0.5 + 0.2 = 0.7? No, > not >= -> normal
        assert result.state == "normal"

    def test_normal_at_lower_edge(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.3},
            historical_average=0.5,
            num_assets=2,
        )
        # 0.3 < 0.3? No -> normal
        assert result.state == "normal"


# ---------------------------------------------------------------------------
# CANONICAL STATE MAPPING
# ---------------------------------------------------------------------------

class TestCanonicalStateMapping:
    def test_normal_maps_to_normal(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.5},
            historical_average=0.5,
            num_assets=2,
        )
        assert result.canonical_state == CorrelationRegimeState.NORMAL

    def test_divergence_maps_to_divergence(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.1},
            historical_average=0.5,
            num_assets=2,
        )
        assert result.canonical_state == CorrelationRegimeState.DIVERGENCE

    def test_convergence_maps_to_coupled(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.75},
            historical_average=0.4,
            num_assets=2,
        )
        assert result.canonical_state == CorrelationRegimeState.COUPLED

    def test_breakdown_maps_to_breakdown(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.85},
            historical_average=0.5,
            num_assets=2,
        )
        assert result.canonical_state == CorrelationRegimeState.BREAKDOWN


# ---------------------------------------------------------------------------
# ALERT LEVELS
# ---------------------------------------------------------------------------

class TestAlertLevels:
    def test_normal_alert(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.5},
            historical_average=0.5,
            num_assets=2,
        )
        assert result.alert_level == ALERT_NORMAL

    def test_divergence_alert(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.1},
            historical_average=0.5,
            num_assets=2,
        )
        assert result.alert_level == ALERT_LOW

    def test_convergence_alert(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.75},
            historical_average=0.4,
            num_assets=2,
        )
        assert result.alert_level == ALERT_HIGH

    def test_breakdown_alert(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.85},
            historical_average=0.5,
            num_assets=2,
        )
        assert result.alert_level == ALERT_CRITICAL


# ---------------------------------------------------------------------------
# DETECT METHOD (from raw returns)
# ---------------------------------------------------------------------------

class TestDetect:
    def test_returns_result(self):
        r = _detect()
        assert isinstance(r, CorrelationRegimeResult)

    def test_num_assets(self):
        r = _detect()
        assert r.num_assets == 2

    def test_pair_correlations_computed(self):
        r = _detect()
        assert ("A", "B") in r.pair_correlations

    def test_average_correlation_stored(self):
        r = _detect()
        assert isinstance(r.average_correlation, float)

    def test_historical_average_stored(self):
        r = _detect(historical_average=0.42)
        assert r.historical_average == 0.42

    def test_three_assets(self):
        returns = {
            "X": [float(i) for i in range(30)],
            "Y": [float(i * 2) for i in range(30)],
            "Z": [float(i * 3) for i in range(30)],
        }
        r = CorrelationRegimeDetector().detect(returns=returns, historical_average=0.5)
        assert r.num_assets == 3
        assert len(r.pair_correlations) == 3


# ---------------------------------------------------------------------------
# DETECT FROM MATRIX
# ---------------------------------------------------------------------------

class TestDetectFromMatrix:
    def test_basic(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.5, ("A", "C"): 0.4},
            historical_average=0.5,
            num_assets=3,
        )
        assert result.num_assets == 3
        assert result.pair_correlations == {("A", "B"): 0.5, ("A", "C"): 0.4}

    def test_empty_matrix(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={},
            historical_average=0.5,
            num_assets=0,
        )
        assert result.average_correlation == 0.0
        assert result.state == "divergence"  # 0.0 < 0.5 - 0.2


# ---------------------------------------------------------------------------
# RESULT IMMUTABILITY
# ---------------------------------------------------------------------------

class TestResultImmutability:
    def test_frozen(self):
        r = _detect()
        with pytest.raises(AttributeError):
            r.state = "normal"

    def test_all_fields_present(self):
        r = _detect()
        assert r.state is not None
        assert r.canonical_state is not None
        assert isinstance(r.average_correlation, float)
        assert isinstance(r.historical_average, float)
        assert r.alert_level is not None
        assert isinstance(r.pair_correlations, dict)
        assert isinstance(r.num_assets, int)


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_result(self):
        r1 = _detect()
        r2 = _detect()
        assert r1.state == r2.state
        assert r1.canonical_state == r2.canonical_state
        assert r1.average_correlation == r2.average_correlation
        assert r1.alert_level == r2.alert_level

    def test_different_inputs_different_result(self):
        r1 = _detect(historical_average=0.1)
        r2 = _detect(historical_average=0.9)
        # Both have corr~1.0 so both are breakdown, but historical_average differs
        assert r1.historical_average != r2.historical_average

    def test_fresh_instance_per_call(self):
        d = CorrelationRegimeDetector()
        r1 = d.detect(returns=_make_correlated_returns(), historical_average=0.5)
        r2 = d.detect_from_matrix(
            pair_correlations={("A", "B"): 0.1},
            historical_average=0.5,
            num_assets=2,
        )
        assert r1.state != r2.state  # breakdown vs divergence


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_negative_correlations(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [5.0, 4.0, 3.0, 2.0, 1.0]
        r = _pearson_correlation(xs, ys)
        assert r < 0

    def test_very_small_series(self):
        returns = {"A": [1.0, 2.0], "B": [3.0, 4.0]}
        pairs = compute_pairwise_correlations(returns)
        assert ("A", "B") in pairs

    def test_zero_historical_average(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.5},
            historical_average=0.0,
            num_assets=2,
        )
        # 0.5 > 0.0 + 0.2 = 0.2 -> convergence
        assert result.state == "convergence"

    def test_negative_historical_average(self):
        detector = CorrelationRegimeDetector()
        result = detector.detect_from_matrix(
            pair_correlations={("A", "B"): 0.5},
            historical_average=-0.5,
            num_assets=2,
        )
        # 0.5 > -0.5 + 0.2 = -0.3 -> convergence
        assert result.state == "convergence"


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.intelligence.correlation_regime import (
            CorrelationRegimeDetector,
            CorrelationRegimeResult,
            compute_pairwise_correlations,
            compute_average_correlation,
        )
        assert CorrelationRegimeDetector is not None
        assert CorrelationRegimeResult is not None
