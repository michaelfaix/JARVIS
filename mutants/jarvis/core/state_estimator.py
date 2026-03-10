# =============================================================================
# JARVIS v6.0.1 — SESSION 05, PHASE 5.5: STATE ESTIMATOR
# File:   jarvis/core/state_estimator.py
# Authority: JARVIS FAS v6.0.1 — 02-05_CORE.md, S05 section
# Phase:  5.5 — StateEstimator (Kalman filter, 12-dimensional latent state)
# =============================================================================
#
# SCOPE (Phase 5.5)
# -----------------
# Implements:
#   - Matrix utilities (pure stdlib, no numpy)
#   - KalmanState  dataclass (frozen=True) — internal covariance carrier
#   - StateEstimator class
#       * predict(state)                  -> LatentState
#       * update(state, observation)      -> LatentState
#       * get_covariance()                -> List[List[float]]  (12x12)
#       * reset()                         -> None
#
# CONSTRAINTS
# -----------
# stdlib only: dataclasses, math, typing.
# No numpy. No scipy. No pandas. No random. No datetime.now().
# No file I/O. No logging.
#
# DETERMINISM GUARANTEES
# ----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects beyond updating internal covariance state.
# DET-04  All arithmetic deterministic (pure Python floating-point).
# DET-05  All branches pure functions of explicit inputs.
# DET-06  No datetime.now().
#
# KALMAN FILTER SPECIFICATION
# ----------------------------
# State dimension:  n = 12  (matches LatentState field count)
# Observation dim:  m = 12  (full-state observation model)
#
# Predict step:
#   x_pred = F * x_t          (state transition: identity = no drift model)
#   P_pred = F * P * F^T + Q  (covariance prediction)
#
# Update step:
#   y      = z - H * x_pred   (innovation / residual)
#   S      = H * P_pred * H^T + R   (innovation covariance)
#   K      = P_pred * H^T * S^{-1}  (Kalman gain)
#   x_upd  = x_pred + K * y   (state update)
#   P_upd  = (I - K * H) * P_pred   (covariance update — Joseph form)
#
# Default matrices:
#   F = I_12  (identity — random-walk prior)
#   H = I_12  (full-state observation)
#   Q = q * I_12  (process noise, q = 1e-4)
#   R = r * I_12  (observation noise, r = 1e-2)
#   P_0 = p0 * I_12  (initial covariance, p0 = 1.0)
#
# DIVERGENCE DETECTION
# ---------------------
# After each update, the condition number of P is estimated.
# If cond(P) > DIVERGENCE_THRESHOLD (1e6), the filter is reset to
# the initial covariance P_0. This prevents numerical blow-up.
#
# TIKHONOV REGULARISATION
# ------------------------
# All matrix inversions use Tikhonov regularisation:
#   (M + lambda * I)^{-1}  with lambda = TIKHONOV_LAMBDA = 1e-6
# This prevents singular matrix errors.
#
# STDLIB MATRIX INVERSION
# -----------------------
# For a 12x12 system we use Gaussian elimination with partial pivoting.
# No numpy, no scipy. Pure Python. O(n^3) — acceptable for n=12.
#
# INVARIANTS
# ----------
# INV-P55-01  P is always symmetric (enforced after every update).
# INV-P55-02  P diagonal entries are always > 0 (floored at epsilon).
# INV-P55-03  predict() returns a valid LatentState.
# INV-P55-04  update() returns a valid LatentState.
# INV-P55-05  get_covariance() returns a deep copy of P (12x12).
# INV-P55-06  Divergence reset restores P to P_0.
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from jarvis.core.state_layer import LatentState


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Latent state dimension.
_DIM: int = 12

#: Divergence threshold for condition number of P.
DIVERGENCE_THRESHOLD: float = 1e6

#: Tikhonov regularisation lambda for matrix inversion.
TIKHONOV_LAMBDA: float = 1e-6

#: Default process noise magnitude.
_DEFAULT_Q: float = 1e-4

#: Default observation noise magnitude.
_DEFAULT_R: float = 1e-2

#: Default initial covariance diagonal magnitude.
_DEFAULT_P0: float = 1.0

#: Minimum diagonal value for P (positivity floor).
_P_MIN_DIAG: float = 1e-12

#: Epsilon for numerical guards.
_EPS: float = 1e-15

# ---------------------------------------------------------------------------
# LatentState field order (must match LatentState dataclass field order).
# ---------------------------------------------------------------------------
_FIELD_NAMES: Tuple[str, ...] = (
    "regime",
    "volatility",
    "trend_strength",
    "mean_reversion",
    "liquidity",
    "stress",
    "momentum",
    "drift",
    "noise",
    "regime_confidence",
    "stability",
    "prediction_uncertainty",
)
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore

# ---------------------------------------------------------------------------
# Pure-stdlib matrix utilities
# ---------------------------------------------------------------------------

def _identity(n: int) -> List[List[float]]:
    args = [n]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__identity__mutmut_orig, x__identity__mutmut_mutants, args, kwargs, None)

# ---------------------------------------------------------------------------
# Pure-stdlib matrix utilities
# ---------------------------------------------------------------------------

def x__identity__mutmut_orig(n: int) -> List[List[float]]:
    """Return an n x n identity matrix."""
    M: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        M[i][i] = 1.0
    return M

# ---------------------------------------------------------------------------
# Pure-stdlib matrix utilities
# ---------------------------------------------------------------------------

def x__identity__mutmut_1(n: int) -> List[List[float]]:
    """Return an n x n identity matrix."""
    M: List[List[float]] = None
    for i in range(n):
        M[i][i] = 1.0
    return M

# ---------------------------------------------------------------------------
# Pure-stdlib matrix utilities
# ---------------------------------------------------------------------------

def x__identity__mutmut_2(n: int) -> List[List[float]]:
    """Return an n x n identity matrix."""
    M: List[List[float]] = [[0.0] / n for _ in range(n)]
    for i in range(n):
        M[i][i] = 1.0
    return M

# ---------------------------------------------------------------------------
# Pure-stdlib matrix utilities
# ---------------------------------------------------------------------------

def x__identity__mutmut_3(n: int) -> List[List[float]]:
    """Return an n x n identity matrix."""
    M: List[List[float]] = [[1.0] * n for _ in range(n)]
    for i in range(n):
        M[i][i] = 1.0
    return M

# ---------------------------------------------------------------------------
# Pure-stdlib matrix utilities
# ---------------------------------------------------------------------------

def x__identity__mutmut_4(n: int) -> List[List[float]]:
    """Return an n x n identity matrix."""
    M: List[List[float]] = [[0.0] * n for _ in range(None)]
    for i in range(n):
        M[i][i] = 1.0
    return M

# ---------------------------------------------------------------------------
# Pure-stdlib matrix utilities
# ---------------------------------------------------------------------------

def x__identity__mutmut_5(n: int) -> List[List[float]]:
    """Return an n x n identity matrix."""
    M: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(None):
        M[i][i] = 1.0
    return M

# ---------------------------------------------------------------------------
# Pure-stdlib matrix utilities
# ---------------------------------------------------------------------------

def x__identity__mutmut_6(n: int) -> List[List[float]]:
    """Return an n x n identity matrix."""
    M: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        M[i][i] = None
    return M

# ---------------------------------------------------------------------------
# Pure-stdlib matrix utilities
# ---------------------------------------------------------------------------

def x__identity__mutmut_7(n: int) -> List[List[float]]:
    """Return an n x n identity matrix."""
    M: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        M[i][i] = 2.0
    return M

x__identity__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__identity__mutmut_1': x__identity__mutmut_1, 
    'x__identity__mutmut_2': x__identity__mutmut_2, 
    'x__identity__mutmut_3': x__identity__mutmut_3, 
    'x__identity__mutmut_4': x__identity__mutmut_4, 
    'x__identity__mutmut_5': x__identity__mutmut_5, 
    'x__identity__mutmut_6': x__identity__mutmut_6, 
    'x__identity__mutmut_7': x__identity__mutmut_7
}
x__identity__mutmut_orig.__name__ = 'x__identity'


def _scalar_diag(n: int, s: float) -> List[List[float]]:
    args = [n, s]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__scalar_diag__mutmut_orig, x__scalar_diag__mutmut_mutants, args, kwargs, None)


def x__scalar_diag__mutmut_orig(n: int, s: float) -> List[List[float]]:
    """Return an n x n diagonal matrix with s on the diagonal."""
    M: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        M[i][i] = s
    return M


def x__scalar_diag__mutmut_1(n: int, s: float) -> List[List[float]]:
    """Return an n x n diagonal matrix with s on the diagonal."""
    M: List[List[float]] = None
    for i in range(n):
        M[i][i] = s
    return M


def x__scalar_diag__mutmut_2(n: int, s: float) -> List[List[float]]:
    """Return an n x n diagonal matrix with s on the diagonal."""
    M: List[List[float]] = [[0.0] / n for _ in range(n)]
    for i in range(n):
        M[i][i] = s
    return M


def x__scalar_diag__mutmut_3(n: int, s: float) -> List[List[float]]:
    """Return an n x n diagonal matrix with s on the diagonal."""
    M: List[List[float]] = [[1.0] * n for _ in range(n)]
    for i in range(n):
        M[i][i] = s
    return M


def x__scalar_diag__mutmut_4(n: int, s: float) -> List[List[float]]:
    """Return an n x n diagonal matrix with s on the diagonal."""
    M: List[List[float]] = [[0.0] * n for _ in range(None)]
    for i in range(n):
        M[i][i] = s
    return M


def x__scalar_diag__mutmut_5(n: int, s: float) -> List[List[float]]:
    """Return an n x n diagonal matrix with s on the diagonal."""
    M: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(None):
        M[i][i] = s
    return M


def x__scalar_diag__mutmut_6(n: int, s: float) -> List[List[float]]:
    """Return an n x n diagonal matrix with s on the diagonal."""
    M: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        M[i][i] = None
    return M

x__scalar_diag__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__scalar_diag__mutmut_1': x__scalar_diag__mutmut_1, 
    'x__scalar_diag__mutmut_2': x__scalar_diag__mutmut_2, 
    'x__scalar_diag__mutmut_3': x__scalar_diag__mutmut_3, 
    'x__scalar_diag__mutmut_4': x__scalar_diag__mutmut_4, 
    'x__scalar_diag__mutmut_5': x__scalar_diag__mutmut_5, 
    'x__scalar_diag__mutmut_6': x__scalar_diag__mutmut_6
}
x__scalar_diag__mutmut_orig.__name__ = 'x__scalar_diag'


def _mat_add(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    args = [A, B]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__mat_add__mutmut_orig, x__mat_add__mutmut_mutants, args, kwargs, None)


def x__mat_add__mutmut_orig(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Element-wise matrix addition. A and B must have same dimensions."""
    n: int = len(A)
    m: int = len(A[0])
    return [[A[i][j] + B[i][j] for j in range(m)] for i in range(n)]


def x__mat_add__mutmut_1(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Element-wise matrix addition. A and B must have same dimensions."""
    n: int = None
    m: int = len(A[0])
    return [[A[i][j] + B[i][j] for j in range(m)] for i in range(n)]


def x__mat_add__mutmut_2(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Element-wise matrix addition. A and B must have same dimensions."""
    n: int = len(A)
    m: int = None
    return [[A[i][j] + B[i][j] for j in range(m)] for i in range(n)]


def x__mat_add__mutmut_3(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Element-wise matrix addition. A and B must have same dimensions."""
    n: int = len(A)
    m: int = len(A[0])
    return [[A[i][j] - B[i][j] for j in range(m)] for i in range(n)]


def x__mat_add__mutmut_4(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Element-wise matrix addition. A and B must have same dimensions."""
    n: int = len(A)
    m: int = len(A[0])
    return [[A[i][j] + B[i][j] for j in range(None)] for i in range(n)]


def x__mat_add__mutmut_5(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Element-wise matrix addition. A and B must have same dimensions."""
    n: int = len(A)
    m: int = len(A[0])
    return [[A[i][j] + B[i][j] for j in range(m)] for i in range(None)]

x__mat_add__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__mat_add__mutmut_1': x__mat_add__mutmut_1, 
    'x__mat_add__mutmut_2': x__mat_add__mutmut_2, 
    'x__mat_add__mutmut_3': x__mat_add__mutmut_3, 
    'x__mat_add__mutmut_4': x__mat_add__mutmut_4, 
    'x__mat_add__mutmut_5': x__mat_add__mutmut_5
}
x__mat_add__mutmut_orig.__name__ = 'x__mat_add'


def _mat_mul(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    args = [A, B]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__mat_mul__mutmut_orig, x__mat_mul__mutmut_mutants, args, kwargs, None)


def x__mat_mul__mutmut_orig(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            s: float = 0.0
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_1(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = None
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            s: float = 0.0
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_2(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = None
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            s: float = 0.0
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_3(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = None
    C: List[List[float]] = [[0.0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            s: float = 0.0
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_4(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = None
    for i in range(r):
        for j in range(c):
            s: float = 0.0
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_5(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] / c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            s: float = 0.0
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_6(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[1.0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            s: float = 0.0
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_7(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] * c for _ in range(None)]
    for i in range(r):
        for j in range(c):
            s: float = 0.0
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_8(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] * c for _ in range(r)]
    for i in range(None):
        for j in range(c):
            s: float = 0.0
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_9(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] * c for _ in range(r)]
    for i in range(r):
        for j in range(None):
            s: float = 0.0
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_10(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            s: float = None
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_11(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            s: float = 1.0
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_12(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            s: float = 0.0
            for l in range(None):
                s += A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_13(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            s: float = 0.0
            for l in range(k):
                s = A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_14(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            s: float = 0.0
            for l in range(k):
                s -= A[i][l] * B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_15(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            s: float = 0.0
            for l in range(k):
                s += A[i][l] / B[l][j]
            C[i][j] = s
    return C


def x__mat_mul__mutmut_16(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Matrix multiplication A @ B. A is (r x k), B is (k x c)."""
    r: int = len(A)
    k: int = len(A[0])
    c: int = len(B[0])
    C: List[List[float]] = [[0.0] * c for _ in range(r)]
    for i in range(r):
        for j in range(c):
            s: float = 0.0
            for l in range(k):
                s += A[i][l] * B[l][j]
            C[i][j] = None
    return C

x__mat_mul__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__mat_mul__mutmut_1': x__mat_mul__mutmut_1, 
    'x__mat_mul__mutmut_2': x__mat_mul__mutmut_2, 
    'x__mat_mul__mutmut_3': x__mat_mul__mutmut_3, 
    'x__mat_mul__mutmut_4': x__mat_mul__mutmut_4, 
    'x__mat_mul__mutmut_5': x__mat_mul__mutmut_5, 
    'x__mat_mul__mutmut_6': x__mat_mul__mutmut_6, 
    'x__mat_mul__mutmut_7': x__mat_mul__mutmut_7, 
    'x__mat_mul__mutmut_8': x__mat_mul__mutmut_8, 
    'x__mat_mul__mutmut_9': x__mat_mul__mutmut_9, 
    'x__mat_mul__mutmut_10': x__mat_mul__mutmut_10, 
    'x__mat_mul__mutmut_11': x__mat_mul__mutmut_11, 
    'x__mat_mul__mutmut_12': x__mat_mul__mutmut_12, 
    'x__mat_mul__mutmut_13': x__mat_mul__mutmut_13, 
    'x__mat_mul__mutmut_14': x__mat_mul__mutmut_14, 
    'x__mat_mul__mutmut_15': x__mat_mul__mutmut_15, 
    'x__mat_mul__mutmut_16': x__mat_mul__mutmut_16
}
x__mat_mul__mutmut_orig.__name__ = 'x__mat_mul'


def _mat_sub(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    args = [A, B]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__mat_sub__mutmut_orig, x__mat_sub__mutmut_mutants, args, kwargs, None)


def x__mat_sub__mutmut_orig(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Element-wise matrix subtraction A - B."""
    n: int = len(A)
    m: int = len(A[0])
    return [[A[i][j] - B[i][j] for j in range(m)] for i in range(n)]


def x__mat_sub__mutmut_1(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Element-wise matrix subtraction A - B."""
    n: int = None
    m: int = len(A[0])
    return [[A[i][j] - B[i][j] for j in range(m)] for i in range(n)]


def x__mat_sub__mutmut_2(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Element-wise matrix subtraction A - B."""
    n: int = len(A)
    m: int = None
    return [[A[i][j] - B[i][j] for j in range(m)] for i in range(n)]


def x__mat_sub__mutmut_3(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Element-wise matrix subtraction A - B."""
    n: int = len(A)
    m: int = len(A[0])
    return [[A[i][j] + B[i][j] for j in range(m)] for i in range(n)]


def x__mat_sub__mutmut_4(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Element-wise matrix subtraction A - B."""
    n: int = len(A)
    m: int = len(A[0])
    return [[A[i][j] - B[i][j] for j in range(None)] for i in range(n)]


def x__mat_sub__mutmut_5(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """Element-wise matrix subtraction A - B."""
    n: int = len(A)
    m: int = len(A[0])
    return [[A[i][j] - B[i][j] for j in range(m)] for i in range(None)]

x__mat_sub__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__mat_sub__mutmut_1': x__mat_sub__mutmut_1, 
    'x__mat_sub__mutmut_2': x__mat_sub__mutmut_2, 
    'x__mat_sub__mutmut_3': x__mat_sub__mutmut_3, 
    'x__mat_sub__mutmut_4': x__mat_sub__mutmut_4, 
    'x__mat_sub__mutmut_5': x__mat_sub__mutmut_5
}
x__mat_sub__mutmut_orig.__name__ = 'x__mat_sub'


def _transpose(A: List[List[float]]) -> List[List[float]]:
    args = [A]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__transpose__mutmut_orig, x__transpose__mutmut_mutants, args, kwargs, None)


def x__transpose__mutmut_orig(A: List[List[float]]) -> List[List[float]]:
    """Matrix transpose."""
    r: int = len(A)
    c: int = len(A[0])
    return [[A[i][j] for i in range(r)] for j in range(c)]


def x__transpose__mutmut_1(A: List[List[float]]) -> List[List[float]]:
    """Matrix transpose."""
    r: int = None
    c: int = len(A[0])
    return [[A[i][j] for i in range(r)] for j in range(c)]


def x__transpose__mutmut_2(A: List[List[float]]) -> List[List[float]]:
    """Matrix transpose."""
    r: int = len(A)
    c: int = None
    return [[A[i][j] for i in range(r)] for j in range(c)]


def x__transpose__mutmut_3(A: List[List[float]]) -> List[List[float]]:
    """Matrix transpose."""
    r: int = len(A)
    c: int = len(A[0])
    return [[A[i][j] for i in range(None)] for j in range(c)]


def x__transpose__mutmut_4(A: List[List[float]]) -> List[List[float]]:
    """Matrix transpose."""
    r: int = len(A)
    c: int = len(A[0])
    return [[A[i][j] for i in range(r)] for j in range(None)]

x__transpose__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__transpose__mutmut_1': x__transpose__mutmut_1, 
    'x__transpose__mutmut_2': x__transpose__mutmut_2, 
    'x__transpose__mutmut_3': x__transpose__mutmut_3, 
    'x__transpose__mutmut_4': x__transpose__mutmut_4
}
x__transpose__mutmut_orig.__name__ = 'x__transpose'


def _mat_vec_mul(A: List[List[float]], v: List[float]) -> List[float]:
    args = [A, v]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__mat_vec_mul__mutmut_orig, x__mat_vec_mul__mutmut_mutants, args, kwargs, None)


def x__mat_vec_mul__mutmut_orig(A: List[List[float]], v: List[float]) -> List[float]:
    """Matrix-vector multiplication A @ v."""
    return [sum(A[i][j] * v[j] for j in range(len(v))) for i in range(len(A))]


def x__mat_vec_mul__mutmut_1(A: List[List[float]], v: List[float]) -> List[float]:
    """Matrix-vector multiplication A @ v."""
    return [sum(None) for i in range(len(A))]


def x__mat_vec_mul__mutmut_2(A: List[List[float]], v: List[float]) -> List[float]:
    """Matrix-vector multiplication A @ v."""
    return [sum(A[i][j] / v[j] for j in range(len(v))) for i in range(len(A))]


def x__mat_vec_mul__mutmut_3(A: List[List[float]], v: List[float]) -> List[float]:
    """Matrix-vector multiplication A @ v."""
    return [sum(A[i][j] * v[j] for j in range(None)) for i in range(len(A))]


def x__mat_vec_mul__mutmut_4(A: List[List[float]], v: List[float]) -> List[float]:
    """Matrix-vector multiplication A @ v."""
    return [sum(A[i][j] * v[j] for j in range(len(v))) for i in range(None)]

x__mat_vec_mul__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__mat_vec_mul__mutmut_1': x__mat_vec_mul__mutmut_1, 
    'x__mat_vec_mul__mutmut_2': x__mat_vec_mul__mutmut_2, 
    'x__mat_vec_mul__mutmut_3': x__mat_vec_mul__mutmut_3, 
    'x__mat_vec_mul__mutmut_4': x__mat_vec_mul__mutmut_4
}
x__mat_vec_mul__mutmut_orig.__name__ = 'x__mat_vec_mul'


def _vec_add(a: List[float], b: List[float]) -> List[float]:
    args = [a, b]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__vec_add__mutmut_orig, x__vec_add__mutmut_mutants, args, kwargs, None)


def x__vec_add__mutmut_orig(a: List[float], b: List[float]) -> List[float]:
    """Vector addition a + b."""
    return [a[i] + b[i] for i in range(len(a))]


def x__vec_add__mutmut_1(a: List[float], b: List[float]) -> List[float]:
    """Vector addition a + b."""
    return [a[i] - b[i] for i in range(len(a))]


def x__vec_add__mutmut_2(a: List[float], b: List[float]) -> List[float]:
    """Vector addition a + b."""
    return [a[i] + b[i] for i in range(None)]

x__vec_add__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__vec_add__mutmut_1': x__vec_add__mutmut_1, 
    'x__vec_add__mutmut_2': x__vec_add__mutmut_2
}
x__vec_add__mutmut_orig.__name__ = 'x__vec_add'


def _vec_sub(a: List[float], b: List[float]) -> List[float]:
    args = [a, b]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__vec_sub__mutmut_orig, x__vec_sub__mutmut_mutants, args, kwargs, None)


def x__vec_sub__mutmut_orig(a: List[float], b: List[float]) -> List[float]:
    """Vector subtraction a - b."""
    return [a[i] - b[i] for i in range(len(a))]


def x__vec_sub__mutmut_1(a: List[float], b: List[float]) -> List[float]:
    """Vector subtraction a - b."""
    return [a[i] + b[i] for i in range(len(a))]


def x__vec_sub__mutmut_2(a: List[float], b: List[float]) -> List[float]:
    """Vector subtraction a - b."""
    return [a[i] - b[i] for i in range(None)]

x__vec_sub__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__vec_sub__mutmut_1': x__vec_sub__mutmut_1, 
    'x__vec_sub__mutmut_2': x__vec_sub__mutmut_2
}
x__vec_sub__mutmut_orig.__name__ = 'x__vec_sub'


def _symmetrise(M: List[List[float]]) -> List[List[float]]:
    args = [M]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__symmetrise__mutmut_orig, x__symmetrise__mutmut_mutants, args, kwargs, None)


def x__symmetrise__mutmut_orig(M: List[List[float]]) -> List[List[float]]:
    """Force symmetry: M = (M + M^T) / 2."""
    n: int = len(M)
    S: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            S[i][j] = (M[i][j] + M[j][i]) * 0.5
    return S


def x__symmetrise__mutmut_1(M: List[List[float]]) -> List[List[float]]:
    """Force symmetry: M = (M + M^T) / 2."""
    n: int = None
    S: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            S[i][j] = (M[i][j] + M[j][i]) * 0.5
    return S


def x__symmetrise__mutmut_2(M: List[List[float]]) -> List[List[float]]:
    """Force symmetry: M = (M + M^T) / 2."""
    n: int = len(M)
    S: List[List[float]] = None
    for i in range(n):
        for j in range(n):
            S[i][j] = (M[i][j] + M[j][i]) * 0.5
    return S


def x__symmetrise__mutmut_3(M: List[List[float]]) -> List[List[float]]:
    """Force symmetry: M = (M + M^T) / 2."""
    n: int = len(M)
    S: List[List[float]] = [[0.0] / n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            S[i][j] = (M[i][j] + M[j][i]) * 0.5
    return S


def x__symmetrise__mutmut_4(M: List[List[float]]) -> List[List[float]]:
    """Force symmetry: M = (M + M^T) / 2."""
    n: int = len(M)
    S: List[List[float]] = [[1.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            S[i][j] = (M[i][j] + M[j][i]) * 0.5
    return S


def x__symmetrise__mutmut_5(M: List[List[float]]) -> List[List[float]]:
    """Force symmetry: M = (M + M^T) / 2."""
    n: int = len(M)
    S: List[List[float]] = [[0.0] * n for _ in range(None)]
    for i in range(n):
        for j in range(n):
            S[i][j] = (M[i][j] + M[j][i]) * 0.5
    return S


def x__symmetrise__mutmut_6(M: List[List[float]]) -> List[List[float]]:
    """Force symmetry: M = (M + M^T) / 2."""
    n: int = len(M)
    S: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(None):
        for j in range(n):
            S[i][j] = (M[i][j] + M[j][i]) * 0.5
    return S


def x__symmetrise__mutmut_7(M: List[List[float]]) -> List[List[float]]:
    """Force symmetry: M = (M + M^T) / 2."""
    n: int = len(M)
    S: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(None):
            S[i][j] = (M[i][j] + M[j][i]) * 0.5
    return S


def x__symmetrise__mutmut_8(M: List[List[float]]) -> List[List[float]]:
    """Force symmetry: M = (M + M^T) / 2."""
    n: int = len(M)
    S: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            S[i][j] = None
    return S


def x__symmetrise__mutmut_9(M: List[List[float]]) -> List[List[float]]:
    """Force symmetry: M = (M + M^T) / 2."""
    n: int = len(M)
    S: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            S[i][j] = (M[i][j] + M[j][i]) / 0.5
    return S


def x__symmetrise__mutmut_10(M: List[List[float]]) -> List[List[float]]:
    """Force symmetry: M = (M + M^T) / 2."""
    n: int = len(M)
    S: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            S[i][j] = (M[i][j] - M[j][i]) * 0.5
    return S


def x__symmetrise__mutmut_11(M: List[List[float]]) -> List[List[float]]:
    """Force symmetry: M = (M + M^T) / 2."""
    n: int = len(M)
    S: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            S[i][j] = (M[i][j] + M[j][i]) * 1.5
    return S

x__symmetrise__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__symmetrise__mutmut_1': x__symmetrise__mutmut_1, 
    'x__symmetrise__mutmut_2': x__symmetrise__mutmut_2, 
    'x__symmetrise__mutmut_3': x__symmetrise__mutmut_3, 
    'x__symmetrise__mutmut_4': x__symmetrise__mutmut_4, 
    'x__symmetrise__mutmut_5': x__symmetrise__mutmut_5, 
    'x__symmetrise__mutmut_6': x__symmetrise__mutmut_6, 
    'x__symmetrise__mutmut_7': x__symmetrise__mutmut_7, 
    'x__symmetrise__mutmut_8': x__symmetrise__mutmut_8, 
    'x__symmetrise__mutmut_9': x__symmetrise__mutmut_9, 
    'x__symmetrise__mutmut_10': x__symmetrise__mutmut_10, 
    'x__symmetrise__mutmut_11': x__symmetrise__mutmut_11
}
x__symmetrise__mutmut_orig.__name__ = 'x__symmetrise'


def _tikhonov_invert(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    args = [M, lam]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__tikhonov_invert__mutmut_orig, x__tikhonov_invert__mutmut_mutants, args, kwargs, None)


def x__tikhonov_invert__mutmut_orig(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_1(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = None
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_2(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = None

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_3(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] - [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_4(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] - (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_5(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i != j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_6(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 1.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_7(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(None)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_8(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [2.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_9(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i != k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_10(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 1.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_11(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(None)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_12(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(None)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_13(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(None):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_14(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = None
        max_row: int = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_15(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(None)
        max_row: int = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_16(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = None
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_17(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(None, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_18(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 1, None):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_19(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_20(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 1, ):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_21(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col - 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_22(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 2, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_23(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 1, n):
            if abs(None) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_24(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) >= max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_25(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = None
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_26(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(None)
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_27(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = None
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_28(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row == col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_29(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = None

        pivot: float = aug[col][col]
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_30(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = None
        if abs(pivot) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_31(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(None) < _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_32(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
        max_val: float = abs(aug[col][col])
        max_row: int = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > max_val:
                max_val = abs(aug[row][col])
                max_row = row
        if max_row != col:
            aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot: float = aug[col][col]
        if abs(pivot) <= _EPS:
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_33(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = None
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_34(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = None

        inv_pivot: float = 1.0 / pivot
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_35(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = None
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_36(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 * pivot
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_37(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 2.0 / pivot
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_38(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 / pivot
        for j in range(None):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_39(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 / pivot
        for j in range(2 / n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_40(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 / pivot
        for j in range(3 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_41(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 / pivot
        for j in range(2 * n):
            aug[col][j] = inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_42(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 / pivot
        for j in range(2 * n):
            aug[col][j] /= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_43(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 / pivot
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(None):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_44(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 / pivot
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row != col:
                continue
            factor: float = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_45(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 / pivot
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                break
            factor: float = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_46(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 / pivot
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = None
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_47(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 / pivot
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(None):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_48(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 / pivot
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(2 / n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_49(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
            aug[col][col] = _EPS
            pivot = _EPS

        inv_pivot: float = 1.0 / pivot
        for j in range(2 * n):
            aug[col][j] *= inv_pivot

        for row in range(n):
            if row == col:
                continue
            factor: float = aug[row][col]
            for j in range(3 * n):
                aug[row][j] -= factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_50(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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
                aug[row][j] = factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_51(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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
                aug[row][j] += factor * aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_52(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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
                aug[row][j] -= factor / aug[col][j]

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_53(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = None
    return inv


def x__tikhonov_invert__mutmut_54(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n - j] for j in range(n)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_55(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(None)] for i in range(n)]
    return inv


def x__tikhonov_invert__mutmut_56(M: List[List[float]], lam: float = TIKHONOV_LAMBDA) -> List[List[float]]:
    """
    Compute (M + lam * I)^{-1} via Gaussian elimination with partial pivoting.

    Tikhonov regularisation ensures the matrix is non-singular even when M
    has very small eigenvalues. This is the ONLY matrix inversion path used
    by StateEstimator — never invert M directly.
    """
    n: int = len(M)
    # Build augmented matrix [M + lam*I | I]
    aug: List[List[float]] = [
        [M[i][j] + (lam if i == j else 0.0) for j in range(n)] + [1.0 if i == k else 0.0 for k in range(n)]
        for i in range(n)
    ]

    for col in range(n):
        # Partial pivoting: find row with max abs in column.
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
            # Singular column — add extra regularisation.
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

    inv: List[List[float]] = [[aug[i][n + j] for j in range(n)] for i in range(None)]
    return inv

x__tikhonov_invert__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__tikhonov_invert__mutmut_1': x__tikhonov_invert__mutmut_1, 
    'x__tikhonov_invert__mutmut_2': x__tikhonov_invert__mutmut_2, 
    'x__tikhonov_invert__mutmut_3': x__tikhonov_invert__mutmut_3, 
    'x__tikhonov_invert__mutmut_4': x__tikhonov_invert__mutmut_4, 
    'x__tikhonov_invert__mutmut_5': x__tikhonov_invert__mutmut_5, 
    'x__tikhonov_invert__mutmut_6': x__tikhonov_invert__mutmut_6, 
    'x__tikhonov_invert__mutmut_7': x__tikhonov_invert__mutmut_7, 
    'x__tikhonov_invert__mutmut_8': x__tikhonov_invert__mutmut_8, 
    'x__tikhonov_invert__mutmut_9': x__tikhonov_invert__mutmut_9, 
    'x__tikhonov_invert__mutmut_10': x__tikhonov_invert__mutmut_10, 
    'x__tikhonov_invert__mutmut_11': x__tikhonov_invert__mutmut_11, 
    'x__tikhonov_invert__mutmut_12': x__tikhonov_invert__mutmut_12, 
    'x__tikhonov_invert__mutmut_13': x__tikhonov_invert__mutmut_13, 
    'x__tikhonov_invert__mutmut_14': x__tikhonov_invert__mutmut_14, 
    'x__tikhonov_invert__mutmut_15': x__tikhonov_invert__mutmut_15, 
    'x__tikhonov_invert__mutmut_16': x__tikhonov_invert__mutmut_16, 
    'x__tikhonov_invert__mutmut_17': x__tikhonov_invert__mutmut_17, 
    'x__tikhonov_invert__mutmut_18': x__tikhonov_invert__mutmut_18, 
    'x__tikhonov_invert__mutmut_19': x__tikhonov_invert__mutmut_19, 
    'x__tikhonov_invert__mutmut_20': x__tikhonov_invert__mutmut_20, 
    'x__tikhonov_invert__mutmut_21': x__tikhonov_invert__mutmut_21, 
    'x__tikhonov_invert__mutmut_22': x__tikhonov_invert__mutmut_22, 
    'x__tikhonov_invert__mutmut_23': x__tikhonov_invert__mutmut_23, 
    'x__tikhonov_invert__mutmut_24': x__tikhonov_invert__mutmut_24, 
    'x__tikhonov_invert__mutmut_25': x__tikhonov_invert__mutmut_25, 
    'x__tikhonov_invert__mutmut_26': x__tikhonov_invert__mutmut_26, 
    'x__tikhonov_invert__mutmut_27': x__tikhonov_invert__mutmut_27, 
    'x__tikhonov_invert__mutmut_28': x__tikhonov_invert__mutmut_28, 
    'x__tikhonov_invert__mutmut_29': x__tikhonov_invert__mutmut_29, 
    'x__tikhonov_invert__mutmut_30': x__tikhonov_invert__mutmut_30, 
    'x__tikhonov_invert__mutmut_31': x__tikhonov_invert__mutmut_31, 
    'x__tikhonov_invert__mutmut_32': x__tikhonov_invert__mutmut_32, 
    'x__tikhonov_invert__mutmut_33': x__tikhonov_invert__mutmut_33, 
    'x__tikhonov_invert__mutmut_34': x__tikhonov_invert__mutmut_34, 
    'x__tikhonov_invert__mutmut_35': x__tikhonov_invert__mutmut_35, 
    'x__tikhonov_invert__mutmut_36': x__tikhonov_invert__mutmut_36, 
    'x__tikhonov_invert__mutmut_37': x__tikhonov_invert__mutmut_37, 
    'x__tikhonov_invert__mutmut_38': x__tikhonov_invert__mutmut_38, 
    'x__tikhonov_invert__mutmut_39': x__tikhonov_invert__mutmut_39, 
    'x__tikhonov_invert__mutmut_40': x__tikhonov_invert__mutmut_40, 
    'x__tikhonov_invert__mutmut_41': x__tikhonov_invert__mutmut_41, 
    'x__tikhonov_invert__mutmut_42': x__tikhonov_invert__mutmut_42, 
    'x__tikhonov_invert__mutmut_43': x__tikhonov_invert__mutmut_43, 
    'x__tikhonov_invert__mutmut_44': x__tikhonov_invert__mutmut_44, 
    'x__tikhonov_invert__mutmut_45': x__tikhonov_invert__mutmut_45, 
    'x__tikhonov_invert__mutmut_46': x__tikhonov_invert__mutmut_46, 
    'x__tikhonov_invert__mutmut_47': x__tikhonov_invert__mutmut_47, 
    'x__tikhonov_invert__mutmut_48': x__tikhonov_invert__mutmut_48, 
    'x__tikhonov_invert__mutmut_49': x__tikhonov_invert__mutmut_49, 
    'x__tikhonov_invert__mutmut_50': x__tikhonov_invert__mutmut_50, 
    'x__tikhonov_invert__mutmut_51': x__tikhonov_invert__mutmut_51, 
    'x__tikhonov_invert__mutmut_52': x__tikhonov_invert__mutmut_52, 
    'x__tikhonov_invert__mutmut_53': x__tikhonov_invert__mutmut_53, 
    'x__tikhonov_invert__mutmut_54': x__tikhonov_invert__mutmut_54, 
    'x__tikhonov_invert__mutmut_55': x__tikhonov_invert__mutmut_55, 
    'x__tikhonov_invert__mutmut_56': x__tikhonov_invert__mutmut_56
}
x__tikhonov_invert__mutmut_orig.__name__ = 'x__tikhonov_invert'


def _condition_number_approx(M: List[List[float]]) -> float:
    args = [M]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__condition_number_approx__mutmut_orig, x__condition_number_approx__mutmut_mutants, args, kwargs, None)


def x__condition_number_approx__mutmut_orig(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = [abs(M[i][i]) for i in range(n)]
    max_d: float = max(diag_vals) if diag_vals else 1.0
    min_d: float = min(diag_vals) if diag_vals else 1.0
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD + 1.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_1(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = None
    diag_vals: List[float] = [abs(M[i][i]) for i in range(n)]
    max_d: float = max(diag_vals) if diag_vals else 1.0
    min_d: float = min(diag_vals) if diag_vals else 1.0
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD + 1.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_2(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = None
    max_d: float = max(diag_vals) if diag_vals else 1.0
    min_d: float = min(diag_vals) if diag_vals else 1.0
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD + 1.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_3(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = [abs(None) for i in range(n)]
    max_d: float = max(diag_vals) if diag_vals else 1.0
    min_d: float = min(diag_vals) if diag_vals else 1.0
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD + 1.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_4(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = [abs(M[i][i]) for i in range(None)]
    max_d: float = max(diag_vals) if diag_vals else 1.0
    min_d: float = min(diag_vals) if diag_vals else 1.0
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD + 1.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_5(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = [abs(M[i][i]) for i in range(n)]
    max_d: float = None
    min_d: float = min(diag_vals) if diag_vals else 1.0
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD + 1.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_6(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = [abs(M[i][i]) for i in range(n)]
    max_d: float = max(None) if diag_vals else 1.0
    min_d: float = min(diag_vals) if diag_vals else 1.0
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD + 1.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_7(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = [abs(M[i][i]) for i in range(n)]
    max_d: float = max(diag_vals) if diag_vals else 2.0
    min_d: float = min(diag_vals) if diag_vals else 1.0
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD + 1.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_8(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = [abs(M[i][i]) for i in range(n)]
    max_d: float = max(diag_vals) if diag_vals else 1.0
    min_d: float = None
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD + 1.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_9(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = [abs(M[i][i]) for i in range(n)]
    max_d: float = max(diag_vals) if diag_vals else 1.0
    min_d: float = min(None) if diag_vals else 1.0
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD + 1.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_10(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = [abs(M[i][i]) for i in range(n)]
    max_d: float = max(diag_vals) if diag_vals else 1.0
    min_d: float = min(diag_vals) if diag_vals else 2.0
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD + 1.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_11(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = [abs(M[i][i]) for i in range(n)]
    max_d: float = max(diag_vals) if diag_vals else 1.0
    min_d: float = min(diag_vals) if diag_vals else 1.0
    if min_d <= _EPS:
        return DIVERGENCE_THRESHOLD + 1.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_12(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = [abs(M[i][i]) for i in range(n)]
    max_d: float = max(diag_vals) if diag_vals else 1.0
    min_d: float = min(diag_vals) if diag_vals else 1.0
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD - 1.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_13(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = [abs(M[i][i]) for i in range(n)]
    max_d: float = max(diag_vals) if diag_vals else 1.0
    min_d: float = min(diag_vals) if diag_vals else 1.0
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD + 2.0  # treat as diverged
    return max_d / min_d


def x__condition_number_approx__mutmut_14(M: List[List[float]]) -> float:
    """
    Approximate condition number of a symmetric positive-definite matrix
    as max_diagonal / min_diagonal.

    This is a lightweight O(n) approximation suitable for divergence
    detection. For a well-conditioned matrix the diagonal approximation
    is conservative (overestimates). For a diverging matrix it correctly
    detects blow-up.
    """
    n: int = len(M)
    diag_vals: List[float] = [abs(M[i][i]) for i in range(n)]
    max_d: float = max(diag_vals) if diag_vals else 1.0
    min_d: float = min(diag_vals) if diag_vals else 1.0
    if min_d < _EPS:
        return DIVERGENCE_THRESHOLD + 1.0  # treat as diverged
    return max_d * min_d

x__condition_number_approx__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__condition_number_approx__mutmut_1': x__condition_number_approx__mutmut_1, 
    'x__condition_number_approx__mutmut_2': x__condition_number_approx__mutmut_2, 
    'x__condition_number_approx__mutmut_3': x__condition_number_approx__mutmut_3, 
    'x__condition_number_approx__mutmut_4': x__condition_number_approx__mutmut_4, 
    'x__condition_number_approx__mutmut_5': x__condition_number_approx__mutmut_5, 
    'x__condition_number_approx__mutmut_6': x__condition_number_approx__mutmut_6, 
    'x__condition_number_approx__mutmut_7': x__condition_number_approx__mutmut_7, 
    'x__condition_number_approx__mutmut_8': x__condition_number_approx__mutmut_8, 
    'x__condition_number_approx__mutmut_9': x__condition_number_approx__mutmut_9, 
    'x__condition_number_approx__mutmut_10': x__condition_number_approx__mutmut_10, 
    'x__condition_number_approx__mutmut_11': x__condition_number_approx__mutmut_11, 
    'x__condition_number_approx__mutmut_12': x__condition_number_approx__mutmut_12, 
    'x__condition_number_approx__mutmut_13': x__condition_number_approx__mutmut_13, 
    'x__condition_number_approx__mutmut_14': x__condition_number_approx__mutmut_14
}
x__condition_number_approx__mutmut_orig.__name__ = 'x__condition_number_approx'


def _floor_diag(M: List[List[float]], floor: float = _P_MIN_DIAG) -> List[List[float]]:
    args = [M, floor]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__floor_diag__mutmut_orig, x__floor_diag__mutmut_mutants, args, kwargs, None)


def x__floor_diag__mutmut_orig(M: List[List[float]], floor: float = _P_MIN_DIAG) -> List[List[float]]:
    """Floor the diagonal of M at `floor` for strict positivity."""
    n: int = len(M)
    result: List[List[float]] = [list(row) for row in M]
    for i in range(n):
        if result[i][i] < floor:
            result[i][i] = floor
    return result


def x__floor_diag__mutmut_1(M: List[List[float]], floor: float = _P_MIN_DIAG) -> List[List[float]]:
    """Floor the diagonal of M at `floor` for strict positivity."""
    n: int = None
    result: List[List[float]] = [list(row) for row in M]
    for i in range(n):
        if result[i][i] < floor:
            result[i][i] = floor
    return result


def x__floor_diag__mutmut_2(M: List[List[float]], floor: float = _P_MIN_DIAG) -> List[List[float]]:
    """Floor the diagonal of M at `floor` for strict positivity."""
    n: int = len(M)
    result: List[List[float]] = None
    for i in range(n):
        if result[i][i] < floor:
            result[i][i] = floor
    return result


def x__floor_diag__mutmut_3(M: List[List[float]], floor: float = _P_MIN_DIAG) -> List[List[float]]:
    """Floor the diagonal of M at `floor` for strict positivity."""
    n: int = len(M)
    result: List[List[float]] = [list(None) for row in M]
    for i in range(n):
        if result[i][i] < floor:
            result[i][i] = floor
    return result


def x__floor_diag__mutmut_4(M: List[List[float]], floor: float = _P_MIN_DIAG) -> List[List[float]]:
    """Floor the diagonal of M at `floor` for strict positivity."""
    n: int = len(M)
    result: List[List[float]] = [list(row) for row in M]
    for i in range(None):
        if result[i][i] < floor:
            result[i][i] = floor
    return result


def x__floor_diag__mutmut_5(M: List[List[float]], floor: float = _P_MIN_DIAG) -> List[List[float]]:
    """Floor the diagonal of M at `floor` for strict positivity."""
    n: int = len(M)
    result: List[List[float]] = [list(row) for row in M]
    for i in range(n):
        if result[i][i] <= floor:
            result[i][i] = floor
    return result


def x__floor_diag__mutmut_6(M: List[List[float]], floor: float = _P_MIN_DIAG) -> List[List[float]]:
    """Floor the diagonal of M at `floor` for strict positivity."""
    n: int = len(M)
    result: List[List[float]] = [list(row) for row in M]
    for i in range(n):
        if result[i][i] < floor:
            result[i][i] = None
    return result

x__floor_diag__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__floor_diag__mutmut_1': x__floor_diag__mutmut_1, 
    'x__floor_diag__mutmut_2': x__floor_diag__mutmut_2, 
    'x__floor_diag__mutmut_3': x__floor_diag__mutmut_3, 
    'x__floor_diag__mutmut_4': x__floor_diag__mutmut_4, 
    'x__floor_diag__mutmut_5': x__floor_diag__mutmut_5, 
    'x__floor_diag__mutmut_6': x__floor_diag__mutmut_6
}
x__floor_diag__mutmut_orig.__name__ = 'x__floor_diag'


# ---------------------------------------------------------------------------
# KalmanState (internal — not part of public API)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KalmanState:
    """
    Immutable carrier for the Kalman filter covariance matrix.
    Used internally by StateEstimator; not exported as part of the public API.

    Fields
    ------
    P : tuple
        Flattened 12x12 covariance matrix (row-major). Length = 144.
        Always symmetric and positive-definite.
    divergence_count : int
        Number of times the filter has been reset due to divergence.
    """
    P: tuple          # flat row-major float[144]
    divergence_count: int

    def as_matrix(self) -> List[List[float]]:
        """Reconstruct P as a 12x12 list-of-lists."""
        return [
            [self.P[i * _DIM + j] for j in range(_DIM)]
            for i in range(_DIM)
        ]

    @staticmethod
    def from_matrix(P_mat: List[List[float]], divergence_count: int = 0) -> "KalmanState":
        """Construct a KalmanState from a 12x12 matrix."""
        flat = tuple(P_mat[i][j] for i in range(_DIM) for j in range(_DIM))
        return KalmanState(P=flat, divergence_count=divergence_count)


# ---------------------------------------------------------------------------
# Latent state <-> vector conversion
# ---------------------------------------------------------------------------

def _state_to_vector(state: LatentState) -> List[float]:
    args = [state]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__state_to_vector__mutmut_orig, x__state_to_vector__mutmut_mutants, args, kwargs, None)


# ---------------------------------------------------------------------------
# Latent state <-> vector conversion
# ---------------------------------------------------------------------------

def x__state_to_vector__mutmut_orig(state: LatentState) -> List[float]:
    """Extract the 12 LatentState fields as an ordered float vector."""
    return [float(getattr(state, name)) for name in _FIELD_NAMES]


# ---------------------------------------------------------------------------
# Latent state <-> vector conversion
# ---------------------------------------------------------------------------

def x__state_to_vector__mutmut_1(state: LatentState) -> List[float]:
    """Extract the 12 LatentState fields as an ordered float vector."""
    return [float(None) for name in _FIELD_NAMES]


# ---------------------------------------------------------------------------
# Latent state <-> vector conversion
# ---------------------------------------------------------------------------

def x__state_to_vector__mutmut_2(state: LatentState) -> List[float]:
    """Extract the 12 LatentState fields as an ordered float vector."""
    return [float(getattr(None, name)) for name in _FIELD_NAMES]


# ---------------------------------------------------------------------------
# Latent state <-> vector conversion
# ---------------------------------------------------------------------------

def x__state_to_vector__mutmut_3(state: LatentState) -> List[float]:
    """Extract the 12 LatentState fields as an ordered float vector."""
    return [float(getattr(state, None)) for name in _FIELD_NAMES]


# ---------------------------------------------------------------------------
# Latent state <-> vector conversion
# ---------------------------------------------------------------------------

def x__state_to_vector__mutmut_4(state: LatentState) -> List[float]:
    """Extract the 12 LatentState fields as an ordered float vector."""
    return [float(getattr(name)) for name in _FIELD_NAMES]


# ---------------------------------------------------------------------------
# Latent state <-> vector conversion
# ---------------------------------------------------------------------------

def x__state_to_vector__mutmut_5(state: LatentState) -> List[float]:
    """Extract the 12 LatentState fields as an ordered float vector."""
    return [float(getattr(state, )) for name in _FIELD_NAMES]

x__state_to_vector__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__state_to_vector__mutmut_1': x__state_to_vector__mutmut_1, 
    'x__state_to_vector__mutmut_2': x__state_to_vector__mutmut_2, 
    'x__state_to_vector__mutmut_3': x__state_to_vector__mutmut_3, 
    'x__state_to_vector__mutmut_4': x__state_to_vector__mutmut_4, 
    'x__state_to_vector__mutmut_5': x__state_to_vector__mutmut_5
}
x__state_to_vector__mutmut_orig.__name__ = 'x__state_to_vector'


def _vector_to_state(vec: List[float], template: LatentState) -> LatentState:
    args = [vec, template]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__vector_to_state__mutmut_orig, x__vector_to_state__mutmut_mutants, args, kwargs, None)


def x__vector_to_state__mutmut_orig(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_1(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(None) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_2(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = None
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_3(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[1]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_4(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = None

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_5(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(None, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_6(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, None)

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_7(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_8(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, )

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_9(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(1, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_10(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(None, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_11(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, None))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_12(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_13(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, ))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_14(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(5, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_15(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(None)))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_16(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(None))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_17(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=None,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_18(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=None,
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_19(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=None,
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_20(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=None,
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_21(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=None,
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_22(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=None,
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_23(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=None,
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_24(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=None,
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_25(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=None,
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_26(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=None,
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_27(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=None,
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_28(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=None,
    )


def x__vector_to_state__mutmut_29(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_30(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_31(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_32(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_33(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_34(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_35(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_36(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_37(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_38(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_39(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_40(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        )


def x__vector_to_state__mutmut_41(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(None,  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_42(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  None),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_43(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_44(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  ),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_45(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[2],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_46(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(None, template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_47(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], None),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_48(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_49(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], ),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_50(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[3], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_51(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(None, template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_52(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], None),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_53(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_54(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], ),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_55(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[4], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_56(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(None, template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_57(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], None),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_58(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_59(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], ),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_60(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[5], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_61(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(None, template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_62(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], None),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_63(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_64(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], ),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_65(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[6], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_66(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(None, template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_67(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], None),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_68(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_69(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], ),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_70(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[7], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_71(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(None, template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_72(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], None),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_73(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_74(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], ),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_75(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[8], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_76(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(None, template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_77(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], None),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_78(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_79(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], ),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_80(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[9], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_81(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(None, template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_82(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], None),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_83(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_84(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], ),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_85(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[10], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_86(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(None, template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_87(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], None),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_88(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_89(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], ),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_90(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[11], template.stability),
        prediction_uncertainty=_safe(vec[11], template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_91(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(None, template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_92(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], None),
    )


def x__vector_to_state__mutmut_93(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(template.prediction_uncertainty),
    )


def x__vector_to_state__mutmut_94(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[11], ),
    )


def x__vector_to_state__mutmut_95(vec: List[float], template: LatentState) -> LatentState:
    """
    Reconstruct a LatentState from a 12-element float vector.
    Applies LatentState construction constraints:
      - regime is rounded to int and clamped to [0, 4]
      - all floats must be finite (replaced with template value on failure)
    """
    def _safe(v: float, fallback: float) -> float:
        return v if math.isfinite(v) else fallback

    regime_raw: float = vec[0]
    regime_int: int = max(0, min(4, int(round(regime_raw))))

    return LatentState(
        regime=regime_int,
        volatility=_safe(vec[1],  template.volatility),
        trend_strength=_safe(vec[2], template.trend_strength),
        mean_reversion=_safe(vec[3], template.mean_reversion),
        liquidity=_safe(vec[4], template.liquidity),
        stress=_safe(vec[5], template.stress),
        momentum=_safe(vec[6], template.momentum),
        drift=_safe(vec[7], template.drift),
        noise=_safe(vec[8], template.noise),
        regime_confidence=_safe(vec[9], template.regime_confidence),
        stability=_safe(vec[10], template.stability),
        prediction_uncertainty=_safe(vec[12], template.prediction_uncertainty),
    )

x__vector_to_state__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__vector_to_state__mutmut_1': x__vector_to_state__mutmut_1, 
    'x__vector_to_state__mutmut_2': x__vector_to_state__mutmut_2, 
    'x__vector_to_state__mutmut_3': x__vector_to_state__mutmut_3, 
    'x__vector_to_state__mutmut_4': x__vector_to_state__mutmut_4, 
    'x__vector_to_state__mutmut_5': x__vector_to_state__mutmut_5, 
    'x__vector_to_state__mutmut_6': x__vector_to_state__mutmut_6, 
    'x__vector_to_state__mutmut_7': x__vector_to_state__mutmut_7, 
    'x__vector_to_state__mutmut_8': x__vector_to_state__mutmut_8, 
    'x__vector_to_state__mutmut_9': x__vector_to_state__mutmut_9, 
    'x__vector_to_state__mutmut_10': x__vector_to_state__mutmut_10, 
    'x__vector_to_state__mutmut_11': x__vector_to_state__mutmut_11, 
    'x__vector_to_state__mutmut_12': x__vector_to_state__mutmut_12, 
    'x__vector_to_state__mutmut_13': x__vector_to_state__mutmut_13, 
    'x__vector_to_state__mutmut_14': x__vector_to_state__mutmut_14, 
    'x__vector_to_state__mutmut_15': x__vector_to_state__mutmut_15, 
    'x__vector_to_state__mutmut_16': x__vector_to_state__mutmut_16, 
    'x__vector_to_state__mutmut_17': x__vector_to_state__mutmut_17, 
    'x__vector_to_state__mutmut_18': x__vector_to_state__mutmut_18, 
    'x__vector_to_state__mutmut_19': x__vector_to_state__mutmut_19, 
    'x__vector_to_state__mutmut_20': x__vector_to_state__mutmut_20, 
    'x__vector_to_state__mutmut_21': x__vector_to_state__mutmut_21, 
    'x__vector_to_state__mutmut_22': x__vector_to_state__mutmut_22, 
    'x__vector_to_state__mutmut_23': x__vector_to_state__mutmut_23, 
    'x__vector_to_state__mutmut_24': x__vector_to_state__mutmut_24, 
    'x__vector_to_state__mutmut_25': x__vector_to_state__mutmut_25, 
    'x__vector_to_state__mutmut_26': x__vector_to_state__mutmut_26, 
    'x__vector_to_state__mutmut_27': x__vector_to_state__mutmut_27, 
    'x__vector_to_state__mutmut_28': x__vector_to_state__mutmut_28, 
    'x__vector_to_state__mutmut_29': x__vector_to_state__mutmut_29, 
    'x__vector_to_state__mutmut_30': x__vector_to_state__mutmut_30, 
    'x__vector_to_state__mutmut_31': x__vector_to_state__mutmut_31, 
    'x__vector_to_state__mutmut_32': x__vector_to_state__mutmut_32, 
    'x__vector_to_state__mutmut_33': x__vector_to_state__mutmut_33, 
    'x__vector_to_state__mutmut_34': x__vector_to_state__mutmut_34, 
    'x__vector_to_state__mutmut_35': x__vector_to_state__mutmut_35, 
    'x__vector_to_state__mutmut_36': x__vector_to_state__mutmut_36, 
    'x__vector_to_state__mutmut_37': x__vector_to_state__mutmut_37, 
    'x__vector_to_state__mutmut_38': x__vector_to_state__mutmut_38, 
    'x__vector_to_state__mutmut_39': x__vector_to_state__mutmut_39, 
    'x__vector_to_state__mutmut_40': x__vector_to_state__mutmut_40, 
    'x__vector_to_state__mutmut_41': x__vector_to_state__mutmut_41, 
    'x__vector_to_state__mutmut_42': x__vector_to_state__mutmut_42, 
    'x__vector_to_state__mutmut_43': x__vector_to_state__mutmut_43, 
    'x__vector_to_state__mutmut_44': x__vector_to_state__mutmut_44, 
    'x__vector_to_state__mutmut_45': x__vector_to_state__mutmut_45, 
    'x__vector_to_state__mutmut_46': x__vector_to_state__mutmut_46, 
    'x__vector_to_state__mutmut_47': x__vector_to_state__mutmut_47, 
    'x__vector_to_state__mutmut_48': x__vector_to_state__mutmut_48, 
    'x__vector_to_state__mutmut_49': x__vector_to_state__mutmut_49, 
    'x__vector_to_state__mutmut_50': x__vector_to_state__mutmut_50, 
    'x__vector_to_state__mutmut_51': x__vector_to_state__mutmut_51, 
    'x__vector_to_state__mutmut_52': x__vector_to_state__mutmut_52, 
    'x__vector_to_state__mutmut_53': x__vector_to_state__mutmut_53, 
    'x__vector_to_state__mutmut_54': x__vector_to_state__mutmut_54, 
    'x__vector_to_state__mutmut_55': x__vector_to_state__mutmut_55, 
    'x__vector_to_state__mutmut_56': x__vector_to_state__mutmut_56, 
    'x__vector_to_state__mutmut_57': x__vector_to_state__mutmut_57, 
    'x__vector_to_state__mutmut_58': x__vector_to_state__mutmut_58, 
    'x__vector_to_state__mutmut_59': x__vector_to_state__mutmut_59, 
    'x__vector_to_state__mutmut_60': x__vector_to_state__mutmut_60, 
    'x__vector_to_state__mutmut_61': x__vector_to_state__mutmut_61, 
    'x__vector_to_state__mutmut_62': x__vector_to_state__mutmut_62, 
    'x__vector_to_state__mutmut_63': x__vector_to_state__mutmut_63, 
    'x__vector_to_state__mutmut_64': x__vector_to_state__mutmut_64, 
    'x__vector_to_state__mutmut_65': x__vector_to_state__mutmut_65, 
    'x__vector_to_state__mutmut_66': x__vector_to_state__mutmut_66, 
    'x__vector_to_state__mutmut_67': x__vector_to_state__mutmut_67, 
    'x__vector_to_state__mutmut_68': x__vector_to_state__mutmut_68, 
    'x__vector_to_state__mutmut_69': x__vector_to_state__mutmut_69, 
    'x__vector_to_state__mutmut_70': x__vector_to_state__mutmut_70, 
    'x__vector_to_state__mutmut_71': x__vector_to_state__mutmut_71, 
    'x__vector_to_state__mutmut_72': x__vector_to_state__mutmut_72, 
    'x__vector_to_state__mutmut_73': x__vector_to_state__mutmut_73, 
    'x__vector_to_state__mutmut_74': x__vector_to_state__mutmut_74, 
    'x__vector_to_state__mutmut_75': x__vector_to_state__mutmut_75, 
    'x__vector_to_state__mutmut_76': x__vector_to_state__mutmut_76, 
    'x__vector_to_state__mutmut_77': x__vector_to_state__mutmut_77, 
    'x__vector_to_state__mutmut_78': x__vector_to_state__mutmut_78, 
    'x__vector_to_state__mutmut_79': x__vector_to_state__mutmut_79, 
    'x__vector_to_state__mutmut_80': x__vector_to_state__mutmut_80, 
    'x__vector_to_state__mutmut_81': x__vector_to_state__mutmut_81, 
    'x__vector_to_state__mutmut_82': x__vector_to_state__mutmut_82, 
    'x__vector_to_state__mutmut_83': x__vector_to_state__mutmut_83, 
    'x__vector_to_state__mutmut_84': x__vector_to_state__mutmut_84, 
    'x__vector_to_state__mutmut_85': x__vector_to_state__mutmut_85, 
    'x__vector_to_state__mutmut_86': x__vector_to_state__mutmut_86, 
    'x__vector_to_state__mutmut_87': x__vector_to_state__mutmut_87, 
    'x__vector_to_state__mutmut_88': x__vector_to_state__mutmut_88, 
    'x__vector_to_state__mutmut_89': x__vector_to_state__mutmut_89, 
    'x__vector_to_state__mutmut_90': x__vector_to_state__mutmut_90, 
    'x__vector_to_state__mutmut_91': x__vector_to_state__mutmut_91, 
    'x__vector_to_state__mutmut_92': x__vector_to_state__mutmut_92, 
    'x__vector_to_state__mutmut_93': x__vector_to_state__mutmut_93, 
    'x__vector_to_state__mutmut_94': x__vector_to_state__mutmut_94, 
    'x__vector_to_state__mutmut_95': x__vector_to_state__mutmut_95
}
x__vector_to_state__mutmut_orig.__name__ = 'x__vector_to_state'


# ---------------------------------------------------------------------------
# StateEstimator
# ---------------------------------------------------------------------------

class StateEstimator:
    """
    Kalman filter for the 12-dimensional JARVIS latent state vector.

    Implements the standard predict / update cycle:
      - predict(): propagates the state and covariance through the
                   state transition model (F = I, no drift).
      - update():  incorporates a new observation (z) and computes the
                   optimal Kalman gain.

    DIVERGENCE PROTECTION:
      After every update(), the approximate condition number of P is
      checked. If it exceeds DIVERGENCE_THRESHOLD (1e6), P is reset to
      the initial covariance P_0. The divergence_count field in the
      internal KalmanState is incremented on each reset.

    NUMERICAL SAFETY:
      - All matrix inversions use Tikhonov regularisation.
      - P is symmetrised after every update.
      - P diagonal is floored at _P_MIN_DIAG after every update.
      - Non-finite observation values are replaced with the predicted
        state values (no observation correction applied for those dims).

    STDLIB ONLY: no numpy, no scipy, no random.
    """

    def __init__(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        args = [q, r, p0]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁStateEstimatorǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁStateEstimatorǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁStateEstimatorǁ__init____mutmut_orig(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_1(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 and not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_2(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q < 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_3(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 1.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_4(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_5(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(None):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_6(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(None)
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_7(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 and not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_8(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r < 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_9(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 1.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_10(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_11(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(None):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_12(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(None)
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_13(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 and not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_14(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 < 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_15(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 1.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_16(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_17(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(None):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_18(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(None)

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_19(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = None
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_20(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = None
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_21(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = None

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_22(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = None
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_23(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(None)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_24(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = None
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_25(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(None)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_26(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = None
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_27(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(None, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_28(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, None)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_29(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_30(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, )
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_31(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = None
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_32(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(None, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_33(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, None)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_34(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_35(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, )
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_36(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = None

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_37(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(None, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_38(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, None)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_39(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_40(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, )

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_41(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = None

    def xǁStateEstimatorǁ__init____mutmut_42(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            None, divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_43(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=None
        )

    def xǁStateEstimatorǁ__init____mutmut_44(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_45(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), )

    def xǁStateEstimatorǁ__init____mutmut_46(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(None, p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_47(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, None), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_48(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(p0), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_49(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, ), divergence_count=0
        )

    def xǁStateEstimatorǁ__init____mutmut_50(
        self,
        q: float = _DEFAULT_Q,
        r: float = _DEFAULT_R,
        p0: float = _DEFAULT_P0,
    ) -> None:
        """
        Initialise the StateEstimator.

        Parameters
        ----------
        q : float
            Process noise magnitude. Used as the diagonal of Q = q * I_12.
            Must be > 0.
        r : float
            Observation noise magnitude. Used as diagonal of R = r * I_12.
            Must be > 0.
        p0 : float
            Initial covariance diagonal. P_0 = p0 * I_12.
            Must be > 0.
        """
        if q <= 0.0 or not math.isfinite(q):
            raise ValueError(f"q must be > 0, got {q!r}.")
        if r <= 0.0 or not math.isfinite(r):
            raise ValueError(f"r must be > 0, got {r!r}.")
        if p0 <= 0.0 or not math.isfinite(p0):
            raise ValueError(f"p0 must be > 0, got {p0!r}.")

        self._q: float = q
        self._r: float = r
        self._p0: float = p0

        # System matrices (fixed, identity-based).
        # F: state transition matrix = I_12 (random walk)
        # H: observation matrix = I_12 (full state observation)
        # Q: process noise covariance = q * I_12
        # R: observation noise covariance = r * I_12
        self._F: List[List[float]] = _identity(_DIM)
        self._H: List[List[float]] = _identity(_DIM)
        self._Q: List[List[float]] = _scalar_diag(_DIM, q)
        self._R: List[List[float]] = _scalar_diag(_DIM, r)
        self._P0_mat: List[List[float]] = _scalar_diag(_DIM, p0)

        # Initial covariance state.
        self._ks: KalmanState = KalmanState.from_matrix(
            _scalar_diag(_DIM, p0), divergence_count=1
        )
    
    xǁStateEstimatorǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁStateEstimatorǁ__init____mutmut_1': xǁStateEstimatorǁ__init____mutmut_1, 
        'xǁStateEstimatorǁ__init____mutmut_2': xǁStateEstimatorǁ__init____mutmut_2, 
        'xǁStateEstimatorǁ__init____mutmut_3': xǁStateEstimatorǁ__init____mutmut_3, 
        'xǁStateEstimatorǁ__init____mutmut_4': xǁStateEstimatorǁ__init____mutmut_4, 
        'xǁStateEstimatorǁ__init____mutmut_5': xǁStateEstimatorǁ__init____mutmut_5, 
        'xǁStateEstimatorǁ__init____mutmut_6': xǁStateEstimatorǁ__init____mutmut_6, 
        'xǁStateEstimatorǁ__init____mutmut_7': xǁStateEstimatorǁ__init____mutmut_7, 
        'xǁStateEstimatorǁ__init____mutmut_8': xǁStateEstimatorǁ__init____mutmut_8, 
        'xǁStateEstimatorǁ__init____mutmut_9': xǁStateEstimatorǁ__init____mutmut_9, 
        'xǁStateEstimatorǁ__init____mutmut_10': xǁStateEstimatorǁ__init____mutmut_10, 
        'xǁStateEstimatorǁ__init____mutmut_11': xǁStateEstimatorǁ__init____mutmut_11, 
        'xǁStateEstimatorǁ__init____mutmut_12': xǁStateEstimatorǁ__init____mutmut_12, 
        'xǁStateEstimatorǁ__init____mutmut_13': xǁStateEstimatorǁ__init____mutmut_13, 
        'xǁStateEstimatorǁ__init____mutmut_14': xǁStateEstimatorǁ__init____mutmut_14, 
        'xǁStateEstimatorǁ__init____mutmut_15': xǁStateEstimatorǁ__init____mutmut_15, 
        'xǁStateEstimatorǁ__init____mutmut_16': xǁStateEstimatorǁ__init____mutmut_16, 
        'xǁStateEstimatorǁ__init____mutmut_17': xǁStateEstimatorǁ__init____mutmut_17, 
        'xǁStateEstimatorǁ__init____mutmut_18': xǁStateEstimatorǁ__init____mutmut_18, 
        'xǁStateEstimatorǁ__init____mutmut_19': xǁStateEstimatorǁ__init____mutmut_19, 
        'xǁStateEstimatorǁ__init____mutmut_20': xǁStateEstimatorǁ__init____mutmut_20, 
        'xǁStateEstimatorǁ__init____mutmut_21': xǁStateEstimatorǁ__init____mutmut_21, 
        'xǁStateEstimatorǁ__init____mutmut_22': xǁStateEstimatorǁ__init____mutmut_22, 
        'xǁStateEstimatorǁ__init____mutmut_23': xǁStateEstimatorǁ__init____mutmut_23, 
        'xǁStateEstimatorǁ__init____mutmut_24': xǁStateEstimatorǁ__init____mutmut_24, 
        'xǁStateEstimatorǁ__init____mutmut_25': xǁStateEstimatorǁ__init____mutmut_25, 
        'xǁStateEstimatorǁ__init____mutmut_26': xǁStateEstimatorǁ__init____mutmut_26, 
        'xǁStateEstimatorǁ__init____mutmut_27': xǁStateEstimatorǁ__init____mutmut_27, 
        'xǁStateEstimatorǁ__init____mutmut_28': xǁStateEstimatorǁ__init____mutmut_28, 
        'xǁStateEstimatorǁ__init____mutmut_29': xǁStateEstimatorǁ__init____mutmut_29, 
        'xǁStateEstimatorǁ__init____mutmut_30': xǁStateEstimatorǁ__init____mutmut_30, 
        'xǁStateEstimatorǁ__init____mutmut_31': xǁStateEstimatorǁ__init____mutmut_31, 
        'xǁStateEstimatorǁ__init____mutmut_32': xǁStateEstimatorǁ__init____mutmut_32, 
        'xǁStateEstimatorǁ__init____mutmut_33': xǁStateEstimatorǁ__init____mutmut_33, 
        'xǁStateEstimatorǁ__init____mutmut_34': xǁStateEstimatorǁ__init____mutmut_34, 
        'xǁStateEstimatorǁ__init____mutmut_35': xǁStateEstimatorǁ__init____mutmut_35, 
        'xǁStateEstimatorǁ__init____mutmut_36': xǁStateEstimatorǁ__init____mutmut_36, 
        'xǁStateEstimatorǁ__init____mutmut_37': xǁStateEstimatorǁ__init____mutmut_37, 
        'xǁStateEstimatorǁ__init____mutmut_38': xǁStateEstimatorǁ__init____mutmut_38, 
        'xǁStateEstimatorǁ__init____mutmut_39': xǁStateEstimatorǁ__init____mutmut_39, 
        'xǁStateEstimatorǁ__init____mutmut_40': xǁStateEstimatorǁ__init____mutmut_40, 
        'xǁStateEstimatorǁ__init____mutmut_41': xǁStateEstimatorǁ__init____mutmut_41, 
        'xǁStateEstimatorǁ__init____mutmut_42': xǁStateEstimatorǁ__init____mutmut_42, 
        'xǁStateEstimatorǁ__init____mutmut_43': xǁStateEstimatorǁ__init____mutmut_43, 
        'xǁStateEstimatorǁ__init____mutmut_44': xǁStateEstimatorǁ__init____mutmut_44, 
        'xǁStateEstimatorǁ__init____mutmut_45': xǁStateEstimatorǁ__init____mutmut_45, 
        'xǁStateEstimatorǁ__init____mutmut_46': xǁStateEstimatorǁ__init____mutmut_46, 
        'xǁStateEstimatorǁ__init____mutmut_47': xǁStateEstimatorǁ__init____mutmut_47, 
        'xǁStateEstimatorǁ__init____mutmut_48': xǁStateEstimatorǁ__init____mutmut_48, 
        'xǁStateEstimatorǁ__init____mutmut_49': xǁStateEstimatorǁ__init____mutmut_49, 
        'xǁStateEstimatorǁ__init____mutmut_50': xǁStateEstimatorǁ__init____mutmut_50
    }
    xǁStateEstimatorǁ__init____mutmut_orig.__name__ = 'xǁStateEstimatorǁ__init__'

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, state: LatentState) -> LatentState:
        args = [state]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁStateEstimatorǁpredict__mutmut_orig'), object.__getattribute__(self, 'xǁStateEstimatorǁpredict__mutmut_mutants'), args, kwargs, self)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_orig(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_1(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_2(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                None
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_3(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(None).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_4(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = None

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_5(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = None
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_6(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(None, self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_7(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, None)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_8(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_9(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, )
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_10(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = None
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_11(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = _symmetrise(None)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_12(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = None

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_13(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(None)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_14(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = None

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_15(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(None, self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_16(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, None)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_17(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(self._ks.divergence_count)

        # State vector unchanged (F = I).
        return state

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁStateEstimatorǁpredict__mutmut_18(self, state: LatentState) -> LatentState:
        """
        Kalman predict step.

        Propagates the state through the transition model and updates the
        internal covariance prediction:
          x_pred = F * x        (F = I, so x_pred = x)
          P_pred = F * P * F^T + Q

        Parameters
        ----------
        state : LatentState
            Current latent state estimate.

        Returns
        -------
        LatentState
            Predicted state (unchanged for F = I, but P is updated internally).

        Notes
        -----
        For F = I, the state vector is unchanged. The covariance grows
        by the process noise Q at each predict step.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )

        P: List[List[float]] = self._ks.as_matrix()

        # P_pred = F * P * F^T + Q  (F = I => P_pred = P + Q)
        P_pred: List[List[float]] = _mat_add(P, self._Q)
        P_pred = _symmetrise(P_pred)
        P_pred = _floor_diag(P_pred)

        # Update internal state (only covariance changes at predict step).
        self._ks = KalmanState.from_matrix(P_pred, )

        # State vector unchanged (F = I).
        return state
    
    xǁStateEstimatorǁpredict__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁStateEstimatorǁpredict__mutmut_1': xǁStateEstimatorǁpredict__mutmut_1, 
        'xǁStateEstimatorǁpredict__mutmut_2': xǁStateEstimatorǁpredict__mutmut_2, 
        'xǁStateEstimatorǁpredict__mutmut_3': xǁStateEstimatorǁpredict__mutmut_3, 
        'xǁStateEstimatorǁpredict__mutmut_4': xǁStateEstimatorǁpredict__mutmut_4, 
        'xǁStateEstimatorǁpredict__mutmut_5': xǁStateEstimatorǁpredict__mutmut_5, 
        'xǁStateEstimatorǁpredict__mutmut_6': xǁStateEstimatorǁpredict__mutmut_6, 
        'xǁStateEstimatorǁpredict__mutmut_7': xǁStateEstimatorǁpredict__mutmut_7, 
        'xǁStateEstimatorǁpredict__mutmut_8': xǁStateEstimatorǁpredict__mutmut_8, 
        'xǁStateEstimatorǁpredict__mutmut_9': xǁStateEstimatorǁpredict__mutmut_9, 
        'xǁStateEstimatorǁpredict__mutmut_10': xǁStateEstimatorǁpredict__mutmut_10, 
        'xǁStateEstimatorǁpredict__mutmut_11': xǁStateEstimatorǁpredict__mutmut_11, 
        'xǁStateEstimatorǁpredict__mutmut_12': xǁStateEstimatorǁpredict__mutmut_12, 
        'xǁStateEstimatorǁpredict__mutmut_13': xǁStateEstimatorǁpredict__mutmut_13, 
        'xǁStateEstimatorǁpredict__mutmut_14': xǁStateEstimatorǁpredict__mutmut_14, 
        'xǁStateEstimatorǁpredict__mutmut_15': xǁStateEstimatorǁpredict__mutmut_15, 
        'xǁStateEstimatorǁpredict__mutmut_16': xǁStateEstimatorǁpredict__mutmut_16, 
        'xǁStateEstimatorǁpredict__mutmut_17': xǁStateEstimatorǁpredict__mutmut_17, 
        'xǁStateEstimatorǁpredict__mutmut_18': xǁStateEstimatorǁpredict__mutmut_18
    }
    xǁStateEstimatorǁpredict__mutmut_orig.__name__ = 'xǁStateEstimatorǁpredict'

    def update(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        args = [state, observation]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁStateEstimatorǁupdate__mutmut_orig'), object.__getattribute__(self, 'xǁStateEstimatorǁupdate__mutmut_mutants'), args, kwargs, self)

    def xǁStateEstimatorǁupdate__mutmut_orig(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_1(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_2(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                None
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_3(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(None).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_4(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is not None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_5(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError(None)

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_6(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("XXobservation must be a dict, got None.XX")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_7(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got none.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_8(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("OBSERVATION MUST BE A DICT, GOT NONE.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_9(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = None
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_10(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(None)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_11(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = None

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_12(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = None
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_13(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = None
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_14(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(None):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_15(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = None
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_16(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(None, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_17(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_18(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, )
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_19(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None or math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_20(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_21(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(None):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_22(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(None)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_23(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(None)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_24(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(False)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_25(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(None)   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_26(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(None)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_27(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(True)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_28(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = None

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_29(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(None, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_30(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, None)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_31(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_32(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, )

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_33(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = None

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_34(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(None)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_35(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = None

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_36(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(None, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_37(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, None)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_38(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_39(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, )

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_40(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(None):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_41(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_42(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(None):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_43(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = None

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_44(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 1.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_45(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = None

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_46(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(None, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_47(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, None)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_48(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_49(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, )

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_50(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = None
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_51(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(None, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_52(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, None)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_53(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_54(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, )
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_55(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = None

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_56(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(None, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_57(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, None)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_58(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_59(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, )

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_60(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = None
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_61(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(None, K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_62(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), None)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_63(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_64(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), )
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_65(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(None), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_66(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = None
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_67(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(None)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_68(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = None
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_69(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(None)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_70(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = None

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_71(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            None,
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_72(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            None,
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_73(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_74(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_75(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(None, I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_76(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), None),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_77(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_78(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), ),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_79(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(None, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_80(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, None), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_81(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_82(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, ), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_83(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(None, KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_84(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), None),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_85(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_86(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), ),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_87(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(None, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_88(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, None), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_89(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_90(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, ), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_91(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = None
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_92(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(None)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_93(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = None

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_94(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(None)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_95(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = None
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_96(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = None
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_97(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(None)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_98(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond >= DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_99(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = None
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_100(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(None) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_101(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count = 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_102(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count -= 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_103(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 2

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_104(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = None

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_105(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(None, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_106(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, None)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_107(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_108(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, )

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_109(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = None
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_110(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(None, state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_111(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, None)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_112(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(state)
        return updated_state

    def xǁStateEstimatorǁupdate__mutmut_113(
        self,
        state: LatentState,
        observation: Dict[str, float],
    ) -> LatentState:
        """
        Kalman update step.

        Incorporates a new observation z and computes the updated state
        estimate and covariance:
          y    = z - H * x_pred           (innovation)
          S    = H * P_pred * H^T + R     (innovation covariance)
          K    = P_pred * H^T * S^{-1}    (Kalman gain)
          x    = x_pred + K * y           (updated state)
          P    = (I - K * H) * P_pred     (updated covariance)

        Non-finite observation values are treated as missing: for those
        dimensions, the Kalman gain is set to 0 (no correction).

        Parameters
        ----------
        state : LatentState
            Predicted state (output of predict()).
        observation : Dict[str, float]
            Mapping from LatentState field names to observed values.
            Missing keys use the predicted state value (no correction).
            Non-finite values are treated as missing.

        Returns
        -------
        LatentState
            Updated state estimate incorporating the observation.

        Notes
        -----
        Updates self._ks (covariance) as the sole side effect.
        Divergence detection runs after every update.
        """
        if not isinstance(state, LatentState):
            raise TypeError(
                f"state must be a LatentState, got {type(state).__name__!r}."
            )
        if observation is None:
            raise TypeError("observation must be a dict, got None.")

        x_pred: List[float] = _state_to_vector(state)
        P_pred: List[List[float]] = self._ks.as_matrix()

        # Build observation vector z (substitute predicted value for missing/NaN).
        z: List[float] = []
        valid_mask: List[bool] = []
        for idx, fname in enumerate(_FIELD_NAMES):
            obs_val = observation.get(fname, None)
            if obs_val is not None and math.isfinite(obs_val):
                z.append(obs_val)
                valid_mask.append(True)
            else:
                z.append(x_pred[idx])   # no correction for missing obs
                valid_mask.append(False)

        # H = I_12 (full observation), so:
        # S = P_pred + R
        S: List[List[float]] = _mat_add(P_pred, self._R)

        # S^{-1} via Tikhonov-regularised inversion.
        S_inv: List[List[float]] = _tikhonov_invert(S)

        # K = P_pred * H^T * S^{-1}  (H = I => K = P_pred * S^{-1})
        K: List[List[float]] = _mat_mul(P_pred, S_inv)

        # For dimensions with no valid observation, zero out the Kalman gain row.
        for j in range(_DIM):
            if not valid_mask[j]:
                for i in range(_DIM):
                    K[i][j] = 0.0

        # Innovation y = z - x_pred  (H = I)
        y: List[float] = _vec_sub(z, x_pred)

        # Updated state: x = x_pred + K * y
        K_y: List[float] = _mat_vec_mul(K, y)
        x_upd: List[float] = _vec_add(x_pred, K_y)

        # Updated covariance: P = (I - K*H) * P_pred  (H = I)
        # Use Joseph stabilised form: P = (I-K)*P_pred*(I-K)^T + K*R*K^T
        I_KH: List[List[float]] = _mat_sub(_identity(_DIM), K)
        I_KH_T: List[List[float]] = _transpose(I_KH)
        KT: List[List[float]] = _transpose(K)
        P_upd: List[List[float]] = _mat_add(
            _mat_mul(_mat_mul(I_KH, P_pred), I_KH_T),
            _mat_mul(_mat_mul(K, self._R), KT),
        )

        # Enforce symmetry and positivity.
        P_upd = _symmetrise(P_upd)
        P_upd = _floor_diag(P_upd)

        # Divergence detection.
        div_count: int = self._ks.divergence_count
        cond: float = _condition_number_approx(P_upd)
        if cond > DIVERGENCE_THRESHOLD:
            # Reset covariance to initial value.
            P_upd = [list(row) for row in self._P0_mat]
            div_count += 1

        self._ks = KalmanState.from_matrix(P_upd, div_count)

        # Reconstruct LatentState from updated vector.
        updated_state: LatentState = _vector_to_state(x_upd, )
        return updated_state
    
    xǁStateEstimatorǁupdate__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁStateEstimatorǁupdate__mutmut_1': xǁStateEstimatorǁupdate__mutmut_1, 
        'xǁStateEstimatorǁupdate__mutmut_2': xǁStateEstimatorǁupdate__mutmut_2, 
        'xǁStateEstimatorǁupdate__mutmut_3': xǁStateEstimatorǁupdate__mutmut_3, 
        'xǁStateEstimatorǁupdate__mutmut_4': xǁStateEstimatorǁupdate__mutmut_4, 
        'xǁStateEstimatorǁupdate__mutmut_5': xǁStateEstimatorǁupdate__mutmut_5, 
        'xǁStateEstimatorǁupdate__mutmut_6': xǁStateEstimatorǁupdate__mutmut_6, 
        'xǁStateEstimatorǁupdate__mutmut_7': xǁStateEstimatorǁupdate__mutmut_7, 
        'xǁStateEstimatorǁupdate__mutmut_8': xǁStateEstimatorǁupdate__mutmut_8, 
        'xǁStateEstimatorǁupdate__mutmut_9': xǁStateEstimatorǁupdate__mutmut_9, 
        'xǁStateEstimatorǁupdate__mutmut_10': xǁStateEstimatorǁupdate__mutmut_10, 
        'xǁStateEstimatorǁupdate__mutmut_11': xǁStateEstimatorǁupdate__mutmut_11, 
        'xǁStateEstimatorǁupdate__mutmut_12': xǁStateEstimatorǁupdate__mutmut_12, 
        'xǁStateEstimatorǁupdate__mutmut_13': xǁStateEstimatorǁupdate__mutmut_13, 
        'xǁStateEstimatorǁupdate__mutmut_14': xǁStateEstimatorǁupdate__mutmut_14, 
        'xǁStateEstimatorǁupdate__mutmut_15': xǁStateEstimatorǁupdate__mutmut_15, 
        'xǁStateEstimatorǁupdate__mutmut_16': xǁStateEstimatorǁupdate__mutmut_16, 
        'xǁStateEstimatorǁupdate__mutmut_17': xǁStateEstimatorǁupdate__mutmut_17, 
        'xǁStateEstimatorǁupdate__mutmut_18': xǁStateEstimatorǁupdate__mutmut_18, 
        'xǁStateEstimatorǁupdate__mutmut_19': xǁStateEstimatorǁupdate__mutmut_19, 
        'xǁStateEstimatorǁupdate__mutmut_20': xǁStateEstimatorǁupdate__mutmut_20, 
        'xǁStateEstimatorǁupdate__mutmut_21': xǁStateEstimatorǁupdate__mutmut_21, 
        'xǁStateEstimatorǁupdate__mutmut_22': xǁStateEstimatorǁupdate__mutmut_22, 
        'xǁStateEstimatorǁupdate__mutmut_23': xǁStateEstimatorǁupdate__mutmut_23, 
        'xǁStateEstimatorǁupdate__mutmut_24': xǁStateEstimatorǁupdate__mutmut_24, 
        'xǁStateEstimatorǁupdate__mutmut_25': xǁStateEstimatorǁupdate__mutmut_25, 
        'xǁStateEstimatorǁupdate__mutmut_26': xǁStateEstimatorǁupdate__mutmut_26, 
        'xǁStateEstimatorǁupdate__mutmut_27': xǁStateEstimatorǁupdate__mutmut_27, 
        'xǁStateEstimatorǁupdate__mutmut_28': xǁStateEstimatorǁupdate__mutmut_28, 
        'xǁStateEstimatorǁupdate__mutmut_29': xǁStateEstimatorǁupdate__mutmut_29, 
        'xǁStateEstimatorǁupdate__mutmut_30': xǁStateEstimatorǁupdate__mutmut_30, 
        'xǁStateEstimatorǁupdate__mutmut_31': xǁStateEstimatorǁupdate__mutmut_31, 
        'xǁStateEstimatorǁupdate__mutmut_32': xǁStateEstimatorǁupdate__mutmut_32, 
        'xǁStateEstimatorǁupdate__mutmut_33': xǁStateEstimatorǁupdate__mutmut_33, 
        'xǁStateEstimatorǁupdate__mutmut_34': xǁStateEstimatorǁupdate__mutmut_34, 
        'xǁStateEstimatorǁupdate__mutmut_35': xǁStateEstimatorǁupdate__mutmut_35, 
        'xǁStateEstimatorǁupdate__mutmut_36': xǁStateEstimatorǁupdate__mutmut_36, 
        'xǁStateEstimatorǁupdate__mutmut_37': xǁStateEstimatorǁupdate__mutmut_37, 
        'xǁStateEstimatorǁupdate__mutmut_38': xǁStateEstimatorǁupdate__mutmut_38, 
        'xǁStateEstimatorǁupdate__mutmut_39': xǁStateEstimatorǁupdate__mutmut_39, 
        'xǁStateEstimatorǁupdate__mutmut_40': xǁStateEstimatorǁupdate__mutmut_40, 
        'xǁStateEstimatorǁupdate__mutmut_41': xǁStateEstimatorǁupdate__mutmut_41, 
        'xǁStateEstimatorǁupdate__mutmut_42': xǁStateEstimatorǁupdate__mutmut_42, 
        'xǁStateEstimatorǁupdate__mutmut_43': xǁStateEstimatorǁupdate__mutmut_43, 
        'xǁStateEstimatorǁupdate__mutmut_44': xǁStateEstimatorǁupdate__mutmut_44, 
        'xǁStateEstimatorǁupdate__mutmut_45': xǁStateEstimatorǁupdate__mutmut_45, 
        'xǁStateEstimatorǁupdate__mutmut_46': xǁStateEstimatorǁupdate__mutmut_46, 
        'xǁStateEstimatorǁupdate__mutmut_47': xǁStateEstimatorǁupdate__mutmut_47, 
        'xǁStateEstimatorǁupdate__mutmut_48': xǁStateEstimatorǁupdate__mutmut_48, 
        'xǁStateEstimatorǁupdate__mutmut_49': xǁStateEstimatorǁupdate__mutmut_49, 
        'xǁStateEstimatorǁupdate__mutmut_50': xǁStateEstimatorǁupdate__mutmut_50, 
        'xǁStateEstimatorǁupdate__mutmut_51': xǁStateEstimatorǁupdate__mutmut_51, 
        'xǁStateEstimatorǁupdate__mutmut_52': xǁStateEstimatorǁupdate__mutmut_52, 
        'xǁStateEstimatorǁupdate__mutmut_53': xǁStateEstimatorǁupdate__mutmut_53, 
        'xǁStateEstimatorǁupdate__mutmut_54': xǁStateEstimatorǁupdate__mutmut_54, 
        'xǁStateEstimatorǁupdate__mutmut_55': xǁStateEstimatorǁupdate__mutmut_55, 
        'xǁStateEstimatorǁupdate__mutmut_56': xǁStateEstimatorǁupdate__mutmut_56, 
        'xǁStateEstimatorǁupdate__mutmut_57': xǁStateEstimatorǁupdate__mutmut_57, 
        'xǁStateEstimatorǁupdate__mutmut_58': xǁStateEstimatorǁupdate__mutmut_58, 
        'xǁStateEstimatorǁupdate__mutmut_59': xǁStateEstimatorǁupdate__mutmut_59, 
        'xǁStateEstimatorǁupdate__mutmut_60': xǁStateEstimatorǁupdate__mutmut_60, 
        'xǁStateEstimatorǁupdate__mutmut_61': xǁStateEstimatorǁupdate__mutmut_61, 
        'xǁStateEstimatorǁupdate__mutmut_62': xǁStateEstimatorǁupdate__mutmut_62, 
        'xǁStateEstimatorǁupdate__mutmut_63': xǁStateEstimatorǁupdate__mutmut_63, 
        'xǁStateEstimatorǁupdate__mutmut_64': xǁStateEstimatorǁupdate__mutmut_64, 
        'xǁStateEstimatorǁupdate__mutmut_65': xǁStateEstimatorǁupdate__mutmut_65, 
        'xǁStateEstimatorǁupdate__mutmut_66': xǁStateEstimatorǁupdate__mutmut_66, 
        'xǁStateEstimatorǁupdate__mutmut_67': xǁStateEstimatorǁupdate__mutmut_67, 
        'xǁStateEstimatorǁupdate__mutmut_68': xǁStateEstimatorǁupdate__mutmut_68, 
        'xǁStateEstimatorǁupdate__mutmut_69': xǁStateEstimatorǁupdate__mutmut_69, 
        'xǁStateEstimatorǁupdate__mutmut_70': xǁStateEstimatorǁupdate__mutmut_70, 
        'xǁStateEstimatorǁupdate__mutmut_71': xǁStateEstimatorǁupdate__mutmut_71, 
        'xǁStateEstimatorǁupdate__mutmut_72': xǁStateEstimatorǁupdate__mutmut_72, 
        'xǁStateEstimatorǁupdate__mutmut_73': xǁStateEstimatorǁupdate__mutmut_73, 
        'xǁStateEstimatorǁupdate__mutmut_74': xǁStateEstimatorǁupdate__mutmut_74, 
        'xǁStateEstimatorǁupdate__mutmut_75': xǁStateEstimatorǁupdate__mutmut_75, 
        'xǁStateEstimatorǁupdate__mutmut_76': xǁStateEstimatorǁupdate__mutmut_76, 
        'xǁStateEstimatorǁupdate__mutmut_77': xǁStateEstimatorǁupdate__mutmut_77, 
        'xǁStateEstimatorǁupdate__mutmut_78': xǁStateEstimatorǁupdate__mutmut_78, 
        'xǁStateEstimatorǁupdate__mutmut_79': xǁStateEstimatorǁupdate__mutmut_79, 
        'xǁStateEstimatorǁupdate__mutmut_80': xǁStateEstimatorǁupdate__mutmut_80, 
        'xǁStateEstimatorǁupdate__mutmut_81': xǁStateEstimatorǁupdate__mutmut_81, 
        'xǁStateEstimatorǁupdate__mutmut_82': xǁStateEstimatorǁupdate__mutmut_82, 
        'xǁStateEstimatorǁupdate__mutmut_83': xǁStateEstimatorǁupdate__mutmut_83, 
        'xǁStateEstimatorǁupdate__mutmut_84': xǁStateEstimatorǁupdate__mutmut_84, 
        'xǁStateEstimatorǁupdate__mutmut_85': xǁStateEstimatorǁupdate__mutmut_85, 
        'xǁStateEstimatorǁupdate__mutmut_86': xǁStateEstimatorǁupdate__mutmut_86, 
        'xǁStateEstimatorǁupdate__mutmut_87': xǁStateEstimatorǁupdate__mutmut_87, 
        'xǁStateEstimatorǁupdate__mutmut_88': xǁStateEstimatorǁupdate__mutmut_88, 
        'xǁStateEstimatorǁupdate__mutmut_89': xǁStateEstimatorǁupdate__mutmut_89, 
        'xǁStateEstimatorǁupdate__mutmut_90': xǁStateEstimatorǁupdate__mutmut_90, 
        'xǁStateEstimatorǁupdate__mutmut_91': xǁStateEstimatorǁupdate__mutmut_91, 
        'xǁStateEstimatorǁupdate__mutmut_92': xǁStateEstimatorǁupdate__mutmut_92, 
        'xǁStateEstimatorǁupdate__mutmut_93': xǁStateEstimatorǁupdate__mutmut_93, 
        'xǁStateEstimatorǁupdate__mutmut_94': xǁStateEstimatorǁupdate__mutmut_94, 
        'xǁStateEstimatorǁupdate__mutmut_95': xǁStateEstimatorǁupdate__mutmut_95, 
        'xǁStateEstimatorǁupdate__mutmut_96': xǁStateEstimatorǁupdate__mutmut_96, 
        'xǁStateEstimatorǁupdate__mutmut_97': xǁStateEstimatorǁupdate__mutmut_97, 
        'xǁStateEstimatorǁupdate__mutmut_98': xǁStateEstimatorǁupdate__mutmut_98, 
        'xǁStateEstimatorǁupdate__mutmut_99': xǁStateEstimatorǁupdate__mutmut_99, 
        'xǁStateEstimatorǁupdate__mutmut_100': xǁStateEstimatorǁupdate__mutmut_100, 
        'xǁStateEstimatorǁupdate__mutmut_101': xǁStateEstimatorǁupdate__mutmut_101, 
        'xǁStateEstimatorǁupdate__mutmut_102': xǁStateEstimatorǁupdate__mutmut_102, 
        'xǁStateEstimatorǁupdate__mutmut_103': xǁStateEstimatorǁupdate__mutmut_103, 
        'xǁStateEstimatorǁupdate__mutmut_104': xǁStateEstimatorǁupdate__mutmut_104, 
        'xǁStateEstimatorǁupdate__mutmut_105': xǁStateEstimatorǁupdate__mutmut_105, 
        'xǁStateEstimatorǁupdate__mutmut_106': xǁStateEstimatorǁupdate__mutmut_106, 
        'xǁStateEstimatorǁupdate__mutmut_107': xǁStateEstimatorǁupdate__mutmut_107, 
        'xǁStateEstimatorǁupdate__mutmut_108': xǁStateEstimatorǁupdate__mutmut_108, 
        'xǁStateEstimatorǁupdate__mutmut_109': xǁStateEstimatorǁupdate__mutmut_109, 
        'xǁStateEstimatorǁupdate__mutmut_110': xǁStateEstimatorǁupdate__mutmut_110, 
        'xǁStateEstimatorǁupdate__mutmut_111': xǁStateEstimatorǁupdate__mutmut_111, 
        'xǁStateEstimatorǁupdate__mutmut_112': xǁStateEstimatorǁupdate__mutmut_112, 
        'xǁStateEstimatorǁupdate__mutmut_113': xǁStateEstimatorǁupdate__mutmut_113
    }
    xǁStateEstimatorǁupdate__mutmut_orig.__name__ = 'xǁStateEstimatorǁupdate'

    def get_covariance(self) -> List[List[float]]:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁStateEstimatorǁget_covariance__mutmut_orig'), object.__getattribute__(self, 'xǁStateEstimatorǁget_covariance__mutmut_mutants'), args, kwargs, self)

    def xǁStateEstimatorǁget_covariance__mutmut_orig(self) -> List[List[float]]:
        """
        Return the current covariance matrix P as a 12x12 list-of-lists.

        Returns a deep copy — modifying the returned matrix does not affect
        the internal filter state.

        The returned matrix is guaranteed to be:
          - 12x12
          - Symmetric (P[i][j] == P[j][i] within float tolerance)
          - Positive-definite (all diagonal entries > _P_MIN_DIAG)
        """
        P: List[List[float]] = self._ks.as_matrix()
        return [list(row) for row in P]

    def xǁStateEstimatorǁget_covariance__mutmut_1(self) -> List[List[float]]:
        """
        Return the current covariance matrix P as a 12x12 list-of-lists.

        Returns a deep copy — modifying the returned matrix does not affect
        the internal filter state.

        The returned matrix is guaranteed to be:
          - 12x12
          - Symmetric (P[i][j] == P[j][i] within float tolerance)
          - Positive-definite (all diagonal entries > _P_MIN_DIAG)
        """
        P: List[List[float]] = None
        return [list(row) for row in P]

    def xǁStateEstimatorǁget_covariance__mutmut_2(self) -> List[List[float]]:
        """
        Return the current covariance matrix P as a 12x12 list-of-lists.

        Returns a deep copy — modifying the returned matrix does not affect
        the internal filter state.

        The returned matrix is guaranteed to be:
          - 12x12
          - Symmetric (P[i][j] == P[j][i] within float tolerance)
          - Positive-definite (all diagonal entries > _P_MIN_DIAG)
        """
        P: List[List[float]] = self._ks.as_matrix()
        return [list(None) for row in P]
    
    xǁStateEstimatorǁget_covariance__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁStateEstimatorǁget_covariance__mutmut_1': xǁStateEstimatorǁget_covariance__mutmut_1, 
        'xǁStateEstimatorǁget_covariance__mutmut_2': xǁStateEstimatorǁget_covariance__mutmut_2
    }
    xǁStateEstimatorǁget_covariance__mutmut_orig.__name__ = 'xǁStateEstimatorǁget_covariance'

    @property
    def divergence_count(self) -> int:
        """Number of times the filter has been reset due to divergence."""
        return self._ks.divergence_count

    def reset(self) -> None:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁStateEstimatorǁreset__mutmut_orig'), object.__getattribute__(self, 'xǁStateEstimatorǁreset__mutmut_mutants'), args, kwargs, self)

    def xǁStateEstimatorǁreset__mutmut_orig(self) -> None:
        """
        Reset the covariance matrix P to the initial value P_0 = p0 * I_12.
        Does not reset the divergence count.
        """
        self._ks = KalmanState.from_matrix(
            _scalar_diag(_DIM, self._p0),
            divergence_count=self._ks.divergence_count,
        )

    def xǁStateEstimatorǁreset__mutmut_1(self) -> None:
        """
        Reset the covariance matrix P to the initial value P_0 = p0 * I_12.
        Does not reset the divergence count.
        """
        self._ks = None

    def xǁStateEstimatorǁreset__mutmut_2(self) -> None:
        """
        Reset the covariance matrix P to the initial value P_0 = p0 * I_12.
        Does not reset the divergence count.
        """
        self._ks = KalmanState.from_matrix(
            None,
            divergence_count=self._ks.divergence_count,
        )

    def xǁStateEstimatorǁreset__mutmut_3(self) -> None:
        """
        Reset the covariance matrix P to the initial value P_0 = p0 * I_12.
        Does not reset the divergence count.
        """
        self._ks = KalmanState.from_matrix(
            _scalar_diag(_DIM, self._p0),
            divergence_count=None,
        )

    def xǁStateEstimatorǁreset__mutmut_4(self) -> None:
        """
        Reset the covariance matrix P to the initial value P_0 = p0 * I_12.
        Does not reset the divergence count.
        """
        self._ks = KalmanState.from_matrix(
            divergence_count=self._ks.divergence_count,
        )

    def xǁStateEstimatorǁreset__mutmut_5(self) -> None:
        """
        Reset the covariance matrix P to the initial value P_0 = p0 * I_12.
        Does not reset the divergence count.
        """
        self._ks = KalmanState.from_matrix(
            _scalar_diag(_DIM, self._p0),
            )

    def xǁStateEstimatorǁreset__mutmut_6(self) -> None:
        """
        Reset the covariance matrix P to the initial value P_0 = p0 * I_12.
        Does not reset the divergence count.
        """
        self._ks = KalmanState.from_matrix(
            _scalar_diag(None, self._p0),
            divergence_count=self._ks.divergence_count,
        )

    def xǁStateEstimatorǁreset__mutmut_7(self) -> None:
        """
        Reset the covariance matrix P to the initial value P_0 = p0 * I_12.
        Does not reset the divergence count.
        """
        self._ks = KalmanState.from_matrix(
            _scalar_diag(_DIM, None),
            divergence_count=self._ks.divergence_count,
        )

    def xǁStateEstimatorǁreset__mutmut_8(self) -> None:
        """
        Reset the covariance matrix P to the initial value P_0 = p0 * I_12.
        Does not reset the divergence count.
        """
        self._ks = KalmanState.from_matrix(
            _scalar_diag(self._p0),
            divergence_count=self._ks.divergence_count,
        )

    def xǁStateEstimatorǁreset__mutmut_9(self) -> None:
        """
        Reset the covariance matrix P to the initial value P_0 = p0 * I_12.
        Does not reset the divergence count.
        """
        self._ks = KalmanState.from_matrix(
            _scalar_diag(_DIM, ),
            divergence_count=self._ks.divergence_count,
        )
    
    xǁStateEstimatorǁreset__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁStateEstimatorǁreset__mutmut_1': xǁStateEstimatorǁreset__mutmut_1, 
        'xǁStateEstimatorǁreset__mutmut_2': xǁStateEstimatorǁreset__mutmut_2, 
        'xǁStateEstimatorǁreset__mutmut_3': xǁStateEstimatorǁreset__mutmut_3, 
        'xǁStateEstimatorǁreset__mutmut_4': xǁStateEstimatorǁreset__mutmut_4, 
        'xǁStateEstimatorǁreset__mutmut_5': xǁStateEstimatorǁreset__mutmut_5, 
        'xǁStateEstimatorǁreset__mutmut_6': xǁStateEstimatorǁreset__mutmut_6, 
        'xǁStateEstimatorǁreset__mutmut_7': xǁStateEstimatorǁreset__mutmut_7, 
        'xǁStateEstimatorǁreset__mutmut_8': xǁStateEstimatorǁreset__mutmut_8, 
        'xǁStateEstimatorǁreset__mutmut_9': xǁStateEstimatorǁreset__mutmut_9
    }
    xǁStateEstimatorǁreset__mutmut_orig.__name__ = 'xǁStateEstimatorǁreset'
