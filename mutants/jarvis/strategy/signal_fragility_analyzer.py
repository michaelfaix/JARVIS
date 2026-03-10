# =============================================================================
# JARVIS v6.1.0 -- SIGNAL FRAGILITY ANALYZER
# File:   jarvis/strategy/signal_fragility_analyzer.py
# Version: 1.0.0
# =============================================================================
#
# SCOPE
# -----
# Deterministic local perturbation analysis of a strategy signal.
# Measures signal robustness across four key input dimensions:
#   - strategy parameters (lookback, threshold, etc.)
#   - volatility
#   - bid-ask spread proxy
#   - cross-asset correlation coefficient
#
# Uses central finite differences with fixed perturbation magnitudes.
# No Monte Carlo. No random sampling. No stochastic components.
#
# CLASSIFICATION: Phase 3 — Decision Quality sub-component.
# Output feeds ONLY DecisionQualityEngine.
# May NOT directly alter Risk Engine thresholds.
#
# PUBLIC SYMBOLS
# --------------
#   FRAGILITY_VOL_DELTA          float constant (0.05)
#   FRAGILITY_SPREAD_DELTA       float constant (0.05)
#   FRAGILITY_CORR_DELTA         float constant (0.05)
#   FRAGILITY_PARAM_DELTA        float constant (0.01)
#   FRAGILITY_HIGH_THRESHOLD     float constant (0.65)
#   W_PARAM                      float constant (0.30)
#   W_VOL                        float constant (0.30)
#   W_SPREAD                     float constant (0.20)
#   W_CORR                       float constant (0.20)
#   SignalFragilityResult        frozen dataclass — computation output
#   SignalFragilityAnalyzer      stateless analyser — compute() method
#
# GOVERNANCE CONSTRAINTS
# ----------------------
#   - DETERMINISTIC: No random seeds, no Monte Carlo, no stochastic sampling.
#   - SNAPSHOT-ONLY: All inputs passed as frozen values.
#   - NO STATE MUTATION: Never calls ctrl.update().
#   - NO StrategyObject MODIFICATION: Purely read-side.
#   - OUTPUT ROUTING: SignalFragilityResult consumed ONLY by
#     DecisionQualityEngine (read-only).
#   - PERTURBATION DELTAS: Fixed, small, deterministic.
#   - FORBIDDEN: Monte Carlo, random sampling, live feed access,
#     execution semantics, broker concepts, StrategyObject writes.
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  No I/O, no logging, no datetime.now().
# DET-05  All branching is deterministic.
# DET-06  Fixed literals are not parametrised.
# DET-07  Same inputs = bit-identical outputs.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No numpy / scipy
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
#   No broker / order / account references
#   No direct Risk Engine threshold modification
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict


# ---------------------------------------------------------------------------
# CONSTANTS — fixed per DET-06
# ---------------------------------------------------------------------------

FRAGILITY_VOL_DELTA: float = 0.05
"""5% relative perturbation on volatility, min floor 0.01."""

FRAGILITY_SPREAD_DELTA: float = 0.05
"""5% relative perturbation on spread, min floor 0.0001."""

FRAGILITY_CORR_DELTA: float = 0.05
"""0.05 absolute perturbation on correlation coefficient."""

FRAGILITY_PARAM_DELTA: float = 0.01
"""1% relative perturbation on each strategy parameter, min floor 1e-6."""

FRAGILITY_HIGH_THRESHOLD: float = 0.65
"""fragility_index >= this => classified HIGH FRAGILITY."""

# Composite weights (must sum to 1.0)
W_PARAM: float = 0.30
W_VOL: float = 0.30
W_SPREAD: float = 0.20
W_CORR: float = 0.20


# ---------------------------------------------------------------------------
# SIGNAL FRAGILITY RESULT (frozen)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SignalFragilityResult:
    """
    Frozen output of SignalFragilityAnalyzer.
    All scores are deterministically derived from snapshot inputs
    using small, fixed delta perturbation analysis.
    No Monte Carlo. No random sampling. No stochastic components.

    Attributes:
        parameter_sensitivity_score:
            Normalized gradient magnitude of signal output with respect
            to key strategy parameters. High = signal is highly sensitive
            to parameter choices. Range [0.0, 1.0].

        volatility_sensitivity_score:
            Normalized signal change when volatility is perturbed by
            ±FRAGILITY_VOL_DELTA. High = signal is fragile under
            volatility regime shift. Range [0.0, 1.0].

        spread_sensitivity_score:
            Normalized signal change when bid-ask spread proxy is
            perturbed by ±FRAGILITY_SPREAD_DELTA. High = signal degrades
            significantly under spread widening. Range [0.0, 1.0].

        correlation_sensitivity_score:
            Normalized signal change when cross-asset correlation
            coefficient is perturbed by ±FRAGILITY_CORR_DELTA.
            High = signal assumption breaks under mild correlation
            shifts. Range [0.0, 1.0].

        fragility_index:
            Composite fragility score; weighted average of four
            sensitivity scores. >= FRAGILITY_HIGH_THRESHOLD (0.65) =>
            classified HIGH FRAGILITY. Range [0.0, 1.0].
    """
    parameter_sensitivity_score: float
    volatility_sensitivity_score: float
    spread_sensitivity_score: float
    correlation_sensitivity_score: float
    fragility_index: float


# ---------------------------------------------------------------------------
# HELPERS (module-private)
# ---------------------------------------------------------------------------

def _safe_delta(base: float, relative: float, minimum: float) -> float:
    """Compute safe perturbation delta — deterministic, no randomness."""
    return max(abs(base) * relative, minimum)


def _clip01(value: float) -> float:
    """Clip a value to [0.0, 1.0]."""
    return max(0.0, min(1.0, value))


def _normalized_sensitivity(
    signal_fn: Callable[..., float],
    base_kwargs: Dict[str, float],
    perturb_key: str,
    delta: float,
) -> float:
    """
    Compute normalized finite-difference sensitivity for one input
    dimension using central finite differences.

    s = |f(x + delta) - f(x - delta)| / (2 * delta)
    Normalized to [0.0, 1.0] by clipping.

    Args:
        signal_fn:    Pure callable accepting keyword arguments.
        base_kwargs:  Baseline keyword arguments for signal_fn.
        perturb_key:  Which keyword argument to perturb.
        delta:        Perturbation magnitude (must be > 0).

    Returns:
        Normalized sensitivity in [0.0, 1.0].
    """
    base_val: float = base_kwargs[perturb_key]

    kwargs_plus = dict(base_kwargs)
    kwargs_plus[perturb_key] = base_val + delta

    kwargs_minus = dict(base_kwargs)
    kwargs_minus[perturb_key] = base_val - delta

    f_plus: float = signal_fn(**kwargs_plus)
    f_minus: float = signal_fn(**kwargs_minus)

    raw_sensitivity: float = abs(f_plus - f_minus) / (2.0 * delta)
    return _clip01(raw_sensitivity)


# ---------------------------------------------------------------------------
# SIGNAL FRAGILITY ANALYZER (stateless)
# ---------------------------------------------------------------------------

class SignalFragilityAnalyzer:
    """
    Deterministic local perturbation analysis of a strategy signal.

    Measures signal robustness across four key input dimensions
    using central finite differences with fixed perturbation magnitudes.

    Stateless: all inputs are passed explicitly to compute().
    No internal buffers, no mutable state, no side effects.

    Performance budget: < 30 ms per evaluation (event-triggered).
    """

    def compute(
        self,
        signal_fn: Callable[..., float],
        base_volatility: float,
        base_spread: float,
        base_correlation: float,
        strategy_params: Dict[str, float],
    ) -> SignalFragilityResult:
        """
        Deterministically compute signal fragility metrics via local
        perturbation analysis.

        Args:
            signal_fn:          Pure callable representing the strategy signal
                                computation. Must accept keyword arguments
                                'volatility', 'spread', 'correlation', and
                                any keys in strategy_params. Must return a
                                single float (signal strength).
            base_volatility:    Current NVU-normalized volatility (snapshot).
                                Must be > 0.
            base_spread:        Current bid-ask spread proxy (snapshot).
                                Must be >= 0.
            base_correlation:   Current cross-asset correlation coefficient
                                (snapshot). Expected range [-1.0, 1.0].
            strategy_params:    Snapshot of key strategy parameters
                                (e.g., {"lookback": 20.0, "threshold": 0.015}).
                                Must be non-empty. Values must be finite floats.

        Returns:
            SignalFragilityResult (frozen, deterministic).

        Raises:
            ValueError: if base_volatility <= 0 or strategy_params is empty.
        """
        # --- Input validation ---
        if base_volatility <= 0.0:
            raise ValueError(
                f"base_volatility must be > 0; got {base_volatility}"
            )
        if not strategy_params:
            raise ValueError("strategy_params must be non-empty")

        # --- Build baseline kwargs ---
        base_kwargs: Dict[str, float] = {
            "volatility": base_volatility,
            "spread": base_spread,
            "correlation": base_correlation,
        }
        base_kwargs.update(strategy_params)

        # --- Volatility sensitivity ---
        vol_delta: float = _safe_delta(
            base_volatility, FRAGILITY_VOL_DELTA, 0.01
        )
        vol_score: float = _normalized_sensitivity(
            signal_fn, base_kwargs, "volatility", vol_delta
        )

        # --- Spread sensitivity ---
        spread_delta: float = _safe_delta(
            base_spread, FRAGILITY_SPREAD_DELTA, 0.0001
        )
        spread_score: float = _normalized_sensitivity(
            signal_fn, base_kwargs, "spread", spread_delta
        )

        # --- Correlation sensitivity ---
        corr_delta: float = FRAGILITY_CORR_DELTA  # absolute
        corr_score: float = _normalized_sensitivity(
            signal_fn, base_kwargs, "correlation", corr_delta
        )

        # --- Parameter sensitivity (mean over all params) ---
        param_scores: list[float] = []
        for p_name, p_val in sorted(strategy_params.items()):
            p_delta: float = _safe_delta(p_val, FRAGILITY_PARAM_DELTA, 1e-6)
            s: float = _normalized_sensitivity(
                signal_fn, base_kwargs, p_name, p_delta
            )
            param_scores.append(s)
        param_score: float = sum(param_scores) / len(param_scores)

        # --- Composite fragility index ---
        fragility: float = _clip01(
            W_PARAM * param_score
            + W_VOL * vol_score
            + W_SPREAD * spread_score
            + W_CORR * corr_score
        )

        return SignalFragilityResult(
            parameter_sensitivity_score=_clip01(param_score),
            volatility_sensitivity_score=vol_score,
            spread_sensitivity_score=spread_score,
            correlation_sensitivity_score=corr_score,
            fragility_index=fragility,
        )


__all__ = [
    "FRAGILITY_VOL_DELTA",
    "FRAGILITY_SPREAD_DELTA",
    "FRAGILITY_CORR_DELTA",
    "FRAGILITY_PARAM_DELTA",
    "FRAGILITY_HIGH_THRESHOLD",
    "W_PARAM",
    "W_VOL",
    "W_SPREAD",
    "W_CORR",
    "SignalFragilityResult",
    "SignalFragilityAnalyzer",
]
