# jarvis/execution/exposure_router.py
# Version: 1.0.0
# External boundary adapter module.
# External to jarvis/core/ and jarvis/risk/ per FAS v6.1.0 architecture rules.
#
# DETERMINISM GUARANTEE:
#   No stochastic operations. No random number generation. No sampling.
#   No external state reads. No side effects. No file I/O. No logging.
#   No environment variable access. No global mutable state.
#   Output is a pure function of inputs.
#
# PURPOSE:
#   Acts as a strict boundary adapter between risk exposure output and
#   portfolio allocation. Delegates all allocation logic exclusively to
#   jarvis.portfolio.allocate_positions.
#   No allocation logic is reimplemented here.
#
# Standard import pattern:
#   from jarvis.execution.exposure_router import route_exposure_to_positions

from jarvis.portfolio import allocate_positions
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


def route_exposure_to_positions(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    args = [total_capital, exposure_fraction, asset_prices]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_route_exposure_to_positions__mutmut_orig, x_route_exposure_to_positions__mutmut_mutants, args, kwargs, None)


def x_route_exposure_to_positions__mutmut_orig(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    positions: dict[str, float] = allocate_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_fraction,
        asset_prices=asset_prices,
    )

    return positions


def x_route_exposure_to_positions__mutmut_1(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction < 0.0 and exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    positions: dict[str, float] = allocate_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_fraction,
        asset_prices=asset_prices,
    )

    return positions


def x_route_exposure_to_positions__mutmut_2(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction <= 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    positions: dict[str, float] = allocate_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_fraction,
        asset_prices=asset_prices,
    )

    return positions


def x_route_exposure_to_positions__mutmut_3(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction < 1.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    positions: dict[str, float] = allocate_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_fraction,
        asset_prices=asset_prices,
    )

    return positions


def x_route_exposure_to_positions__mutmut_4(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction < 0.0 or exposure_fraction >= 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    positions: dict[str, float] = allocate_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_fraction,
        asset_prices=asset_prices,
    )

    return positions


def x_route_exposure_to_positions__mutmut_5(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction < 0.0 or exposure_fraction > 2.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    positions: dict[str, float] = allocate_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_fraction,
        asset_prices=asset_prices,
    )

    return positions


def x_route_exposure_to_positions__mutmut_6(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            None
        )

    positions: dict[str, float] = allocate_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_fraction,
        asset_prices=asset_prices,
    )

    return positions


def x_route_exposure_to_positions__mutmut_7(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    positions: dict[str, float] = None

    return positions


def x_route_exposure_to_positions__mutmut_8(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    positions: dict[str, float] = allocate_positions(
        total_capital=None,
        exposure_fraction=exposure_fraction,
        asset_prices=asset_prices,
    )

    return positions


def x_route_exposure_to_positions__mutmut_9(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    positions: dict[str, float] = allocate_positions(
        total_capital=total_capital,
        exposure_fraction=None,
        asset_prices=asset_prices,
    )

    return positions


def x_route_exposure_to_positions__mutmut_10(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    positions: dict[str, float] = allocate_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_fraction,
        asset_prices=None,
    )

    return positions


def x_route_exposure_to_positions__mutmut_11(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    positions: dict[str, float] = allocate_positions(
        exposure_fraction=exposure_fraction,
        asset_prices=asset_prices,
    )

    return positions


def x_route_exposure_to_positions__mutmut_12(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    positions: dict[str, float] = allocate_positions(
        total_capital=total_capital,
        asset_prices=asset_prices,
    )

    return positions


def x_route_exposure_to_positions__mutmut_13(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Boundary adapter between risk exposure and portfolio allocation.

    Validates exposure_fraction, then delegates to
    jarvis.portfolio.allocate_positions. Does not reimplement
    allocation logic.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
        Validated downstream by allocate_positions.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0]. Validated here before delegation.
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.
        Validated downstream by allocate_positions.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Returned unchanged from allocate_positions.

    Raises
    ------
    ValueError
        If exposure_fraction < 0.0 or exposure_fraction > 1.0.
        If total_capital <= 0 (raised by allocate_positions).
        If asset_prices is empty (raised by allocate_positions).
        If any asset price <= 0 (raised by allocate_positions).

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    positions: dict[str, float] = allocate_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_fraction,
        )

    return positions

x_route_exposure_to_positions__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_route_exposure_to_positions__mutmut_1': x_route_exposure_to_positions__mutmut_1, 
    'x_route_exposure_to_positions__mutmut_2': x_route_exposure_to_positions__mutmut_2, 
    'x_route_exposure_to_positions__mutmut_3': x_route_exposure_to_positions__mutmut_3, 
    'x_route_exposure_to_positions__mutmut_4': x_route_exposure_to_positions__mutmut_4, 
    'x_route_exposure_to_positions__mutmut_5': x_route_exposure_to_positions__mutmut_5, 
    'x_route_exposure_to_positions__mutmut_6': x_route_exposure_to_positions__mutmut_6, 
    'x_route_exposure_to_positions__mutmut_7': x_route_exposure_to_positions__mutmut_7, 
    'x_route_exposure_to_positions__mutmut_8': x_route_exposure_to_positions__mutmut_8, 
    'x_route_exposure_to_positions__mutmut_9': x_route_exposure_to_positions__mutmut_9, 
    'x_route_exposure_to_positions__mutmut_10': x_route_exposure_to_positions__mutmut_10, 
    'x_route_exposure_to_positions__mutmut_11': x_route_exposure_to_positions__mutmut_11, 
    'x_route_exposure_to_positions__mutmut_12': x_route_exposure_to_positions__mutmut_12, 
    'x_route_exposure_to_positions__mutmut_13': x_route_exposure_to_positions__mutmut_13
}
x_route_exposure_to_positions__mutmut_orig.__name__ = 'x_route_exposure_to_positions'
