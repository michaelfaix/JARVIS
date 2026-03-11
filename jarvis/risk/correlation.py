# =============================================================================
# jarvis/risk/correlation.py -- Dynamic Correlation Model (Phase MA-5)
#
# Time-varying, regime-dependent correlation estimation for portfolio risk.
# Computes base correlations from return series, applies regime adjustments,
# and enforces positive semi-definite matrix constraint.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   correlation.py -> jarvis.core.regime (CorrelationRegimeState,
#                     GlobalRegimeState, HierarchicalRegime)
#   correlation.py -> (stdlib + math only)
#
# DETERMINISM GUARANTEES: DET-01 through DET-07 enforced.
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly.
#   DET-03  No side effects.
#   DET-05  Same inputs -> same outputs.
#   DET-06  Fixed literals not parameterizable.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01: No numpy. Pure stdlib math.
#   PROHIBITED-02: No file I/O.
#   PROHIBITED-03: No logging/print.
#   PROHIBITED-05: No global mutable state.
#   PROHIBITED-08: No new Enum definitions.
#   PROHIBITED-09: No string-based regime branching (uses Enum instances).
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from jarvis.core.regime import (
    CorrelationRegimeState,
    GlobalRegimeState,
    HierarchicalRegime,
)


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

# Default rolling window for base correlation
DEFAULT_LOOKBACK: int = 90

# Crisis correlation override (FAS: all correlations -> 0.8 in crisis)
CRISIS_CORRELATION: float = 0.8

# Crisis blend weights (FAS: 20% base, 80% crisis)
CRISIS_BASE_WEIGHT: float = 0.2
CRISIS_OVERRIDE_WEIGHT: float = 0.8

# Divergence scaling (FAS: correlations * 0.7 in divergence)
DIVERGENCE_SCALING: float = 0.7

# Panic correlation boost (FAS: off-diagonal * 1.5, cap at 0.95)
PANIC_BOOST: float = 1.5
PANIC_CAP: float = 0.95

# PSD eigenvalue floor
PSD_EIGENVALUE_FLOOR: float = 1e-8

# Maximum correlation matrix size (for safety)
MAX_MATRIX_SIZE: int = 100


# =============================================================================
# SECTION 2 -- RESULT DATACLASS
# =============================================================================

@dataclass(frozen=True)
class CorrelationMatrixResult:
    """Dynamic correlation matrix result.

    Attributes:
        matrix: NxN correlation matrix as tuple of tuples (immutable).
        symbols: Ordered list of symbols corresponding to matrix rows/cols.
        regime_state: Correlation regime state applied.
        average_correlation: Mean off-diagonal correlation.
        is_crisis_override: Whether crisis correlation override was applied.
        result_hash: SHA-256[:16] for determinism verification.
    """
    matrix: Tuple[Tuple[float, ...], ...]
    symbols: Tuple[str, ...]
    regime_state: CorrelationRegimeState
    average_correlation: float
    is_crisis_override: bool
    result_hash: str

    def get_correlation(self, symbol_a: str, symbol_b: str) -> float:
        """Look up correlation between two symbols.

        Args:
            symbol_a: First symbol.
            symbol_b: Second symbol.

        Returns:
            Correlation value.

        Raises:
            ValueError: If symbol not found.
        """
        if symbol_a not in self.symbols:
            raise ValueError(f"Symbol not found: {symbol_a}")
        if symbol_b not in self.symbols:
            raise ValueError(f"Symbol not found: {symbol_b}")
        i = self.symbols.index(symbol_a)
        j = self.symbols.index(symbol_b)
        return self.matrix[i][j]


# =============================================================================
# SECTION 3 -- PURE MATH HELPERS (stdlib only, DET-01)
# =============================================================================

def _pearson(xs: List[float], ys: List[float]) -> float:
    """Pearson correlation coefficient. Pure stdlib.

    Returns 0.0 if either series has zero variance or lengths differ.
    """
    n = len(xs)
    if n < 2 or n != len(ys):
        return 0.0

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    cov = 0.0
    var_x = 0.0
    var_y = 0.0

    for i in range(n):
        dx = xs[i] - mean_x
        dy = ys[i] - mean_y
        cov += dx * dy
        var_x += dx * dx
        var_y += dy * dy

    if var_x < 1e-15 or var_y < 1e-15:
        return 0.0

    r = cov / math.sqrt(var_x * var_y)
    return max(-1.0, min(1.0, r))


def _compute_base_correlation(
    returns: Dict[str, List[float]],
    symbols: List[str],
    lookback: int,
) -> List[List[float]]:
    """Compute rolling Pearson correlation matrix.

    Args:
        returns: Dict mapping symbol -> return series.
        symbols: Ordered list of symbols.
        lookback: Number of most recent returns to use.

    Returns:
        NxN correlation matrix as list of lists.
    """
    n = len(symbols)
    matrix = [[0.0] * n for _ in range(n)]

    # Extract truncated return series
    series = {}
    for s in symbols:
        raw = returns.get(s, [])
        series[s] = raw[-lookback:] if len(raw) > lookback else raw

    for i in range(n):
        matrix[i][i] = 1.0
        for j in range(i + 1, n):
            r = _pearson(series[symbols[i]], series[symbols[j]])
            matrix[i][j] = r
            matrix[j][i] = r

    return matrix


def _apply_crisis_override(
    base: List[List[float]],
) -> List[List[float]]:
    """Apply crisis correlation override: blend 20% base + 80% crisis.

    FAS: In crisis, all off-diagonal correlations forced toward 0.8.
    """
    n = len(base)
    result = [[0.0] * n for _ in range(n)]

    for i in range(n):
        result[i][i] = 1.0
        for j in range(i + 1, n):
            blended = (
                CRISIS_BASE_WEIGHT * base[i][j]
                + CRISIS_OVERRIDE_WEIGHT * CRISIS_CORRELATION
            )
            result[i][j] = max(-1.0, min(1.0, blended))
            result[j][i] = result[i][j]

    return result


def _apply_divergence_scaling(
    base: List[List[float]],
) -> List[List[float]]:
    """Apply divergence scaling: off-diagonal * 0.7.

    FAS: In divergence, correlations are lower (good for diversification).
    """
    n = len(base)
    result = [[0.0] * n for _ in range(n)]

    for i in range(n):
        result[i][i] = 1.0
        for j in range(i + 1, n):
            scaled = base[i][j] * DIVERGENCE_SCALING
            result[i][j] = max(-1.0, min(1.0, scaled))
            result[j][i] = result[i][j]

    return result


def _apply_panic_boost(
    base: List[List[float]],
) -> List[List[float]]:
    """Apply panic correlation boost: off-diagonal * 1.5, cap at 0.95.

    FAS: In panic, all correlations increase.
    """
    n = len(base)
    result = [[0.0] * n for _ in range(n)]

    for i in range(n):
        result[i][i] = 1.0
        for j in range(i + 1, n):
            boosted = base[i][j] * PANIC_BOOST
            capped = max(-PANIC_CAP, min(PANIC_CAP, boosted))
            result[i][j] = capped
            result[j][i] = capped

    return result


def _nearest_psd(matrix: List[List[float]]) -> List[List[float]]:
    """Project matrix to nearest positive semi-definite.

    Uses iterative diagonal adjustment (Higham-like simplified).
    For small matrices this is sufficient without numpy eigendecomposition.

    Ensures all eigenvalues (via Gershgorin bounds) are non-negative,
    and diagonal remains 1.0.
    """
    n = len(matrix)
    if n <= 1:
        return [[1.0]] if n == 1 else []

    # Copy
    result = [row[:] for row in matrix]

    # Ensure symmetry
    for i in range(n):
        for j in range(i + 1, n):
            avg = (result[i][j] + result[j][i]) / 2.0
            result[i][j] = avg
            result[j][i] = avg

    # Clip off-diagonal to [-1, 1]
    for i in range(n):
        result[i][i] = 1.0
        for j in range(n):
            if i != j:
                result[i][j] = max(-1.0, min(1.0, result[i][j]))

    # Check if already PSD via Cholesky attempt
    if _is_psd(result):
        return result

    # Shrink off-diagonal toward zero until PSD
    for shrink_iter in range(50):
        alpha = 1.0 - (shrink_iter + 1) * 0.02
        if alpha <= 0.0:
            # Identity matrix as fallback
            return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

        shrunk = [[0.0] * n for _ in range(n)]
        for i in range(n):
            shrunk[i][i] = 1.0
            for j in range(i + 1, n):
                val = result[i][j] * alpha
                shrunk[i][j] = val
                shrunk[j][i] = val

        if _is_psd(shrunk):
            return shrunk

    # Ultimate fallback: identity
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def _is_psd(matrix: List[List[float]]) -> bool:
    """Check if matrix is positive semi-definite via Cholesky attempt."""
    n = len(matrix)
    L = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i + 1):
            s = sum(L[i][k] * L[j][k] for k in range(j))
            if i == j:
                val = matrix[i][i] - s
                if val < -1e-10:
                    return False
                L[i][j] = math.sqrt(max(val, 0.0))
            else:
                if abs(L[j][j]) < 1e-15:
                    L[i][j] = 0.0
                else:
                    L[i][j] = (matrix[i][j] - s) / L[j][j]
    return True


def _average_off_diagonal(matrix: List[List[float]]) -> float:
    """Compute mean of off-diagonal elements."""
    n = len(matrix)
    if n < 2:
        return 0.0

    total = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += matrix[i][j]
            count += 1

    return total / count if count > 0 else 0.0


# =============================================================================
# SECTION 4 -- DYNAMIC CORRELATION MODEL
# =============================================================================

class DynamicCorrelationModel:
    """Time-varying, regime-dependent correlation model.

    Estimates current correlation matrix from return series and adjusts
    based on the active regime:
    - BREAKDOWN: crisis override (all correlations -> 0.8)
    - DIVERGENCE: reduce correlations (* 0.7)
    - COUPLED: slight boost (normal matrix)
    - NORMAL: base correlations

    Additionally, if global regime is CRISIS, panic boost is applied.

    All inputs are explicit parameters (DET-02).
    No internal state retained between calls (DET-03, PROHIBITED-05).
    """

    def estimate(
        self,
        *,
        returns: Dict[str, List[float]],
        symbols: List[str],
        regime: HierarchicalRegime,
        lookback: int = DEFAULT_LOOKBACK,
    ) -> CorrelationMatrixResult:
        """Estimate dynamic correlation matrix.

        Args:
            returns: Dict mapping symbol -> return series.
            symbols: Ordered list of symbols to include.
            regime: Current HierarchicalRegime.
            lookback: Rolling window for base correlation.

        Returns:
            CorrelationMatrixResult with regime-adjusted matrix.
        """
        n = len(symbols)

        if n == 0:
            return self._empty_result(regime.correlation_regime)

        if n == 1:
            return self._single_asset_result(
                symbols[0], regime.correlation_regime
            )

        # 1. Base correlation
        base = _compute_base_correlation(returns, symbols, lookback)

        # 2. Regime adjustment
        is_crisis = False
        corr_regime = regime.correlation_regime

        if corr_regime == CorrelationRegimeState.BREAKDOWN:
            adjusted = _apply_crisis_override(base)
            is_crisis = True
        elif corr_regime == CorrelationRegimeState.DIVERGENCE:
            adjusted = _apply_divergence_scaling(base)
        elif regime.global_regime == GlobalRegimeState.CRISIS:
            adjusted = _apply_panic_boost(base)
            is_crisis = True
        else:
            adjusted = base

        # 3. Ensure PSD
        psd = _nearest_psd(adjusted)

        # 4. Compute average off-diagonal
        avg_corr = _average_off_diagonal(psd)

        # Convert to immutable tuples
        matrix_tuple = tuple(tuple(row) for row in psd)
        symbols_tuple = tuple(symbols)

        # Deterministic hash
        payload = {
            "symbols": list(symbols_tuple),
            "avg_corr": round(avg_corr, 8),
            "regime": corr_regime.value,
            "is_crisis": is_crisis,
            "n": n,
        }
        result_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]

        return CorrelationMatrixResult(
            matrix=matrix_tuple,
            symbols=symbols_tuple,
            regime_state=corr_regime,
            average_correlation=avg_corr,
            is_crisis_override=is_crisis,
            result_hash=result_hash,
        )

    def estimate_from_matrix(
        self,
        *,
        base_matrix: List[List[float]],
        symbols: List[str],
        regime: HierarchicalRegime,
    ) -> CorrelationMatrixResult:
        """Apply regime adjustments to a pre-computed correlation matrix.

        Args:
            base_matrix: Pre-computed NxN correlation matrix.
            symbols: Ordered symbol list.
            regime: Current HierarchicalRegime.

        Returns:
            CorrelationMatrixResult with regime-adjusted matrix.
        """
        n = len(symbols)
        corr_regime = regime.correlation_regime
        is_crisis = False

        if corr_regime == CorrelationRegimeState.BREAKDOWN:
            adjusted = _apply_crisis_override(base_matrix)
            is_crisis = True
        elif corr_regime == CorrelationRegimeState.DIVERGENCE:
            adjusted = _apply_divergence_scaling(base_matrix)
        elif regime.global_regime == GlobalRegimeState.CRISIS:
            adjusted = _apply_panic_boost(base_matrix)
            is_crisis = True
        else:
            adjusted = [row[:] for row in base_matrix]

        psd = _nearest_psd(adjusted)
        avg_corr = _average_off_diagonal(psd)

        matrix_tuple = tuple(tuple(row) for row in psd)
        symbols_tuple = tuple(symbols)

        payload = {
            "symbols": list(symbols_tuple),
            "avg_corr": round(avg_corr, 8),
            "regime": corr_regime.value,
            "is_crisis": is_crisis,
            "n": n,
        }
        result_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]

        return CorrelationMatrixResult(
            matrix=matrix_tuple,
            symbols=symbols_tuple,
            regime_state=corr_regime,
            average_correlation=avg_corr,
            is_crisis_override=is_crisis,
            result_hash=result_hash,
        )

    # -----------------------------------------------------------------
    # EDGE CASE HELPERS
    # -----------------------------------------------------------------

    def _empty_result(
        self, corr_regime: CorrelationRegimeState
    ) -> CorrelationMatrixResult:
        payload = {"symbols": [], "avg_corr": 0.0, "regime": corr_regime.value,
                   "is_crisis": False, "n": 0}
        h = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        return CorrelationMatrixResult(
            matrix=(), symbols=(), regime_state=corr_regime,
            average_correlation=0.0, is_crisis_override=False, result_hash=h,
        )

    def _single_asset_result(
        self, symbol: str, corr_regime: CorrelationRegimeState
    ) -> CorrelationMatrixResult:
        payload = {"symbols": [symbol], "avg_corr": 0.0,
                   "regime": corr_regime.value, "is_crisis": False, "n": 1}
        h = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        return CorrelationMatrixResult(
            matrix=((1.0,),), symbols=(symbol,), regime_state=corr_regime,
            average_correlation=0.0, is_crisis_override=False, result_hash=h,
        )
