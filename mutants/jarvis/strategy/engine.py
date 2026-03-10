# =============================================================================
# JARVIS v6.1.0 -- STRATEGY ENGINE (SCAFFOLD)
# File:   jarvis/strategy/engine.py
# Version: 1.1.0
# =============================================================================
#
# SCOPE
# -----
# Minimal deterministic strategy scaffold. Generates directional signals
# from a returns series based on configurable momentum and mean-reversion
# lookbacks. No alpha optimisation. No model fitting. Pure functions only.
#
# PUBLIC FUNCTIONS
# ----------------
#   momentum_signal(returns, lookback) -> float  in [-1.0, 1.0]
#   mean_reversion_signal(returns, lookback) -> float  in [-1.0, 1.0]
#   combine_signals(signals, weights) -> float  in [-1.0, 1.0]
#
# DETERMINISM CONSTRAINTS
# -----------------------
# All functions are pure. No randomness, I/O, state, or side effects.
# =============================================================================

from __future__ import annotations

import math
from typing import List, Sequence
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


def _clip(value: float, lo: float, hi: float) -> float:
    args = [value, lo, hi]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__clip__mutmut_orig, x__clip__mutmut_mutants, args, kwargs, None)


def x__clip__mutmut_orig(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def x__clip__mutmut_1(value: float, lo: float, hi: float) -> float:
    return max(None, min(hi, value))


def x__clip__mutmut_2(value: float, lo: float, hi: float) -> float:
    return max(lo, None)


def x__clip__mutmut_3(value: float, lo: float, hi: float) -> float:
    return max(min(hi, value))


def x__clip__mutmut_4(value: float, lo: float, hi: float) -> float:
    return max(lo, )


def x__clip__mutmut_5(value: float, lo: float, hi: float) -> float:
    return max(lo, min(None, value))


def x__clip__mutmut_6(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, None))


def x__clip__mutmut_7(value: float, lo: float, hi: float) -> float:
    return max(lo, min(value))


def x__clip__mutmut_8(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, ))

x__clip__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__clip__mutmut_1': x__clip__mutmut_1, 
    'x__clip__mutmut_2': x__clip__mutmut_2, 
    'x__clip__mutmut_3': x__clip__mutmut_3, 
    'x__clip__mutmut_4': x__clip__mutmut_4, 
    'x__clip__mutmut_5': x__clip__mutmut_5, 
    'x__clip__mutmut_6': x__clip__mutmut_6, 
    'x__clip__mutmut_7': x__clip__mutmut_7, 
    'x__clip__mutmut_8': x__clip__mutmut_8
}
x__clip__mutmut_orig.__name__ = 'x__clip'


def momentum_signal(returns: List[float], lookback: int) -> float:
    args = [returns, lookback]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_momentum_signal__mutmut_orig, x_momentum_signal__mutmut_mutants, args, kwargs, None)


def x_momentum_signal__mutmut_orig(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_1(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 and len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_2(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback <= 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_3(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 2 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_4(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) <= lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_5(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 1.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_6(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = None
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_7(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[+lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_8(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = None
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_9(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = None
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_10(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) * n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_11(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(None) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_12(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = None
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_13(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) * max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_14(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum(None) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_15(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) * 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_16(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r + mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_17(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 3 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_18(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(None, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_19(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, None)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_20(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_21(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, )
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_22(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n + 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_23(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 2, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_24(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 2)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_25(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = None
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_26(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(None)
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_27(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(None, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_28(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, None))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_29(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_30(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, ))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_31(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1.000000000000001))
    signal = mu / sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_32(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = None
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_33(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu * sd
    return _clip(signal, -1.0, 1.0)


def x_momentum_signal__mutmut_34(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(None, -1.0, 1.0)


def x_momentum_signal__mutmut_35(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, None, 1.0)


def x_momentum_signal__mutmut_36(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, None)


def x_momentum_signal__mutmut_37(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(-1.0, 1.0)


def x_momentum_signal__mutmut_38(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, 1.0)


def x_momentum_signal__mutmut_39(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, )


def x_momentum_signal__mutmut_40(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, +1.0, 1.0)


def x_momentum_signal__mutmut_41(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -2.0, 1.0)


def x_momentum_signal__mutmut_42(returns: List[float], lookback: int) -> float:
    """
    Momentum signal: sign of average return over lookback window, scaled by
    magnitude relative to realised std.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    if lookback < 1 or len(returns) < lookback:
        return 0.0
    window = returns[-lookback:]
    n = len(window)
    mu = sum(window) / n
    variance = sum((r - mu) ** 2 for r in window) / max(n - 1, 1)
    sd = math.sqrt(max(variance, 1e-15))
    signal = mu / sd
    return _clip(signal, -1.0, 2.0)

x_momentum_signal__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_momentum_signal__mutmut_1': x_momentum_signal__mutmut_1, 
    'x_momentum_signal__mutmut_2': x_momentum_signal__mutmut_2, 
    'x_momentum_signal__mutmut_3': x_momentum_signal__mutmut_3, 
    'x_momentum_signal__mutmut_4': x_momentum_signal__mutmut_4, 
    'x_momentum_signal__mutmut_5': x_momentum_signal__mutmut_5, 
    'x_momentum_signal__mutmut_6': x_momentum_signal__mutmut_6, 
    'x_momentum_signal__mutmut_7': x_momentum_signal__mutmut_7, 
    'x_momentum_signal__mutmut_8': x_momentum_signal__mutmut_8, 
    'x_momentum_signal__mutmut_9': x_momentum_signal__mutmut_9, 
    'x_momentum_signal__mutmut_10': x_momentum_signal__mutmut_10, 
    'x_momentum_signal__mutmut_11': x_momentum_signal__mutmut_11, 
    'x_momentum_signal__mutmut_12': x_momentum_signal__mutmut_12, 
    'x_momentum_signal__mutmut_13': x_momentum_signal__mutmut_13, 
    'x_momentum_signal__mutmut_14': x_momentum_signal__mutmut_14, 
    'x_momentum_signal__mutmut_15': x_momentum_signal__mutmut_15, 
    'x_momentum_signal__mutmut_16': x_momentum_signal__mutmut_16, 
    'x_momentum_signal__mutmut_17': x_momentum_signal__mutmut_17, 
    'x_momentum_signal__mutmut_18': x_momentum_signal__mutmut_18, 
    'x_momentum_signal__mutmut_19': x_momentum_signal__mutmut_19, 
    'x_momentum_signal__mutmut_20': x_momentum_signal__mutmut_20, 
    'x_momentum_signal__mutmut_21': x_momentum_signal__mutmut_21, 
    'x_momentum_signal__mutmut_22': x_momentum_signal__mutmut_22, 
    'x_momentum_signal__mutmut_23': x_momentum_signal__mutmut_23, 
    'x_momentum_signal__mutmut_24': x_momentum_signal__mutmut_24, 
    'x_momentum_signal__mutmut_25': x_momentum_signal__mutmut_25, 
    'x_momentum_signal__mutmut_26': x_momentum_signal__mutmut_26, 
    'x_momentum_signal__mutmut_27': x_momentum_signal__mutmut_27, 
    'x_momentum_signal__mutmut_28': x_momentum_signal__mutmut_28, 
    'x_momentum_signal__mutmut_29': x_momentum_signal__mutmut_29, 
    'x_momentum_signal__mutmut_30': x_momentum_signal__mutmut_30, 
    'x_momentum_signal__mutmut_31': x_momentum_signal__mutmut_31, 
    'x_momentum_signal__mutmut_32': x_momentum_signal__mutmut_32, 
    'x_momentum_signal__mutmut_33': x_momentum_signal__mutmut_33, 
    'x_momentum_signal__mutmut_34': x_momentum_signal__mutmut_34, 
    'x_momentum_signal__mutmut_35': x_momentum_signal__mutmut_35, 
    'x_momentum_signal__mutmut_36': x_momentum_signal__mutmut_36, 
    'x_momentum_signal__mutmut_37': x_momentum_signal__mutmut_37, 
    'x_momentum_signal__mutmut_38': x_momentum_signal__mutmut_38, 
    'x_momentum_signal__mutmut_39': x_momentum_signal__mutmut_39, 
    'x_momentum_signal__mutmut_40': x_momentum_signal__mutmut_40, 
    'x_momentum_signal__mutmut_41': x_momentum_signal__mutmut_41, 
    'x_momentum_signal__mutmut_42': x_momentum_signal__mutmut_42
}
x_momentum_signal__mutmut_orig.__name__ = 'x_momentum_signal'


def mean_reversion_signal(returns: List[float], lookback: int) -> float:
    args = [returns, lookback]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_mean_reversion_signal__mutmut_orig, x_mean_reversion_signal__mutmut_mutants, args, kwargs, None)


def x_mean_reversion_signal__mutmut_orig(returns: List[float], lookback: int) -> float:
    """
    Mean-reversion signal: negative of momentum signal.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    return -momentum_signal(returns, lookback)


def x_mean_reversion_signal__mutmut_1(returns: List[float], lookback: int) -> float:
    """
    Mean-reversion signal: negative of momentum signal.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    return +momentum_signal(returns, lookback)


def x_mean_reversion_signal__mutmut_2(returns: List[float], lookback: int) -> float:
    """
    Mean-reversion signal: negative of momentum signal.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    return -momentum_signal(None, lookback)


def x_mean_reversion_signal__mutmut_3(returns: List[float], lookback: int) -> float:
    """
    Mean-reversion signal: negative of momentum signal.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    return -momentum_signal(returns, None)


def x_mean_reversion_signal__mutmut_4(returns: List[float], lookback: int) -> float:
    """
    Mean-reversion signal: negative of momentum signal.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    return -momentum_signal(lookback)


def x_mean_reversion_signal__mutmut_5(returns: List[float], lookback: int) -> float:
    """
    Mean-reversion signal: negative of momentum signal.

    Returns value in [-1.0, 1.0].
    Returns 0.0 when len(returns) < lookback or lookback < 1.
    """
    return -momentum_signal(returns, )

x_mean_reversion_signal__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_mean_reversion_signal__mutmut_1': x_mean_reversion_signal__mutmut_1, 
    'x_mean_reversion_signal__mutmut_2': x_mean_reversion_signal__mutmut_2, 
    'x_mean_reversion_signal__mutmut_3': x_mean_reversion_signal__mutmut_3, 
    'x_mean_reversion_signal__mutmut_4': x_mean_reversion_signal__mutmut_4, 
    'x_mean_reversion_signal__mutmut_5': x_mean_reversion_signal__mutmut_5
}
x_mean_reversion_signal__mutmut_orig.__name__ = 'x_mean_reversion_signal'


def combine_signals(signals: Sequence[float], weights: Sequence[float]) -> float:
    args = [signals, weights]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_combine_signals__mutmut_orig, x_combine_signals__mutmut_mutants, args, kwargs, None)


def x_combine_signals__mutmut_orig(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_1(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) == len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_2(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            None
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_3(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_4(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 1.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_5(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = None
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_6(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(None)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_7(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight <= 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_8(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1.000000000000001:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_9(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 1.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_10(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = None
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_11(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) * total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_12(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(None) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_13(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s / w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_14(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(None, weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_15(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, None)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_16(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(weights)) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_17(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, )) / total_weight
    return _clip(combined, -1.0, 1.0)


def x_combine_signals__mutmut_18(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(None, -1.0, 1.0)


def x_combine_signals__mutmut_19(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, None, 1.0)


def x_combine_signals__mutmut_20(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, None)


def x_combine_signals__mutmut_21(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(-1.0, 1.0)


def x_combine_signals__mutmut_22(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, 1.0)


def x_combine_signals__mutmut_23(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, )


def x_combine_signals__mutmut_24(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, +1.0, 1.0)


def x_combine_signals__mutmut_25(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -2.0, 1.0)


def x_combine_signals__mutmut_26(signals: Sequence[float], weights: Sequence[float]) -> float:
    """
    Weighted combination of signals, normalised to [-1.0, 1.0].

    Args:
        signals: Sequence of floats, each in [-1.0, 1.0].
        weights: Corresponding non-negative weights.

    Returns:
        Weighted sum / sum(weights), clipped to [-1.0, 1.0].
        Returns 0.0 if weights sum to zero or sequences are empty.

    Raises:
        ValueError if len(signals) != len(weights).
    """
    if len(signals) != len(weights):
        raise ValueError(
            f"signals and weights must have equal length; "
            f"got {len(signals)} vs {len(weights)}"
        )
    if not signals:
        return 0.0
    total_weight = sum(weights)
    if total_weight < 1e-15:
        return 0.0
    combined = sum(s * w for s, w in zip(signals, weights)) / total_weight
    return _clip(combined, -1.0, 2.0)

x_combine_signals__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_combine_signals__mutmut_1': x_combine_signals__mutmut_1, 
    'x_combine_signals__mutmut_2': x_combine_signals__mutmut_2, 
    'x_combine_signals__mutmut_3': x_combine_signals__mutmut_3, 
    'x_combine_signals__mutmut_4': x_combine_signals__mutmut_4, 
    'x_combine_signals__mutmut_5': x_combine_signals__mutmut_5, 
    'x_combine_signals__mutmut_6': x_combine_signals__mutmut_6, 
    'x_combine_signals__mutmut_7': x_combine_signals__mutmut_7, 
    'x_combine_signals__mutmut_8': x_combine_signals__mutmut_8, 
    'x_combine_signals__mutmut_9': x_combine_signals__mutmut_9, 
    'x_combine_signals__mutmut_10': x_combine_signals__mutmut_10, 
    'x_combine_signals__mutmut_11': x_combine_signals__mutmut_11, 
    'x_combine_signals__mutmut_12': x_combine_signals__mutmut_12, 
    'x_combine_signals__mutmut_13': x_combine_signals__mutmut_13, 
    'x_combine_signals__mutmut_14': x_combine_signals__mutmut_14, 
    'x_combine_signals__mutmut_15': x_combine_signals__mutmut_15, 
    'x_combine_signals__mutmut_16': x_combine_signals__mutmut_16, 
    'x_combine_signals__mutmut_17': x_combine_signals__mutmut_17, 
    'x_combine_signals__mutmut_18': x_combine_signals__mutmut_18, 
    'x_combine_signals__mutmut_19': x_combine_signals__mutmut_19, 
    'x_combine_signals__mutmut_20': x_combine_signals__mutmut_20, 
    'x_combine_signals__mutmut_21': x_combine_signals__mutmut_21, 
    'x_combine_signals__mutmut_22': x_combine_signals__mutmut_22, 
    'x_combine_signals__mutmut_23': x_combine_signals__mutmut_23, 
    'x_combine_signals__mutmut_24': x_combine_signals__mutmut_24, 
    'x_combine_signals__mutmut_25': x_combine_signals__mutmut_25, 
    'x_combine_signals__mutmut_26': x_combine_signals__mutmut_26
}
x_combine_signals__mutmut_orig.__name__ = 'x_combine_signals'


__all__ = [
    "momentum_signal",
    "mean_reversion_signal",
    "combine_signals",
]
