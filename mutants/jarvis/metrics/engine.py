# =============================================================================
# JARVIS v6.1.0 -- METRICS ENGINE
# File:   jarvis/metrics/engine.py
# Version: 1.1.0
# =============================================================================
#
# SCOPE
# -----
# Pure deterministic performance metrics. All functions are stateless,
# side-effect-free, and take no external dependencies beyond stdlib math.
#
# PUBLIC FUNCTIONS
# ----------------
#   sharpe_ratio(returns, periods_per_year, risk_free_rate) -> float
#   max_drawdown(returns) -> float
#   calmar_ratio(returns, periods_per_year) -> float
#   regime_conditional_returns(returns, regime_labels) -> dict
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  No I/O, no logging, no datetime.now().
# =============================================================================

from __future__ import annotations

import math
from typing import List, Sequence, Dict
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
# HELPERS
# ---------------------------------------------------------------------------

def _mean(values: Sequence[float]) -> float:
    args = [values]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__mean__mutmut_orig, x__mean__mutmut_mutants, args, kwargs, None)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def x__mean__mutmut_orig(values: Sequence[float]) -> float:
    n = len(values)
    if n == 0:
        return 0.0
    return sum(values) / n


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def x__mean__mutmut_1(values: Sequence[float]) -> float:
    n = None
    if n == 0:
        return 0.0
    return sum(values) / n


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def x__mean__mutmut_2(values: Sequence[float]) -> float:
    n = len(values)
    if n != 0:
        return 0.0
    return sum(values) / n


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def x__mean__mutmut_3(values: Sequence[float]) -> float:
    n = len(values)
    if n == 1:
        return 0.0
    return sum(values) / n


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def x__mean__mutmut_4(values: Sequence[float]) -> float:
    n = len(values)
    if n == 0:
        return 1.0
    return sum(values) / n


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def x__mean__mutmut_5(values: Sequence[float]) -> float:
    n = len(values)
    if n == 0:
        return 0.0
    return sum(values) * n


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def x__mean__mutmut_6(values: Sequence[float]) -> float:
    n = len(values)
    if n == 0:
        return 0.0
    return sum(None) / n

x__mean__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__mean__mutmut_1': x__mean__mutmut_1, 
    'x__mean__mutmut_2': x__mean__mutmut_2, 
    'x__mean__mutmut_3': x__mean__mutmut_3, 
    'x__mean__mutmut_4': x__mean__mutmut_4, 
    'x__mean__mutmut_5': x__mean__mutmut_5, 
    'x__mean__mutmut_6': x__mean__mutmut_6
}
x__mean__mutmut_orig.__name__ = 'x__mean'


def _std(values: Sequence[float], ddof: int = 1) -> float:
    args = [values, ddof]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__std__mutmut_orig, x__std__mutmut_mutants, args, kwargs, None)


def x__std__mutmut_orig(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_1(values: Sequence[float], ddof: int = 2) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_2(values: Sequence[float], ddof: int = 1) -> float:
    n = None
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_3(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n < ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_4(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 1.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_5(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = None
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_6(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(None)
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_7(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = None
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_8(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) * (n - ddof)
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_9(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum(None) / (n - ddof)
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_10(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) * 2 for x in values) / (n - ddof)
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_11(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x + mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_12(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 3 for x in values) / (n - ddof)
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_13(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / (n + ddof)
    return math.sqrt(max(variance, 0.0))


def x__std__mutmut_14(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(None)


def x__std__mutmut_15(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(None, 0.0))


def x__std__mutmut_16(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(variance, None))


def x__std__mutmut_17(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(0.0))


def x__std__mutmut_18(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(variance, ))


def x__std__mutmut_19(values: Sequence[float], ddof: int = 1) -> float:
    n = len(values)
    if n <= ddof:
        return 0.0
    mu = _mean(values)
    variance = sum((x - mu) ** 2 for x in values) / (n - ddof)
    return math.sqrt(max(variance, 1.0))

x__std__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__std__mutmut_1': x__std__mutmut_1, 
    'x__std__mutmut_2': x__std__mutmut_2, 
    'x__std__mutmut_3': x__std__mutmut_3, 
    'x__std__mutmut_4': x__std__mutmut_4, 
    'x__std__mutmut_5': x__std__mutmut_5, 
    'x__std__mutmut_6': x__std__mutmut_6, 
    'x__std__mutmut_7': x__std__mutmut_7, 
    'x__std__mutmut_8': x__std__mutmut_8, 
    'x__std__mutmut_9': x__std__mutmut_9, 
    'x__std__mutmut_10': x__std__mutmut_10, 
    'x__std__mutmut_11': x__std__mutmut_11, 
    'x__std__mutmut_12': x__std__mutmut_12, 
    'x__std__mutmut_13': x__std__mutmut_13, 
    'x__std__mutmut_14': x__std__mutmut_14, 
    'x__std__mutmut_15': x__std__mutmut_15, 
    'x__std__mutmut_16': x__std__mutmut_16, 
    'x__std__mutmut_17': x__std__mutmut_17, 
    'x__std__mutmut_18': x__std__mutmut_18, 
    'x__std__mutmut_19': x__std__mutmut_19
}
x__std__mutmut_orig.__name__ = 'x__std'


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def sharpe_ratio(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    args = [returns, periods_per_year, risk_free_rate]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_sharpe_ratio__mutmut_orig, x_sharpe_ratio__mutmut_mutants, args, kwargs, None)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_orig(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_1(
    returns:          List[float],
    periods_per_year: int   = 253,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_2(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 1.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_3(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year <= 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_4(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 2:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_5(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(None)
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_6(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) <= 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_7(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 3:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_8(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 1.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_9(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = None
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_10(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate * periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_11(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = None
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_12(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r + daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_13(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = None
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_14(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(None)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_15(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = None
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_16(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(None, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_17(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=None)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_18(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_19(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, )
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_20(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=2)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_21(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd <= 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_22(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1.000000000000001:
        return 0.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_23(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 1.0
    return (mu / sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_24(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) / math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_25(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu * sd) * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------------
# SHARPE RATIO
# ---------------------------------------------------------------------------

def x_sharpe_ratio__mutmut_26(
    returns:          List[float],
    periods_per_year: int   = 252,
    risk_free_rate:   float = 0.0,
) -> float:
    """
    Annualised Sharpe ratio.

    Formula:
        excess = returns - risk_free_rate / periods_per_year
        sharpe = mean(excess) / std(excess, ddof=1) * sqrt(periods_per_year)

    Returns 0.0 when std == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / periods_per_year
    excess = [r - daily_rf for r in returns]
    mu = _mean(excess)
    sd = _std(excess, ddof=1)
    if sd < 1e-15:
        return 0.0
    return (mu / sd) * math.sqrt(None)

x_sharpe_ratio__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_sharpe_ratio__mutmut_1': x_sharpe_ratio__mutmut_1, 
    'x_sharpe_ratio__mutmut_2': x_sharpe_ratio__mutmut_2, 
    'x_sharpe_ratio__mutmut_3': x_sharpe_ratio__mutmut_3, 
    'x_sharpe_ratio__mutmut_4': x_sharpe_ratio__mutmut_4, 
    'x_sharpe_ratio__mutmut_5': x_sharpe_ratio__mutmut_5, 
    'x_sharpe_ratio__mutmut_6': x_sharpe_ratio__mutmut_6, 
    'x_sharpe_ratio__mutmut_7': x_sharpe_ratio__mutmut_7, 
    'x_sharpe_ratio__mutmut_8': x_sharpe_ratio__mutmut_8, 
    'x_sharpe_ratio__mutmut_9': x_sharpe_ratio__mutmut_9, 
    'x_sharpe_ratio__mutmut_10': x_sharpe_ratio__mutmut_10, 
    'x_sharpe_ratio__mutmut_11': x_sharpe_ratio__mutmut_11, 
    'x_sharpe_ratio__mutmut_12': x_sharpe_ratio__mutmut_12, 
    'x_sharpe_ratio__mutmut_13': x_sharpe_ratio__mutmut_13, 
    'x_sharpe_ratio__mutmut_14': x_sharpe_ratio__mutmut_14, 
    'x_sharpe_ratio__mutmut_15': x_sharpe_ratio__mutmut_15, 
    'x_sharpe_ratio__mutmut_16': x_sharpe_ratio__mutmut_16, 
    'x_sharpe_ratio__mutmut_17': x_sharpe_ratio__mutmut_17, 
    'x_sharpe_ratio__mutmut_18': x_sharpe_ratio__mutmut_18, 
    'x_sharpe_ratio__mutmut_19': x_sharpe_ratio__mutmut_19, 
    'x_sharpe_ratio__mutmut_20': x_sharpe_ratio__mutmut_20, 
    'x_sharpe_ratio__mutmut_21': x_sharpe_ratio__mutmut_21, 
    'x_sharpe_ratio__mutmut_22': x_sharpe_ratio__mutmut_22, 
    'x_sharpe_ratio__mutmut_23': x_sharpe_ratio__mutmut_23, 
    'x_sharpe_ratio__mutmut_24': x_sharpe_ratio__mutmut_24, 
    'x_sharpe_ratio__mutmut_25': x_sharpe_ratio__mutmut_25, 
    'x_sharpe_ratio__mutmut_26': x_sharpe_ratio__mutmut_26
}
x_sharpe_ratio__mutmut_orig.__name__ = 'x_sharpe_ratio'


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def max_drawdown(returns: List[float]) -> float:
    args = [returns]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_max_drawdown__mutmut_orig, x_max_drawdown__mutmut_mutants, args, kwargs, None)


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_orig(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_1(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) <= 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_2(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 3:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_3(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 1.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_4(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = None
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_5(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 2.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_6(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = None
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_7(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 2.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_8(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = None
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_9(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 1.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_10(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum = (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_11(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum /= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_12(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 - r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_13(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (2.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_14(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum >= peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_15(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = None
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_16(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = None
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_17(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) * max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_18(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak + cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_19(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(None, 1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_20(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, None)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_21(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(1e-15)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_22(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, )
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_23(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1.000000000000001)
        if dd > max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_24(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd >= max_dd:
            max_dd = dd
    return max_dd


# ---------------------------------------------------------------------------
# MAX DRAWDOWN
# ---------------------------------------------------------------------------

def x_max_drawdown__mutmut_25(returns: List[float]) -> float:
    """
    Maximum drawdown from peak.

    Formula:
        cumulative = cumprod(1 + r)
        running_peak = running maximum of cumulative
        drawdown = (running_peak - cumulative) / running_peak
        max_drawdown = max(drawdown)

    Returns 0.0 for empty or single-element returns.
    """
    if len(returns) < 2:
        return 0.0
    cum = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cum *= (1.0 + r)
        if cum > peak:
            peak = cum
        dd = (peak - cum) / max(peak, 1e-15)
        if dd > max_dd:
            max_dd = None
    return max_dd

x_max_drawdown__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_max_drawdown__mutmut_1': x_max_drawdown__mutmut_1, 
    'x_max_drawdown__mutmut_2': x_max_drawdown__mutmut_2, 
    'x_max_drawdown__mutmut_3': x_max_drawdown__mutmut_3, 
    'x_max_drawdown__mutmut_4': x_max_drawdown__mutmut_4, 
    'x_max_drawdown__mutmut_5': x_max_drawdown__mutmut_5, 
    'x_max_drawdown__mutmut_6': x_max_drawdown__mutmut_6, 
    'x_max_drawdown__mutmut_7': x_max_drawdown__mutmut_7, 
    'x_max_drawdown__mutmut_8': x_max_drawdown__mutmut_8, 
    'x_max_drawdown__mutmut_9': x_max_drawdown__mutmut_9, 
    'x_max_drawdown__mutmut_10': x_max_drawdown__mutmut_10, 
    'x_max_drawdown__mutmut_11': x_max_drawdown__mutmut_11, 
    'x_max_drawdown__mutmut_12': x_max_drawdown__mutmut_12, 
    'x_max_drawdown__mutmut_13': x_max_drawdown__mutmut_13, 
    'x_max_drawdown__mutmut_14': x_max_drawdown__mutmut_14, 
    'x_max_drawdown__mutmut_15': x_max_drawdown__mutmut_15, 
    'x_max_drawdown__mutmut_16': x_max_drawdown__mutmut_16, 
    'x_max_drawdown__mutmut_17': x_max_drawdown__mutmut_17, 
    'x_max_drawdown__mutmut_18': x_max_drawdown__mutmut_18, 
    'x_max_drawdown__mutmut_19': x_max_drawdown__mutmut_19, 
    'x_max_drawdown__mutmut_20': x_max_drawdown__mutmut_20, 
    'x_max_drawdown__mutmut_21': x_max_drawdown__mutmut_21, 
    'x_max_drawdown__mutmut_22': x_max_drawdown__mutmut_22, 
    'x_max_drawdown__mutmut_23': x_max_drawdown__mutmut_23, 
    'x_max_drawdown__mutmut_24': x_max_drawdown__mutmut_24, 
    'x_max_drawdown__mutmut_25': x_max_drawdown__mutmut_25
}
x_max_drawdown__mutmut_orig.__name__ = 'x_max_drawdown'


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def calmar_ratio(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    args = [returns, periods_per_year]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_calmar_ratio__mutmut_orig, x_calmar_ratio__mutmut_mutants, args, kwargs, None)


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_orig(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_1(
    returns:          List[float],
    periods_per_year: int = 253,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_2(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year <= 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_3(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 2:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_4(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(None)
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_5(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) <= 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_6(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 3:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_7(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 1.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_8(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = None
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_9(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = None
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_10(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 2.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_11(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total = (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_12(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total /= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_13(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 - r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_14(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (2.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_15(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = None
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_16(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) + 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_17(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total * (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_18(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year * n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_19(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 2.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_20(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = None
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_21(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(None)
    if mdd < 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_22(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd <= 1e-15:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_23(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1.000000000000001:
        return 0.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_24(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 1.0
    return ann_return / mdd


# ---------------------------------------------------------------------------
# CALMAR RATIO
# ---------------------------------------------------------------------------

def x_calmar_ratio__mutmut_25(
    returns:          List[float],
    periods_per_year: int = 252,
) -> float:
    """
    Calmar ratio: annualised return / max drawdown.

    Returns 0.0 when max_drawdown == 0 or returns is empty.
    Raises ValueError if periods_per_year < 1.
    """
    if periods_per_year < 1:
        raise ValueError(f"periods_per_year must be >= 1; got {periods_per_year}")
    if len(returns) < 2:
        return 0.0
    n = len(returns)
    total = 1.0
    for r in returns:
        total *= (1.0 + r)
    ann_return = total ** (periods_per_year / n) - 1.0
    mdd = max_drawdown(returns)
    if mdd < 1e-15:
        return 0.0
    return ann_return * mdd

x_calmar_ratio__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_calmar_ratio__mutmut_1': x_calmar_ratio__mutmut_1, 
    'x_calmar_ratio__mutmut_2': x_calmar_ratio__mutmut_2, 
    'x_calmar_ratio__mutmut_3': x_calmar_ratio__mutmut_3, 
    'x_calmar_ratio__mutmut_4': x_calmar_ratio__mutmut_4, 
    'x_calmar_ratio__mutmut_5': x_calmar_ratio__mutmut_5, 
    'x_calmar_ratio__mutmut_6': x_calmar_ratio__mutmut_6, 
    'x_calmar_ratio__mutmut_7': x_calmar_ratio__mutmut_7, 
    'x_calmar_ratio__mutmut_8': x_calmar_ratio__mutmut_8, 
    'x_calmar_ratio__mutmut_9': x_calmar_ratio__mutmut_9, 
    'x_calmar_ratio__mutmut_10': x_calmar_ratio__mutmut_10, 
    'x_calmar_ratio__mutmut_11': x_calmar_ratio__mutmut_11, 
    'x_calmar_ratio__mutmut_12': x_calmar_ratio__mutmut_12, 
    'x_calmar_ratio__mutmut_13': x_calmar_ratio__mutmut_13, 
    'x_calmar_ratio__mutmut_14': x_calmar_ratio__mutmut_14, 
    'x_calmar_ratio__mutmut_15': x_calmar_ratio__mutmut_15, 
    'x_calmar_ratio__mutmut_16': x_calmar_ratio__mutmut_16, 
    'x_calmar_ratio__mutmut_17': x_calmar_ratio__mutmut_17, 
    'x_calmar_ratio__mutmut_18': x_calmar_ratio__mutmut_18, 
    'x_calmar_ratio__mutmut_19': x_calmar_ratio__mutmut_19, 
    'x_calmar_ratio__mutmut_20': x_calmar_ratio__mutmut_20, 
    'x_calmar_ratio__mutmut_21': x_calmar_ratio__mutmut_21, 
    'x_calmar_ratio__mutmut_22': x_calmar_ratio__mutmut_22, 
    'x_calmar_ratio__mutmut_23': x_calmar_ratio__mutmut_23, 
    'x_calmar_ratio__mutmut_24': x_calmar_ratio__mutmut_24, 
    'x_calmar_ratio__mutmut_25': x_calmar_ratio__mutmut_25
}
x_calmar_ratio__mutmut_orig.__name__ = 'x_calmar_ratio'


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def regime_conditional_returns(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    args = [returns, regime_labels]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_regime_conditional_returns__mutmut_orig, x_regime_conditional_returns__mutmut_mutants, args, kwargs, None)


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_orig(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_1(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) == len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_2(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            None
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_3(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) != 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_4(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 1:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_5(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = None
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_6(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(None, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_7(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, None):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_8(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_9(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, ):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_10(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_11(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = None
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_12(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(None)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_13(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = None
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_14(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(None):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_15(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = None
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_16(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "XXmeanXX":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_17(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "MEAN":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_18(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(None),
            "count": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_19(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "XXcountXX": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_20(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "COUNT": float(len(vals)),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_21(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(None),
            "total": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_22(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "XXtotalXX": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_23(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "TOTAL": sum(vals),
        }
    return result


# ---------------------------------------------------------------------------
# REGIME-CONDITIONAL RETURNS
# ---------------------------------------------------------------------------

def x_regime_conditional_returns__mutmut_24(
    returns:        List[float],
    regime_labels:  List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean return and count per regime label.

    Args:
        returns:       Per-period returns. Length must equal len(regime_labels).
        regime_labels: String label per period (e.g. 'RISK_ON', 'CRISIS').

    Returns:
        dict mapping regime label -> {'mean': float, 'count': int, 'total': float}

    Raises:
        ValueError if lengths differ or either is empty.
    """
    if len(returns) != len(regime_labels):
        raise ValueError(
            f"returns and regime_labels must have equal length; "
            f"got {len(returns)} vs {len(regime_labels)}"
        )
    if len(returns) == 0:
        return {}

    buckets: Dict[str, List[float]] = {}
    for r, label in zip(returns, regime_labels):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(r)

    result: Dict[str, Dict[str, float]] = {}
    for label, vals in sorted(buckets.items()):
        result[label] = {
            "mean":  _mean(vals),
            "count": float(len(vals)),
            "total": sum(None),
        }
    return result

x_regime_conditional_returns__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_regime_conditional_returns__mutmut_1': x_regime_conditional_returns__mutmut_1, 
    'x_regime_conditional_returns__mutmut_2': x_regime_conditional_returns__mutmut_2, 
    'x_regime_conditional_returns__mutmut_3': x_regime_conditional_returns__mutmut_3, 
    'x_regime_conditional_returns__mutmut_4': x_regime_conditional_returns__mutmut_4, 
    'x_regime_conditional_returns__mutmut_5': x_regime_conditional_returns__mutmut_5, 
    'x_regime_conditional_returns__mutmut_6': x_regime_conditional_returns__mutmut_6, 
    'x_regime_conditional_returns__mutmut_7': x_regime_conditional_returns__mutmut_7, 
    'x_regime_conditional_returns__mutmut_8': x_regime_conditional_returns__mutmut_8, 
    'x_regime_conditional_returns__mutmut_9': x_regime_conditional_returns__mutmut_9, 
    'x_regime_conditional_returns__mutmut_10': x_regime_conditional_returns__mutmut_10, 
    'x_regime_conditional_returns__mutmut_11': x_regime_conditional_returns__mutmut_11, 
    'x_regime_conditional_returns__mutmut_12': x_regime_conditional_returns__mutmut_12, 
    'x_regime_conditional_returns__mutmut_13': x_regime_conditional_returns__mutmut_13, 
    'x_regime_conditional_returns__mutmut_14': x_regime_conditional_returns__mutmut_14, 
    'x_regime_conditional_returns__mutmut_15': x_regime_conditional_returns__mutmut_15, 
    'x_regime_conditional_returns__mutmut_16': x_regime_conditional_returns__mutmut_16, 
    'x_regime_conditional_returns__mutmut_17': x_regime_conditional_returns__mutmut_17, 
    'x_regime_conditional_returns__mutmut_18': x_regime_conditional_returns__mutmut_18, 
    'x_regime_conditional_returns__mutmut_19': x_regime_conditional_returns__mutmut_19, 
    'x_regime_conditional_returns__mutmut_20': x_regime_conditional_returns__mutmut_20, 
    'x_regime_conditional_returns__mutmut_21': x_regime_conditional_returns__mutmut_21, 
    'x_regime_conditional_returns__mutmut_22': x_regime_conditional_returns__mutmut_22, 
    'x_regime_conditional_returns__mutmut_23': x_regime_conditional_returns__mutmut_23, 
    'x_regime_conditional_returns__mutmut_24': x_regime_conditional_returns__mutmut_24
}
x_regime_conditional_returns__mutmut_orig.__name__ = 'x_regime_conditional_returns'


__all__ = [
    "sharpe_ratio",
    "max_drawdown",
    "calmar_ratio",
    "regime_conditional_returns",
]
