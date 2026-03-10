# =============================================================================
# JARVIS v6.0.1 — SESSION 05, PHASE 5.3: REGIME DETECTOR
# File:   jarvis/core/regime_detector.py
# Authority: JARVIS FAS v6.0.1 — 02-05_CORE.md, S05 section
# Phase:  5.3 — RegimeDetector (HMM-based regime detection)
# =============================================================================
#
# SCOPE (Phase 5.3)
# -----------------
# Implements:
#   - RegimeResult  dataclass (frozen=True)
#   - RegimeDetector class
#       * detect_regime(features) -> RegimeResult
#       * transition_probability() -> List[List[float]]  (5x5 stochastic matrix)
#       * regime_confidence() -> float  in [0.0, 1.0]
#
# CONSTRAINTS
# -----------
# stdlib only: dataclasses, math, typing.
# No numpy. No scipy. No pandas. No random. No datetime.now().
# No file I/O. No logging. No global mutable state.
# Regime enums sourced exclusively from jarvis.core.regime.
# LatentState sourced from jarvis.core.state_layer.
#
# DETERMINISM GUARANTEES
# ----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  All arithmetic deterministic.
# DET-05  All branches pure functions of explicit inputs.
# DET-06  No datetime.now().
#
# HMM MODEL SPECIFICATION
# -----------------------
# 5 hidden states (indices 0-4) mapping to GlobalRegimeState:
#   0 -> RISK_ON      (Bull / trending up / low vol)
#   1 -> RISK_OFF     (Bear / trending down / elevated stress)
#   2 -> TRANSITION   (Sideways / mean-reverting)
#   3 -> RISK_OFF     (High volatility / directionally ambiguous)
#   4 -> CRISIS       (Shock / structural break)
#
# Forward algorithm: pure Python, O(T * N^2) where N=5.
# Emission probabilities: Gaussian approximation via math.exp.
# Transition matrix: ergodic (all states reachable), row-stochastic.
# Confidence: max posterior probability over current state distribution.
#
# INVARIANTS
# ----------
# INV-P53-01  transition_probability() returns a 5x5 list-of-lists.
# INV-P53-02  Each row of the transition matrix sums to 1.0.
# INV-P53-03  All entries clipped to [1e-6, 1 - 1e-6] before normalisation.
# INV-P53-04  regime_confidence() always returns a value in [0.0, 1.0].
# INV-P53-05  detect_regime() never raises on finite feature inputs.
# INV-P53-06  RegimeResult.hmm_index is always in {0, 1, 2, 3, 4}.
# INV-P53-07  RegimeResult.confidence is in [0.0, 1.0].
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

from jarvis.core.regime import GlobalRegimeState


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Number of HMM hidden states.
_N_STATES: int = 5

#: Epsilon floor for probabilities to avoid log(0).
_PROB_EPS: float = 1e-10

#: Clip bounds for transition matrix entries (before row normalisation).
_T_MIN: float = 1e-6
_T_MAX: float = 1.0 - 1e-6

#: Mapping from HMM state index -> GlobalRegimeState.
_STATE_TO_REGIME: Dict[int, GlobalRegimeState] = {
    0: GlobalRegimeState.RISK_ON,
    1: GlobalRegimeState.RISK_OFF,
    2: GlobalRegimeState.TRANSITION,
    3: GlobalRegimeState.RISK_OFF,
    4: GlobalRegimeState.CRISIS,
}

#: Default prior (uniform over 5 states).
_UNIFORM_PRIOR: List[float] = [1.0 / _N_STATES] * _N_STATES

# ---------------------------------------------------------------------------
# Default ergodic transition matrix (row-stochastic, all entries in [T_MIN, T_MAX]).
# Rows sum to 1.0. Designed to be sticky (high self-transition) while
# allowing inter-state transitions.
# State order: RISK_ON, RISK_OFF, TRANSITION, HIGH_VOL, CRISIS
# ---------------------------------------------------------------------------
_DEFAULT_TRANSITION: List[List[float]] = [
    # to:   0      1      2      3      4
    [0.70,  0.10,  0.10,  0.06,  0.04],  # from 0: RISK_ON
    [0.10,  0.65,  0.10,  0.10,  0.05],  # from 1: RISK_OFF
    [0.15,  0.15,  0.55,  0.10,  0.05],  # from 2: TRANSITION
    [0.08,  0.15,  0.12,  0.55,  0.10],  # from 3: HIGH_VOL
    [0.05,  0.10,  0.10,  0.15,  0.60],  # from 4: CRISIS
]

# ---------------------------------------------------------------------------
# Default emission means (per feature key, per state).
# Features are assumed z-scored. Emission probability modelled as
# isotropic Gaussian with unit variance (simplified for stdlib-only).
# ---------------------------------------------------------------------------
_EMISSION_MEANS: Dict[str, List[float]] = {
    # State order: RISK_ON, RISK_OFF, TRANSITION, HIGH_VOL, CRISIS
    "volatility":          [0.3,   0.8,   0.5,  1.2,  2.0],
    "trend_strength":      [0.7,  -0.5,   0.0,  0.1, -0.3],
    "mean_reversion":      [0.1,   0.2,   0.8,  0.3,  0.1],
    "stress":              [0.1,   0.6,   0.3,  0.8,  1.5],
    "momentum":            [0.6,  -0.5,   0.0,  0.1, -0.2],
    "liquidity":           [0.8,   0.3,   0.5,  0.2,  0.1],
}

# Emission sigma (shared across all features and states — simplified HMM).
_EMISSION_SIGMA: float = 0.5
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
# Helpers
# ---------------------------------------------------------------------------

def _gaussian_log_prob(x: float, mu: float, sigma: float) -> float:
    args = [x, mu, sigma]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__gaussian_log_prob__mutmut_orig, x__gaussian_log_prob__mutmut_mutants, args, kwargs, None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_orig(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 * ((x - mu) / sigma) ** 2 - math.log(sigma) - 0.5 * math.log(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_1(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 * ((x - mu) / sigma) ** 2 - math.log(sigma) + 0.5 * math.log(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_2(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 * ((x - mu) / sigma) ** 2 + math.log(sigma) - 0.5 * math.log(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_3(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 / ((x - mu) / sigma) ** 2 - math.log(sigma) - 0.5 * math.log(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_4(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return +0.5 * ((x - mu) / sigma) ** 2 - math.log(sigma) - 0.5 * math.log(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_5(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -1.5 * ((x - mu) / sigma) ** 2 - math.log(sigma) - 0.5 * math.log(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_6(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 * ((x - mu) / sigma) * 2 - math.log(sigma) - 0.5 * math.log(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_7(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 * ((x - mu) * sigma) ** 2 - math.log(sigma) - 0.5 * math.log(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_8(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 * ((x + mu) / sigma) ** 2 - math.log(sigma) - 0.5 * math.log(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_9(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 * ((x - mu) / sigma) ** 3 - math.log(sigma) - 0.5 * math.log(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_10(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 * ((x - mu) / sigma) ** 2 - math.log(None) - 0.5 * math.log(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_11(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 * ((x - mu) / sigma) ** 2 - math.log(sigma) - 0.5 / math.log(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_12(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 * ((x - mu) / sigma) ** 2 - math.log(sigma) - 1.5 * math.log(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_13(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 * ((x - mu) / sigma) ** 2 - math.log(sigma) - 0.5 * math.log(None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_14(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 * ((x - mu) / sigma) ** 2 - math.log(sigma) - 0.5 * math.log(2.0 / math.pi)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def x__gaussian_log_prob__mutmut_15(x: float, mu: float, sigma: float) -> float:
    """Log probability of x under N(mu, sigma^2). sigma must be > 0."""
    return -0.5 * ((x - mu) / sigma) ** 2 - math.log(sigma) - 0.5 * math.log(3.0 * math.pi)

x__gaussian_log_prob__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__gaussian_log_prob__mutmut_1': x__gaussian_log_prob__mutmut_1, 
    'x__gaussian_log_prob__mutmut_2': x__gaussian_log_prob__mutmut_2, 
    'x__gaussian_log_prob__mutmut_3': x__gaussian_log_prob__mutmut_3, 
    'x__gaussian_log_prob__mutmut_4': x__gaussian_log_prob__mutmut_4, 
    'x__gaussian_log_prob__mutmut_5': x__gaussian_log_prob__mutmut_5, 
    'x__gaussian_log_prob__mutmut_6': x__gaussian_log_prob__mutmut_6, 
    'x__gaussian_log_prob__mutmut_7': x__gaussian_log_prob__mutmut_7, 
    'x__gaussian_log_prob__mutmut_8': x__gaussian_log_prob__mutmut_8, 
    'x__gaussian_log_prob__mutmut_9': x__gaussian_log_prob__mutmut_9, 
    'x__gaussian_log_prob__mutmut_10': x__gaussian_log_prob__mutmut_10, 
    'x__gaussian_log_prob__mutmut_11': x__gaussian_log_prob__mutmut_11, 
    'x__gaussian_log_prob__mutmut_12': x__gaussian_log_prob__mutmut_12, 
    'x__gaussian_log_prob__mutmut_13': x__gaussian_log_prob__mutmut_13, 
    'x__gaussian_log_prob__mutmut_14': x__gaussian_log_prob__mutmut_14, 
    'x__gaussian_log_prob__mutmut_15': x__gaussian_log_prob__mutmut_15
}
x__gaussian_log_prob__mutmut_orig.__name__ = 'x__gaussian_log_prob'


def _emission_log_prob(features: Dict[str, float], state_idx: int) -> float:
    args = [features, state_idx]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__emission_log_prob__mutmut_orig, x__emission_log_prob__mutmut_mutants, args, kwargs, None)


def x__emission_log_prob__mutmut_orig(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_1(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = None
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_2(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 1.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_3(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = None
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_4(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(None, 0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_5(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, None)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_6(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_7(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, )
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_8(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 1.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_9(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_10(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(None):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_11(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = None
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_12(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = 1.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_13(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = None
        log_p += _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_14(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p = _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_15(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p -= _gaussian_log_prob(value, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_16(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(None, mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_17(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, None, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_18(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, None)
    return log_p


def x__emission_log_prob__mutmut_19(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(mu, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_20(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, _EMISSION_SIGMA)
    return log_p


def x__emission_log_prob__mutmut_21(features: Dict[str, float], state_idx: int) -> float:
    """
    Log emission probability P(features | state_idx).
    Only features present in _EMISSION_MEANS are used.
    Non-finite feature values are silently replaced with 0.0.
    """
    log_p: float = 0.0
    for feat_name, state_means in _EMISSION_MEANS.items():
        value: float = features.get(feat_name, 0.0)
        if not math.isfinite(value):
            value = 0.0
        mu: float = state_means[state_idx]
        log_p += _gaussian_log_prob(value, mu, )
    return log_p

x__emission_log_prob__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__emission_log_prob__mutmut_1': x__emission_log_prob__mutmut_1, 
    'x__emission_log_prob__mutmut_2': x__emission_log_prob__mutmut_2, 
    'x__emission_log_prob__mutmut_3': x__emission_log_prob__mutmut_3, 
    'x__emission_log_prob__mutmut_4': x__emission_log_prob__mutmut_4, 
    'x__emission_log_prob__mutmut_5': x__emission_log_prob__mutmut_5, 
    'x__emission_log_prob__mutmut_6': x__emission_log_prob__mutmut_6, 
    'x__emission_log_prob__mutmut_7': x__emission_log_prob__mutmut_7, 
    'x__emission_log_prob__mutmut_8': x__emission_log_prob__mutmut_8, 
    'x__emission_log_prob__mutmut_9': x__emission_log_prob__mutmut_9, 
    'x__emission_log_prob__mutmut_10': x__emission_log_prob__mutmut_10, 
    'x__emission_log_prob__mutmut_11': x__emission_log_prob__mutmut_11, 
    'x__emission_log_prob__mutmut_12': x__emission_log_prob__mutmut_12, 
    'x__emission_log_prob__mutmut_13': x__emission_log_prob__mutmut_13, 
    'x__emission_log_prob__mutmut_14': x__emission_log_prob__mutmut_14, 
    'x__emission_log_prob__mutmut_15': x__emission_log_prob__mutmut_15, 
    'x__emission_log_prob__mutmut_16': x__emission_log_prob__mutmut_16, 
    'x__emission_log_prob__mutmut_17': x__emission_log_prob__mutmut_17, 
    'x__emission_log_prob__mutmut_18': x__emission_log_prob__mutmut_18, 
    'x__emission_log_prob__mutmut_19': x__emission_log_prob__mutmut_19, 
    'x__emission_log_prob__mutmut_20': x__emission_log_prob__mutmut_20, 
    'x__emission_log_prob__mutmut_21': x__emission_log_prob__mutmut_21
}
x__emission_log_prob__mutmut_orig.__name__ = 'x__emission_log_prob'


def _log_sum_exp(log_probs: List[float]) -> float:
    args = [log_probs]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__log_sum_exp__mutmut_orig, x__log_sum_exp__mutmut_mutants, args, kwargs, None)


def x__log_sum_exp__mutmut_orig(log_probs: List[float]) -> float:
    """Numerically stable log-sum-exp over a list of log probabilities."""
    if not log_probs:
        return -math.inf
    max_lp: float = max(log_probs)
    if not math.isfinite(max_lp):
        return -math.inf
    return max_lp + math.log(sum(math.exp(lp - max_lp) for lp in log_probs))


def x__log_sum_exp__mutmut_1(log_probs: List[float]) -> float:
    """Numerically stable log-sum-exp over a list of log probabilities."""
    if log_probs:
        return -math.inf
    max_lp: float = max(log_probs)
    if not math.isfinite(max_lp):
        return -math.inf
    return max_lp + math.log(sum(math.exp(lp - max_lp) for lp in log_probs))


def x__log_sum_exp__mutmut_2(log_probs: List[float]) -> float:
    """Numerically stable log-sum-exp over a list of log probabilities."""
    if not log_probs:
        return +math.inf
    max_lp: float = max(log_probs)
    if not math.isfinite(max_lp):
        return -math.inf
    return max_lp + math.log(sum(math.exp(lp - max_lp) for lp in log_probs))


def x__log_sum_exp__mutmut_3(log_probs: List[float]) -> float:
    """Numerically stable log-sum-exp over a list of log probabilities."""
    if not log_probs:
        return -math.inf
    max_lp: float = None
    if not math.isfinite(max_lp):
        return -math.inf
    return max_lp + math.log(sum(math.exp(lp - max_lp) for lp in log_probs))


def x__log_sum_exp__mutmut_4(log_probs: List[float]) -> float:
    """Numerically stable log-sum-exp over a list of log probabilities."""
    if not log_probs:
        return -math.inf
    max_lp: float = max(None)
    if not math.isfinite(max_lp):
        return -math.inf
    return max_lp + math.log(sum(math.exp(lp - max_lp) for lp in log_probs))


def x__log_sum_exp__mutmut_5(log_probs: List[float]) -> float:
    """Numerically stable log-sum-exp over a list of log probabilities."""
    if not log_probs:
        return -math.inf
    max_lp: float = max(log_probs)
    if math.isfinite(max_lp):
        return -math.inf
    return max_lp + math.log(sum(math.exp(lp - max_lp) for lp in log_probs))


def x__log_sum_exp__mutmut_6(log_probs: List[float]) -> float:
    """Numerically stable log-sum-exp over a list of log probabilities."""
    if not log_probs:
        return -math.inf
    max_lp: float = max(log_probs)
    if not math.isfinite(None):
        return -math.inf
    return max_lp + math.log(sum(math.exp(lp - max_lp) for lp in log_probs))


def x__log_sum_exp__mutmut_7(log_probs: List[float]) -> float:
    """Numerically stable log-sum-exp over a list of log probabilities."""
    if not log_probs:
        return -math.inf
    max_lp: float = max(log_probs)
    if not math.isfinite(max_lp):
        return +math.inf
    return max_lp + math.log(sum(math.exp(lp - max_lp) for lp in log_probs))


def x__log_sum_exp__mutmut_8(log_probs: List[float]) -> float:
    """Numerically stable log-sum-exp over a list of log probabilities."""
    if not log_probs:
        return -math.inf
    max_lp: float = max(log_probs)
    if not math.isfinite(max_lp):
        return -math.inf
    return max_lp - math.log(sum(math.exp(lp - max_lp) for lp in log_probs))


def x__log_sum_exp__mutmut_9(log_probs: List[float]) -> float:
    """Numerically stable log-sum-exp over a list of log probabilities."""
    if not log_probs:
        return -math.inf
    max_lp: float = max(log_probs)
    if not math.isfinite(max_lp):
        return -math.inf
    return max_lp + math.log(None)


def x__log_sum_exp__mutmut_10(log_probs: List[float]) -> float:
    """Numerically stable log-sum-exp over a list of log probabilities."""
    if not log_probs:
        return -math.inf
    max_lp: float = max(log_probs)
    if not math.isfinite(max_lp):
        return -math.inf
    return max_lp + math.log(sum(None))


def x__log_sum_exp__mutmut_11(log_probs: List[float]) -> float:
    """Numerically stable log-sum-exp over a list of log probabilities."""
    if not log_probs:
        return -math.inf
    max_lp: float = max(log_probs)
    if not math.isfinite(max_lp):
        return -math.inf
    return max_lp + math.log(sum(math.exp(None) for lp in log_probs))


def x__log_sum_exp__mutmut_12(log_probs: List[float]) -> float:
    """Numerically stable log-sum-exp over a list of log probabilities."""
    if not log_probs:
        return -math.inf
    max_lp: float = max(log_probs)
    if not math.isfinite(max_lp):
        return -math.inf
    return max_lp + math.log(sum(math.exp(lp + max_lp) for lp in log_probs))

x__log_sum_exp__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__log_sum_exp__mutmut_1': x__log_sum_exp__mutmut_1, 
    'x__log_sum_exp__mutmut_2': x__log_sum_exp__mutmut_2, 
    'x__log_sum_exp__mutmut_3': x__log_sum_exp__mutmut_3, 
    'x__log_sum_exp__mutmut_4': x__log_sum_exp__mutmut_4, 
    'x__log_sum_exp__mutmut_5': x__log_sum_exp__mutmut_5, 
    'x__log_sum_exp__mutmut_6': x__log_sum_exp__mutmut_6, 
    'x__log_sum_exp__mutmut_7': x__log_sum_exp__mutmut_7, 
    'x__log_sum_exp__mutmut_8': x__log_sum_exp__mutmut_8, 
    'x__log_sum_exp__mutmut_9': x__log_sum_exp__mutmut_9, 
    'x__log_sum_exp__mutmut_10': x__log_sum_exp__mutmut_10, 
    'x__log_sum_exp__mutmut_11': x__log_sum_exp__mutmut_11, 
    'x__log_sum_exp__mutmut_12': x__log_sum_exp__mutmut_12
}
x__log_sum_exp__mutmut_orig.__name__ = 'x__log_sum_exp'


def _normalise(probs: List[float]) -> List[float]:
    args = [probs]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__normalise__mutmut_orig, x__normalise__mutmut_mutants, args, kwargs, None)


def x__normalise__mutmut_orig(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(_PROB_EPS, v) if math.isfinite(v) else _PROB_EPS
        for v in probs
    ]
    total: float = sum(safe)
    if total <= 0.0:
        return [1.0 / _N_STATES] * _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_1(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = None
    total: float = sum(safe)
    if total <= 0.0:
        return [1.0 / _N_STATES] * _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_2(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(None, v) if math.isfinite(v) else _PROB_EPS
        for v in probs
    ]
    total: float = sum(safe)
    if total <= 0.0:
        return [1.0 / _N_STATES] * _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_3(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(_PROB_EPS, None) if math.isfinite(v) else _PROB_EPS
        for v in probs
    ]
    total: float = sum(safe)
    if total <= 0.0:
        return [1.0 / _N_STATES] * _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_4(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(v) if math.isfinite(v) else _PROB_EPS
        for v in probs
    ]
    total: float = sum(safe)
    if total <= 0.0:
        return [1.0 / _N_STATES] * _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_5(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(_PROB_EPS, ) if math.isfinite(v) else _PROB_EPS
        for v in probs
    ]
    total: float = sum(safe)
    if total <= 0.0:
        return [1.0 / _N_STATES] * _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_6(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(_PROB_EPS, v) if math.isfinite(None) else _PROB_EPS
        for v in probs
    ]
    total: float = sum(safe)
    if total <= 0.0:
        return [1.0 / _N_STATES] * _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_7(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(_PROB_EPS, v) if math.isfinite(v) else _PROB_EPS
        for v in probs
    ]
    total: float = None
    if total <= 0.0:
        return [1.0 / _N_STATES] * _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_8(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(_PROB_EPS, v) if math.isfinite(v) else _PROB_EPS
        for v in probs
    ]
    total: float = sum(None)
    if total <= 0.0:
        return [1.0 / _N_STATES] * _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_9(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(_PROB_EPS, v) if math.isfinite(v) else _PROB_EPS
        for v in probs
    ]
    total: float = sum(safe)
    if total < 0.0:
        return [1.0 / _N_STATES] * _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_10(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(_PROB_EPS, v) if math.isfinite(v) else _PROB_EPS
        for v in probs
    ]
    total: float = sum(safe)
    if total <= 1.0:
        return [1.0 / _N_STATES] * _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_11(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(_PROB_EPS, v) if math.isfinite(v) else _PROB_EPS
        for v in probs
    ]
    total: float = sum(safe)
    if total <= 0.0:
        return [1.0 / _N_STATES] / _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_12(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(_PROB_EPS, v) if math.isfinite(v) else _PROB_EPS
        for v in probs
    ]
    total: float = sum(safe)
    if total <= 0.0:
        return [1.0 * _N_STATES] * _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_13(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(_PROB_EPS, v) if math.isfinite(v) else _PROB_EPS
        for v in probs
    ]
    total: float = sum(safe)
    if total <= 0.0:
        return [2.0 / _N_STATES] * _N_STATES
    return [v / total for v in safe]


def x__normalise__mutmut_14(probs: List[float]) -> List[float]:
    """
    Normalise a list of non-negative values to sum to 1.0.
    Any non-finite value is replaced with _PROB_EPS before normalisation.
    If all values are zero (or sum is zero), returns uniform distribution.
    """
    safe: List[float] = [
        max(_PROB_EPS, v) if math.isfinite(v) else _PROB_EPS
        for v in probs
    ]
    total: float = sum(safe)
    if total <= 0.0:
        return [1.0 / _N_STATES] * _N_STATES
    return [v * total for v in safe]

x__normalise__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__normalise__mutmut_1': x__normalise__mutmut_1, 
    'x__normalise__mutmut_2': x__normalise__mutmut_2, 
    'x__normalise__mutmut_3': x__normalise__mutmut_3, 
    'x__normalise__mutmut_4': x__normalise__mutmut_4, 
    'x__normalise__mutmut_5': x__normalise__mutmut_5, 
    'x__normalise__mutmut_6': x__normalise__mutmut_6, 
    'x__normalise__mutmut_7': x__normalise__mutmut_7, 
    'x__normalise__mutmut_8': x__normalise__mutmut_8, 
    'x__normalise__mutmut_9': x__normalise__mutmut_9, 
    'x__normalise__mutmut_10': x__normalise__mutmut_10, 
    'x__normalise__mutmut_11': x__normalise__mutmut_11, 
    'x__normalise__mutmut_12': x__normalise__mutmut_12, 
    'x__normalise__mutmut_13': x__normalise__mutmut_13, 
    'x__normalise__mutmut_14': x__normalise__mutmut_14
}
x__normalise__mutmut_orig.__name__ = 'x__normalise'


# ---------------------------------------------------------------------------
# RegimeResult
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegimeResult:
    """
    Immutable result of a single regime detection step.

    Fields
    ------
    hmm_index : int
        Index of the most probable HMM hidden state (0-4).
    regime : GlobalRegimeState
        Canonical macro regime corresponding to hmm_index.
    confidence : float
        Posterior probability of the most probable state. In [0.0, 1.0].
    posterior : tuple[float, ...]
        Full posterior distribution over all 5 states.
        Sums to 1.0 (within floating-point tolerance).
    """
    hmm_index: int
    regime: GlobalRegimeState
    confidence: float
    posterior: tuple  # tuple[float, ...] — length 5

    def __post_init__(self) -> None:
        if self.hmm_index not in _STATE_TO_REGIME:
            raise ValueError(
                f"RegimeResult.hmm_index must be in {{0,1,2,3,4}}, "
                f"got {self.hmm_index!r}."
            )
        if not isinstance(self.regime, GlobalRegimeState):
            raise TypeError(
                f"RegimeResult.regime must be a GlobalRegimeState member, "
                f"got {type(self.regime).__name__!r}."
            )
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"RegimeResult.confidence must be in [0.0, 1.0], "
                f"got {self.confidence!r}."
            )
        if len(self.posterior) != _N_STATES:
            raise ValueError(
                f"RegimeResult.posterior must have length {_N_STATES}, "
                f"got {len(self.posterior)}."
            )


# ---------------------------------------------------------------------------
# RegimeDetector
# ---------------------------------------------------------------------------

class RegimeDetector:
    """
    HMM-based regime detector.

    Maintains a running posterior distribution over 5 hidden states and
    updates it at each call to detect_regime() using the forward algorithm.

    IMMUTABILITY NOTE:
      The transition matrix and emission parameters are fixed at construction.
      The only mutable state is the current posterior (self._posterior),
      which is updated deterministically at each detect_regime() call.

    DETERMINISM:
      Given identical feature sequences, successive calls to detect_regime()
      will produce identical outputs. The posterior is reset to the uniform
      prior only by calling reset().

    STDLIB ONLY: no numpy, no scipy, no random.
    """

    def __init__(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        args = [transition_matrix, initial_prior]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRegimeDetectorǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁRegimeDetectorǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁRegimeDetectorǁ__init____mutmut_orig(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_1(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is not None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_2(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = None
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_3(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(None) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_4(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = None

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_5(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(None)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_6(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(None):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_7(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = None
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_8(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(None, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_9(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, None) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_10(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_11(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, ) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_12(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(None, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_13(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, None)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_14(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_15(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, )) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_16(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = None

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_17(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(None)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_18(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is not None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_19(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = None
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_20(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(None)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_21(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) == _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_22(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    None
                )
            self._posterior = _normalise(list(initial_prior))

    def xǁRegimeDetectorǁ__init____mutmut_23(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = None

    def xǁRegimeDetectorǁ__init____mutmut_24(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(None)

    def xǁRegimeDetectorǁ__init____mutmut_25(
        self,
        transition_matrix: List[List[float]] | None = None,
        initial_prior: List[float] | None = None,
    ) -> None:
        """
        Initialise the regime detector.

        Parameters
        ----------
        transition_matrix : List[List[float]] or None
            5x5 row-stochastic transition matrix. If None, the default
            ergodic matrix is used. Rows must sum to 1.0; entries are
            clipped to [T_MIN, T_MAX] and renormalised on construction.
        initial_prior : List[float] or None
            Initial state distribution over 5 states. If None, uniform
            prior [0.2, 0.2, 0.2, 0.2, 0.2] is used.
        """
        # Validate and store transition matrix.
        if transition_matrix is None:
            self._transition: List[List[float]] = [
                list(row) for row in _DEFAULT_TRANSITION
            ]
        else:
            self._transition = self._validate_transition(transition_matrix)

        # Normalise rows of the stored transition matrix.
        for i in range(_N_STATES):
            row = [max(_T_MIN, min(_T_MAX, v)) for v in self._transition[i]]
            self._transition[i] = _normalise(row)

        # Initialise posterior.
        if initial_prior is None:
            self._posterior: List[float] = list(_UNIFORM_PRIOR)
        else:
            if len(initial_prior) != _N_STATES:
                raise ValueError(
                    f"initial_prior must have length {_N_STATES}, "
                    f"got {len(initial_prior)}."
                )
            self._posterior = _normalise(list(None))
    
    xǁRegimeDetectorǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRegimeDetectorǁ__init____mutmut_1': xǁRegimeDetectorǁ__init____mutmut_1, 
        'xǁRegimeDetectorǁ__init____mutmut_2': xǁRegimeDetectorǁ__init____mutmut_2, 
        'xǁRegimeDetectorǁ__init____mutmut_3': xǁRegimeDetectorǁ__init____mutmut_3, 
        'xǁRegimeDetectorǁ__init____mutmut_4': xǁRegimeDetectorǁ__init____mutmut_4, 
        'xǁRegimeDetectorǁ__init____mutmut_5': xǁRegimeDetectorǁ__init____mutmut_5, 
        'xǁRegimeDetectorǁ__init____mutmut_6': xǁRegimeDetectorǁ__init____mutmut_6, 
        'xǁRegimeDetectorǁ__init____mutmut_7': xǁRegimeDetectorǁ__init____mutmut_7, 
        'xǁRegimeDetectorǁ__init____mutmut_8': xǁRegimeDetectorǁ__init____mutmut_8, 
        'xǁRegimeDetectorǁ__init____mutmut_9': xǁRegimeDetectorǁ__init____mutmut_9, 
        'xǁRegimeDetectorǁ__init____mutmut_10': xǁRegimeDetectorǁ__init____mutmut_10, 
        'xǁRegimeDetectorǁ__init____mutmut_11': xǁRegimeDetectorǁ__init____mutmut_11, 
        'xǁRegimeDetectorǁ__init____mutmut_12': xǁRegimeDetectorǁ__init____mutmut_12, 
        'xǁRegimeDetectorǁ__init____mutmut_13': xǁRegimeDetectorǁ__init____mutmut_13, 
        'xǁRegimeDetectorǁ__init____mutmut_14': xǁRegimeDetectorǁ__init____mutmut_14, 
        'xǁRegimeDetectorǁ__init____mutmut_15': xǁRegimeDetectorǁ__init____mutmut_15, 
        'xǁRegimeDetectorǁ__init____mutmut_16': xǁRegimeDetectorǁ__init____mutmut_16, 
        'xǁRegimeDetectorǁ__init____mutmut_17': xǁRegimeDetectorǁ__init____mutmut_17, 
        'xǁRegimeDetectorǁ__init____mutmut_18': xǁRegimeDetectorǁ__init____mutmut_18, 
        'xǁRegimeDetectorǁ__init____mutmut_19': xǁRegimeDetectorǁ__init____mutmut_19, 
        'xǁRegimeDetectorǁ__init____mutmut_20': xǁRegimeDetectorǁ__init____mutmut_20, 
        'xǁRegimeDetectorǁ__init____mutmut_21': xǁRegimeDetectorǁ__init____mutmut_21, 
        'xǁRegimeDetectorǁ__init____mutmut_22': xǁRegimeDetectorǁ__init____mutmut_22, 
        'xǁRegimeDetectorǁ__init____mutmut_23': xǁRegimeDetectorǁ__init____mutmut_23, 
        'xǁRegimeDetectorǁ__init____mutmut_24': xǁRegimeDetectorǁ__init____mutmut_24, 
        'xǁRegimeDetectorǁ__init____mutmut_25': xǁRegimeDetectorǁ__init____mutmut_25
    }
    xǁRegimeDetectorǁ__init____mutmut_orig.__name__ = 'xǁRegimeDetectorǁ__init__'

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_regime(self, features: Dict[str, float]) -> RegimeResult:
        args = [features]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRegimeDetectorǁdetect_regime__mutmut_orig'), object.__getattribute__(self, 'xǁRegimeDetectorǁdetect_regime__mutmut_mutants'), args, kwargs, self)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_orig(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_1(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is not None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_2(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError(None)

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_3(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("XXfeatures must be a dict, got None.XX")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_4(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got none.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_5(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("FEATURES MUST BE A DICT, GOT NONE.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_6(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = None
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_7(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] / _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_8(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [1.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_9(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(None):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_10(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = None

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_11(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                None
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_12(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] / self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_13(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(None)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_14(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = None
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_15(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(None, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_16(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, None) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_17(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_18(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, ) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_19(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(None)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_20(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = None
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_21(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(None)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_22(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = None

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_23(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(None) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_24(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le + max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_25(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = None

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_26(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] / emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_27(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(None)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_28(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = None

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_29(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(None)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_30(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = None
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_31(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(None, key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_32(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=None)
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_33(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_34(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), )
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_35(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(None), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_36(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: None)
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_37(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = None

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_38(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(None, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_39(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, None)

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_40(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_41(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, )

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_42(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(1.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_43(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(None, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_44(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, None))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_45(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_46(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, ))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_47(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(2.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_48(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=None,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_49(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=None,
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_50(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=None,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_51(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=None,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_52(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_53(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            confidence=confidence,
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_54(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            posterior=tuple(self._posterior),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_55(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁRegimeDetectorǁdetect_regime__mutmut_56(self, features: Dict[str, float]) -> RegimeResult:
        """
        Update the posterior state distribution given new feature observations
        and return the most probable regime.

        Uses the HMM forward step: prediction (transition) followed by
        update (emission likelihood weighting), then normalisation.

        Parameters
        ----------
        features : Dict[str, float]
            Feature dict. Keys matching _EMISSION_MEANS are used.
            Unknown keys are ignored. Non-finite values are replaced with 0.0.
            Must not be None.

        Returns
        -------
        RegimeResult
            Immutable result containing the most probable state, its
            canonical GlobalRegimeState, confidence, and full posterior.

        Notes
        -----
        Deterministic. Updates self._posterior as the only side effect.
        """
        if features is None:
            raise TypeError("features must be a dict, got None.")

        # --- Prediction step: propagate prior through transition matrix ---
        predicted: List[float] = [0.0] * _N_STATES
        for j in range(_N_STATES):
            predicted[j] = sum(
                self._posterior[i] * self._transition[i][j]
                for i in range(_N_STATES)
            )

        # --- Update step: weight by emission probabilities ---
        log_emit: List[float] = [
            _emission_log_prob(features, j) for j in range(_N_STATES)
        ]
        # Convert log emission to linear scale, centred for numerical stability.
        max_log_emit: float = max(log_emit)
        emit_scale: List[float] = [
            math.exp(le - max_log_emit) for le in log_emit
        ]

        unnorm: List[float] = [
            predicted[j] * emit_scale[j] for j in range(_N_STATES)
        ]

        # --- Normalise posterior ---
        self._posterior = _normalise(unnorm)

        # --- Compute result ---
        best_idx: int = max(range(_N_STATES), key=lambda j: self._posterior[j])
        confidence: float = max(0.0, min(1.0, self._posterior[best_idx]))

        return RegimeResult(
            hmm_index=best_idx,
            regime=_STATE_TO_REGIME[best_idx],
            confidence=confidence,
            posterior=tuple(None),
        )
    
    xǁRegimeDetectorǁdetect_regime__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRegimeDetectorǁdetect_regime__mutmut_1': xǁRegimeDetectorǁdetect_regime__mutmut_1, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_2': xǁRegimeDetectorǁdetect_regime__mutmut_2, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_3': xǁRegimeDetectorǁdetect_regime__mutmut_3, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_4': xǁRegimeDetectorǁdetect_regime__mutmut_4, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_5': xǁRegimeDetectorǁdetect_regime__mutmut_5, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_6': xǁRegimeDetectorǁdetect_regime__mutmut_6, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_7': xǁRegimeDetectorǁdetect_regime__mutmut_7, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_8': xǁRegimeDetectorǁdetect_regime__mutmut_8, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_9': xǁRegimeDetectorǁdetect_regime__mutmut_9, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_10': xǁRegimeDetectorǁdetect_regime__mutmut_10, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_11': xǁRegimeDetectorǁdetect_regime__mutmut_11, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_12': xǁRegimeDetectorǁdetect_regime__mutmut_12, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_13': xǁRegimeDetectorǁdetect_regime__mutmut_13, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_14': xǁRegimeDetectorǁdetect_regime__mutmut_14, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_15': xǁRegimeDetectorǁdetect_regime__mutmut_15, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_16': xǁRegimeDetectorǁdetect_regime__mutmut_16, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_17': xǁRegimeDetectorǁdetect_regime__mutmut_17, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_18': xǁRegimeDetectorǁdetect_regime__mutmut_18, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_19': xǁRegimeDetectorǁdetect_regime__mutmut_19, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_20': xǁRegimeDetectorǁdetect_regime__mutmut_20, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_21': xǁRegimeDetectorǁdetect_regime__mutmut_21, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_22': xǁRegimeDetectorǁdetect_regime__mutmut_22, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_23': xǁRegimeDetectorǁdetect_regime__mutmut_23, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_24': xǁRegimeDetectorǁdetect_regime__mutmut_24, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_25': xǁRegimeDetectorǁdetect_regime__mutmut_25, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_26': xǁRegimeDetectorǁdetect_regime__mutmut_26, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_27': xǁRegimeDetectorǁdetect_regime__mutmut_27, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_28': xǁRegimeDetectorǁdetect_regime__mutmut_28, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_29': xǁRegimeDetectorǁdetect_regime__mutmut_29, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_30': xǁRegimeDetectorǁdetect_regime__mutmut_30, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_31': xǁRegimeDetectorǁdetect_regime__mutmut_31, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_32': xǁRegimeDetectorǁdetect_regime__mutmut_32, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_33': xǁRegimeDetectorǁdetect_regime__mutmut_33, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_34': xǁRegimeDetectorǁdetect_regime__mutmut_34, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_35': xǁRegimeDetectorǁdetect_regime__mutmut_35, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_36': xǁRegimeDetectorǁdetect_regime__mutmut_36, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_37': xǁRegimeDetectorǁdetect_regime__mutmut_37, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_38': xǁRegimeDetectorǁdetect_regime__mutmut_38, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_39': xǁRegimeDetectorǁdetect_regime__mutmut_39, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_40': xǁRegimeDetectorǁdetect_regime__mutmut_40, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_41': xǁRegimeDetectorǁdetect_regime__mutmut_41, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_42': xǁRegimeDetectorǁdetect_regime__mutmut_42, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_43': xǁRegimeDetectorǁdetect_regime__mutmut_43, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_44': xǁRegimeDetectorǁdetect_regime__mutmut_44, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_45': xǁRegimeDetectorǁdetect_regime__mutmut_45, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_46': xǁRegimeDetectorǁdetect_regime__mutmut_46, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_47': xǁRegimeDetectorǁdetect_regime__mutmut_47, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_48': xǁRegimeDetectorǁdetect_regime__mutmut_48, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_49': xǁRegimeDetectorǁdetect_regime__mutmut_49, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_50': xǁRegimeDetectorǁdetect_regime__mutmut_50, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_51': xǁRegimeDetectorǁdetect_regime__mutmut_51, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_52': xǁRegimeDetectorǁdetect_regime__mutmut_52, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_53': xǁRegimeDetectorǁdetect_regime__mutmut_53, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_54': xǁRegimeDetectorǁdetect_regime__mutmut_54, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_55': xǁRegimeDetectorǁdetect_regime__mutmut_55, 
        'xǁRegimeDetectorǁdetect_regime__mutmut_56': xǁRegimeDetectorǁdetect_regime__mutmut_56
    }
    xǁRegimeDetectorǁdetect_regime__mutmut_orig.__name__ = 'xǁRegimeDetectorǁdetect_regime'

    def transition_probability(self) -> List[List[float]]:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRegimeDetectorǁtransition_probability__mutmut_orig'), object.__getattribute__(self, 'xǁRegimeDetectorǁtransition_probability__mutmut_mutants'), args, kwargs, self)

    def xǁRegimeDetectorǁtransition_probability__mutmut_orig(self) -> List[List[float]]:
        """
        Return the current 5x5 row-stochastic transition matrix.

        INV-P53-01: Returns a 5x5 list-of-lists.
        INV-P53-02: Each row sums to 1.0.
        INV-P53-03: All entries in [1e-6, 1 - 1e-6] (clipped on construction).

        Returns
        -------
        List[List[float]]
            A deep copy of the internal transition matrix.
            Modifying the returned list does not affect the detector state.
        """
        return [list(row) for row in self._transition]

    def xǁRegimeDetectorǁtransition_probability__mutmut_1(self) -> List[List[float]]:
        """
        Return the current 5x5 row-stochastic transition matrix.

        INV-P53-01: Returns a 5x5 list-of-lists.
        INV-P53-02: Each row sums to 1.0.
        INV-P53-03: All entries in [1e-6, 1 - 1e-6] (clipped on construction).

        Returns
        -------
        List[List[float]]
            A deep copy of the internal transition matrix.
            Modifying the returned list does not affect the detector state.
        """
        return [list(None) for row in self._transition]
    
    xǁRegimeDetectorǁtransition_probability__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRegimeDetectorǁtransition_probability__mutmut_1': xǁRegimeDetectorǁtransition_probability__mutmut_1
    }
    xǁRegimeDetectorǁtransition_probability__mutmut_orig.__name__ = 'xǁRegimeDetectorǁtransition_probability'

    def regime_confidence(self) -> float:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRegimeDetectorǁregime_confidence__mutmut_orig'), object.__getattribute__(self, 'xǁRegimeDetectorǁregime_confidence__mutmut_mutants'), args, kwargs, self)

    def xǁRegimeDetectorǁregime_confidence__mutmut_orig(self) -> float:
        """
        Return the confidence in the current most probable regime.

        This is the maximum value in the current posterior distribution,
        representing R from D(t). Always in [0.0, 1.0].

        Returns
        -------
        float
            Maximum posterior probability. In [0.0, 1.0].
        """
        return max(0.0, min(1.0, max(self._posterior)))

    def xǁRegimeDetectorǁregime_confidence__mutmut_1(self) -> float:
        """
        Return the confidence in the current most probable regime.

        This is the maximum value in the current posterior distribution,
        representing R from D(t). Always in [0.0, 1.0].

        Returns
        -------
        float
            Maximum posterior probability. In [0.0, 1.0].
        """
        return max(None, min(1.0, max(self._posterior)))

    def xǁRegimeDetectorǁregime_confidence__mutmut_2(self) -> float:
        """
        Return the confidence in the current most probable regime.

        This is the maximum value in the current posterior distribution,
        representing R from D(t). Always in [0.0, 1.0].

        Returns
        -------
        float
            Maximum posterior probability. In [0.0, 1.0].
        """
        return max(0.0, None)

    def xǁRegimeDetectorǁregime_confidence__mutmut_3(self) -> float:
        """
        Return the confidence in the current most probable regime.

        This is the maximum value in the current posterior distribution,
        representing R from D(t). Always in [0.0, 1.0].

        Returns
        -------
        float
            Maximum posterior probability. In [0.0, 1.0].
        """
        return max(min(1.0, max(self._posterior)))

    def xǁRegimeDetectorǁregime_confidence__mutmut_4(self) -> float:
        """
        Return the confidence in the current most probable regime.

        This is the maximum value in the current posterior distribution,
        representing R from D(t). Always in [0.0, 1.0].

        Returns
        -------
        float
            Maximum posterior probability. In [0.0, 1.0].
        """
        return max(0.0, )

    def xǁRegimeDetectorǁregime_confidence__mutmut_5(self) -> float:
        """
        Return the confidence in the current most probable regime.

        This is the maximum value in the current posterior distribution,
        representing R from D(t). Always in [0.0, 1.0].

        Returns
        -------
        float
            Maximum posterior probability. In [0.0, 1.0].
        """
        return max(1.0, min(1.0, max(self._posterior)))

    def xǁRegimeDetectorǁregime_confidence__mutmut_6(self) -> float:
        """
        Return the confidence in the current most probable regime.

        This is the maximum value in the current posterior distribution,
        representing R from D(t). Always in [0.0, 1.0].

        Returns
        -------
        float
            Maximum posterior probability. In [0.0, 1.0].
        """
        return max(0.0, min(None, max(self._posterior)))

    def xǁRegimeDetectorǁregime_confidence__mutmut_7(self) -> float:
        """
        Return the confidence in the current most probable regime.

        This is the maximum value in the current posterior distribution,
        representing R from D(t). Always in [0.0, 1.0].

        Returns
        -------
        float
            Maximum posterior probability. In [0.0, 1.0].
        """
        return max(0.0, min(1.0, None))

    def xǁRegimeDetectorǁregime_confidence__mutmut_8(self) -> float:
        """
        Return the confidence in the current most probable regime.

        This is the maximum value in the current posterior distribution,
        representing R from D(t). Always in [0.0, 1.0].

        Returns
        -------
        float
            Maximum posterior probability. In [0.0, 1.0].
        """
        return max(0.0, min(max(self._posterior)))

    def xǁRegimeDetectorǁregime_confidence__mutmut_9(self) -> float:
        """
        Return the confidence in the current most probable regime.

        This is the maximum value in the current posterior distribution,
        representing R from D(t). Always in [0.0, 1.0].

        Returns
        -------
        float
            Maximum posterior probability. In [0.0, 1.0].
        """
        return max(0.0, min(1.0, ))

    def xǁRegimeDetectorǁregime_confidence__mutmut_10(self) -> float:
        """
        Return the confidence in the current most probable regime.

        This is the maximum value in the current posterior distribution,
        representing R from D(t). Always in [0.0, 1.0].

        Returns
        -------
        float
            Maximum posterior probability. In [0.0, 1.0].
        """
        return max(0.0, min(2.0, max(self._posterior)))

    def xǁRegimeDetectorǁregime_confidence__mutmut_11(self) -> float:
        """
        Return the confidence in the current most probable regime.

        This is the maximum value in the current posterior distribution,
        representing R from D(t). Always in [0.0, 1.0].

        Returns
        -------
        float
            Maximum posterior probability. In [0.0, 1.0].
        """
        return max(0.0, min(1.0, max(None)))
    
    xǁRegimeDetectorǁregime_confidence__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRegimeDetectorǁregime_confidence__mutmut_1': xǁRegimeDetectorǁregime_confidence__mutmut_1, 
        'xǁRegimeDetectorǁregime_confidence__mutmut_2': xǁRegimeDetectorǁregime_confidence__mutmut_2, 
        'xǁRegimeDetectorǁregime_confidence__mutmut_3': xǁRegimeDetectorǁregime_confidence__mutmut_3, 
        'xǁRegimeDetectorǁregime_confidence__mutmut_4': xǁRegimeDetectorǁregime_confidence__mutmut_4, 
        'xǁRegimeDetectorǁregime_confidence__mutmut_5': xǁRegimeDetectorǁregime_confidence__mutmut_5, 
        'xǁRegimeDetectorǁregime_confidence__mutmut_6': xǁRegimeDetectorǁregime_confidence__mutmut_6, 
        'xǁRegimeDetectorǁregime_confidence__mutmut_7': xǁRegimeDetectorǁregime_confidence__mutmut_7, 
        'xǁRegimeDetectorǁregime_confidence__mutmut_8': xǁRegimeDetectorǁregime_confidence__mutmut_8, 
        'xǁRegimeDetectorǁregime_confidence__mutmut_9': xǁRegimeDetectorǁregime_confidence__mutmut_9, 
        'xǁRegimeDetectorǁregime_confidence__mutmut_10': xǁRegimeDetectorǁregime_confidence__mutmut_10, 
        'xǁRegimeDetectorǁregime_confidence__mutmut_11': xǁRegimeDetectorǁregime_confidence__mutmut_11
    }
    xǁRegimeDetectorǁregime_confidence__mutmut_orig.__name__ = 'xǁRegimeDetectorǁregime_confidence'

    def current_posterior(self) -> List[float]:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRegimeDetectorǁcurrent_posterior__mutmut_orig'), object.__getattribute__(self, 'xǁRegimeDetectorǁcurrent_posterior__mutmut_mutants'), args, kwargs, self)

    def xǁRegimeDetectorǁcurrent_posterior__mutmut_orig(self) -> List[float]:
        """
        Return the current state posterior distribution as a list of 5 floats.
        Sums to 1.0 (within floating-point tolerance).
        Returns a copy; modifying it does not affect detector state.
        """
        return list(self._posterior)

    def xǁRegimeDetectorǁcurrent_posterior__mutmut_1(self) -> List[float]:
        """
        Return the current state posterior distribution as a list of 5 floats.
        Sums to 1.0 (within floating-point tolerance).
        Returns a copy; modifying it does not affect detector state.
        """
        return list(None)
    
    xǁRegimeDetectorǁcurrent_posterior__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRegimeDetectorǁcurrent_posterior__mutmut_1': xǁRegimeDetectorǁcurrent_posterior__mutmut_1
    }
    xǁRegimeDetectorǁcurrent_posterior__mutmut_orig.__name__ = 'xǁRegimeDetectorǁcurrent_posterior'

    def reset(self, prior: List[float] | None = None) -> None:
        args = [prior]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁRegimeDetectorǁreset__mutmut_orig'), object.__getattribute__(self, 'xǁRegimeDetectorǁreset__mutmut_mutants'), args, kwargs, self)

    def xǁRegimeDetectorǁreset__mutmut_orig(self, prior: List[float] | None = None) -> None:
        """
        Reset the posterior to the uniform prior (or a supplied prior).

        Parameters
        ----------
        prior : List[float] or None
            If None, resets to the uniform distribution.
            If supplied, must have length 5 and contain non-negative values.
        """
        if prior is None:
            self._posterior = list(_UNIFORM_PRIOR)
        else:
            if len(prior) != _N_STATES:
                raise ValueError(
                    f"prior must have length {_N_STATES}, got {len(prior)}."
                )
            self._posterior = _normalise(list(prior))

    def xǁRegimeDetectorǁreset__mutmut_1(self, prior: List[float] | None = None) -> None:
        """
        Reset the posterior to the uniform prior (or a supplied prior).

        Parameters
        ----------
        prior : List[float] or None
            If None, resets to the uniform distribution.
            If supplied, must have length 5 and contain non-negative values.
        """
        if prior is not None:
            self._posterior = list(_UNIFORM_PRIOR)
        else:
            if len(prior) != _N_STATES:
                raise ValueError(
                    f"prior must have length {_N_STATES}, got {len(prior)}."
                )
            self._posterior = _normalise(list(prior))

    def xǁRegimeDetectorǁreset__mutmut_2(self, prior: List[float] | None = None) -> None:
        """
        Reset the posterior to the uniform prior (or a supplied prior).

        Parameters
        ----------
        prior : List[float] or None
            If None, resets to the uniform distribution.
            If supplied, must have length 5 and contain non-negative values.
        """
        if prior is None:
            self._posterior = None
        else:
            if len(prior) != _N_STATES:
                raise ValueError(
                    f"prior must have length {_N_STATES}, got {len(prior)}."
                )
            self._posterior = _normalise(list(prior))

    def xǁRegimeDetectorǁreset__mutmut_3(self, prior: List[float] | None = None) -> None:
        """
        Reset the posterior to the uniform prior (or a supplied prior).

        Parameters
        ----------
        prior : List[float] or None
            If None, resets to the uniform distribution.
            If supplied, must have length 5 and contain non-negative values.
        """
        if prior is None:
            self._posterior = list(None)
        else:
            if len(prior) != _N_STATES:
                raise ValueError(
                    f"prior must have length {_N_STATES}, got {len(prior)}."
                )
            self._posterior = _normalise(list(prior))

    def xǁRegimeDetectorǁreset__mutmut_4(self, prior: List[float] | None = None) -> None:
        """
        Reset the posterior to the uniform prior (or a supplied prior).

        Parameters
        ----------
        prior : List[float] or None
            If None, resets to the uniform distribution.
            If supplied, must have length 5 and contain non-negative values.
        """
        if prior is None:
            self._posterior = list(_UNIFORM_PRIOR)
        else:
            if len(prior) == _N_STATES:
                raise ValueError(
                    f"prior must have length {_N_STATES}, got {len(prior)}."
                )
            self._posterior = _normalise(list(prior))

    def xǁRegimeDetectorǁreset__mutmut_5(self, prior: List[float] | None = None) -> None:
        """
        Reset the posterior to the uniform prior (or a supplied prior).

        Parameters
        ----------
        prior : List[float] or None
            If None, resets to the uniform distribution.
            If supplied, must have length 5 and contain non-negative values.
        """
        if prior is None:
            self._posterior = list(_UNIFORM_PRIOR)
        else:
            if len(prior) != _N_STATES:
                raise ValueError(
                    None
                )
            self._posterior = _normalise(list(prior))

    def xǁRegimeDetectorǁreset__mutmut_6(self, prior: List[float] | None = None) -> None:
        """
        Reset the posterior to the uniform prior (or a supplied prior).

        Parameters
        ----------
        prior : List[float] or None
            If None, resets to the uniform distribution.
            If supplied, must have length 5 and contain non-negative values.
        """
        if prior is None:
            self._posterior = list(_UNIFORM_PRIOR)
        else:
            if len(prior) != _N_STATES:
                raise ValueError(
                    f"prior must have length {_N_STATES}, got {len(prior)}."
                )
            self._posterior = None

    def xǁRegimeDetectorǁreset__mutmut_7(self, prior: List[float] | None = None) -> None:
        """
        Reset the posterior to the uniform prior (or a supplied prior).

        Parameters
        ----------
        prior : List[float] or None
            If None, resets to the uniform distribution.
            If supplied, must have length 5 and contain non-negative values.
        """
        if prior is None:
            self._posterior = list(_UNIFORM_PRIOR)
        else:
            if len(prior) != _N_STATES:
                raise ValueError(
                    f"prior must have length {_N_STATES}, got {len(prior)}."
                )
            self._posterior = _normalise(None)

    def xǁRegimeDetectorǁreset__mutmut_8(self, prior: List[float] | None = None) -> None:
        """
        Reset the posterior to the uniform prior (or a supplied prior).

        Parameters
        ----------
        prior : List[float] or None
            If None, resets to the uniform distribution.
            If supplied, must have length 5 and contain non-negative values.
        """
        if prior is None:
            self._posterior = list(_UNIFORM_PRIOR)
        else:
            if len(prior) != _N_STATES:
                raise ValueError(
                    f"prior must have length {_N_STATES}, got {len(prior)}."
                )
            self._posterior = _normalise(list(None))
    
    xǁRegimeDetectorǁreset__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁRegimeDetectorǁreset__mutmut_1': xǁRegimeDetectorǁreset__mutmut_1, 
        'xǁRegimeDetectorǁreset__mutmut_2': xǁRegimeDetectorǁreset__mutmut_2, 
        'xǁRegimeDetectorǁreset__mutmut_3': xǁRegimeDetectorǁreset__mutmut_3, 
        'xǁRegimeDetectorǁreset__mutmut_4': xǁRegimeDetectorǁreset__mutmut_4, 
        'xǁRegimeDetectorǁreset__mutmut_5': xǁRegimeDetectorǁreset__mutmut_5, 
        'xǁRegimeDetectorǁreset__mutmut_6': xǁRegimeDetectorǁreset__mutmut_6, 
        'xǁRegimeDetectorǁreset__mutmut_7': xǁRegimeDetectorǁreset__mutmut_7, 
        'xǁRegimeDetectorǁreset__mutmut_8': xǁRegimeDetectorǁreset__mutmut_8
    }
    xǁRegimeDetectorǁreset__mutmut_orig.__name__ = 'xǁRegimeDetectorǁreset'

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_transition(matrix: List[List[float]]) -> List[List[float]]:
        """
        Validate the shape of a transition matrix. Raises ValueError on
        wrong shape. Does NOT renormalise — that is done in __init__.
        """
        if len(matrix) != _N_STATES:
            raise ValueError(
                f"transition_matrix must have {_N_STATES} rows, "
                f"got {len(matrix)}."
            )
        for i, row in enumerate(matrix):
            if len(row) != _N_STATES:
                raise ValueError(
                    f"transition_matrix row {i} must have {_N_STATES} "
                    f"columns, got {len(row)}."
                )
        return [list(row) for row in matrix]
