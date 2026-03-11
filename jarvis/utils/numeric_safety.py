# jarvis/utils/numeric_safety.py
# Version: 6.1.0
# Numerical safety utilities for the JARVIS platform.
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
from typing import List, Union

from jarvis.utils.exceptions import NumericalInstabilityError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PROB_FLOOR: float = 1e-6
_PROB_CEIL: float = 1.0 - 1e-6
_EPS: float = 1e-15
_NEAR_ZERO: float = 1e-15
_DIAG_FLOOR: float = 1e-12


def clip_probability(prob: float, context: str = "") -> float:
    """
    Clip a probability value to [1e-6, 1 - 1e-6].

    Raises NumericalInstabilityError if the input is NaN or Inf.

    Parameters
    ----------
    prob : float
        Probability value to clip.
    context : str
        Optional context string for error messages.

    Returns
    -------
    float
        Clipped probability in [1e-6, 1 - 1e-6].
    """
    check_nan_inf(prob, context or "clip_probability")
    if prob < _PROB_FLOOR:
        return _PROB_FLOOR
    if prob > _PROB_CEIL:
        return _PROB_CEIL
    return prob


def safe_divide(numerator: float, denominator: float, context: str = "") -> float:
    """
    Safe division with epsilon floor. Returns 0.0 if both values are near zero.

    Parameters
    ----------
    numerator : float
        Numerator of the division.
    denominator : float
        Denominator of the division.
    context : str
        Optional context string for error messages.

    Returns
    -------
    float
        Result of the division, or 0.0 if both near zero.
    """
    check_nan_inf(numerator, context or "safe_divide numerator")
    check_nan_inf(denominator, context or "safe_divide denominator")

    if abs(numerator) < _NEAR_ZERO and abs(denominator) < _NEAR_ZERO:
        return 0.0

    if abs(denominator) < _NEAR_ZERO:
        # Use epsilon floor to avoid division by zero
        denominator = _NEAR_ZERO if denominator >= 0 else -_NEAR_ZERO

    return numerator / denominator


def enforce_psd(matrix: List[List[float]]) -> List[List[float]]:
    """
    Enforce positive semi-definite property for a covariance matrix.

    Uses symmetrisation + diagonal floor approach (same as state_estimator.py).

    Parameters
    ----------
    matrix : List[List[float]]
        Square matrix to enforce PSD on.

    Returns
    -------
    List[List[float]]
        Symmetrised matrix with floored diagonal entries.
    """
    n: int = len(matrix)
    if n == 0:
        return []

    # Validate square
    for row in matrix:
        if len(row) != n:
            raise ValueError("Matrix must be square.")

    # Check for NaN/Inf
    for i in range(n):
        for j in range(n):
            if not math.isfinite(matrix[i][j]):
                raise NumericalInstabilityError(
                    f"enforce_psd: NaN/Inf at [{i}][{j}]"
                )

    # Symmetrise: M = (M + M^T) / 2
    sym: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            sym[i][j] = (matrix[i][j] + matrix[j][i]) * 0.5

    # Floor diagonal entries
    for i in range(n):
        if sym[i][i] < _DIAG_FLOOR:
            sym[i][i] = _DIAG_FLOOR

    return sym


def safe_matrix_inverse(
    matrix: List[List[float]], lambda_: float = 1e-6
) -> List[List[float]]:
    """
    Tikhonov-regularised matrix inverse via Gaussian elimination
    with partial pivoting.

    Computes (M + lambda * I)^{-1}.

    Parameters
    ----------
    matrix : List[List[float]]
        Square matrix to invert.
    lambda_ : float
        Tikhonov regularisation parameter (added to diagonal).

    Returns
    -------
    List[List[float]]
        Regularised inverse matrix.
    """
    n: int = len(matrix)
    if n == 0:
        return []

    # Validate square
    for row in matrix:
        if len(row) != n:
            raise ValueError("Matrix must be square.")

    # Build augmented matrix [M + lambda*I | I]
    aug: List[List[float]] = [
        [
            matrix[i][j] + (lambda_ if i == j else 0.0)
            for j in range(n)
        ]
        + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 / pivot
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [
        [aug[i][n + j] for j in range(n)] for i in range(n)
    ]
    return inv


def check_nan_inf(value: Union[float, List[float]], context: str) -> None:
    """
    Check for NaN or Inf values. Raises NumericalInstabilityError if found.

    Parameters
    ----------
    value : float or List[float]
        Value(s) to check.
    context : str
        Context string for error messages.

    Raises
    ------
    NumericalInstabilityError
        If any value is NaN or Inf.
    """
    if isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            if not math.isfinite(v):
                raise NumericalInstabilityError(
                    f"{context}: NaN/Inf at index {i}, value={v!r}"
                )
    else:
        if not math.isfinite(value):
            raise NumericalInstabilityError(
                f"{context}: NaN/Inf detected, value={value!r}"
            )
