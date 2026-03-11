# jarvis/utils/helpers.py
# Version: 6.1.0
# Calibration and statistical helper functions for the JARVIS platform.
#
# CONSTRAINTS
# -----------
# stdlib only: math, typing. No numpy. No scipy. No file I/O. No logging.
#
# DETERMINISM GUARANTEES
# ----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  All arithmetic deterministic (pure Python floating-point).
# DET-05  All branches pure functions of explicit inputs.

import math
from typing import List, Tuple


def compute_ece(
    confidences: List[float], outcomes: List[float], bins: int = 10
) -> float:
    """
    Expected Calibration Error via equal-width binning.

    Parameters
    ----------
    confidences : List[float]
        Predicted probabilities in [0, 1].
    outcomes : List[float]
        Binary outcomes (0.0 or 1.0).
    bins : int
        Number of equal-width bins.

    Returns
    -------
    float
        Weighted average of |accuracy - confidence| per bin.
    """
    n: int = len(confidences)
    if n == 0:
        return 0.0
    if len(outcomes) != n:
        raise ValueError("confidences and outcomes must have same length.")

    ece: float = 0.0
    for b in range(bins):
        lower: float = b / bins
        upper: float = (b + 1) / bins

        # Collect indices in this bin
        bin_confs: List[float] = []
        bin_outcomes: List[float] = []
        for i in range(n):
            # Include upper boundary only in the last bin
            if b == bins - 1:
                in_bin = lower <= confidences[i] <= upper
            else:
                in_bin = lower <= confidences[i] < upper
            if in_bin:
                bin_confs.append(confidences[i])
                bin_outcomes.append(outcomes[i])

        bin_size: int = len(bin_confs)
        if bin_size == 0:
            continue

        avg_conf: float = sum(bin_confs) / bin_size
        avg_acc: float = sum(bin_outcomes) / bin_size
        ece += (bin_size / n) * abs(avg_acc - avg_conf)

    return ece


def compute_mce(
    confidences: List[float], outcomes: List[float], bins: int = 10
) -> float:
    """
    Maximum Calibration Error.

    Parameters
    ----------
    confidences : List[float]
        Predicted probabilities in [0, 1].
    outcomes : List[float]
        Binary outcomes (0.0 or 1.0).
    bins : int
        Number of equal-width bins.

    Returns
    -------
    float
        Maximum |accuracy - confidence| across all non-empty bins.
    """
    n: int = len(confidences)
    if n == 0:
        return 0.0
    if len(outcomes) != n:
        raise ValueError("confidences and outcomes must have same length.")

    mce: float = 0.0
    for b in range(bins):
        lower: float = b / bins
        upper: float = (b + 1) / bins

        bin_confs: List[float] = []
        bin_outcomes: List[float] = []
        for i in range(n):
            if b == bins - 1:
                in_bin = lower <= confidences[i] <= upper
            else:
                in_bin = lower <= confidences[i] < upper
            if in_bin:
                bin_confs.append(confidences[i])
                bin_outcomes.append(outcomes[i])

        bin_size: int = len(bin_confs)
        if bin_size == 0:
            continue

        avg_conf: float = sum(bin_confs) / bin_size
        avg_acc: float = sum(bin_outcomes) / bin_size
        gap: float = abs(avg_acc - avg_conf)
        if gap > mce:
            mce = gap

    return mce


def compute_brier_score(
    confidences: List[float], outcomes: List[float]
) -> float:
    """
    Brier Score: mean squared error of probability predictions.

    Parameters
    ----------
    confidences : List[float]
        Predicted probabilities in [0, 1].
    outcomes : List[float]
        Binary outcomes (0.0 or 1.0).

    Returns
    -------
    float
        Mean of (confidence - outcome)^2.
    """
    n: int = len(confidences)
    if n == 0:
        return 0.0
    if len(outcomes) != n:
        raise ValueError("confidences and outcomes must have same length.")

    total: float = 0.0
    for i in range(n):
        diff: float = confidences[i] - outcomes[i]
        total += diff * diff
    return total / n


def ks_statistic(
    sample1: List[float], sample2: List[float]
) -> Tuple[float, float]:
    """
    Kolmogorov-Smirnov two-sample statistic.

    Computes the maximum absolute difference between the empirical
    cumulative distribution functions of two samples.

    Parameters
    ----------
    sample1 : List[float]
        First sample.
    sample2 : List[float]
        Second sample.

    Returns
    -------
    Tuple[float, float]
        (ks_statistic, approximate_p_value).
        p_value is computed via the asymptotic formula.
    """
    n1: int = len(sample1)
    n2: int = len(sample2)

    if n1 == 0 or n2 == 0:
        return (0.0, 1.0)

    # Merge and sort all values
    sorted1: List[float] = sorted(sample1)
    sorted2: List[float] = sorted(sample2)

    # Compute KS statistic by walking through both sorted arrays
    all_values: List[float] = sorted(set(sorted1 + sorted2))

    ks: float = 0.0
    for val in all_values:
        # Empirical CDF for sample1: fraction of values <= val
        cdf1: float = _ecdf_at(sorted1, val)
        cdf2: float = _ecdf_at(sorted2, val)
        diff: float = abs(cdf1 - cdf2)
        if diff > ks:
            ks = diff

    # Asymptotic p-value approximation
    # Using the formula: p ≈ 2 * exp(-2 * (ks * sqrt(n_eff))^2)
    # where n_eff = n1*n2/(n1+n2)
    n_eff: float = (n1 * n2) / (n1 + n2)
    lambda_val: float = ks * math.sqrt(n_eff)
    if lambda_val == 0.0:
        p_value: float = 1.0
    else:
        p_value = 2.0 * math.exp(-2.0 * lambda_val * lambda_val)
        # Clamp to [0, 1]
        if p_value > 1.0:
            p_value = 1.0
        if p_value < 0.0:
            p_value = 0.0

    return (ks, p_value)


def _ecdf_at(sorted_sample: List[float], value: float) -> float:
    """
    Empirical CDF at a given value for a sorted sample.

    Returns the fraction of sample values <= value.
    """
    n: int = len(sorted_sample)
    if n == 0:
        return 0.0

    # Binary search for the rightmost position <= value
    count: int = 0
    lo: int = 0
    hi: int = n
    while lo < hi:
        mid: int = (lo + hi) // 2
        if sorted_sample[mid] <= value:
            lo = mid + 1
        else:
            hi = mid
    count = lo

    return count / n


def wasserstein_distance(
    dist1: List[float], dist2: List[float]
) -> float:
    """
    Earth Mover's Distance (1D Wasserstein) via sorted arrays.

    For 1D distributions, the Wasserstein-1 distance equals:
        W_1 = (1/n) * sum(|sorted1[i] - sorted2[i]|)
    when both distributions have the same number of samples.

    For unequal sizes, uses linear interpolation of the empirical CDFs.

    Parameters
    ----------
    dist1 : List[float]
        First distribution sample.
    dist2 : List[float]
        Second distribution sample.

    Returns
    -------
    float
        1D Wasserstein distance.
    """
    n1: int = len(dist1)
    n2: int = len(dist2)

    if n1 == 0 or n2 == 0:
        return 0.0

    sorted1: List[float] = sorted(dist1)
    sorted2: List[float] = sorted(dist2)

    if n1 == n2:
        # Simple case: sum of absolute differences of order statistics
        total: float = 0.0
        for i in range(n1):
            total += abs(sorted1[i] - sorted2[i])
        return total / n1

    # General case: integrate |CDF1 - CDF2| over all values
    # Merge all unique breakpoints from both sorted arrays
    all_vals: List[float] = sorted(sorted1 + sorted2)

    total = 0.0
    prev_val: float = all_vals[0]
    prev_cdf1: float = _ecdf_at(sorted1, prev_val)
    prev_cdf2: float = _ecdf_at(sorted2, prev_val)

    for i in range(1, len(all_vals)):
        curr_val: float = all_vals[i]
        curr_cdf1: float = _ecdf_at(sorted1, curr_val)
        curr_cdf2: float = _ecdf_at(sorted2, curr_val)

        # Trapezoidal integration of |CDF1 - CDF2|
        width: float = curr_val - prev_val
        height: float = (abs(prev_cdf1 - prev_cdf2) + abs(curr_cdf1 - curr_cdf2)) * 0.5
        total += width * height

        prev_val = curr_val
        prev_cdf1 = curr_cdf1
        prev_cdf2 = curr_cdf2

    return total
