# jarvis/portfolio/portfolio_allocator.py
# Version: 1.0.0
# External portfolio allocation module.
# External to jarvis/core/ and jarvis/risk/ per FAS v6.1.0 architecture rules.
#
# DETERMINISM GUARANTEE:
#   No stochastic operations. No random number generation. No sampling.
#   No external state reads. No side effects. No file I/O. No logging.
#   No environment variable access. No global mutable state.
#   Output is a pure function of inputs.
#
# Standard import pattern:
#   from jarvis.portfolio.portfolio_allocator import allocate_positions


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
def allocate_positions(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    args = [total_capital, exposure_fraction, asset_prices]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_allocate_positions__mutmut_orig, x_allocate_positions__mutmut_mutants, args, kwargs, None)
def x_allocate_positions__mutmut_orig(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_1(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital < 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_2(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 1.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_3(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            None
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_4(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 and exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_5(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction <= 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_6(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 1.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_7(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction >= 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_8(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 2.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_9(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            None
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_10(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_11(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            None
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_12(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "XXasset_prices must be non-empty. Received an empty dict.XX"
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_13(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_14(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "ASSET_PRICES MUST BE NON-EMPTY. RECEIVED AN EMPTY DICT."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_15(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = None
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_16(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price < 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_17(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 1.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_18(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            None
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_19(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = None

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_20(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = None

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_21(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital / exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_22(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = None

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_23(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital * number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital / price
        for symbol, price in asset_prices.items()
    }

    return positions
def x_allocate_positions__mutmut_24(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = None

    return positions
def x_allocate_positions__mutmut_25(
    total_capital: float,
    exposure_fraction: float,
    asset_prices: dict[str, float],
) -> dict[str, float]:
    """
    Compute equal-weight position sizes for a set of assets.

    Parameters
    ----------
    total_capital : float
        Total portfolio capital available. Must be strictly positive.
    exposure_fraction : float
        Fraction of total_capital to allocate across all assets.
        Must be in [0.0, 1.0].
    asset_prices : dict[str, float]
        Mapping of asset symbol to current price.
        Must be non-empty. All prices must be strictly positive.

    Returns
    -------
    dict[str, float]
        Mapping of asset symbol to position size (number of units).
        Position size = equal_weight_capital / asset_price.
        When exposure_fraction is 0.0, all position sizes are 0.0.

    Raises
    ------
    ValueError
        If total_capital <= 0.
        If exposure_fraction < 0 or exposure_fraction > 1.
        If asset_prices is empty.
        If any asset price <= 0.

    Notes
    -----
    Deterministic. No side effects. No global state. Pure function.
    """
    # ------------------------------------------------------------------
    # Input validation.
    # ------------------------------------------------------------------
    if total_capital <= 0.0:
        raise ValueError(
            f"total_capital must be strictly positive. Received: {total_capital}"
        )

    if exposure_fraction < 0.0 or exposure_fraction > 1.0:
        raise ValueError(
            f"exposure_fraction must be in [0.0, 1.0]. Received: {exposure_fraction}"
        )

    if not asset_prices:
        raise ValueError(
            "asset_prices must be non-empty. Received an empty dict."
        )

    invalid_prices: list[str] = [
        symbol for symbol, price in asset_prices.items() if price <= 0.0
    ]
    if invalid_prices:
        raise ValueError(
            f"All asset prices must be strictly positive. "
            f"Non-positive prices found for: {invalid_prices}"
        )

    # ------------------------------------------------------------------
    # Computation.
    # ------------------------------------------------------------------
    number_of_assets: int = len(asset_prices)

    allocated_capital: float = total_capital * exposure_fraction

    equal_weight_capital: float = allocated_capital / number_of_assets

    positions: dict[str, float] = {
        symbol: equal_weight_capital * price
        for symbol, price in asset_prices.items()
    }

    return positions

x_allocate_positions__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_allocate_positions__mutmut_1': x_allocate_positions__mutmut_1, 
    'x_allocate_positions__mutmut_2': x_allocate_positions__mutmut_2, 
    'x_allocate_positions__mutmut_3': x_allocate_positions__mutmut_3, 
    'x_allocate_positions__mutmut_4': x_allocate_positions__mutmut_4, 
    'x_allocate_positions__mutmut_5': x_allocate_positions__mutmut_5, 
    'x_allocate_positions__mutmut_6': x_allocate_positions__mutmut_6, 
    'x_allocate_positions__mutmut_7': x_allocate_positions__mutmut_7, 
    'x_allocate_positions__mutmut_8': x_allocate_positions__mutmut_8, 
    'x_allocate_positions__mutmut_9': x_allocate_positions__mutmut_9, 
    'x_allocate_positions__mutmut_10': x_allocate_positions__mutmut_10, 
    'x_allocate_positions__mutmut_11': x_allocate_positions__mutmut_11, 
    'x_allocate_positions__mutmut_12': x_allocate_positions__mutmut_12, 
    'x_allocate_positions__mutmut_13': x_allocate_positions__mutmut_13, 
    'x_allocate_positions__mutmut_14': x_allocate_positions__mutmut_14, 
    'x_allocate_positions__mutmut_15': x_allocate_positions__mutmut_15, 
    'x_allocate_positions__mutmut_16': x_allocate_positions__mutmut_16, 
    'x_allocate_positions__mutmut_17': x_allocate_positions__mutmut_17, 
    'x_allocate_positions__mutmut_18': x_allocate_positions__mutmut_18, 
    'x_allocate_positions__mutmut_19': x_allocate_positions__mutmut_19, 
    'x_allocate_positions__mutmut_20': x_allocate_positions__mutmut_20, 
    'x_allocate_positions__mutmut_21': x_allocate_positions__mutmut_21, 
    'x_allocate_positions__mutmut_22': x_allocate_positions__mutmut_22, 
    'x_allocate_positions__mutmut_23': x_allocate_positions__mutmut_23, 
    'x_allocate_positions__mutmut_24': x_allocate_positions__mutmut_24, 
    'x_allocate_positions__mutmut_25': x_allocate_positions__mutmut_25
}
x_allocate_positions__mutmut_orig.__name__ = 'x_allocate_positions'
