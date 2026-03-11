# tests/unit/utils/test_helpers.py
# Unit tests for jarvis/utils/helpers.py

import math

import pytest

from jarvis.utils.helpers import (
    compute_ece,
    compute_mce,
    compute_brier_score,
    ks_statistic,
    wasserstein_distance,
)


# ---------------------------------------------------------------------------
# compute_ece
# ---------------------------------------------------------------------------

class TestComputeECE:

    def test_known_calibration(self):
        """Perfectly calibrated predictions have ECE = 0."""
        # All predictions at 0.5, half are 1, half are 0
        confidences = [0.5, 0.5, 0.5, 0.5]
        outcomes = [1.0, 0.0, 1.0, 0.0]
        ece = compute_ece(confidences, outcomes, bins=10)
        assert ece == pytest.approx(0.0, abs=1e-10)

    def test_empty_input(self):
        assert compute_ece([], []) == 0.0

    def test_single_element(self):
        ece = compute_ece([0.9], [1.0], bins=10)
        # Bin [0.9, 1.0]: avg_conf=0.9, avg_acc=1.0, gap=0.1, weight=1.0
        assert ece == pytest.approx(0.1, abs=1e-10)

    def test_miscalibrated_high(self):
        """High confidence, all wrong: ECE should be high."""
        confidences = [0.95, 0.95, 0.95, 0.95]
        outcomes = [0.0, 0.0, 0.0, 0.0]
        ece = compute_ece(confidences, outcomes, bins=10)
        assert ece == pytest.approx(0.95, abs=1e-10)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            compute_ece([0.5], [1.0, 0.0])


# ---------------------------------------------------------------------------
# compute_mce
# ---------------------------------------------------------------------------

class TestComputeMCE:

    def test_known_values(self):
        """MCE should be the max gap across bins."""
        confidences = [0.1, 0.9]
        outcomes = [0.0, 0.0]
        mce = compute_mce(confidences, outcomes, bins=10)
        # Bin with 0.9: gap = |0.0 - 0.9| = 0.9
        assert mce == pytest.approx(0.9, abs=1e-10)

    def test_empty_input(self):
        assert compute_mce([], []) == 0.0

    def test_perfect_calibration(self):
        confidences = [0.5, 0.5, 0.5, 0.5]
        outcomes = [1.0, 0.0, 1.0, 0.0]
        mce = compute_mce(confidences, outcomes, bins=10)
        assert mce == pytest.approx(0.0, abs=1e-10)


# ---------------------------------------------------------------------------
# compute_brier_score
# ---------------------------------------------------------------------------

class TestComputeBrierScore:

    def test_perfect_predictions(self):
        """Perfect predictions yield Brier score = 0."""
        confidences = [1.0, 0.0, 1.0, 0.0]
        outcomes = [1.0, 0.0, 1.0, 0.0]
        assert compute_brier_score(confidences, outcomes) == pytest.approx(0.0)

    def test_worst_predictions(self):
        """Worst predictions yield Brier score = 1."""
        confidences = [0.0, 1.0, 0.0, 1.0]
        outcomes = [1.0, 0.0, 1.0, 0.0]
        assert compute_brier_score(confidences, outcomes) == pytest.approx(1.0)

    def test_empty_input(self):
        assert compute_brier_score([], []) == 0.0

    def test_midpoint_predictions(self):
        """All 0.5 predictions against 0/1 outcomes yield 0.25."""
        confidences = [0.5, 0.5]
        outcomes = [0.0, 1.0]
        assert compute_brier_score(confidences, outcomes) == pytest.approx(0.25)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            compute_brier_score([0.5], [1.0, 0.0])


# ---------------------------------------------------------------------------
# ks_statistic
# ---------------------------------------------------------------------------

class TestKSStatistic:

    def test_identical_samples(self):
        """Identical samples should have KS = 0, p = 1."""
        sample = [1.0, 2.0, 3.0, 4.0, 5.0]
        ks, p = ks_statistic(sample, sample)
        assert ks == pytest.approx(0.0)
        assert p == pytest.approx(1.0)

    def test_completely_different_samples(self):
        """Non-overlapping samples should have high KS."""
        sample1 = [float(i) for i in range(20)]
        sample2 = [float(i + 100) for i in range(20)]
        ks, p = ks_statistic(sample1, sample2)
        assert ks == pytest.approx(1.0)
        assert p < 0.05

    def test_empty_sample(self):
        ks, p = ks_statistic([], [1.0, 2.0])
        assert ks == 0.0
        assert p == 1.0

    def test_both_empty(self):
        ks, p = ks_statistic([], [])
        assert ks == 0.0
        assert p == 1.0

    def test_p_value_in_range(self):
        sample1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        sample2 = [1.5, 2.5, 3.5, 4.5, 5.5]
        ks, p = ks_statistic(sample1, sample2)
        assert 0.0 <= ks <= 1.0
        assert 0.0 <= p <= 1.0


# ---------------------------------------------------------------------------
# wasserstein_distance
# ---------------------------------------------------------------------------

class TestWassersteinDistance:

    def test_identical_distributions(self):
        dist = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert wasserstein_distance(dist, dist) == pytest.approx(0.0)

    def test_different_distributions(self):
        dist1 = [0.0, 0.0, 0.0]
        dist2 = [1.0, 1.0, 1.0]
        wd = wasserstein_distance(dist1, dist2)
        assert wd == pytest.approx(1.0)

    def test_shifted_distributions(self):
        dist1 = [1.0, 2.0, 3.0]
        dist2 = [2.0, 3.0, 4.0]
        wd = wasserstein_distance(dist1, dist2)
        assert wd == pytest.approx(1.0)

    def test_empty_distributions(self):
        assert wasserstein_distance([], []) == 0.0
        assert wasserstein_distance([1.0], []) == 0.0
        assert wasserstein_distance([], [1.0]) == 0.0

    def test_single_element(self):
        wd = wasserstein_distance([0.0], [5.0])
        assert wd == pytest.approx(5.0)

    def test_non_negative(self):
        dist1 = [1.0, 3.0, 5.0]
        dist2 = [2.0, 4.0, 6.0]
        assert wasserstein_distance(dist1, dist2) >= 0.0


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:

    def test_ece_deterministic(self):
        confs = [0.1, 0.4, 0.6, 0.9]
        outs = [0.0, 0.0, 1.0, 1.0]
        r1 = compute_ece(confs, outs)
        r2 = compute_ece(confs, outs)
        assert r1 == r2

    def test_brier_deterministic(self):
        confs = [0.3, 0.7]
        outs = [0.0, 1.0]
        r1 = compute_brier_score(confs, outs)
        r2 = compute_brier_score(confs, outs)
        assert r1 == r2

    def test_ks_deterministic(self):
        s1 = [1.0, 2.0, 3.0]
        s2 = [1.5, 2.5, 3.5]
        r1 = ks_statistic(s1, s2)
        r2 = ks_statistic(s1, s2)
        assert r1 == r2

    def test_wasserstein_deterministic(self):
        d1 = [1.0, 2.0, 3.0]
        d2 = [2.0, 3.0, 4.0]
        r1 = wasserstein_distance(d1, d2)
        r2 = wasserstein_distance(d1, d2)
        assert r1 == r2
