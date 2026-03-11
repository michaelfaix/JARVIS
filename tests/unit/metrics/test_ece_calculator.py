# =============================================================================
# tests/unit/metrics/test_ece_calculator.py
# Tests for jarvis/metrics/ece_calculator.py
# =============================================================================

from __future__ import annotations

import math

import pytest

from jarvis.metrics.ece_calculator import (
    N_BINS,
    MIN_SAMPLES,
    ECE_HARD_GATE,
    CONFIDENCE_FLOOR,
    CONFIDENCE_CEILING,
    BinStatistics,
    ECEResult,
    compute_ece,
    compute_ece_scalar,
    _clamp_confidence,
    _validate_inputs,
)


# =============================================================================
# HELPERS
# =============================================================================

def _perfectly_calibrated(n: int = 100) -> tuple[list[float], list[float]]:
    """Create perfectly calibrated data: confidence == outcome."""
    confs = [i / (n - 1) for i in range(n)]
    outcomes = list(confs)
    return confs, outcomes


def _completely_miscalibrated(n: int = 100) -> tuple[list[float], list[float]]:
    """All confidences high (0.9), all outcomes 0.0."""
    return [0.9] * n, [0.0] * n


def _binary_outcomes(n: int = 100) -> tuple[list[float], list[float]]:
    """Alternating outcomes with linearly spaced confidence."""
    confs = [(i + 1) / (n + 1) for i in range(n)]
    outcomes = [1.0 if i % 2 == 0 else 0.0 for i in range(n)]
    return confs, outcomes


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_n_bins(self):
        assert N_BINS == 10

    def test_min_samples(self):
        assert MIN_SAMPLES == 1

    def test_ece_hard_gate(self):
        assert ECE_HARD_GATE == 0.05

    def test_confidence_floor(self):
        assert CONFIDENCE_FLOOR == 1e-6

    def test_confidence_ceiling(self):
        assert CONFIDENCE_CEILING == 1.0 - 1e-6

    def test_floor_less_than_ceiling(self):
        assert CONFIDENCE_FLOOR < CONFIDENCE_CEILING


# =============================================================================
# SECTION 2 -- BinStatistics FROZEN
# =============================================================================

class TestBinStatisticsFrozen:
    def test_frozen(self):
        bs = BinStatistics(
            bin_index=0, n_samples=10,
            avg_confidence=0.3, avg_accuracy=0.4,
            bin_weight=0.1, abs_error=0.1,
        )
        with pytest.raises(AttributeError):
            bs.bin_index = 1

    def test_fields(self):
        bs = BinStatistics(
            bin_index=2, n_samples=15,
            avg_confidence=0.5, avg_accuracy=0.6,
            bin_weight=0.15, abs_error=0.1,
        )
        assert bs.bin_index == 2
        assert bs.n_samples == 15
        assert bs.avg_confidence == 0.5
        assert bs.avg_accuracy == 0.6
        assert bs.bin_weight == 0.15
        assert bs.abs_error == 0.1

    def test_equality(self):
        a = BinStatistics(0, 10, 0.3, 0.4, 0.1, 0.1)
        b = BinStatistics(0, 10, 0.3, 0.4, 0.1, 0.1)
        assert a == b


# =============================================================================
# SECTION 3 -- ECEResult FROZEN
# =============================================================================

class TestECEResultFrozen:
    def test_frozen(self):
        r = ECEResult(
            ece=0.03, n_bins_used=10, n_samples=100,
            max_bin_error=0.08, bin_statistics=(), is_calibrated=True,
        )
        with pytest.raises(AttributeError):
            r.ece = 0.0

    def test_fields(self):
        r = ECEResult(
            ece=0.04, n_bins_used=8, n_samples=80,
            max_bin_error=0.10, bin_statistics=(), is_calibrated=True,
        )
        assert r.ece == 0.04
        assert r.n_bins_used == 8
        assert r.n_samples == 80
        assert r.max_bin_error == 0.10
        assert r.bin_statistics == ()
        assert r.is_calibrated is True


# =============================================================================
# SECTION 4 -- _clamp_confidence
# =============================================================================

class TestClampConfidence:
    def test_normal_value(self):
        assert _clamp_confidence(0.5) == 0.5

    def test_zero_clamped(self):
        assert _clamp_confidence(0.0) == CONFIDENCE_FLOOR

    def test_one_clamped(self):
        assert _clamp_confidence(1.0) == CONFIDENCE_CEILING

    def test_negative_clamped(self):
        assert _clamp_confidence(-0.1) == CONFIDENCE_FLOOR

    def test_above_one_clamped(self):
        assert _clamp_confidence(1.5) == CONFIDENCE_CEILING

    def test_floor_value_returned(self):
        assert _clamp_confidence(CONFIDENCE_FLOOR) == CONFIDENCE_FLOOR

    def test_ceiling_value_returned(self):
        assert _clamp_confidence(CONFIDENCE_CEILING) == CONFIDENCE_CEILING

    def test_midpoint(self):
        assert _clamp_confidence(0.5) == 0.5


# =============================================================================
# SECTION 5 -- _validate_inputs
# =============================================================================

class TestValidateInputs:
    def test_valid_inputs(self):
        _validate_inputs([0.5, 0.7], [1.0, 0.0])

    def test_empty_confidences_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            _validate_inputs([], [])

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="equal length"):
            _validate_inputs([0.5, 0.7], [1.0])

    def test_confidence_not_list_raises(self):
        with pytest.raises(TypeError, match="confidences must be a list or tuple"):
            _validate_inputs("bad", [1.0])

    def test_outcomes_not_list_raises(self):
        with pytest.raises(TypeError, match="outcomes must be a list or tuple"):
            _validate_inputs([0.5], "bad")

    def test_confidence_nan_raises(self):
        with pytest.raises(ValueError, match="finite"):
            _validate_inputs([float("nan")], [1.0])

    def test_confidence_inf_raises(self):
        with pytest.raises(ValueError, match="finite"):
            _validate_inputs([float("inf")], [1.0])

    def test_confidence_negative_raises(self):
        with pytest.raises(ValueError, match=r"\[0, 1\]"):
            _validate_inputs([-0.1], [1.0])

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValueError, match=r"\[0, 1\]"):
            _validate_inputs([1.1], [1.0])

    def test_outcome_nan_raises(self):
        with pytest.raises(ValueError, match="finite"):
            _validate_inputs([0.5], [float("nan")])

    def test_outcome_negative_raises(self):
        with pytest.raises(ValueError, match=r"\[0, 1\]"):
            _validate_inputs([0.5], [-0.1])

    def test_outcome_above_one_raises(self):
        with pytest.raises(ValueError, match=r"\[0, 1\]"):
            _validate_inputs([0.5], [1.1])

    def test_confidence_string_element_raises(self):
        with pytest.raises(TypeError, match="confidences.*must be numeric"):
            _validate_inputs(["bad"], [1.0])

    def test_outcome_string_element_raises(self):
        with pytest.raises(TypeError, match="outcomes.*must be numeric"):
            _validate_inputs([0.5], ["bad"])

    def test_integers_accepted(self):
        _validate_inputs([0, 1], [1, 0])

    def test_tuple_inputs_accepted(self):
        _validate_inputs((0.5, 0.7), (1.0, 0.0))


# =============================================================================
# SECTION 6 -- compute_ece BASIC
# =============================================================================

class TestComputeEceBasic:
    def test_returns_ece_result(self):
        confs, outs = _perfectly_calibrated()
        result = compute_ece(confs, outs)
        assert isinstance(result, ECEResult)

    def test_n_samples(self):
        confs, outs = _perfectly_calibrated(50)
        result = compute_ece(confs, outs)
        assert result.n_samples == 50

    def test_ece_non_negative(self):
        confs, outs = _binary_outcomes()
        result = compute_ece(confs, outs)
        assert result.ece >= 0.0

    def test_ece_at_most_one(self):
        confs, outs = _completely_miscalibrated()
        result = compute_ece(confs, outs)
        assert result.ece <= 1.0

    def test_ece_finite(self):
        confs, outs = _binary_outcomes()
        result = compute_ece(confs, outs)
        assert math.isfinite(result.ece)

    def test_max_bin_error_non_negative(self):
        confs, outs = _binary_outcomes()
        result = compute_ece(confs, outs)
        assert result.max_bin_error >= 0.0

    def test_bin_statistics_is_tuple(self):
        confs, outs = _binary_outcomes()
        result = compute_ece(confs, outs)
        assert isinstance(result.bin_statistics, tuple)

    def test_bin_statistics_entries(self):
        confs, outs = _binary_outcomes()
        result = compute_ece(confs, outs)
        for bs in result.bin_statistics:
            assert isinstance(bs, BinStatistics)


# =============================================================================
# SECTION 7 -- PERFECT CALIBRATION
# =============================================================================

class TestPerfectCalibration:
    def test_ece_near_zero(self):
        confs, outs = _perfectly_calibrated(200)
        result = compute_ece(confs, outs)
        assert result.ece < 0.02

    def test_is_calibrated(self):
        confs, outs = _perfectly_calibrated(200)
        result = compute_ece(confs, outs)
        assert result.is_calibrated is True

    def test_all_bins_low_error(self):
        confs, outs = _perfectly_calibrated(200)
        result = compute_ece(confs, outs)
        for bs in result.bin_statistics:
            assert bs.abs_error < 0.1


# =============================================================================
# SECTION 8 -- COMPLETE MISCALIBRATION
# =============================================================================

class TestCompleteMiscalibration:
    def test_high_ece(self):
        confs, outs = _completely_miscalibrated()
        result = compute_ece(confs, outs)
        assert result.ece > 0.5

    def test_not_calibrated(self):
        confs, outs = _completely_miscalibrated()
        result = compute_ece(confs, outs)
        assert result.is_calibrated is False

    def test_ece_equals_confidence_minus_accuracy(self):
        """All conf=0.9, all outcome=0.0 → ECE = 0.9."""
        confs, outs = _completely_miscalibrated(100)
        result = compute_ece(confs, outs)
        assert result.ece == pytest.approx(0.9, abs=0.01)


# =============================================================================
# SECTION 9 -- SMALL INPUTS
# =============================================================================

class TestSmallInputs:
    def test_single_sample(self):
        result = compute_ece([0.8], [1.0])
        assert isinstance(result, ECEResult)
        assert result.n_samples == 1

    def test_two_samples(self):
        result = compute_ece([0.3, 0.7], [0.0, 1.0])
        assert result.n_samples == 2

    def test_three_samples(self):
        result = compute_ece([0.2, 0.5, 0.9], [0.0, 1.0, 1.0])
        assert result.n_samples == 3
        assert result.ece >= 0.0

    def test_fewer_samples_than_bins(self):
        """With n < N_BINS, should still work correctly."""
        result = compute_ece([0.5] * 5, [1.0] * 5)
        assert result.n_samples == 5
        assert result.n_bins_used >= 1

    def test_single_sample_perfect(self):
        result = compute_ece([0.8], [0.8])
        assert result.ece == pytest.approx(0.0, abs=1e-10)

    def test_single_sample_imperfect(self):
        result = compute_ece([0.9], [0.0])
        assert result.ece == pytest.approx(0.9, abs=0.01)


# =============================================================================
# SECTION 10 -- BIN STRUCTURE
# =============================================================================

class TestBinStructure:
    def test_n_bins_used_at_most_n_bins(self):
        confs, outs = _binary_outcomes(200)
        result = compute_ece(confs, outs)
        assert result.n_bins_used <= N_BINS

    def test_bin_weights_sum_to_one(self):
        confs, outs = _binary_outcomes(200)
        result = compute_ece(confs, outs)
        total_weight = sum(bs.bin_weight for bs in result.bin_statistics)
        assert total_weight == pytest.approx(1.0, abs=1e-10)

    def test_bin_samples_sum_to_n(self):
        confs, outs = _binary_outcomes(200)
        result = compute_ece(confs, outs)
        total_samples = sum(bs.n_samples for bs in result.bin_statistics)
        assert total_samples == 200

    def test_bins_sorted_by_confidence(self):
        """Bins should be ordered by increasing average confidence."""
        confs, outs = _binary_outcomes(200)
        result = compute_ece(confs, outs)
        avg_confs = [bs.avg_confidence for bs in result.bin_statistics]
        assert avg_confs == sorted(avg_confs)

    def test_bin_index_sequential(self):
        confs, outs = _binary_outcomes(200)
        result = compute_ece(confs, outs)
        for i, bs in enumerate(result.bin_statistics):
            assert bs.bin_index == i

    def test_each_bin_has_positive_samples(self):
        confs, outs = _binary_outcomes(200)
        result = compute_ece(confs, outs)
        for bs in result.bin_statistics:
            assert bs.n_samples >= MIN_SAMPLES

    def test_abs_error_matches_diff(self):
        confs, outs = _binary_outcomes(200)
        result = compute_ece(confs, outs)
        for bs in result.bin_statistics:
            expected = abs(bs.avg_confidence - bs.avg_accuracy)
            assert bs.abs_error == pytest.approx(expected, abs=1e-14)

    def test_max_bin_error_is_max(self):
        confs, outs = _binary_outcomes(200)
        result = compute_ece(confs, outs)
        max_err = max(bs.abs_error for bs in result.bin_statistics)
        assert result.max_bin_error == pytest.approx(max_err, abs=1e-14)


# =============================================================================
# SECTION 11 -- CONFIDENCE CLAMPING
# =============================================================================

class TestConfidenceClamping:
    def test_zero_confidence_clamped(self):
        result = compute_ece([0.0, 0.5], [0.0, 1.0])
        assert isinstance(result, ECEResult)

    def test_one_confidence_clamped(self):
        result = compute_ece([1.0, 0.5], [1.0, 0.0])
        assert isinstance(result, ECEResult)

    def test_boundary_values_no_error(self):
        result = compute_ece([0.0, 1.0], [0.0, 1.0])
        assert result.ece < 0.02


# =============================================================================
# SECTION 12 -- IS_CALIBRATED FLAG
# =============================================================================

class TestIsCalibratedFlag:
    def test_calibrated_when_ece_low(self):
        confs, outs = _perfectly_calibrated(200)
        result = compute_ece(confs, outs)
        assert result.is_calibrated is True
        assert result.ece < ECE_HARD_GATE

    def test_not_calibrated_when_ece_high(self):
        confs, outs = _completely_miscalibrated()
        result = compute_ece(confs, outs)
        assert result.is_calibrated is False
        assert result.ece >= ECE_HARD_GATE

    def test_boundary_ece_exact_gate(self):
        """ECE exactly at gate → NOT calibrated (strict <)."""
        r = ECEResult(
            ece=ECE_HARD_GATE, n_bins_used=10, n_samples=100,
            max_bin_error=0.05, bin_statistics=(), is_calibrated=False,
        )
        assert r.is_calibrated is False


# =============================================================================
# SECTION 13 -- compute_ece_scalar
# =============================================================================

class TestComputeEceScalar:
    def test_returns_float(self):
        confs, outs = _binary_outcomes()
        result = compute_ece_scalar(confs, outs)
        assert isinstance(result, float)

    def test_matches_compute_ece(self):
        confs, outs = _binary_outcomes()
        full = compute_ece(confs, outs)
        scalar = compute_ece_scalar(confs, outs)
        assert scalar == full.ece

    def test_perfect_calibration(self):
        confs, outs = _perfectly_calibrated(200)
        assert compute_ece_scalar(confs, outs) < 0.02

    def test_miscalibration(self):
        confs, outs = _completely_miscalibrated()
        assert compute_ece_scalar(confs, outs) > 0.5

    def test_propagates_errors(self):
        with pytest.raises(ValueError, match="must not be empty"):
            compute_ece_scalar([], [])

    def test_propagates_type_errors(self):
        with pytest.raises(TypeError):
            compute_ece_scalar("bad", [1.0])


# =============================================================================
# SECTION 14 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_same_inputs_same_output(self):
        confs, outs = _binary_outcomes(100)
        r1 = compute_ece(confs, outs)
        r2 = compute_ece(confs, outs)
        assert r1.ece == r2.ece
        assert r1.max_bin_error == r2.max_bin_error
        assert r1.n_bins_used == r2.n_bins_used

    def test_scalar_deterministic(self):
        confs, outs = _binary_outcomes(100)
        results = [compute_ece_scalar(confs, outs) for _ in range(10)]
        assert len(set(results)) == 1

    def test_bin_statistics_deterministic(self):
        confs, outs = _binary_outcomes(100)
        r1 = compute_ece(confs, outs)
        r2 = compute_ece(confs, outs)
        assert len(r1.bin_statistics) == len(r2.bin_statistics)
        for b1, b2 in zip(r1.bin_statistics, r2.bin_statistics):
            assert b1 == b2

    def test_order_independence_equal_confidence(self):
        """When confidences are identical, ECE should be identical
        regardless of outcome ordering (bins get same aggregate stats)."""
        c = [0.5] * 20
        o1 = [1.0] * 10 + [0.0] * 10
        o2 = [0.0] * 10 + [1.0] * 10
        assert compute_ece_scalar(c, o1) == compute_ece_scalar(c, o2)


# =============================================================================
# SECTION 15 -- EDGE CASES
# =============================================================================

class TestEdgeCases:
    def test_all_same_confidence(self):
        result = compute_ece([0.5] * 100, [1.0 if i % 2 == 0 else 0.0 for i in range(100)])
        assert math.isfinite(result.ece)

    def test_all_same_outcome(self):
        confs = [(i + 1) / 101 for i in range(100)]
        result = compute_ece(confs, [1.0] * 100)
        assert math.isfinite(result.ece)

    def test_all_zeros(self):
        result = compute_ece([0.0] * 50, [0.0] * 50)
        assert math.isfinite(result.ece)

    def test_all_ones(self):
        result = compute_ece([1.0] * 50, [1.0] * 50)
        assert math.isfinite(result.ece)

    def test_soft_labels(self):
        """Outcomes can be continuous in [0, 1], not just binary."""
        confs = [0.3, 0.5, 0.7]
        outs = [0.25, 0.55, 0.65]
        result = compute_ece(confs, outs)
        assert result.ece < 0.10

    def test_large_input(self):
        n = 10_000
        confs = [(i % 100) / 100.0 for i in range(n)]
        outs = [1.0 if i % 3 == 0 else 0.0 for i in range(n)]
        result = compute_ece(confs, outs)
        assert math.isfinite(result.ece)
        assert result.n_samples == n

    def test_integer_inputs(self):
        result = compute_ece([0, 1, 0, 1], [0, 1, 1, 0])
        assert math.isfinite(result.ece)


# =============================================================================
# SECTION 16 -- ECE MATHEMATICAL PROPERTIES
# =============================================================================

class TestEceMathProperties:
    def test_ece_increases_with_miscalibration(self):
        """More miscalibrated → higher ECE."""
        good_c = [0.3, 0.5, 0.7, 0.9] * 25
        good_o = [0.0, 1.0, 1.0, 1.0] * 25
        bad_c = [0.9] * 100
        bad_o = [0.0] * 100
        ece_good = compute_ece_scalar(good_c, good_o)
        ece_bad = compute_ece_scalar(bad_c, bad_o)
        assert ece_bad > ece_good

    def test_ece_symmetric_around_accuracy(self):
        """conf=0.8 with outcome=0.6 and conf=0.6 with outcome=0.8
        should produce similar per-bin errors."""
        r1 = compute_ece([0.8] * 50, [0.6] * 50)
        r2 = compute_ece([0.6] * 50, [0.8] * 50)
        assert r1.ece == pytest.approx(r2.ece, abs=0.01)

    def test_ece_weighted_sum_correct(self):
        """Verify ECE = sum(bin_weight * abs_error) manually."""
        confs, outs = _binary_outcomes(200)
        result = compute_ece(confs, outs)
        manual_ece = sum(bs.bin_weight * bs.abs_error for bs in result.bin_statistics)
        assert result.ece == pytest.approx(manual_ece, abs=1e-14)

    def test_max_bin_error_gte_ece(self):
        """MCE >= ECE always (max >= weighted average)."""
        confs, outs = _binary_outcomes(200)
        result = compute_ece(confs, outs)
        assert result.max_bin_error >= result.ece - 1e-14


# =============================================================================
# SECTION 17 -- IMPORT CONTRACT
# =============================================================================

class TestImportContract:
    def test_import_from_module(self):
        from jarvis.metrics.ece_calculator import compute_ece, ECEResult
        assert callable(compute_ece)
        assert ECEResult is not None

    def test_import_from_package(self):
        from jarvis.metrics import compute_ece, ECEResult, BinStatistics
        assert callable(compute_ece)
        assert ECEResult is not None
        assert BinStatistics is not None

    def test_import_constants_from_package(self):
        from jarvis.metrics import (
            N_BINS, MIN_SAMPLES, ECE_HARD_GATE,
            CONFIDENCE_FLOOR, CONFIDENCE_CEILING,
        )
        assert N_BINS == 10
        assert ECE_HARD_GATE == 0.05

    def test_import_scalar_from_package(self):
        from jarvis.metrics import compute_ece_scalar
        assert callable(compute_ece_scalar)


# =============================================================================
# SECTION 18 -- MUTANT KILLERS
# =============================================================================

class TestMutantKillers:
    def test_ece_not_negated(self):
        """Kills: return -ece or ece *= -1."""
        confs, outs = _completely_miscalibrated()
        result = compute_ece(confs, outs)
        assert result.ece > 0.0

    def test_abs_error_not_signed(self):
        """Kills: abs() removal → negative errors."""
        confs, outs = _binary_outcomes(200)
        result = compute_ece(confs, outs)
        for bs in result.bin_statistics:
            assert bs.abs_error >= 0.0

    def test_bin_weight_uses_division(self):
        """Kills: bin_weight = bin_n * n (multiply instead of divide)."""
        confs, outs = _binary_outcomes(200)
        result = compute_ece(confs, outs)
        for bs in result.bin_statistics:
            assert 0.0 < bs.bin_weight <= 1.0

    def test_is_calibrated_uses_less_than(self):
        """Kills: < mutated to <= or > in is_calibrated."""
        r_low = compute_ece([0.01] * 100, [0.01] * 100)
        assert r_low.is_calibrated is True
        r_high = compute_ece([0.9] * 100, [0.0] * 100)
        assert r_high.is_calibrated is False

    def test_ece_accumulation_not_zeroed(self):
        """Kills: ece = 0.0 never updated (loop skipped)."""
        confs, outs = _completely_miscalibrated()
        assert compute_ece_scalar(confs, outs) > 0.0

    def test_sort_key_is_confidence_not_outcome(self):
        """Kills: sort by outcome instead of confidence."""
        confs = [0.9, 0.1, 0.5, 0.3, 0.7] * 20
        outs = [0.1, 0.9, 0.5, 0.7, 0.3] * 20
        result = compute_ece(confs, outs)
        # Bins should be sorted by confidence
        avg_confs = [bs.avg_confidence for bs in result.bin_statistics]
        assert avg_confs == sorted(avg_confs)

    def test_clamping_direction_correct(self):
        """Kills: floor/ceiling swapped in _clamp_confidence."""
        assert _clamp_confidence(0.0) == CONFIDENCE_FLOOR
        assert _clamp_confidence(1.0) == CONFIDENCE_CEILING
        assert CONFIDENCE_FLOOR < 0.5 < CONFIDENCE_CEILING

    def test_validate_rejects_out_of_range(self):
        """Kills: boundary check removed or inverted."""
        with pytest.raises(ValueError):
            _validate_inputs([1.5], [0.5])
        with pytest.raises(ValueError):
            _validate_inputs([0.5], [1.5])
        with pytest.raises(ValueError):
            _validate_inputs([-0.1], [0.5])
        with pytest.raises(ValueError):
            _validate_inputs([0.5], [-0.1])
